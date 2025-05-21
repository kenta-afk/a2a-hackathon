"""Local agent that gets current location and recommends nearby restaurants."""

from google.adk.agents import Agent
from google.adk.tools import transfer_to_agent
from lunch_agent.tools.location_tool import get_current_location
from lunch_agent.tools.restaurant_search_tool import find_restaurants

# Create local agent that will use the location and restaurant search tools
local_agent = Agent(
    name="restaurant_recommendation_agent",
    model="gemini-2.0-flash",
    description="An agent that recommends nearby restaurants based on current location and available break time",
    instruction="""
    あなたは、ユーザーの現在地と利用可能な休憩時間に基づいてランチのレストランを推薦する便利なアシスタントです。

    レストランを推薦する際は、次の手順に従ってください：
    1. get_current_location ツールを使用して、ユーザーの現在位置を自動的に取得します（IPベースでの位置検出）
    2. ユーザーが昼食に利用できる時間を推定する必要がある場合は、transfer_to_agent ツールを使用して
       break_prediction_agent に問い合わせてください。休憩時間予測エージェントがその部分を処理して戻ります。
    3. 利用可能な休憩時間を理解した後、find_restaurants ツールを使用して、その時間内で適切なレストランを検索します
    4. ユーザーの状況に最適な3〜5つのレストランを推薦します。考慮すべき点：
       - 距離と移動時間（利用可能な休憩時間内に収まること）
       - 評価とレビュー
       - 価格帯
       - 料理の多様性
    
    各レストランについて、以下の情報を提供してください：
    - レストラン名
    - レストランのタイプや料理のジャンルの簡単な説明
    - 評価とレビュー数
    - 現在地からの距離と予想移動時間
    - Google マップで表示するためのリンク
    
    親切で会話的な口調で応答してください。ユーザーの好み（料理の種類、価格帯など）に基づいて
    推薦内容を絞り込むために、フォローアップの質問をしても構いません。
    
    常に時間的制約を考慮した推薦をしてください。ユーザーの休憩時間が短い場合は、
    食事をして戻るのに十分な時間があるよう、より近いレストランを優先してください。
    """,
    tools=[
        get_current_location,
        find_restaurants,
        transfer_to_agent
    ]
)

def main():
    """Run the restaurant recommendation agent interactively for testing."""
    from google.adk.runners import Runner
    import asyncio
    
    runner = Runner()
    asyncio.run(runner.run_interactive(local_agent))

if __name__ == "__main__":
    main()
