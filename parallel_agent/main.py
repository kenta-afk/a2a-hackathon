"""並列処理エージェントの起動スクリプト"""

from google.adk.runners import Runner
import asyncio
from parallel_agent.parallel_agent import parallel_agent

def main():
    """エージェントを起動する"""
    runner = Runner()
    asyncio.run(runner.run_interactive(parallel_agent))

if __name__ == "__main__":
    main()
