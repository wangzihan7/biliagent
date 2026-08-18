import os
import re
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"
RUN_TIMESTAMP = os.getenv("RUN_TIMESTAMP") or datetime.now().strftime("%Y%m%d-%H%M%S")
BASE_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "runs" / RUN_TIMESTAMP

# 轻量代理管理：仅使用环境变量或从 PROXY_EXTRACT_URL 拉取一次
_LOGGED_ENV_PROXY = False
_INLINE_PROXY = None
_LAST_INLINE_FETCH = 0.0
_INLINE_FETCH_INTERVAL = int(os.getenv("PROXY_REFRESH_INTERVAL_SEC", "40"))
_PROXY_EXTRACT_URL = os.getenv("PROXY_EXTRACT_URL")


def _get_env(name: str) -> str:
    """Read an environment variable by trying both upper and lower case keys."""
    return os.getenv(name) or os.getenv(name.lower(), "") or ""


def build_cookie_string() -> str:
    """
    Build a minimal cookie string required for authenticated Bilibili requests.
    Values are read from environment variables (upper or lower case):
    - SESSDATA / sessdata
    - bili_jct
    - buvid3
    - DedeUserID / dedeuserid
    """
    parts = []

    sessdata = _get_env("SESSDATA")
    bili_jct = _get_env("bili_jct")
    buvid3 = _get_env("buvid3")
    dedeuserid = _get_env("DedeUserID") or _get_env("dedeuserid")

    if sessdata:
        parts.append(f"SESSDATA={sessdata}")
    if bili_jct:
        parts.append(f"bili_jct={bili_jct}")
    if buvid3:
        parts.append(f"buvid3={buvid3}")
    if dedeuserid:
        parts.append(f"DedeUserID={dedeuserid}")

    return "; ".join(parts)


def build_headers(
    referer: Optional[str] = None, user_agent: str = DEFAULT_USER_AGENT
) -> Dict[str, str]:
    """Return standard request headers with optional referer and cookies."""
    headers: Dict[str, str] = {
        "User-Agent": user_agent,
    }
    if referer:
        headers["Referer"] = referer

    cookie = build_cookie_string()
    if cookie:
        headers["Cookie"] = cookie

    return headers


def get_proxies() -> Optional[Dict[str, str]]:
    """
    Build a proxies dict for requests if USE_PROXY is enabled.
    Reads from PROXY / HTTP_PROXY / HTTPS_PROXY envs; 不再从 bilibili_tools 拉取代理池。
    """
    if not USE_PROXY:
        try:
            print("[proxy] disabled (USE_PROXY=false)")
        except Exception:
            pass
        return None
    proxy = _get_env("PROXY") or _get_env("HTTP_PROXY") or _get_env("HTTPS_PROXY")
    if not proxy:
        # 尝试从 PROXY_EXTRACT_URL 拉取一次
        if not _PROXY_EXTRACT_URL:
            print("[proxy] enabled but no PROXY env or PROXY_EXTRACT_URL, skip")
            return None
        global _INLINE_PROXY, _LAST_INLINE_FETCH
        now = time.time()
        if not _INLINE_PROXY or (now - _LAST_INLINE_FETCH) > _INLINE_FETCH_INTERVAL:
            try:
                print("[proxy] fetching proxy from PROXY_EXTRACT_URL ...")
                resp = requests.get(_PROXY_EXTRACT_URL, timeout=10)
                if resp.status_code == 200:
                    raw = resp.text.strip().splitlines()
                    first = raw[0].strip() if raw else ""
                    if ":" in first:
                        proxy_str = first if first.startswith("http") else f"http://{first}"
                        _INLINE_PROXY = {"http": proxy_str, "https": proxy_str}
                        _LAST_INLINE_FETCH = now
                        print(f"[proxy] got proxy {proxy_str}")
                    else:
                        print(f"[proxy] invalid proxy format from extract url: {first}")
                        _INLINE_PROXY = None
                else:
                    print(f"[proxy] fetch proxy failed status={resp.status_code}")
            except Exception as e:
                print(f"[proxy] fetch proxy error: {e}")
                _INLINE_PROXY = None
        return _INLINE_PROXY

    global _LOGGED_ENV_PROXY
    if not _LOGGED_ENV_PROXY:
        try:
            print(f"[proxy] using proxy: {proxy}")
        except Exception:
            pass
        _LOGGED_ENV_PROXY = True
    return {
        "http": proxy,
        "https": proxy,
    }


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_output_dir(kind: str) -> Path:
    """Default output directory under runs/<timestamp>/<kind>."""
    return ensure_dir(BASE_OUTPUT_DIR / kind)


_INVALID_CHARS = re.compile(r'[\\/*?:"<>|]')


def sanitize_filename(name: str) -> str:
    """Remove characters not allowed in file names on common OS."""
    return _INVALID_CHARS.sub("", name)
