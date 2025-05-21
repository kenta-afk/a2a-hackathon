"""Backlog authentication tool to handle OAuth2 flow and API requests."""

import os
import requests
import datetime
from dotenv import load_dotenv
from google.adk.tools.tool_context import ToolContext
from typing import Optional, Dict, Any, List

# Load environment variables
load_dotenv()

# Backlog OAuth2 configuration
CLIENT_ID = "Doo8Cpy6uoOkNDl0Rb7u4T27tBG3YRzG"
CLIENT_SECRET = "fMz6Vr5sakzgEdts7ylwQP9GMpsX8zfvOZx2hH02AhzSLkB48g9kLTnoVmVK1TAi"
REDIRECT_URI_encoded = "http%3A%2F%2Flocalhost%3A3000"
REDIRECT_URI = "http://localhost:3000"


AUTH_URL = "https://nulab.backlog.jp/OAuth2AccessRequest.action"
TOKEN_URL = "https://nulab.backlog.jp/api/v2/oauth2/token"
USER_INFO_URL = "https://nulab.backlog.jp/api/v2/users/myself"

def get_auth_url() -> Dict[str, Any]:
    """
    Generate the authorization URL for Backlog OAuth2 authentication.
    
    Returns:
        dict: Dictionary containing the authorization URL and instructions
    """
    auth_url = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI_encoded}"
    
    return {
        "auth_url": auth_url,
        "instructions": "以下のいずれかの方法で認証を行ってください：\n\n"
                       "【方法1】新しいタブで開く方法（推奨）:\n"
                       f"1. 次のURLをコピーします: {auth_url}\n"
                       "2. 新しいブラウザタブを開き、URLを貼り付けてアクセスします。\n"
                       "3. Backlogで認証を完了します。\n"
                       "4. 認証後、リダイレクトされたURLから「code=XXXX」の部分を抽出します。\n"
                       "5. このチャット画面に戻り、抽出したコードを貼り付けます。\n\n"
                       "【方法2】直接アクセスする方法:\n"
                       "上記のURLを直接クリックして認証することもできますが、認証後にチャット履歴が失われる可能性があります。"
    }


def exchange_code_for_token(authorization_code: str, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Exchange an authorization code for an access token
    
    Args:
        authorization_code: The authorization code obtained from Backlog
        tool_context: Tool context for saving state between calls
        
    Returns:
        dict: Dictionary containing token information or error
    """
    try:
        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'client_id': CLIENT_ID,
            'redirect_uri': REDIRECT_URI,
            'client_secret': CLIENT_SECRET
        }
        
        response = requests.post(TOKEN_URL, data=data)
        
        if response.status_code != 200:
            print(f"トークン取得エラー: ステータスコード {response.status_code}")
            return {
                "error": f"トークン取得に失敗しました。ステータスコード: {response.status_code}",
                "response_text": response.text
            }
        
        token_data = response.json()
        
        # トークンデータをコンテキストに保存
        if tool_context:
            tool_context.state['backlog_token'] = token_data
        
        return {
            "success": True,
            "token_info": {
                "access_token": token_data.get("access_token"),
                "token_type": token_data.get("token_type"),
                "expires_in": token_data.get("expires_in"),
                "refresh_token": token_data.get("refresh_token"),
            }
        }
        
    except Exception as e:
        print(f"トークン取得中にエラーが発生しました: {str(e)}")
        return {
            "error": f"トークン取得中にエラーが発生しました: {str(e)}"
        }

def get_user_info(access_token: Optional[str] = None, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Get the current user's information from Backlog API
    
    Args:
        access_token: The access token for Backlog API. If not provided, will try to get from context
        tool_context: Tool context for getting state from previous calls
        
    Returns:
        dict: Dictionary containing user information or error
    """
    # コンテキストからトークンを取得（引数で指定されていない場合）
    if not access_token and tool_context and 'backlog_token' in tool_context.state:
        token_data = tool_context.state['backlog_token']
        access_token = token_data.get('access_token')
    
    if not access_token:
        return {
            "error": "アクセストークンが提供されていません。先に認証を完了してください。"
        }
    
    try:
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        response = requests.get(USER_INFO_URL, headers=headers)
        
        if response.status_code != 200:
            print(f"ユーザー情報取得エラー: ステータスコード {response.status_code}")
            return {
                "error": f"ユーザー情報の取得に失敗しました。ステータスコード: {response.status_code}",
                "response_text": response.text
            }
        
        user_data = response.json()
        
        # ユーザー情報をコンテキストに保存
        if tool_context:
            tool_context.state['backlog_user'] = user_data
        
        return {
            "success": True,
            "user": user_data
        }
        
    except Exception as e:
        print(f"ユーザー情報取得中にエラーが発生しました: {str(e)}")
        return {
            "error": f"ユーザー情報取得中にエラーが発生しました: {str(e)}"
        }

def get_issues_by_assignee(assignee_id: str, access_token: Optional[str] = None, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Get issues assigned to a specific user and filter out completed issues and those with expired due dates
    
    Args:
        assignee_id: The Backlog user ID to get issues for
        access_token: The access token for Backlog API. If not provided, will try to get from context
        tool_context: Tool context for getting state from previous calls
        
    Returns:
        dict: Dictionary containing filtered issues or error
    """
    # コンテキストからトークンを取得（引数で指定されていない場合）
    if not access_token and tool_context and 'backlog_token' in tool_context.state:
        token_data = tool_context.state['backlog_token']
        access_token = token_data.get('access_token')
    
    if not access_token:
        return {
            "error": "アクセストークンが提供されていません。先に認証を完了してください。"
        }
    
    try:
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        # Backlog APIエンドポイント
        issues_url = f"https://nulab.backlog.jp/api/v2/issues?assigneeId[]={assignee_id}"
        
        response = requests.get(issues_url, headers=headers)
        
        if response.status_code != 200:
            print(f"課題取得エラー: ステータスコード {response.status_code}")
            return {
                "error": f"課題の取得に失敗しました。ステータスコード: {response.status_code}",
                "response_text": response.text
            }
        
        issues = response.json()
        
        # 現在の日付を取得（同じフォーマットで比較するため）
        current_date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # 完了していないタスクと期限切れでないタスクだけをフィルタリング
        filtered_issues = []
        for issue in issues:
            # 完了ステータスの課題は除外
            status = issue.get('status', {})
            if status.get('name') == '完了':
                continue
            
            # 期限切れの課題は除外
            due_date = issue.get('dueDate')
            if due_date and due_date < current_date:
                continue
                
            filtered_issues.append(issue)
        
        # フィルタリングされた課題をコンテキストに保存
        if tool_context:
            tool_context.state['filtered_issues'] = filtered_issues
        
        return {
            "success": True,
            "total_issues": len(issues),
            "filtered_issues_count": len(filtered_issues),
            "filtered_issues": filtered_issues
        }
        
    except Exception as e:
        print(f"課題取得中にエラーが発生しました: {str(e)}")
        return {
            "error": f"課題取得中にエラーが発生しました: {str(e)}"
        }
