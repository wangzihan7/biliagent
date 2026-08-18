#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 简易 JWT 工具（HS256）

import os
import time
import hmac
import json
import base64
from typing import Dict, Optional


JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALG = "HS256"
JWT_EXPIRE_SECONDS = int(os.getenv("JWT_EXPIRE_SECONDS", "86400"))  # 默认 1 天


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(payload: Dict, expires_in: Optional[int] = None) -> str:
    """生成 HS256 JWT"""
    exp = int(time.time()) + (expires_in or JWT_EXPIRE_SECONDS)
    header = {"alg": JWT_ALG, "typ": "JWT"}
    payload = {**payload, "exp": exp}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(JWT_SECRET.encode("utf-8"), signing_input, "sha256").digest()
    token = f"{header_b64}.{payload_b64}.{_b64url_encode(signature)}"
    return token


def decode_token(token: str) -> Dict:
    """验证并解码 JWT，过期或签名错误则抛异常"""
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError:
        raise ValueError("invalid token format")
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(JWT_SECRET.encode("utf-8"), signing_input, "sha256").digest()
    actual_sig = _b64url_decode(sig_b64)
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("invalid signature")
    payload = json.loads(_b64url_decode(payload_b64))
    if "exp" in payload and int(time.time()) > int(payload["exp"]):
        raise ValueError("token expired")
    return payload
