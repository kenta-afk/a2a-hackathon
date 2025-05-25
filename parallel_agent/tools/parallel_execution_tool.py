"""並列処理実行ツール

このツールはGoogle ADKを使用して複数のエージェントを並列に実行するための機能を提供します。
"""
import asyncio
import concurrent.futures
import os
import subprocess
from typing import Dict, List, Optional, Any, TypedDict, Callable

from google.adk.tool import tool

class AgentExecutionResult(TypedDict):
    """エージェント実行結果を表す型"""
    agent_name: str
    status: str
    output: Optional[str]
    error: Optional[str]

@tool(
    name="run_agents_parallel",
    description="複数のエージェントを並列に実行するツール",
    input_schema={
        "type": "object",
        "properties": {
            "agents": {
                "type": "array",
                "description": "実行するエージェントの名前のリスト",
                "items": {
                    "type": "string",
                    "enum": ["calendar_agent", "lunch_agent", "take_issue_agent"]
                }
            },
            "timeout": {
                "type": "integer",
                "description": "タイムアウト時間（秒）",
                "default": 30
            }
        },
        "required": ["agents"]
    }
)
async def run_agents_parallel(
    agents: List[str],
    timeout: int = 30
) -> Dict[str, List[AgentExecutionResult]]:
    """
    指定されたエージェントを並列に実行します。
    
    Args:
        agents: 実行するエージェントの名前のリスト
        timeout: タイムアウト時間（秒）
        
    Returns:
        各エージェントの実行結果
    """
    results = []
    
    # タスクリストを作成
    tasks = []
    for agent_name in agents:
        task = asyncio.create_task(_execute_agent(agent_name, timeout))
        tasks.append(task)
    
    # 全てのタスクを完了するまで待機
    completed_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 結果を整形
    for i, result in enumerate(completed_results):
        if isinstance(result, Exception):
            # 例外が発生した場合はエラーとして記録
            results.append({
                "agent_name": agents[i],
                "status": "error",
                "output": None,
                "error": str(result)
            })
        else:
            results.append(result)
    
    return {"results": results}

async def _execute_agent(agent_name: str, timeout: int) -> AgentExecutionResult:
    """
    指定されたエージェントを実行します。
    
    Args:
        agent_name: エージェント名
        timeout: タイムアウト時間（秒）
        
    Returns:
        エージェントの実行結果
    """
    # エージェント名からモジュールパスを生成
    module_path = f"{agent_name}.main"
    
    def run_process():
        try:
            # エージェントをサブプロセスとして実行
            process = subprocess.run(
                ["python", "-m", module_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            if process.returncode == 0:
                return {
                    "agent_name": agent_name,
                    "status": "success",
                    "output": process.stdout,
                    "error": None
                }
            else:
                return {
                    "agent_name": agent_name,
                    "status": "failed",
                    "output": process.stdout,
                    "error": process.stderr
                }
        except subprocess.TimeoutExpired:
            return {
                "agent_name": agent_name,
                "status": "timeout",
                "output": None,
                "error": f"エージェントの実行がタイムアウトしました（{timeout}秒）"
            }
        except Exception as e:
            return {
                "agent_name": agent_name,
                "status": "error",
                "output": None,
                "error": str(e)
            }
    
    # 並行実行でCPUバインドな処理を実行
    with concurrent.futures.ProcessPoolExecutor() as executor:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, run_process)
    
    return result
