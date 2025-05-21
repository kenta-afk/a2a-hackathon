"""
Main entry point for the calendar agent.
This file orchestrates the agent and handles the user interaction.
"""

import os
import asyncio
from dotenv import load_dotenv
from google.adk.runners import Runner
from calendar_agent.calendar_agent import local_agent
import google.generativeai as genai

# .envファイルから環境変数を読み込む
load_dotenv()

async def main():
    """Main entry point for the calendar agent."""
    
    # Google API Keyの確認
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if not google_api_key:
        print("エラー: Google AI APIキーが設定されていません。")
        print(".envファイルにGOOGLE_API_KEYを設定してください。")
        print("Gemini APIキーは https://ai.google.dev/ から取得できます。")
        return
    
    # Gemini API設定
    genai.configure(api_key=google_api_key)
    
    # GoogleカレンダーAPIのクライアントIDを確認
    client_id = os.getenv('CLIENT_ID')
    if not client_id:
        print("警告: GoogleカレンダーAPIのクライアントIDが設定されていません。")
        print("カレンダーAPIへのアクセスが失敗する可能性があります。")
        print(".envファイルにCLIENT_ID=your_client_idを設定してください。")
        print()
    
    # エージェントをWebUIで実行
    print("カレンダーエージェントを起動中...")
    print("ウェブブラウザが開き、エージェントとのインタラクションが可能になります。")
    print("エージェントを停止するには、コンソールで Ctrl+C を押してください。")
    
    # ローカルエージェントをルートエージェントとして使用
    runner = Runner()
    await runner.run_web_ui(local_agent)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nエージェントを停止しています...")
