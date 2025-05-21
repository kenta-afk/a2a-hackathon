"""
Google Calendar events debug script
このモジュールはGoogleサービスアカウントを使用してCalendar APIにアクセスする方法をテストするためのものです。
"""

import os
import asyncio
import datetime
import pytz
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

# サービスアカウントの設定
SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'calendar_agent/service-account.json'

async def debug_calendar():
    """サービスアカウントを使用してGoogle Calendar APIをデバッグします"""
    print("\n📅 Google Calendar APIのデバッグを開始します...")
    
    # 環境変数のロード（必要に応じて使用）
    load_dotenv()
    
    try:
        # サービスアカウントの認証情報取得
        print("\n🔑 サービスアカウント認証情報の読み込みを試みます...")
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            print(f"❌ サービスアカウントファイルが見つかりません: {SERVICE_ACCOUNT_FILE}")
            return
                
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        print(f"✅ サービスアカウント認証情報を読み込みました")
        
        # Calendar APIサービスの構築
        print("\n🔄 Calendar APIサービスの構築を試みます...")
        service = build('calendar', 'v3', credentials=credentials)
        print("✅ Calendar APIサービスの構築に成功しました")
        
        # 今日の日付のイベントを取得
        print("\n📋 本日のイベント取得を試みます...")
        
        # カレンダーIDの設定
        # 注意: サービスアカウントでは 'primary' は使用できません
        # 対象ユーザーのメールアドレスをカレンダーIDとして指定する必要があります
        # また、そのカレンダーをサービスアカウントと共有している必要があります
        calendar_id = os.environ.get("CALENDAR_ID")
        if not calendar_id:
            print("⚠️ CALENDAR_ID環境変数が設定されていません。対象のカレンダーIDを指定してください。")
            print("  サービスアカウントには共有設定が必要です。")
            # フォールバック用のデフォルト値（実際のメールアドレスを指定する必要があります）
            calendar_id = 'your-calendar-id@gmail.com'  # この部分は実際のカレンダーIDに変更してください
        
        print(f"📆 カレンダーID: {calendar_id}")
        
        # タイムゾーン設定を明示的に指定
        japan_tz = pytz.timezone('Asia/Tokyo')
        start_of_day = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
        end_of_day = datetime.datetime.combine(datetime.date.today(), datetime.time.max)
        
        start_of_day_utc = start_of_day.astimezone(japan_tz).isoformat()
        end_of_day_utc = end_of_day.astimezone(japan_tz).isoformat()
        
        print(f"🕒 取得期間: {start_of_day_utc} 〜 {end_of_day_utc}")
        
        try:
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=start_of_day_utc,
                timeMax=end_of_day_utc,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            print("✅ API呼び出し成功")
        except Exception as e:
            print(f"❌ API呼び出し失敗: {e}")
            raise
        
        events = events_result.get('items', [])
        
        print(f"✅ イベント取得に成功しました: {type(events)}")
        print(f"📄 イベント数: {len(events)}")
        
        # イベントの内容を確認
        if events:
            # 最初の3つだけ表示
            for event in events[:3]:
                summary = event.get('summary', 'No Title')
                start = event.get('start', {})
                start_time = start.get('dateTime', start.get('date', 'No time'))
                print(f"  - {summary} ({start_time})")
        else:
            print("  イベントはありません")
        
    except Exception as e:
        print(f"❌ APIデバッグ中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 Google Calendar API デバッグツール 🔍")
    asyncio.run(debug_calendar())
