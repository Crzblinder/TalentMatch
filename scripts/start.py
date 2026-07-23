#!/usr/bin/env python3
"""
TalentMatch 智能快速启动脚本

功能：
- 自动识别操作系统、Python/Node 环境
- 检测网络环境（中国大陆 / 海外 / 内网 / 代理）
- 自动配置 HuggingFace 镜像、代理等
- 检查端口占用并自动选择备用端口
- 自动创建虚拟环境、安装依赖、初始化数据库、注入种子数据
- 支持仅启动后端/前端、Docker 模式、跳过种子数据等选项

用法：
    python scripts/start.py
    python scripts/start.py --backend-only
    python scripts/start.py --frontend-only --port-frontend 3000
    python scripts/start.py --docker
    python scripts/start.py --no-seed --skip-deps
"""

from __future__ import annotations

import argparse
import http.client
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

# 项目路径
ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
VENV_DIR = BACKEND_DIR / ".venv"

# 默认端口
DEFAULT_BACKEND_PORT = 8000
DEFAULT_FRONTEND_PORT = 5173

# 中国大陆网络判定相关域名
CHINA_DOMAINS = ["baidu.com", "aliyun.com"]


def print_info(msg: str) -> None:
    """打印普通信息"""
    print(f"[INFO] {msg}")


def print_ok(msg: str) -> None:
    """打印成功信息"""
    print(f"[OK] {msg}")


def print_warn(msg: str) -> None:
    """打印警告信息"""
    print(f"[WARN] {msg}")


def print_error(msg: str) -> None:
    """打印错误信息"""
    print(f"[ERROR] {msg}", file=sys.stderr)


def get_os() -> str:
    """获取操作系统简称"""
    system = platform.system().lower()
    if "windows" in system:
        return "windows"
    if "darwin" in system:
        return "macos"
    return "linux"


def resolve_python() -> str:
    """解析可用的 Python 解释器路径，优先虚拟环境"""
    os_type = get_os()
    if os_type == "windows":
        venv_python = VENV_DIR / "Scripts" / "python.exe"
    else:
        venv_python = VENV_DIR / "bin" / "python"

    if venv_python.exists():
        return str(venv_python)

    for cmd in ("py", "python3", "python"):
        path = shutil.which(cmd)
        if path:
            return path

    print_error("未找到 Python 解释器，请安装 Python 3.11+ 并添加到 PATH")
    sys.exit(1)


def resolve_npm() -> str:
    """解析 npm 路径"""
    npm = shutil.which("npm")
    if not npm:
        print_error("未找到 npm，请安装 Node.js 18+ 并添加到 PATH")
        sys.exit(1)
    return npm


