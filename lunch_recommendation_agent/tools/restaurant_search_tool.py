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

# Get Google Maps API key from environment variables
API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Constants
DEFAULT_RADIUS = 1000  # デフォルト検索半径（メートル）
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
        検索半径（メートル）
    """
    # 食事時間の割り当て（通常30〜40分）
    eating_time = min(40, break_time_minutes * 0.7)
    
    # 残りは移動時間（往復）
    travel_time_one_way = (break_time_minutes - eating_time) / 2
    
    # 移動時間を距離に変換
    max_distance = travel_time_one_way * 60 * WALKING_SPEED
    
    # 適切な範囲に制限
    radius = min(2000, max(500, math.floor(max_distance)))
    
    return radius

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
        print("Google Maps APIキーが設定されていません")
        return {
            "error": "Google Maps APIキーが設定されていません",
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
    
    # Google Places API検索パラメータ
    url = (
        "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        f"?location={location.get('latitude')},{location.get('longitude')}"
        f"&radius={search_radius}"
        f"&type=restaurant&language=ja&key={API_KEY}&opennow=true"
    )
    
    # 料理の種類が指定されていれば追加
    if cuisine_preference:
        url += f"&keyword={cuisine_preference}"
    
    # 価格帯が指定されていれば追加
    if price_level is not None:
        url += f"&maxprice={min(4, max(0, price_level))}"
    
    print(f"レストラン検索URL: {url}")
    print("Google Places APIでレストランを検索中...")
    
    try:
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"APIリクエスト失敗: ステータスコード {response.status_code}")
            return fallback_restaurant_data(location, search_radius, tool_context)
        
        # レスポンスをJSONに変換
        data = response.json()
        
        # APIステータスをチェック
        if data.get("status") != "OK":
            error_msg = data.get("error_message", "エラーメッセージなし")
            print(f"APIエラー: {data.get('status')}, {error_msg}")
            return fallback_restaurant_data(location, search_radius, tool_context)
        
        # 検索結果を処理
        restaurants = []
        for place in data.get("results", []):
            # 場所の座標を取得
            place_lat = place["geometry"]["location"]["lat"]
            place_lng = place["geometry"]["location"]["lng"]
            
            # 直線距離を計算（ハーバサイン公式）
            lat1, lon1 = map(math.radians, [location.get('latitude'), location.get('longitude')])
            lat2, lon2 = map(math.radians, [place_lat, place_lng])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            distance = c * 6371000  # 地球の半径（メートル）
            
            # 所要時間を推定
            travel_time = estimate_travel_time(distance)
            
            # レストラン情報を構築
            restaurant = {
                "name": place.get("name", "名前なし"),
                "address": place.get("vicinity", "住所不明"),
                "rating": place.get("rating", "評価なし"),
                "user_ratings_total": place.get("user_ratings_total", 0),
                "price_level": place.get("price_level", "不明"),
                "distance_meters": round(distance),
                "estimated_travel_time_minutes": travel_time,
                "place_id": place.get("place_id", ""),
                "maps_url": f"https://www.google.com/maps/place/?q=place_id:{place.get('place_id')}"
            }
            
            restaurants.append(restaurant)
            print(f"🍴 {restaurant['name']} ({restaurant['rating']}): {restaurant['address']} - 徒歩{travel_time}分")
        
        # レストランを評価（70%）と距離（30%）で並べ替え
        restaurants.sort(key=lambda x: (
            -(float(x["rating"]) if isinstance(x["rating"], (int, float)) else 0) * 0.7 +
            x["estimated_travel_time_minutes"] * 0.3
        ))
        
        # 結果を10件に制限
        restaurants = restaurants[:10]
        
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
                "radius_meters": search_radius,
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
            "rating": 4.5,
            "user_ratings_total": 1245,
            "price_level": 3,
            "distance_meters": round(random.uniform(200, 800)),
            "cuisine_type": "もつ鍋",
            "description": "福岡名物のもつ鍋が楽しめる人気店。特製のスープと新鮮なもつが絶品。"
        },
        {
            "name": "一蘭 天神店",
            "address": "福岡県福岡市中央区天神3-2-13",
            "rating": 4.3,
            "user_ratings_total": 2156,
            "price_level": 2,
            "distance_meters": round(random.uniform(300, 900)),
            "cuisine_type": "ラーメン",
            "description": "豚骨ラーメンで有名な福岡を代表する人気チェーン。個室型の席が特徴。"
        },
        {
            "name": "鮨処 銀座 福榮 福岡店",
            "address": "福岡県福岡市中央区大名1-15-11",
            "rating": 4.7,
            "user_ratings_total": 876,
            "price_level": 4,
            "distance_meters": round(random.uniform(400, 1000)),
            "cuisine_type": "寿司",
            "description": "厳選された新鮮な海の幸を使った高級寿司店。職人の技が光る。"
        },
        {
            "name": "焼鳥 笑まる 博多駅前店",
            "address": "福岡県福岡市博多区博多駅前3-21-12",
            "rating": 4.4,
            "user_ratings_total": 1123,
            "price_level": 3,
            "distance_meters": round(random.uniform(500, 1100)),
            "cuisine_type": "焼鳥",
            "description": "素材にこだわった炭火焼の焼鳥が人気。店内は活気があり、博多の雰囲気が楽しめる。"
        },
        {
            "name": "水炊き 博多華味鳥 中洲本店",
            "address": "福岡県福岡市博多区中洲5-4-6",
            "rating": 4.6,
            "user_ratings_total": 1532,
            "price_level": 3,
            "distance_meters": round(random.uniform(600, 1200)),
            "cuisine_type": "水炊き",
            "description": "福岡名物の水炊きを提供する名店。特製の白濁スープと鶏肉の旨みが絶品。"
        },
        {
            "name": "ひょうたん寿司 福岡本店",
            "address": "福岡県福岡市中央区天神2-13-18",
            "rating": 4.2,
            "user_ratings_total": 987,
            "price_level": 3,
            "distance_meters": round(random.uniform(300, 850)),
            "cuisine_type": "寿司",
            "description": "地元で人気の寿司店。リーズナブルな価格で本格的な寿司が楽しめる。"
        },
        {
            "name": "博多 十和蔵",
            "address": "福岡県福岡市博多区中洲3-7-14",
            "rating": 4.3,
            "user_ratings_total": 756,
            "price_level": 3,
            "distance_meters": round(random.uniform(700, 1300)),
            "cuisine_type": "居酒屋",
            "description": "新鮮な魚介類と豊富な日本酒が楽しめる居酒屋。地元の食材を生かした料理が豊富。"
        },
        {
            "name": "博多 一風堂 本店",
            "address": "福岡県福岡市中央区薬院1-1-12",
            "rating": 4.4,
            "user_ratings_total": 1876,
            "price_level": 2,
            "distance_meters": round(random.uniform(800, 1400)),
            "cuisine_type": "ラーメン",
            "description": "世界的に有名な博多ラーメン店。独自のスープと太さの異なる麺が選べる。"
        },
        {
            "name": "たつみ寿司 天神店",
            "address": "福岡県福岡市中央区今泉1-9-12",
            "rating": 4.1,
            "user_ratings_total": 654,
            "price_level": 2,
            "distance_meters": round(random.uniform(400, 950)),
            "cuisine_type": "寿司",
            "description": "ランチタイムのにぎり寿司セットがリーズナブルで人気。アットホームな雰囲気が特徴。"
        },
        {
            "name": "やま中 天神本店",
            "address": "福岡県福岡市中央区大名1-11-25",
            "rating": 4.5,
            "user_ratings_total": 1023,
            "price_level": 3,
            "distance_meters": round(random.uniform(500, 1050)),
            "cuisine_type": "うどん",
            "description": "コシのある手打ちうどんが評判。季節の食材を使ったメニューも豊富で、地元民に愛されている。"
        }
    ]
    
    # 各レストランに推定所要時間を追加
    for restaurant in sample_restaurants:
        travel_time = estimate_travel_time(restaurant["distance_meters"])
        restaurant["estimated_travel_time_minutes"] = travel_time
        restaurant["place_id"] = f"sample_{hash(restaurant['name']) % 10000}"
        restaurant["maps_url"] = f"https://www.google.com/maps/search/?api=1&query={restaurant['name']} {restaurant['address']}"
        print(f"🍴 {restaurant['name']} ({restaurant['rating']}): {restaurant['address']} - 徒歩{travel_time}分")
    
    # レストランを評価（70%）と距離（30%）で並べ替え
    sample_restaurants.sort(key=lambda x: (
        -(float(x["rating"]) if isinstance(x["rating"], (int, float)) else 0) * 0.7 +
        x["estimated_travel_time_minutes"] * 0.3
    ))
    
    # 検索結果をコンテキストに保存
    if tool_context:
        tool_context.state['restaurant_results'] = sample_restaurants
    
    # 検索結果と使用したパラメータを返す
    return {
        "notice": "Google Places APIのエラーのため、サンプルデータを使用しています。",
        "restaurants": sample_restaurants,
        "search_parameters": {
            "location": f"{location.get('city', '福岡市')}, {location.get('region', '福岡県')}",
            "latitude": location.get('latitude'),
            "longitude": location.get('longitude'),
            "radius_meters": search_radius,
            "using_sample_data": True
        }
    }
