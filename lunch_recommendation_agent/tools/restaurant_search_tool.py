"""Restaurant search tool for finding restaurants near the current location."""

import os
import math
import random
import requests
from dotenv import load_dotenv
from google.adk.tools.tool_context import ToolContext
from typing import Optional, Dict, List, Any

# Load environment variables
load_dotenv()

# Get Hotpepper API key from environment variables
API_KEY = os.getenv('HOTPEPPER_API_KEY')

# Constants
DEFAULT_RADIUS = 3  # デフォルト検索半径（3=1000m）
WALKING_SPEED = 1.4  # 平均歩行速度（メートル/秒）

def estimate_travel_time(distance_meters: float) -> int:
    """
    歩行距離から所要時間を推定する
    
    Args:
        distance_meters: 距離（メートル）
        
    Returns:
        推定所要時間（分）
    """
    # 分単位の歩行時間を計算
    walking_time_minutes = (distance_meters / WALKING_SPEED) / 60
    
    # 信号や待ち時間のバッファを追加
    buffer_time = min(5, walking_time_minutes * 0.15)
    
    return math.ceil(walking_time_minutes + buffer_time)

def calculate_search_radius(break_time_minutes: int) -> int:
    """
    休憩時間に基づいて適切な検索半径を計算
    
    Args:
        break_time_minutes: 利用可能な休憩時間（分）
        
    Returns:
        検索半径（1-5の整数値）
    """
    # 食事時間の割り当て（通常30〜40分）
    eating_time = min(40, break_time_minutes * 0.7)
    
    # 残りは移動時間（往復）
    travel_time_one_way = (break_time_minutes - eating_time) / 2
    
    # 移動時間を距離に変換
    max_distance = travel_time_one_way * 60 * WALKING_SPEED
    
    # 適切な範囲に対応するHotpepper API検索範囲コードを返す
    # 1=300m、2=500m、3=1000m、4=2000m、5=3000m
    if max_distance <= 300:
        return 1
    elif max_distance <= 500:
        return 2
    elif max_distance <= 1000:
        return 3
    elif max_distance <= 2000:
        return 4
    else:
        return 5

