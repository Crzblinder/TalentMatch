"""本地前后端生命周期管理（上下文管理器）。

供 E2E 测试使用：自动初始化数据库、注入最小测试数据、启动后端与前端，
测试完成后清理进程。
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
E2E_DIR = ROOT / "e2e"

BACKEND_PORT = 8000
FRONTEND_PORT = 5173

PYTHON = sys.executable
NODE = shutil.which("node") or "node"


def _wait_for_port(port: int, timeout: float = 120.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return
        except OSError:
            time.sleep(0.5)
    raise RuntimeError(f"Port {port} did not become ready within {timeout}s")


def _kill_proc(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], check=False)
        else:
            proc.terminate()
        proc.wait(timeout=10)


@contextmanager
def server_context() -> Generator[tuple[subprocess.Popen, subprocess.Popen], None, None]:
    """启动前后端服务并 yield 进程元组，退出时自动停止。"""
    env = {**os.environ, "OPENAI_API_KEY": ""}

    # 1. 初始化数据库并注入最小测试数据
    subprocess.run(
        [PYTHON, "scripts/init_db.py"],
        cwd=BACKEND_DIR,
        check=True,
        env=env,
    )
    subprocess.run(
        [PYTHON, "../e2e/seed_minimal.py"],
        cwd=BACKEND_DIR,
        check=True,
        env=env,
    )

    # 2. 启动后端
    backend_proc = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(BACKEND_PORT)],
        cwd=BACKEND_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )

    # 3. 启动前端
    frontend_proc = subprocess.Popen(
        [NODE, "./node_modules/vite/bin/vite.js", "--host", "127.0.0.1"],
        cwd=FRONTEND_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )

    try:
        _wait_for_port(BACKEND_PORT)
        _wait_for_port(FRONTEND_PORT)
        yield backend_proc, frontend_proc
    finally:
        _kill_proc(frontend_proc)
        _kill_proc(backend_proc)


if __name__ == "__main__":
    print("Starting servers for manual smoke test...")
    with server_context():
        print(f"Backend: http://127.0.0.1:{BACKEND_PORT}")
        print(f"Frontend: http://127.0.0.1:{FRONTEND_PORT}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping servers...")
