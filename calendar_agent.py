"""
Google Calendar Agent
This module provides functionality to retrieve calendar events using Google API.
"""

import os
import datetime
from typing import List, Dict, Any
import pickle
import google.oauth2.credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# OAuth 2.0スコープの設定
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

class CalendarAgent:
    """Agent for retrieving and formatting Google Calendar events."""

    def __init__(self):
        """Initialize the Calendar Agent with Google Calendar API."""
        # 環境変数から直接CLIENT_IDを取得
        self.client_id = os.environ.get("CLIENT_ID")
        
        if not self.client_id:
            raise ValueError("環境変数 CLIENT_ID が設定されていません")
        
        self.service = None

    def _get_credentials(self):
        """
        Get valid user credentials for Calendar API.
        
        Returns:
            Credentials, the obtained credential.
        """
        creds = None
        # トークンファイルのパス
        token_path = 'token.pickle'
        
        # トークンファイルが存在していれば、そこから認証情報を取得
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
                
        # 有効な認証情報がなければ、ユーザーに認証してもらう
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                client_config = {
                    "installed": {
                        "client_id": self.client_id,
                        "project_id": "calendar-integration",
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "redirect_uris": ["http://localhost:3000"]
                    }
                }
                flow = InstalledAppFlow.from_client_config(
                    client_config, SCOPES)
                # Explicitly set the exact redirect URI to match what's in Google Cloud Console
                flow.redirect_uri = 'http://localhost:3000'
                creds = flow.run_local_server(port=3000)
                
            # 次回のために認証情報を保存
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
                
        return creds
    
    def get_events_for_date(self, date: datetime.date = None) -> List[Dict[str, Any]]:
        """
        Get calendar events for a specific date.
        
        Args:
            date: The date to get events for. Defaults to today.
            
        Returns:
            List of event dictionaries with formatted information.
        """
        if date is None:
            date = datetime.date.today()
        
        # Format date for API query
        date_str = date.strftime("%Y-%m-%d")
        
        # カレンダーイベント取得の時間範囲設定
        start_time = datetime.datetime.combine(date, datetime.time.min).isoformat() + 'Z'
        end_time = datetime.datetime.combine(date, datetime.time.max).isoformat() + 'Z'
        
        # Googleカレンダーサービスの取得
        if not self.service:
            creds = self._get_credentials()
            self.service = build('calendar', 'v3', credentials=creds)
        
        # カレンダーイベントの取得
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        # イベント結果の処理
        events = events_result.get('items', [])
        
        # Format events for display
        formatted_events = []
        for i, event in enumerate(events):
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            # Extract the time part only (format: HH:MM)
            start_time = self._format_time(start)
            end_time = self._format_time(end)
            
            formatted_events.append({
                'name': f"meeting{i+1}",
                'title': event.get('summary', 'No Title'),
                'start_time': start_time,
                'end_time': end_time,
                'formatted': f"meeting{i+1} {start_time}~{end_time}"
            })
            
        return formatted_events
    
    def _format_time(self, datetime_str: str) -> str:
        """
        Format a datetime string to HH:MM format.
        
        Args:
            datetime_str: ISO format datetime string
            
        Returns:
            Time in HH:MM format
        """
        # Handle different datetime formats
        if 'T' in datetime_str:
            # It's a datetime with time component
            time_part = datetime_str.split('T')[1][:5]  # Extract HH:MM
            return time_part
        else:
            # It's a date without time
            return "All day"

    def get_formatted_schedule(self, date: datetime.date = None) -> List[str]:
        """
        Get a list of formatted schedule entries.
        
        Args:
            date: The date to get schedule for. Defaults to today.
            
        Returns:
            List of formatted schedule strings.
        """
        events = self.get_events_for_date(date)
        return [event['formatted'] for event in events]
