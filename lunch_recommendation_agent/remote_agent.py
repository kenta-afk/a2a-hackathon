"""Remote break time prediction agent."""

from google.adk.agents import Agent
from lunch_recommendation_agent.tools.break_prediction_tool import predict_break_duration

# Create the remote break time prediction agent
break_prediction_agent = Agent(
    name="break_prediction_agent",
    model="gemini-2.0-flash",
    description="An agent that predicts available break time for lunch",
    instruction="""
    あなたは、ユーザーが昼食に利用できる時間を予測する専門エージェントです。
    
    休憩時間について質問された場合：
    1. predict_break_duration ツールを使用して予測を生成します
    2. 予測要因と時間を分析します
    3. ユーザーに昼食にどれだけの時間があるか、どの要因が予測に影響したかを説明します
    4. 予測の信頼度が低い場合は、見積もりが概算であることを伝えます
    
    常に役立つ情報を提供する応対をしてください。あなたの目標は、ユーザーが昼食を適切に
    計画できるよう、正確な休憩時間の予測を提供することです。
    
    レストランの提案はしないでください。それは他のエージェントの責任です。
    あなたの唯一の焦点は休憩時間の予測です。
    """,
    tools=[predict_break_duration]
)

def main():
    """Run the break prediction agent interactively for testing."""
    from google.adk.runners import Runner
    import asyncio
    
    runner = Runner()
    asyncio.run(runner.run_interactive(break_prediction_agent))

if __name__ == "__main__":
    main()
