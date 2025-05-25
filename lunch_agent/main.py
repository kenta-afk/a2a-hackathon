"""
Main entry point for the lunch recommendation agent.
This file orchestrates the agents and handles the user interaction.
"""

import os
import asyncio
from dotenv import load_dotenv
from google.adk.runners import Runner
from lunch_recommendation_agent.local_agent import local_agent
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

async def main():
    """Main entry point for the lunch recommendation agent."""
    
    # Check for required environment variables
    maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not maps_api_key:
        print("警告: Google Maps APIキーが設定されていません。")
        print("API呼び出しは失敗し、デフォルトのデータが使用される可能性があります。")
        print(".envファイルをセットアップしてください。サンプルは.env.exampleにあります。")
        print()
    
    # Set up Gemini API key
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if not google_api_key:
        print("エラー: Google AI APIキーが設定されていません。")
        print(".envファイルにGOOGLE_API_KEYを設定してください。サンプルは.env.exampleにあります。")
        print("Gemini APIキーは https://ai.google.dev/ から取得できます。")
        return
    
    # Configure Google Generative AI with API key
    genai.configure(api_key=google_api_key)
    
    # Run the agent with Web UI
    print("ランチレコメンデーションエージェントを起動中...")
    print("ウェブブラウザが開き、エージェントとのインタラクションが可能になります。")
    print("エージェントを停止するには、コンソールで Ctrl+C を押してください。")
    
    # Use the local agent as the root agent
    runner = Runner()
    await runner.run_web_ui(local_agent)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nエージェントを停止しています...")