def check_python_version(python: str) -> bool:
    """检查 Python 版本是否 >= 3.11"""
    try:
        result = subprocess.run(
            [python, "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        version_str = result.stdout.strip().split()[1]
        major, minor = map(int, version_str.split(".")[:2])
        if major < 3 or (major == 3 and minor < 11):
            print_warn(f"Python 版本为 {version_str}，建议使用 3.11+")
            return False
        return True
    except Exception as e:
        print_warn(f"无法检测 Python 版本: {e}")
        return False


def is_port_open(host: str, port: int) -> bool:
    """检查端口是否已被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def find_free_port(start: int, end: int = 65535) -> int:
    """在指定范围内寻找可用端口"""
    for port in range(start, min(end, 65536)):
        if not is_port_open("127.0.0.1", port):
            return port
    print_error("未找到可用端口")
    sys.exit(1)


def http_ping(url: str, timeout: float = 3.0) -> bool:
    """简单的 HTTP/HTTPS 连通性探测"""
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        host = parsed.hostname or parsed.path
        if not host:
            return False
        if parsed.scheme == "https" or not parsed.scheme:
            conn_cls = http.client.HTTPSConnection
        else:
            conn_cls = http.client.HTTPConnection
        conn = conn_cls(host, timeout=timeout)
        conn.request("HEAD", "/", headers={"User-Agent": "TalentMatch-Start/1.0"})
        conn.close()
        return True
    except Exception:
        return False


def detect_network() -> dict:
    """探测当前网络环境"""
    print_info("正在探测网络环境...")
    result = {
        "has_internet": False,
        "in_china": False,
        "github_ok": False,
        "hf_ok": False,
        "proxy_set": bool(os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY")),
    }

    # 探测全球站点
    result["github_ok"] = http_ping("https://github.com", timeout=3.0)
    result["hf_ok"] = http_ping("https://huggingface.co", timeout=3.0)

    # 探测中国站点
    china_ok = any(http_ping(f"https://{d}", timeout=2.0) for d in CHINA_DOMAINS)

    if result["github_ok"] or result["hf_ok"]:
        result["has_internet"] = True

    #  heuristic：能连上国内站但连不上 GitHub/HF，判定为大陆网络
    if china_ok and not (result["github_ok"] or result["hf_ok"]):
        result["in_china"] = True
    elif china_ok and result["github_ok"]:
        # 两者都能访问，按系统时区/语言辅助判断
        if platform.system().lower() == "windows":
            import ctypes

            try:
                lang_id = ctypes.windll.kernel32.GetSystemDefaultUILanguage()
                if lang_id in (0x0804, 0x1004, 0x0404):  # 中文语言包
                    result["in_china"] = True
            except Exception:
                pass

    if result["in_china"]:
        print_ok("检测到中国大陆网络环境，将自动使用镜像源")
    elif result["has_internet"]:
        print_ok("检测到海外网络环境，可直接访问 HuggingFace/GitHub")
    else:
        print_warn("未检测到可用互联网连接，将使用本地缓存或降级模式")

    if result["proxy_set"]:
        print_info(f"检测到代理设置: HTTP_PROXY={os.environ.get('HTTP_PROXY')}")

    return result


def setup_env(network: dict) -> dict:
    """根据网络环境设置环境变量"""
    env = os.environ.copy()

    # 中国大陆使用 HF 镜像
    if network["in_china"] and not env.get("HF_ENDPOINT"):
        env["HF_ENDPOINT"] = "https://hf-mirror.com"
        print_info(f"已设置 HF_ENDPOINT={env['HF_ENDPOINT']}")

    # 优先使用 SQLite 作为本地快速启动数据库
    sqlite_url = f"sqlite:///{(BACKEND_DIR / 'talentmatch.db').as_posix()}"
    env.setdefault("DATABASE_URL", sqlite_url)
    print_info(f"数据库使用: {env['DATABASE_URL']}")

    # 关闭调度器，避免本地开发时自动触发采集任务
    env.setdefault("SCHEDULER_ENABLED", "false")

    # 没有 API Key 时自动降级为规则引擎
    if not env.get("OPENAI_API_KEY"):
        env.setdefault("USE_LOCAL_LLM", "true")
        print_info("未检测到 OPENAI_API_KEY，已启用本地 LLM 降级/规则引擎模式")

    return env


def create_venv(python: str) -> str:
    """如果不存在虚拟环境则创建"""
    if VENV_DIR.exists():
        return resolve_python()

    print_info("正在创建后端虚拟环境...")
    subprocess.run([python, "-m", "venv", str(VENV_DIR)], check=True)
    print_ok("虚拟环境创建完成")
    return resolve_python()


def install_backend_deps(python: str, env: dict, skip: bool = False) -> None:
    """安装后端依赖"""
    if skip:
        print_info("跳过后端依赖安装 (--skip-deps)")
        return

    print_info("正在安装/更新后端依赖...")
    req_file = BACKEND_DIR / "requirements.txt"
    subprocess.run(
        [python, "-m", "pip", "install", "-q", "--upgrade", "pip"],
        cwd=BACKEND_DIR,
        env=env,
        check=True,
    )
    subprocess.run(
        [python, "-m", "pip", "install", "-q", "-r", str(req_file)],
        cwd=BACKEND_DIR,
        env=env,
        check=True,
    )
    print_ok("后端依赖安装完成")


def init_backend_db(python: str, env: dict, seed: bool = True) -> None:
    """初始化数据库并注入种子数据"""
    print_info("正在初始化数据库...")
    subprocess.run([python, "scripts/init_db.py"], cwd=BACKEND_DIR, env=env, check=True)

    if seed:
        print_info("正在注入种子数据...")
        result = subprocess.run(
            [python, "scripts/seed_data.py"],
            cwd=BACKEND_DIR,
            env=env,
        )
        if result.returncode != 0:
            print_warn("种子数据注入失败（通常与 HuggingFace 模型下载有关），应用仍会启动")
    else:
        print_info("跳过种子数据注入 (--no-seed)")


def install_frontend_deps(npm: str, skip: bool = False) -> None:
    """安装前端依赖"""
    if skip:
        print_info("跳过前端依赖安装 (--skip-deps)")
        return

    if (FRONTEND_DIR / "node_modules").exists():
        print_info("检测到 node_modules，执行 npm install 以确保依赖一致...")
    else:
        print_info("正在安装前端依赖...")
    subprocess.run([npm, "install"], cwd=FRONTEND_DIR, check=True)
    print_ok("前端依赖安装完成")


def kill_process_on_port(port: int) -> None:
    """尝试释放被占用的端口"""
    os_type = get_os()
    try:
        if os_type == "windows":
            # 通过 netstat 查找 PID 并 taskkill
            result = subprocess.run(
                ["netstat", "-ano", "|", "findstr", f":{port}"],
                capture_output=True,
                text=True,
                shell=True,
            )
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 5 and f":{port}" in parts[1]:
                    pid = parts[-1]
                    subprocess.run(["taskkill", "/F", "/PID", pid], check=False)
                    print_info(f"已终止占用端口 {port} 的进程 PID={pid}")
        else:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True,
            )
            for pid in result.stdout.strip().split():
                subprocess.run(["kill", "-9", pid], check=False)
                print_info(f"已终止占用端口 {port} 的进程 PID={pid}")
    except Exception as e:
        print_warn(f"无法自动释放端口 {port}: {e}")


def start_backend(python: str, env: dict, port: int) -> subprocess.Popen:
    """启动后端服务，输出直接继承当前终端"""
    print_info(f"正在启动后端服务（端口 {port}）...")
    return subprocess.Popen(
        [
            python, "-m", "uvicorn", "app.main:app",
            "--host", "127.0.0.1", "--port", str(port), "--reload",
        ],
        cwd=BACKEND_DIR,
        env=env,
    )


def start_celery_worker(python: str, env: dict) -> subprocess.Popen:
    """启动 Celery Worker，输出直接继承当前终端"""
    print_info("正在启动 Celery Worker...")
    return subprocess.Popen(
        [
            python, "-m", "celery", "-A", "app.tasks.celery_app",
            "worker", "--loglevel=info", "--concurrency=2",
        ],
        cwd=BACKEND_DIR,
        env=env,
    )


def start_frontend(npm: str, env: dict, port: int) -> subprocess.Popen:
    """启动前端服务，输出直接继承当前终端"""
    print_info(f"正在启动前端服务（端口 {port}）...")
    return subprocess.Popen(
        [npm, "run", "dev", "--", "--host", "127.0.0.1", "--port", str(port)],
        cwd=FRONTEND_DIR,
        env=env,
    )


def wait_for_port(port: int, timeout: float = 60.0) -> bool:
    """等待端口就绪"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_port_open("127.0.0.1", port):
            return True
        time.sleep(0.5)
    return False


def start_docker() -> None:
    """使用 Docker Compose 启动"""
    if not shutil.which("docker") or not shutil.which("docker-compose"):
        print_error("未找到 docker 或 docker-compose，请安装 Docker 后再试")
        sys.exit(1)

    print_info("正在使用 Docker Compose 启动全栈...")
    subprocess.run(["docker", "compose", "up", "--build", "-d"], cwd=ROOT, check=True)
    print_ok("Docker 容器已启动")
    print_info("前端访问: http://localhost:5173")
    print_info("后端访问: http://localhost:8000")


def main() -> None:
    parser = argparse.ArgumentParser(description="TalentMatch 智能快速启动脚本")
    parser.add_argument("--backend-only", action="store_true", help="仅启动后端")
    parser.add_argument("--frontend-only", action="store_true", help="仅启动前端")
    parser.add_argument("--docker", action="store_true", help="使用 Docker Compose 启动")
    parser.add_argument("--no-seed", action="store_true", help="不注入种子数据")
    parser.add_argument("--skip-deps", action="store_true", help="跳过依赖安装")
    parser.add_argument("--port-backend", type=int, default=DEFAULT_BACKEND_PORT, help="后端端口")
    parser.add_argument("--port-frontend", type=int, default=DEFAULT_FRONTEND_PORT, help="前端端口")
    parser.add_argument("--kill-port", action="store_true", help="端口被占用时自动结束占用进程")
    parser.add_argument("--dry-run", action="store_true", help="仅检测环境，不启动服务")
    parser.add_argument("--open-browser", action="store_true", help="服务启动后自动打开浏览器")
    args = parser.parse_args()

    print_info(f"操作系统: {platform.system()} {platform.release()}")
    print_info(f"项目根目录: {ROOT}")

    # Docker 模式直接走 Docker Compose
    if args.docker:
        if args.dry_run:
            print_info("Docker 模式 --dry-run 仅检测 Docker 可用性")
            if shutil.which("docker") and shutil.which("docker-compose"):
                print_ok("Docker 和 docker-compose 已安装")
            else:
                print_error("未找到 docker 或 docker-compose")
                sys.exit(1)
            return
        start_docker()
        return

    # 解析环境
    python = resolve_python()
    print_info(f"Python: {python}")
    check_python_version(python)

    network = detect_network()
    env = setup_env(network)

    if args.dry_run:
        npm = resolve_npm()
        print_info(f"npm: {npm}")
        print_info(f"虚拟环境: {'已存在' if VENV_DIR.exists() else '未创建'}")
        print_info(f"后端端口 8000 占用: {is_port_open('127.0.0.1', 8000)}")
        print_info(f"前端端口 5173 占用: {is_port_open('127.0.0.1', 5173)}")
        print_ok("环境检测完成，--dry-run 结束")
        return

    # 仅前端模式
    if args.frontend_only:
        npm = resolve_npm()
        install_frontend_deps(npm, args.skip_deps)
        if is_port_open("127.0.0.1", args.port_frontend):
            if args.kill_port:
                kill_process_on_port(args.port_frontend)
            else:
                print_warn(f"端口 {args.port_frontend} 已被占用，尝试寻找可用端口...")
                args.port_frontend = find_free_port(args.port_frontend + 1)
        proc = start_frontend(npm, env, args.port_frontend)
        if wait_for_port(args.port_frontend):
            print_ok(f"前端已启动: http://127.0.0.1:{args.port_frontend}")
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
        return

    # 后端准备（默认及仅后端模式都需要）
    python = create_venv(python)
    install_backend_deps(python, env, args.skip_deps)
    init_backend_db(python, env, not args.no_seed)

    # 仅后端模式
    if args.backend_only:
        if is_port_open("127.0.0.1", args.port_backend):
            if args.kill_port:
                kill_process_on_port(args.port_backend)
            else:
                print_warn(f"端口 {args.port_backend} 已被占用，尝试寻找可用端口...")
                args.port_backend = find_free_port(args.port_backend + 1)
        backend_proc = start_backend(python, env, args.port_backend)
        worker_proc = start_celery_worker(python, env)
        if wait_for_port(args.port_backend):
            print_ok(f"后端已启动: http://127.0.0.1:{args.port_backend}")
            print_ok(f"API 文档: http://127.0.0.1:{args.port_backend}/docs")
            print_ok("Celery Worker 已启动")
        try:
            backend_proc.wait()
        except KeyboardInterrupt:
            print_info("\n正在停止服务...")
            backend_proc.terminate()
            worker_proc.terminate()
            backend_proc.wait(timeout=10)
            worker_proc.wait(timeout=10)
            print_ok("服务已停止")
        return

    # 全栈模式
    npm = resolve_npm()
    install_frontend_deps(npm, args.skip_deps)

    # 检查并处理端口占用
    for name, port in [("后端", args.port_backend), ("前端", args.port_frontend)]:
        if is_port_open("127.0.0.1", port):
            if args.kill_port:
                kill_process_on_port(port)
            else:
                print_warn(f"{name}端口 {port} 已被占用，尝试寻找可用端口...")
                if name == "后端":
                    args.port_backend = find_free_port(port + 1)
                else:
                    args.port_frontend = find_free_port(port + 1)

    backend_proc = start_backend(python, env, args.port_backend)
    worker_proc = start_celery_worker(python, env)
    if not wait_for_port(args.port_backend):
        print_error("后端服务启动超时")
        backend_proc.terminate()
        worker_proc.terminate()
        sys.exit(1)

    frontend_proc = start_frontend(npm, env, args.port_frontend)
    if not wait_for_port(args.port_frontend):
        print_error("前端服务启动超时")
        frontend_proc.terminate()
        backend_proc.terminate()
        worker_proc.terminate()
        sys.exit(1)

    url = f"http://127.0.0.1:{args.port_frontend}"
    print_ok("=" * 50)
    print_ok("TalentMatch 已启动")
    print_ok(f"  前端: {url}")
    print_ok(f"  后端: http://127.0.0.1:{args.port_backend}")
    print_ok(f"  API 文档: http://127.0.0.1:{args.port_backend}/docs")
    print_ok("  Celery Worker 已启动")
    print_ok("=" * 50)

    if args.open_browser:
        print_info(f"正在打开浏览器: {url}")
        webbrowser.open(url)

    print_info("按 Ctrl+C 停止所有服务")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print_info("\n正在停止服务...")
        backend_proc.terminate()
        worker_proc.terminate()
        frontend_proc.terminate()
        backend_proc.wait(timeout=10)
        worker_proc.wait(timeout=10)
        frontend_proc.wait(timeout=10)
        print_ok("服务已停止")


if __name__ == "__main__":
    main()
