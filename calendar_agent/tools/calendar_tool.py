"""
Google Calendar events retrieval tool.
This tool provides functionality to retrieve calendar events using Google ADK.
"""

import asyncio
import datetime
from typing import List, Dict, Any, Optional
from google.adk.tools.tool_context import ToolContext

async def get_calendar_events(date: Optional[str] = None, tool_context: Optional[ToolContext] = None) -> List[Dict[str, Any]]:
    """
    指定された日付のGoogleカレンダーイベントを取得します。
    
    Args:
        date: イベントを取得する日付（YYYY-MM-DD形式）。指定がない場合は今日の予定を取得します。
        
    Returns:
        List of event dictionaries with formatted information.
    """
    # 日付が指定されていない場合は今日の日付を使用
    if not date:
        target_date = datetime.date.today()
    else:
        target_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    
    # 日付の文字列表現
    date_str = target_date.strftime("%Y-%m-%d")
    
    # Google ADK からカレンダーサービスを取得
    toolkit = asyncio.get_running_loop().toolkit
    calendar = await toolkit.get_calendar()
    
    # 指定日の時間範囲を設定
    time_min = f"{date_str}T00:00:00Z"
    time_max = f"{date_str}T23:59:59Z"
    
    # カレンダーイベントの取得
    events = await calendar.events.list(
        calendar_id='primary',
        time_min=time_min,
        time_max=time_max,
        single_events=True,
        order_by='startTime'
    )
    
    # APIレスポンスの構造に応じてイベントを取得
    events_list = []
    if hasattr(events, 'items'):
        events_list = events.items
    elif isinstance(events, list):
        events_list = events
    elif isinstance(events, dict) and 'items' in events:
        events_list = events['items']
    
    # イベントを整形
    formatted_events = []
    for i, event in enumerate(events_list):
        # イベントの開始・終了時間を取得
        start = event.get('start', {})
        end = event.get('end', {})
        
        start_time = start.get('dateTime', start.get('date', ''))
        end_time = end.get('dateTime', end.get('date', ''))
        
        # 時間部分のみを抽出（HH:MM形式）
        start_time_formatted = _format_time(start_time)
        end_time_formatted = _format_time(end_time)
        
        # フォーマット済みのイベントを追加
        formatted_events.append({
            'name': f"meeting{i+1}",
            'title': event.get('summary', 'No Title'),
            'start_time': start_time_formatted,
            'end_time': end_time_formatted,
            'formatted': f"meeting{i+1} {start_time_formatted}~{end_time_formatted} {event.get('summary', 'No Title')}"
        })
    
    return formatted_events

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
