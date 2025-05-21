"""Local agent that retrieves calendar events using Google Calendar API."""

from google.adk.agents import Agent
from calendar_agent.tools.calendar_tool import get_calendar_events

# カレンダーエージェントを作成
local_agent = Agent(
    name="calendar_agent",
    model="gemini-2.0-flash",
    description="指定された日付のGoogleカレンダー予定を取得し、整理して表示するエージェント",
    instruction="""
    あなたは、ユーザーのGoogleカレンダーから予定を取得し、見やすく整理して表示する便利なアシスタントです。

    カレンダースケジュールを取得・表示する際は、次の手順に従ってください：
    1. get_calendar_events ツールを使用して、指定された日付（または指定がない場合は今日）のカレンダーイベントを取得します
    2. 取得したスケジュールを時系列順に整理し、見やすく表示します
    3. スケジュールの概要（予定の数、最初の予定と最後の予定の時間帯など）を簡潔に説明します
    4. 予定が空いている時間帯があれば、それも表示します
    
    各イベントについて、以下の情報を提供してください：
    - イベント名
    - 開始時間と終了時間
    - （もしあれば）イベントの追加情報や注意点
    
    親切で明確な口調で応答してください。ユーザーが日付を指定していない場合は今日の予定を表示し、
    明日以降の予定を確認したい場合は日付を指定するよう促してください。
    
    カレンダーへのアクセスに関する権限やプライバシーについて適切に配慮してください。
    エラーが発生した場合は、問題の内容と可能な解決策を明確に説明してください。
    """,
    tools=[get_calendar_events]
)

def main():
    """Run the calendar agent interactively for testing."""
    from google.adk.runners import Runner
    import asyncio
    
    runner = Runner()
    asyncio.run(runner.run_interactive(local_agent))

if __name__ == "__main__":
    main()
