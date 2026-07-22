"""临时脚本：验证 stdio MCP Server 能启动、返回工具列表并响应工具调用。"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

BACKEND_DIR = Path(__file__).resolve().parent


async def main() -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(BACKEND_DIR / "mcp_server.py"), "--log-level", "ERROR"],
        cwd=str(BACKEND_DIR),
        env={
            **os.environ,
            "OPENAI_API_KEY": "",
            "DATABASE_URL": "sqlite:///./test_mcp_stdio.db",
            "VECTOR_DB_PATH": "./test_mcp_stdio_chroma",
        },
    )
    print("connecting...", flush=True)
    async with stdio_client(params) as (read_stream, write_stream):
        print("connected", flush=True)
        async with ClientSession(read_stream, write_stream) as session:
            print("initializing...", flush=True)
            init_result = await session.initialize()
            print("server:", init_result.serverInfo.name, init_result.serverInfo.version)

            print("listing tools...", flush=True)
            tools = await session.list_tools()
            print("tools:", [t.name for t in tools.tools])

            print("calling tool...", flush=True)
            result = await session.call_tool("detect_job_search_obstacles", {
                "resume_data": {"skills": ["Python"]},
                "jd_data": {"required_skills": ["Python", "FastAPI"]},
            })
            print("call_tool returned", flush=True)
            payload = json.loads(result.content[0].text)
            print("obstacles count:", len(payload.get("obstacles", [])))


if __name__ == "__main__":
    asyncio.run(main())
