"""
Main entry point for the Backlog agent.
This file orchestrates the agent and handles the user interaction.
"""

import os
import asyncio
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.runners.web import WebUIParameters
from take_issue_agent.agent import backlog_agent
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

async def main():
    """Main entry point for the Backlog agent."""
    
    # Set up Gemini API key
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if not google_api_key:
        print("エラー: Google AI APIキーが設定されていません。")
        print(".envファイルにGOOGLE_API_KEYを設定してください。")
        print("Gemini APIキーは https://ai.google.dev/ から取得できます。")
        return
    
    # Configure Google Generative AI with API key
    genai.configure(api_key=google_api_key)
    
    # Run the agent with Web UI
    print("Backlogエージェントを起動中...")
    print("ウェブブラウザが開き、エージェントとのインタラクションが可能になります。")
    print("エージェントを停止するには、コンソールで Ctrl+C を押してください。")
    
    # Create Runner and register the agent
    runner = Runner()
    runner.register_agent(backlog_agent.name, backlog_agent)
    
    # Print registered agent for debugging
    print(f"登録されたエージェント: {backlog_agent.name}")
    
    # Web UI パラメータを設定
    web_params = WebUIParameters(
        query_parameters_handler=lambda params: {
            "user_input": f"認証コード: {params.get('code')}" if params.get("code") else None
        }
    )
    
    # Run the agent with Web UI
    await runner.run_web_ui(backlog_agent, web_ui_params=web_params)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nエージェントを停止しています...")
