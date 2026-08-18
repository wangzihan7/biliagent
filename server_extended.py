#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 扩展版服务器 - 包含用户管理和持久化存储

import os
import socket
import sys
from typing import Optional

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from server.api_router import router
from server.exceptions import AppError
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

app = FastAPI(
    title="BiliAgent Server Extended",
    version="2.0",
    description="B站数据分析API - 支持用户管理、会话管理和持久化存储"
)


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 根路径重定向到文档
@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")

# 添加API路由
app.include_router(router)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _is_bind_error(exc: OSError) -> bool:
    errno = getattr(exc, "errno", None)
    if errno is None and exc.args:
        first = exc.args[0]
        errno = first if isinstance(first, int) else None
    return errno in {13, 48, 98, 10013, 10048}


def _can_listen(host: str, port: int):
    """
    Attempt to bind (and immediately release) a socket to verify permissions/availability.
    Returns tuple (True, None) when binding succeeds, otherwise (False, error).
    """
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        return False, None, exc

    last_error: Optional[OSError] = None
    for family, socktype, proto, _, addr in infos:
        try:
            with socket.socket(family, socktype, proto) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(addr)
                actual_port = sock.getsockname()[1]
            return True, actual_port, None
        except OSError as exc:
            last_error = exc

    return False, None, last_error or OSError(f"Unable to bind to {host}:{port}")


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Run the BiliAgent extended server.")
    parser.add_argument(
        "--host",
        default=os.getenv("SERVER_HOST", "127.0.0.1"),
        help="Host interface to bind (env: SERVER_HOST).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("SERVER_PORT", "8300")),
        help="Port to bind (env: SERVER_PORT).",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=_env_bool("SERVER_RELOAD", False),
        help="Enable autoreload (env: SERVER_RELOAD).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=int(os.getenv("SERVER_WORKERS", "1")),
        help="Number of worker processes (env: SERVER_WORKERS).",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("SERVER_LOG_LEVEL", "info"),
        help="Uvicorn log level (env: SERVER_LOG_LEVEL).",
    )
    parser.add_argument(
        "--max-port-attempts",
        type=int,
        default=int(os.getenv("SERVER_MAX_PORT_ATTEMPTS", "10")),
        help="How many times to try the next port when binding fails (env: SERVER_MAX_PORT_ATTEMPTS).",
    )
    parser.add_argument(
        "--auto-port",
        dest="auto_port",
        action="store_true",
        help="Automatically increment the port if binding fails (env: SERVER_AUTO_PORT).",
    )
    parser.add_argument(
        "--no-auto-port",
        dest="auto_port",
        action="store_false",
        help="Disable automatic port fallback.",
    )
    parser.set_defaults(auto_port=_env_bool("SERVER_AUTO_PORT", True))
    args = parser.parse_args()

    max_port_attempts = max(1, args.max_port_attempts)
    selected_host = args.host
    selected_port = args.port
    precheck_attempts = 0
    last_error: Optional[OSError] = None

    while True:
        can_bind, actual_port, error = _can_listen(selected_host, selected_port)
        if can_bind:
            selected_port = actual_port
            break

        last_error = error
        if not args.auto_port or precheck_attempts >= max_port_attempts:
            if args.auto_port:
                can_bind, actual_port, random_error = _can_listen(selected_host, 0)
                if can_bind:
                    print(
                        f"⚠️ Auto-selected port range exhausted ({last_error}). "
                        f"Falling back to OS-assigned port {actual_port}."
                    )
                    selected_port = actual_port
                    break
                last_error = random_error
            raise last_error or PermissionError(
                "Unable to bind to any port; try running with administrator privileges or choose --host 0.0.0.0"
            )

        next_port = selected_port + 1
        precheck_attempts += 1
        print(
            f"⚠️ Port {selected_port} unavailable during pre-check ({error}). "
            f"Trying port {next_port} [{precheck_attempts}/{max_port_attempts}]..."
        )
        selected_port = next_port

    run_kwargs = {
        "app": app,
        "host": selected_host,
        "port": selected_port,
        "log_level": args.log_level,
    }
    if args.reload:
        if args.workers != 1:
            print("⚠️ Reload mode only supports a single worker; forcing workers=1.")
        run_kwargs["reload"] = True
    else:
        run_kwargs["workers"] = args.workers

    attempts = 0
    current_port = selected_port

    while True:
        run_kwargs["port"] = current_port
        try:
            uvicorn.run(**run_kwargs)
            break
        except OSError as exc:
            if not _is_bind_error(exc):
                raise
            if not args.auto_port or attempts >= max_port_attempts:
                if args.auto_port:
                    can_bind, auto_port_val, random_error = _can_listen(selected_host, 0)
                    if can_bind:
                        print(
                            f"⚠️ Runtime bind failed on port {current_port} ({exc}). "
                            f"Switching to OS-assigned port {auto_port_val}."
                        )
                        current_port = auto_port_val
                        attempts = 0
                        continue
                    raise random_error or exc
                raise exc

            attempts += 1
            next_port = current_port + 1
            print(
                f"⚠️ Port {current_port} unavailable ({exc}). "
                f"Trying port {next_port} [{attempts}/{max_port_attempts}]..."
            )
            current_port = next_port
