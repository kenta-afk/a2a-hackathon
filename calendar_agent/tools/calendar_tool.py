"""
Google Calendar events retrieval tool.
This tool provides functionality to retrieve calendar events using Google Service Account.
"""

import os
import datetime
import pytz
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

# サービスアカウントの設定
SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.readonly']
SERVICE_ACCOUNT_FILE = 'calendar_agent/service-account.json'

def get_calendar_service():
    """
    Calendar APIのサービスインスタンスを取得します。
    
    注意: サービスアカウントで個人のGoogleカレンダーにアクセスするには、
    カレンダー共有設定でサービスアカウントのメールアドレスに読み取り権限を付与する必要があります。
    
    手順:
    1. Googleカレンダー設定を開く
    2. 共有したいカレンダーの「アクセス権限の設定」を開く
    3. 「特定のユーザーとの共有」で、サービスアカウントのメールアドレスを追加
    4. 権限レベルを「予定の閲覧」以上に設定
    5. 保存する
    
    または、共有可能なカレンダーURLがある場合:
    1. そのURLからカレンダーIDを取得（例: https://calendar.google.com/calendar/u/0?cid=aG91c2hpbnJpQGdtYWlsLmNvbQ）
    2. cidパラメータの値をBase64デコードするとカレンダーID（例: houshinri@gmail.com）が得られます
    3. そのカレンダーIDを環境変数CALENDAR_IDに設定する
    
    Returns:
        Calendar APIのサービスインスタンス
    """
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"サービスアカウントファイルが見つかりません: {SERVICE_ACCOUNT_FILE}")
    
    # サービスアカウントの認証情報を読み込み
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
    # サービスアカウントのメールアドレスを表示（デバッグ用）
    service_account_info = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE).service_account_email
    print(f"🔑 サービスアカウントのメールアドレス: {service_account_info}")
    print(f"💡 このメールアドレスにカレンダーの共有設定が必要です")
    
    # Google Calendar APIのサービスを構築
    service = build('calendar', 'v3', credentials=credentials)
    return service

def get_calendar_events(date: Optional[str] = None, calendar_id: Optional[str] = None) -> Dict[str, Any]:
    """
    指定された日付のGoogleカレンダーイベントを取得します。
    
    Args:
        date: イベントを取得する日付（YYYY-MM-DD形式）。指定がない場合は今日の予定を取得します。
        calendar_id: 取得するカレンダーのID。指定がない場合は環境変数から取得します。
        
    Returns:
        Dictionary with status, events list, and error message if applicable.
    """
    result = {
        "status": "success",
        "events": [],
        "error": None,
        "date": None
    }
    
    try:
        # 日付が指定されていない場合は今日の日付を使用
        if not date:
            target_date = datetime.date.today()
        else:
            target_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        
        # 結果に日付を設定
        result["date"] = target_date.strftime("%Y-%m-%d")
        
        # Calendar APIサービスを取得
        service = get_calendar_service()
        
        # サービスアカウントではカレンダーIDが必須
        if calendar_id is None:
            load_dotenv()
            calendar_id = os.environ.get("CALENDAR_ID")
            print(f"🔍 環境変数から取得したカレンダーID: {calendar_id}")
            if not calendar_id:
                error_msg = "カレンダーIDが指定されていません。環境変数CALENDAR_IDを設定するか、関数の引数で指定してください。"
                print(f"❌ {error_msg}")
                result["status"] = "error"
                result["error"] = error_msg
                return result
        
        # 指定日の時間範囲を設定（タイムゾーンを考慮）
        japan_tz = pytz.timezone('Asia/Tokyo')
        start_of_day = datetime.datetime.combine(target_date, datetime.time.min)
        end_of_day = datetime.datetime.combine(target_date, datetime.time.max)
        
        time_min = start_of_day.astimezone(japan_tz).isoformat()
        time_max = end_of_day.astimezone(japan_tz).isoformat()
        
        # APIリクエストの実行と例外処理
        try:
            # カレンダーイベントの取得
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            print(f"✅ カレンダー '{calendar_id}' から {len(events)} 件のイベントを取得しました")
            
        except Exception as e:
            error_msg = f"カレンダーイベント取得中にエラーが発生しました: {str(e)}"
            print(f"❌ {error_msg}")
            result["status"] = "error"
            result["error"] = error_msg
            return result
            
    except Exception as e:
        error_msg = f"カレンダーツールでエラーが発生しました: {str(e)}"
        print(f"❌ {error_msg}")
        result["status"] = "error"
        result["error"] = error_msg
        return result
    
    # イベントを整形
    formatted_events = []
    for i, event in enumerate(events):
        # イベントの開始・終了時間を取得
        start = event.get('start', {})
        end = event.get('end', {})
        
        start_time = start.get('dateTime', start.get('date', ''))
        end_time = end.get('dateTime', end.get('date', ''))
        
        # 時間部分のみを抽出（HH:MM形式）
        start_time_formatted = _format_time(start_time)
        end_time_formatted = _format_time(end_time)
        
        # フォーマット済みのイベントを追加
        event_data = {
            'name': f"meeting{i+1}",
            'title': event.get('summary', 'No Title'),
            'start_time': start_time_formatted,
            'end_time': end_time_formatted,
            'formatted': f"meeting{i+1} {start_time_formatted}~{end_time_formatted} {event.get('summary', 'No Title')}"
        }
        formatted_events.append(event_data)
    
    # 結果に整形済みイベントを設定
    result["events"] = formatted_events
    return result

def _format_time(datetime_str: str) -> str:
    """
    ISO形式の日時文字列からHH:MM形式の時間を抽出します。
    
    Args:
        datetime_str: ISO形式の日時文字列
        
    Returns:
        HH:MM形式の時間文字列または「終日」
    """
    if 'T' in datetime_str:
        # 時間コンポーネントを含む日時
        time_part = datetime_str.split('T')[1][:5]  # HH:MMを抽出
        return time_part
    else:
        # 時間のない日付
        return "終日"

# 非同期関数のために同期バージョンも提供
async def get_calendar_events_async(date: Optional[str] = None, tool_context=None, calendar_id: Optional[str] = None) -> Dict[str, Any]:
    """
    指定された日付のGoogleカレンダーイベントを非同期で取得するためのラッパー関数。
    
    Args:
        date: イベントを取得する日付（YYYY-MM-DD形式）。指定がない場合は今日の予定を取得します。
        tool_context: 互換性のためのダミーパラメータ
        calendar_id: 取得するカレンダーのID。指定がない場合は環境変数から取得します。
        
    Returns:
        Dictionary with status, events list, and error message if applicable.
    """
    return get_calendar_events(date, calendar_id)
