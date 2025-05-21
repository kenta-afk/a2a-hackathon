"""
Google Calendar events debug script
This module helps diagnose and confirm the correct Google ADK usage.
"""

import os
import asyncio
# from dotenv import load_dotenv

# ADKのインポート方法を確認するための複数のオプション
try:
    print("インポート方法のデバッグを開始します...")
    # 方法1: 直接インポート
    try:
        import adk
        print("✅ 'import adk' が成功しました")
        ADK_IMPORT = 'direct'
    except ImportError as e:
        print(f"❌ 'import adk' は失敗しました: {e}")
        
    # 方法2: googleパッケージからインポート
    try:
        from google import adk
        print("✅ 'from google import adk' が成功しました")
        ADK_IMPORT = 'from_google'
    except ImportError as e:
        print(f"❌ 'from google import adk' は失敗しました: {e}")
        
    # 方法3: google_adkからインポート
    try:
        import google_adk
        print("✅ 'import google_adk' が成功しました")
        ADK_IMPORT = 'google_adk'
    except ImportError as e:
        print(f"❌ 'import google_adk' は失敗しました: {e}")
        
except Exception as e:
    print(f"インポートデバッグ中にエラーが発生しました: {e}")

async def debug_calendar():
    """Google ADKの正しい使用方法をデバッグします"""
    print("\n📅 Google Calendar ADKのデバッグを開始します...")
    
    # 環境変数のロード
    # load_dotenv()
    client_id = os.environ.get("CLIENT_ID")
    
    if not client_id:
        print("❌ .env ファイルにCLIENT_IDが設定されていません")
        return
    
    print(f"✅ CLIENT_IDを読み込みました: {client_id[:5]}...")
    
    # ADKの初期化（成功したインポート方法に基づく）
    print("\n🔑 ADK初期化を試みます...")
    try:
        if 'ADK_IMPORT' not in globals():
            print("❌ ADKのインポートに成功していません")
            return
            
        if ADK_IMPORT == 'direct':
            print("🔍 'import adk' を使用してADKを初期化します")
            toolkit = adk.init(client_id=client_id)
        elif ADK_IMPORT == 'from_google':
            print("🔍 'from google import adk' を使用してADKを初期化します")
            toolkit = adk.init(client_id=client_id)
        elif ADK_IMPORT == 'google_adk':
            print("🔍 'import google_adk' を使用してADKを初期化します")
            toolkit = google_adk.init(client_id=client_id)
            
        print("✅ ADKの初期化に成功しました")
            
        # カレンダーサービスの取得
        print("\n🔄 カレンダーサービスの取得を試みます...")
        calendar = await toolkit.get_calendar()
        print("✅ カレンダーサービスの取得に成功しました")
        
        # 今日の日付のイベントを取得
        print("\n📋 本日のイベント取得を試みます...")
        today = "2025-05-21"
        events = await calendar.events.list(
            calendar_id='primary',
            time_min=f"{today}T00:00:00Z",
            time_max=f"{today}T23:59:59Z",
            single_events=True,
            order_by='startTime'
        )
        
        print(f"✅ イベント取得に成功しました: {type(events)}")
        print(f"📊 イベントデータ構造: {events.__class__.__name__}")
        
        if hasattr(events, 'items'):
            print(f"📄 イベント数: {len(events.items)}")
        elif isinstance(events, list):
            print(f"📄 イベント数: {len(events)}")
        elif isinstance(events, dict) and 'items' in events:
            print(f"📄 イベント数: {len(events['items'])}")
        else:
            print(f"⚠️ 予期しないイベントデータ形式: {events}")
        
    except Exception as e:
        print(f"❌ ADKデバッグ中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 Google ADK Calendar デバッグツール 🔍")
    asyncio.run(debug_calendar())
