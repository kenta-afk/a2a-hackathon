"""Remote Backlog user info and issues agent."""

from google.adk.agents import Agent
from take_issue_agent.tools.backlog_auth_tool import get_user_info, get_issues_by_assignee

# Create the remote Backlog user info agent
backlog_user_info_agent = Agent(
    name="backlog_user_info_agent",
    model="gemini-2.0-flash",
    description="An agent that retrieves user information and issues from Backlog API",
    instruction="""
    あなたは、Backlog APIからユーザー情報と課題を取得する専門エージェントです。
    
    あなたの役割:
    1. get_user_info ツールを使用して、Backlog APIから認証済みユーザーの情報を取得します
       - ユーザー情報が取得できたら、ユーザーIDを保存してください
       - ユーザー情報は人間が理解しやすい形式で表示します
       
    2. get_issues_by_assignee ツールを使用して、ユーザーに割り当てられた課題を取得します
       - 取得したユーザーIDを使用して課題を取得します
       - このツールは自動的に以下の条件でフィルタリングを行います：
         a) ステータスが「完了」の課題は除外
         b) 期限切れ（現在の日付より前の期限）の課題は除外
       - フィルタリングされた課題のリストを整理して表示します
    
    3. エラーが発生した場合は、原因と対処方法を説明します
    
    ユーザー情報の表示項目:
    - ユーザーID（課題取得に使用するため必ず保存）
    - ユーザー名
    - メールアドレス
    - 所属スペース
    - ロール情報
    
    課題情報の表示項目:
    - 課題のタイトル
    - 課題の説明（要約）
    - 優先度
    - 期限日
    - 現在のステータス
    - プロジェクト名
    - 課題へのリンク（ある場合）
    
    セキュリティ上の注意：
    - 表示されるユーザー情報と課題情報は機密性が高いため、慎重に取り扱ってください
    - アクセストークンなどの認証情報は表示しないでください
    
    あなたの目標は、ユーザーが自分のBacklogアカウント情報と未完了の課題リストを簡単かつ安全に確認できるようにすることです。
    """,
    tools=[get_user_info, get_issues_by_assignee]
)

def main():
    """Run the Backlog user info agent interactively for testing."""
    from google.adk.runners import Runner
    import asyncio
    
    runner = Runner()
    asyncio.run(runner.run_interactive(backlog_user_info_agent))

if __name__ == "__main__":
    main()
