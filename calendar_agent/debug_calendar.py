"""
Google Calendar events debug script
このモジュールはGoogle ADKの正しい使用方法を確認・テストするためのものです。
"""

import os
import asyncio
from dotenv import load_dotenv

# ADKのインポート方法のデバッグ
try:
    print("インポート方法のデバッグを開始します...")
    # 方法1: 直接インポート
    try:
        import google.adk as adk
        print("✅ 'import google.adk as adk' が成功しました")
        ADK_IMPORT = 'google.adk'
    except ImportError as e:
        print(f"❌ 'import google.adk' は失敗しました: {e}")
        
    # 方法2: google_adkからインポート
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
    load_dotenv()
    client_id = os.environ.get("GOOGLE_API_KEY")
    
    if not client_id:
        print("❌ .env ファイルにCLIENT_IDが設定されていません")
        return
    
    print(f"✅ CLIENT_IDを読み込みました: {client_id[:5]}...")
    
    # API Keyを確認
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ .env ファイルにGOOGLE_API_KEYが設定されていません")
    else:
        print(f"✅ GOOGLE_API_KEYを読み込みました: {api_key[:5]}...")
    
    # ADKの初期化（成功したインポート方法に基づく）
    print("\n🔑 ADK初期化を試みます...")
    try:
        if 'ADK_IMPORT' not in globals():
            print("❌ ADKのインポートに成功していません")
            return
            
        if ADK_IMPORT == 'google.adk':
            print("🔍 'import google.adk' を使用してADKを初期化します")
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
        import datetime
        today = datetime.date.today().strftime("%Y-%m-%d")
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
            # イベントの内容を確認
            for event in events.items[:3]:  # 最初の3つだけ表示
                summary = event.get('summary', 'No Title')
                start = event.get('start', {})
                start_time = start.get('dateTime', start.get('date', 'No time'))
                print(f"  - {summary} ({start_time})")
        elif isinstance(events, list):
            print(f"📄 イベント数: {len(events)}")
            # リスト形式の場合の表示
            for event in events[:3]:
                summary = event.get('summary', 'No Title')
                start = event.get('start', {})
                start_time = start.get('dateTime', start.get('date', 'No time'))
                print(f"  - {summary} ({start_time})")
        elif isinstance(events, dict) and 'items' in events:
            print(f"📄 イベント数: {len(events['items'])}")
            # 辞書形式の場合の表示
            for event in events['items'][:3]:
                summary = event.get('summary', 'No Title')
                start = event.get('start', {})
                start_time = start.get('dateTime', start.get('date', 'No time'))
                print(f"  - {summary} ({start_time})")
        else:
            print(f"⚠️ 予期しないイベントデータ形式: {events}")
        
    except Exception as e:
        print(f"❌ ADKデバッグ中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 Google ADK Calendar デバッグツール 🔍")
    asyncio.run(debug_calendar())
