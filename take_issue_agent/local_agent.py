"""Local agent that authenticates with Backlog and retrieves user information and issues."""

from google.adk.agents import Agent
from google.adk.tools import transfer_to_agent
from take_issue_agent.tools.backlog_auth_tool import get_auth_url, exchange_code_for_token, get_user_info
from take_issue_agent.remote_agent import backlog_user_info_agent

# Get the name of the remote agent to ensure consistency in references
REMOTE_AGENT_NAME = backlog_user_info_agent.name

# Create local agent that will handle Backlog authentication
local_agent = Agent(
    name="backlog_auth_agent",
    model="gemini-2.0-flash",
    description="An agent that handles Backlog authentication and delegates user info and issues retrieval",
    instruction=f"""
    あなたは、Backlogの認証を管理し、ユーザー情報と課題を取得するためのエージェントです。
    
    ユーザー情報・課題を取得するための手順：
    1. get_auth_url ツールを使用して、Backlog認証のためのURLを生成します。
    2. 認証URLと以下の2つの方法を明確に説明してください：
       【方法1】新しいタブで開く方法（推奨）：
       - ユーザーがURLをコピーして新しいタブで開くよう説明する
       - この方法ではチャット履歴が保持されることを強調する
       
       【方法2】直接URLをクリックする方法：
       - この方法ではチャット履歴が失われる可能性があることを説明する
       
    3. ユーザーが認証コードを提供したら、exchange_code_for_token ツールを使用してアクセストークンを取得します。
    4. アクセストークンの取得に成功したら、get_user_info ツールを使用してユーザー情報を取得します。
       - ユーザーIDを必ず取得してください（これは課題取得に必要です）
    5. ユーザー情報（特にユーザーID）を取得できたら、transfer_to_agent ツールを使用して "{REMOTE_AGENT_NAME}" に処理を委譲し、
       ユーザーIDを使用して課題の取得と表示を行います。
    
    ユーザーからの入力解析：
    - ユーザーの入力から「code=」に続く部分や、単独で入力されたコードを抽出してください。
    - URLの一部として提供された場合や、メッセージ中に含まれるコードを適切に識別してください。
    
    ユーザーに対して：
    - 常に丁寧で明確な指示を提供してください。
    - 認証URLを新しいタブで開く方法を丁寧に説明し、その利点（チャット履歴の保持）を強調してください。
    - リダイレクト後のURLからcodeパラメータを見つける方法を具体的に説明してください。
    - エラーが発生した場合は、問題の内容と対処法を説明してください。
    
    セキュリティ上の注意：
    - アクセストークンやリフレッシュトークンなどの機密情報は、必要以上に表示しないでください。
    - ユーザーに認証情報の安全な管理を促してください。
    """,
    tools=[
        get_auth_url,
        exchange_code_for_token,
        get_user_info,
        transfer_to_agent
    ]
)

def main():
    """Run the Backlog user info agent interactively for testing."""
    from google.adk.runners import Runner
    import asyncio
    
    runner = Runner()
    asyncio.run(runner.run_interactive(local_agent))

if __name__ == "__main__":
    main()