def find_restaurants(cuisine_preference: Optional[str] = None, price_level: Optional[int] = None, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    現在地周辺のレストランを検索
    
    Args:
        cuisine_preference: 料理の種類（例: "日本食", "イタリアン"）
        price_level: 価格帯（0-4、0=無料、4=高級）
        tool_context: 前回のツール呼び出しから状態を保持するコンテキスト
        
    Returns:
        dict: 検索結果を含む辞書:
            - restaurants: レストランのリスト
            - search_parameters: 検索に使用されたパラメータ
    """
    if not API_KEY:
        print("Hotpepper APIキーが設定されていません")
        return {
            "error": "Hotpepper APIキーが設定されていません",
            "restaurants": [],
            "search_parameters": {}
        }
    
    # コンテキストから位置情報を取得、なければデフォルト値を使用
    location = {}
    if tool_context and 'current_location' in tool_context.state:
        location = tool_context.state['current_location']
    
    # 位置情報がない場合はデフォルト値を使用
    if not location or not location.get('latitude') or not location.get('longitude'):
        # デフォルトは福岡の座標
        location = {
            "latitude": 33.5902,
            "longitude": 130.4017,
            "city": "福岡市",
            "region": "福岡県"
        }
    
    # コンテキストから休憩時間の予測を取得
    break_prediction = {}
    if tool_context and 'break_prediction' in tool_context.state:
        break_prediction = tool_context.state['break_prediction']
    
    # 休憩時間に基づいて検索半径を決定、なければデフォルト値
    if break_prediction and 'duration_minutes' in break_prediction:
        search_radius = calculate_search_radius(break_prediction['duration_minutes'])
    else:
        search_radius = DEFAULT_RADIUS
    
    # Hotpepper API検索パラメータ
    url = "https://webservice.recruit.co.jp/hotpepper/gourmet/v1/"
    
    params = {
        "key": API_KEY,
        "lat": location.get('latitude'),
        "lng": location.get('longitude'),
        "range": search_radius,  # 検索範囲：1〜5（1=300m、2=500m、3=1000m、4=2000m、5=3000m）
        "order": 4,  # 評価順（1=標準、4=おすすめ順）
        "count": 10,  # 最大件数
        "format": "json"
    }
    
    # 料理の種類が指定されていれば追加
    if cuisine_preference:
        params["keyword"] = cuisine_preference
    
    # 予算コードの変換（Google APIの価格帯からHotpepper APIの予算コードへ）
    budget_map = {
        0: "B001",  # 無料 -> ~500円
        1: "B002,B003",  # 格安 -> 501〜1500円
        2: "B004,B005",  # 手頃 -> 1501〜3000円
        3: "B006,B007,B008",  # やや高級 -> 3001〜7000円
        4: "B009,B010,B011,B012,B013"  # 高級 -> 7001円以上
    }
    
    # 価格帯が指定されていれば追加
    if price_level is not None and price_level in budget_map:
        params["budget"] = budget_map[price_level]
    
    print(f"レストラン検索パラメータ: {params}")
    print("Hotpepper APIでレストランを検索中...")
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            print(f"APIリクエスト失敗: ステータスコード {response.status_code}")
            return fallback_restaurant_data(location, search_radius, tool_context)
        
        # レスポンスをJSONに変換
        data = response.json()
        
        # 検索結果を処理
        results = data.get("results", {})
        shops = results.get("shop", [])
        
        if not shops:
            print("検索結果が見つかりませんでした")
            return fallback_restaurant_data(location, search_radius, tool_context)
        
        restaurants = []
        for shop in shops:
            # 店舗の座標を取得
            shop_lat = float(shop["lat"])
            shop_lng = float(shop["lng"])
            
            # 直線距離を計算（ハーバサイン公式）
            lat1, lon1 = map(math.radians, [location.get('latitude'), location.get('longitude')])
            lat2, lon2 = map(math.radians, [shop_lat, shop_lng])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            distance = c * 6371000  # 地球の半径（メートル）
            
            # 所要時間を推定
            travel_time = estimate_travel_time(distance)
            
            # レストラン情報を構築
            restaurant = {
                "name": shop.get("name", "名前なし"),
                "address": shop.get("address", "住所不明"),
                "catch": shop.get("catch", ""),
                "genre": shop.get("genre", {}).get("name", ""),
                "budget": shop.get("budget", {}).get("average", "予算情報なし"),
                "distance_meters": round(distance),
                "estimated_travel_time_minutes": travel_time,
                "shop_id": shop.get("id", ""),
                "photo": shop.get("photo", {}).get("pc", {}).get("l", ""),
                "urls": shop.get("urls", {}).get("pc", ""),
                "open": shop.get("open", "営業時間情報なし"),
                "close": shop.get("close", ""),
                "maps_url": f"https://www.google.com/maps/search/?api=1&query={shop.get('name')} {shop.get('address')}"
            }
            
            restaurants.append(restaurant)
            print(f"🍴 {restaurant['name']} ({restaurant['genre']}): {restaurant['address']} - 徒歩{travel_time}分")
        
        # レストランを距離で並べ替え
        restaurants.sort(key=lambda x: x["estimated_travel_time_minutes"])
        
        # 検索結果をコンテキストに保存
        if tool_context:
            tool_context.state['restaurant_results'] = restaurants
        
        # 検索結果と使用したパラメータを返す
        result = {
            "restaurants": restaurants,
            "search_parameters": {
                "location": f"{location.get('city', '不明')}, {location.get('region', '不明')}",
                "latitude": location.get('latitude'),
                "longitude": location.get('longitude'),
                "range": search_radius,
                "cuisine_preference": cuisine_preference,
                "price_level": price_level
            }
        }
        
        return result
        
    except Exception as e:
        print(f"レストラン検索中にエラーが発生しました: {str(e)}")
        return fallback_restaurant_data(location, search_radius, tool_context)

def fallback_restaurant_data(location, search_radius, tool_context=None):
    """APIが失敗した場合のフォールバックとしてサンプルレストランデータを生成する"""
    print("APIエラーのためサンプルデータを使用します")
    
    # 福岡市のサンプルレストラン（APIが使えない場合のフォールバック）
    sample_restaurants = [
        {
            "name": "博多もつ鍋 やまや 天神店",
            "address": "福岡県福岡市中央区天神2-8-221",
            "catch": "博多名物もつ鍋と明太子の美味しいお店",
            "genre": "もつ鍋",
            "budget": "3000円～4000円",
            "distance_meters": 450,
            "estimated_travel_time_minutes": 6,
            "shop_id": "sample_1",
            "photo": "https://imgfp.hotp.jp/IMGH/61/98/P038366198_238.jpg",
            "urls": "https://www.hotpepper.jp/strJ000989092/",
            "open": "月～日 11:30～翌0:00",
            "close": "不定休（要確認）",
            "maps_url": "https://www.google.com/maps/search/?api=1&query=博多もつ鍋 やまや 天神店 福岡県福岡市中央区天神2-8-221"
        },
        {
            "name": "一蘭 天神店",
            "address": "福岡県福岡市中央区天神3-2-13",
            "catch": "一蘭特製「天然とんこつラーメン」",
            "genre": "ラーメン",
            "budget": "1000円～1500円",
            "distance_meters": 520,
            "estimated_travel_time_minutes": 7,
            "shop_id": "sample_2",
            "photo": "https://imgfp.hotp.jp/IMGH/21/04/P038072104_238.jpg",
            "urls": "https://www.hotpepper.jp/strJ000010292/",
            "open": "24時間営業",
            "close": "年中無休",
            "maps_url": "https://www.google.com/maps/search/?api=1&query=一蘭 天神店 福岡県福岡市中央区天神3-2-13"
        },
        {
            "name": "鮨処 銀座 福榮 福岡店",
            "address": "福岡県福岡市中央区大名1-15-11",
            "catch": "厳選食材の江戸前鮨を楽しむ",
            "genre": "寿司",
            "budget": "5000円～10000円",
            "distance_meters": 680,
            "estimated_travel_time_minutes": 10,
            "shop_id": "sample_3",
            "photo": "https://imgfp.hotp.jp/IMGH/58/27/P038715827_238.jpg",
            "urls": "https://www.hotpepper.jp/strJ001214309/",
            "open": "11:30～14:00 17:00～23:00",
            "close": "月曜日（祝日の場合は翌日）",
            "maps_url": "https://www.google.com/maps/search/?api=1&query=鮨処 銀座 福榮 福岡店 福岡県福岡市中央区大名1-15-11"
        },
        {
            "name": "焼鳥 笑まる 博多駅前店",
            "address": "福岡県福岡市博多区博多駅前3-21-12",
            "catch": "名物！炭火焼きの極上焼き鳥",
            "genre": "焼鳥",
            "budget": "3000円～4000円",
            "distance_meters": 750,
            "estimated_travel_time_minutes": 11,
            "shop_id": "sample_4",
            "photo": "https://imgfp.hotp.jp/IMGH/24/43/P037512443_238.jpg",
            "urls": "https://www.hotpepper.jp/strJ001234567/",
            "open": "17:00～翌0:00",
            "close": "日曜日",
            "maps_url": "https://www.google.com/maps/search/?api=1&query=焼鳥 笑まる 博多駅前店 福岡県福岡市博多区博多駅前3-21-12"
        },
        {
            "name": "水炊き 博多華味鳥 中洲本店",
            "address": "福岡県福岡市博多区中洲5-4-6",
            "catch": "厳選された九州の水炊き料理専門店",
            "genre": "水炊き",
            "budget": "4000円～6000円",
            "distance_meters": 850,
            "estimated_travel_time_minutes": 13,
            "shop_id": "sample_5",
            "photo": "https://imgfp.hotp.jp/IMGH/86/35/P038318635_238.jpg",
            "urls": "https://www.hotpepper.jp/strJ000974235/",
            "open": "11:00～15:00 17:00～23:00",
            "close": "不定休",
            "maps_url": "https://www.google.com/maps/search/?api=1&query=水炊き 博多華味鳥 中洲本店 福岡県福岡市博多区中洲5-4-6"
        },
        {
            "name": "ひょうたん寿司 福岡本店",
            "address": "福岡県福岡市中央区天神2-13-18",
            "catch": "本格寿司をリーズナブルに楽しめる",
            "genre": "寿司",
            "budget": "2000円～3000円",
            "distance_meters": 480,
            "estimated_travel_time_minutes": 7,
            "shop_id": "sample_6",
            "photo": "https://imgfp.hotp.jp/IMGH/67/84/P037406784_238.jpg",
            "urls": "https://www.hotpepper.jp/strJ000974631/",
            "open": "11:00～22:30",
            "close": "年中無休",
            "maps_url": "https://www.google.com/maps/search/?api=1&query=ひょうたん寿司 福岡本店 福岡県福岡市中央区天神2-13-18"
        },
        {
            "name": "博多 十和蔵",
            "address": "福岡県福岡市博多区中洲3-7-14",
            "catch": "博多の新鮮な海鮮と地酒を満喫",
            "genre": "居酒屋",
            "budget": "4000円～5000円",
            "distance_meters": 920,
            "estimated_travel_time_minutes": 14,
            "shop_id": "sample_7",
            "photo": "https://imgfp.hotp.jp/IMGH/55/04/P038595504_238.jpg",
            "urls": "https://www.hotpepper.jp/strJ000974512/",
            "open": "17:00～翌1:00",
            "close": "月曜日",
            "maps_url": "https://www.google.com/maps/search/?api=1&query=博多 十和蔵 福岡県福岡市博多区中洲3-7-14"
        },
        {
            "name": "博多 一風堂 本店",
            "address": "福岡県福岡市中央区薬院1-1-12",
            "catch": "世界に誇る博多豚骨ラーメン",
            "genre": "ラーメン",
            "budget": "1000円～1500円",
            "distance_meters": 1200,
            "estimated_travel_time_minutes": 18,
            "shop_id": "sample_8",
            "photo": "https://imgfp.hotp.jp/IMGH/70/98/P037407098_238.jpg",
            "urls": "https://www.hotpepper.jp/strJ000010007/",
            "open": "11:00～翌3:00",
            "close": "年中無休",
            "maps_url": "https://www.google.com/maps/search/?api=1&query=博多 一風堂 本店 福岡県福岡市中央区薬院1-1-12"
        },
        {
            "name": "たつみ寿司 天神店",
            "address": "福岡県福岡市中央区今泉1-9-12",
            "catch": "ランチ人気のリーズナブル寿司",
            "genre": "寿司",
            "budget": "1500円～2000円",
            "distance_meters": 580,
            "estimated_travel_time_minutes": 8,
            "shop_id": "sample_9",
            "photo": "https://imgfp.hotp.jp/IMGH/93/46/P038619346_238.jpg",
            "urls": "https://www.hotpepper.jp/strJ000974358/",
            "open": "11:30～22:00",
            "close": "水曜日",
            "maps_url": "https://www.google.com/maps/search/?api=1&query=たつみ寿司 天神店 福岡県福岡市中央区今泉1-9-12"
        },
        {
            "name": "やま中 天神本店",
            "address": "福岡県福岡市中央区大名1-11-25",
            "catch": "博多の名物出汁うどん",
            "genre": "うどん",
            "budget": "1000円～1500円",
            "distance_meters": 620,
            "estimated_travel_time_minutes": 9,
            "shop_id": "sample_10",
            "photo": "https://imgfp.hotp.jp/IMGH/65/98/P038426598_238.jpg",
            "urls": "https://www.hotpepper.jp/strJ000974159/",
            "open": "11:00～22:00",
            "close": "年中無休",
            "maps_url": "https://www.google.com/maps/search/?api=1&query=やま中 天神本店 福岡県福岡市中央区大名1-11-25"
        }
    ]
    
    # レストランをすでに所要時間を含んでいるので、改めて出力
    for restaurant in sample_restaurants:
        travel_time = restaurant["estimated_travel_time_minutes"]
        print(f"🍴 {restaurant['name']} ({restaurant['genre']}): {restaurant['address']} - 徒歩{travel_time}分")
    
    # レストランを距離で並べ替え
    sample_restaurants.sort(key=lambda x: x["estimated_travel_time_minutes"])
    
    # 検索結果をコンテキストに保存
    if tool_context:
        tool_context.state['restaurant_results'] = sample_restaurants
    
    # 検索結果と使用したパラメータを返す
    return {
        "notice": "Hotpepper APIのエラーのため、サンプルデータを使用しています。",
        "restaurants": sample_restaurants,
        "search_parameters": {
            "location": f"{location.get('city', '福岡市')}, {location.get('region', '福岡県')}",
            "latitude": location.get('latitude'),
            "longitude": location.get('longitude'),
            "range": search_radius,
            "using_sample_data": True
        }
    }
