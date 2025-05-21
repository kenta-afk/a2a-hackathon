"""Location tool for getting current location information."""

import os
import json
import requests
from typing import Optional
from dotenv import load_dotenv
from google.adk.tools.tool_context import ToolContext

# Load environment variables
load_dotenv()

# Get API keys from environment variables
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
IPINFO_TOKEN = os.getenv('IPINFO_TOKEN')

def get_current_location(address: Optional[str] = None, city: Optional[str] = None, region: Optional[str] = None, tool_context: Optional[ToolContext] = None) -> dict:
    """
    Get the current location information using IP geolocation or specified location.
    
    Args:
        address: 完全な住所（指定された場合はGoogle Mapsで変換）
        city: 都市名（addressが指定されていない場合に使用）
        region: 地域名（addressが指定されていない場合に使用）
        tool_context: ツールコンテキスト
    
    Returns:
        dict: A dictionary containing location information including:
            - latitude
            - longitude
            - city
            - region
            - country
    """
    # デフォルト値（API呼び出しが失敗した場合のフォールバック）
    default_location = {
        "latitude": 33.5902,  # 福岡市の座標
        "longitude": 130.4017,
        "city": "福岡市",
        "region": "福岡県",
        "country": "日本"
    }
    
    # 日本語への変換マッピング
    city_mapping = {
        "Tokyo": "東京",
        "Fukuoka": "福岡市",
        "Osaka": "大阪市",
        "Kyoto": "京都市",
        "Sapporo": "札幌市",
        "Nagoya": "名古屋市",
        "Yokohama": "横浜市"
    }
    
    region_mapping = {
        "Tokyo": "東京都",
        "Fukuoka": "福岡県",
        "Osaka": "大阪府",
        "Kyoto": "京都府",
        "Hokkaido": "北海道",
        "Aichi": "愛知県",
        "Kanagawa": "神奈川県"
    }
    
    try:
        # 完全な住所が指定されている場合
        if address:
            print(f"指定された住所を使用します: {address}")
            if GOOGLE_MAPS_API_KEY:
                # Google Maps Geocoding APIを使用して住所を座標に変換
                print(f"Google Maps Geocoding APIを使用して位置情報を取得中...")
                geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_MAPS_API_KEY}&language=ja"
                geocode_response = requests.get(geocode_url)
                
                if geocode_response.status_code == 200:
                    geocode_data = geocode_response.json()
                    
                    if geocode_data.get("status") == "OK" and geocode_data.get("results"):
                        result = geocode_data["results"][0]
                        
                        # 座標情報を取得
                        location = result.get("geometry", {}).get("location", {})
                        latitude = location.get("lat")
                        longitude = location.get("lng")
                        
                        # 住所情報を解析
                        city = ""
                        region = ""
                        country = ""
                        
                        for component in result.get("address_components", []):
                            types = component.get("types", [])
                            if "locality" in types:
                                city = component.get("long_name", "")
                            elif "administrative_area_level_1" in types:
                                region = component.get("long_name", "")
                            elif "country" in types:
                                country = component.get("long_name", "")
                        
                        location_info = {
                            "latitude": latitude,
                            "longitude": longitude,
                            "city": city,
                            "region": region,
                            "country": country
                        }
                        
                        print(f"Google Mapsから位置情報を取得しました: {city}, {region}, {country}")
                        
                        # Store the location in tool context
                        if tool_context:
                            tool_context.state['current_location'] = location_info
                        
                        return location_info
                    else:
                        print(f"Geocoding API結果エラー: {geocode_data.get('status')}")
                else:
                    print(f"Geocoding APIエラー: {geocode_response.status_code}")
            else:
                print("Google Maps APIキーが設定されていません")
                
        # 都市と地域が指定されている場合
        elif city and region:
            print(f"指定された都市と地域を使用します: {city}, {region}")
            
            # 主要都市の座標マッピング
            city_coordinates = {
                "福岡市": (33.5902, 130.4017),
                "東京": (35.6762, 139.6503),
                "大阪市": (34.6937, 135.5022),
                "京都市": (35.0116, 135.7681),
                "札幌市": (43.0618, 141.3545),
                "名古屋市": (35.1815, 136.9066),
                "横浜市": (35.4437, 139.6380)
            }
            
            # 都市の座標を取得（マッピングにない場合は福岡の座標をデフォルトとする）
            lat, lon = city_coordinates.get(city, (33.5902, 130.4017))
            
            location_info = {
                "latitude": lat,
                "longitude": lon,
                "city": city,
                "region": region,
                "country": "日本"
            }
            
            # Store the location in tool context
            if tool_context:
                tool_context.state['current_location'] = location_info
            
            return location_info
        
        # IPInfoを使って現在地を取得
        else:
            print("IPInfo.ioを使用して位置情報を取得中...")
            
            if IPINFO_TOKEN:
                ipinfo_response = requests.get(f"https://ipinfo.io/json", 
                                             headers={"Authorization": f"Bearer {IPINFO_TOKEN}"})
                
                if ipinfo_response.status_code == 200:
                    ipinfo_data = ipinfo_response.json()
                    print(f"取得した位置情報データ: {ipinfo_data}")
                    
                    # 緯度・経度の分解
                    lat_lng = ipinfo_data.get('loc', '').split(',')
                    if len(lat_lng) == 2:
                        latitude = float(lat_lng[0])
                        longitude = float(lat_lng[1])
                    else:
                        latitude = default_location["latitude"]
                        longitude = default_location["longitude"]
                    
                    # 都市名の日本語変換
                    city_name = ipinfo_data.get('city', '')
                    city = city_mapping.get(city_name, city_name)
                    
                    # 地域名の日本語変換
                    region_name = ipinfo_data.get('region', '')
                    region = region_mapping.get(region_name, region_name)
                    
                    # 国名の変換
                    country = "日本" if ipinfo_data.get("country") == "JP" else ipinfo_data.get("country", "")
                    
                    location_info = {
                        "latitude": latitude,
                        "longitude": longitude,
                        "city": city,
                        "region": region,
                        "country": country
                    }
                    
                    print(f"IPInfo.ioから位置情報を取得しました: {city}, {region}, {country}")
                else:
                    print(f"IPInfo.io APIエラー: {ipinfo_response.status_code}")
                    location_info = default_location
            else:
                print("IPInfo.ioのトークンが設定されていません")
                location_info = default_location
    except Exception as e:
        print(f"位置情報の取得中にエラーが発生しました: {str(e)}")
        location_info = default_location
    
    # Store the location in tool context for other tools to use
    if tool_context:
        tool_context.state['current_location'] = location_info
    
    print(f"位置情報を取得しました: {location_info['city']}, {location_info['region']}")
    return location_info
