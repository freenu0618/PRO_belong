# belong/web/api/jwt_utils.py
from __future__ import annotations

import datetime as dt
from functools import wraps
from typing import Any, Dict, Optional, List

import jwt
from flask import current_app, jsonify, request, g


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _jwt_alg_candidates() -> List[str]:
    """
    현재 설정값을 1순위로 두고, 개발 중 설정이 흔들렸을 때도
    검증이 되도록 HS256을 후보에 포함한다.
    """
    alg = (current_app.config.get("JWT_ALG") or "HS256").strip()
    # 중복 제거 + 순서 유지
    cands = []
    for a in [alg, "HS256"]:
        if a and a not in cands:
            cands.append(a)
    return cands


def _jwt_secret_candidates() -> List[str]:
    """
    ✅ 핵심: 발급/검증 시 사용 가능한 시크릿 후보를 모두 모아둔다.
    - JWT_SECRET, SECRET_KEY, fallback
    - None/빈문자 방어
    - 중복 제거
    """
    raw = [
        current_app.config.get("JWT_SECRET"),
        current_app.config.get("SECRET_KEY"),
        "dev-secret-change-me",
    ]

    cands: List[str] = []
    for s in raw:
        if not s:
            continue
        if isinstance(s, bytes):
            try:
                s = s.decode("utf-8", errors="ignore")
            except Exception:
                continue
        if not isinstance(s, str):
            continue
        s = s.strip()
        if not s:
            continue
        if s not in cands:
            cands.append(s)

    # 최후의 안전장치
    if not cands:
        cands = ["dev-secret-change-me"]

    return cands


def _jwt_exp_minutes() -> int:
    try:
        return int(current_app.config.get("JWT_EXPIRE_MINUTES") or 60)
    except Exception:
        return 60


def create_access_token(claims: Dict[str, Any]) -> str:
    """
    claims 예:
      {"sub": user.id, "username": user.username, "email": user.email}

    발급은 1순위 시크릿(후보 중 첫 번째)로 통일.
    """
    now = _utcnow()
    payload = dict(claims)
    payload["iat"] = int(now.timestamp())
    payload["exp"] = int((now + dt.timedelta(minutes=_jwt_exp_minutes())).timestamp())

    secret = _jwt_secret_candidates()[0]
    alg = _jwt_alg_candidates()[0]

    token = jwt.encode(payload, secret, algorithm=alg)

    # PyJWT v2는 str, v1은 bytes일 수 있어 방어
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def _get_bearer_token() -> Optional[str]:
    auth = (request.headers.get("Authorization", "") or "").strip()

    # "Bearer <token>" (대소문자/공백 방어)
    if not auth.lower().startswith("bearer"):
        return None

    parts = auth.split(None, 1)  # 공백 기준 2조각
    if len(parts) != 2:
        return None

    token = parts[1].strip()

    # 혹시 "토큰" 처럼 따옴표가 들어가면 제거
    if (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
        token = token[1:-1].strip()

    return token or None


def _decode_with_candidates(token: str) -> Dict[str, Any]:
    """
    시크릿/알고리즘 후보로 순차 디코드 시도.
    발급/검증 설정이 바뀌는 개발 단계에서 '빙빙 도는' 문제를 끊는 용도.
    """
    last_err: Exception | None = None
    algs = _jwt_alg_candidates()
    secrets = _jwt_secret_candidates()

    for alg in algs:
        for secret in secrets:
            try:
                return jwt.decode(
                    token,
                    secret,
                    algorithms=[alg],
                    options={"require": ["exp", "iat"]},
                )
            except Exception as e:
                last_err = e
                continue

    # 전부 실패면 마지막 에러를 올린다
    if last_err:
        raise last_err
    raise jwt.InvalidTokenError("decode failed")


def jwt_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        token = _get_bearer_token()
        if not token:
            return jsonify({"status": "error", "message": "인증 토큰이 필요합니다."}), 401

        try:
            payload = _decode_with_candidates(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"status": "error", "message": "토큰이 만료되었습니다."}), 401
        except jwt.InvalidTokenError as e:
            # 디버그 모드면 원인도 같이 내려서 바로 잡기 쉽게
            if current_app.debug:
                return jsonify(
                    {
                        "status": "error",
                        "message": "유효하지 않은 토큰입니다.",
                        "debug": {
                            "reason": e.__class__.__name__,
                            "detail": str(e),
                            "alg_candidates": _jwt_alg_candidates(),
                            "secret_candidates_count": len(_jwt_secret_candidates()),
                        },
                    }
                ), 401
            return jsonify({"status": "error", "message": "유효하지 않은 토큰입니다."}), 401

        g.jwt_payload = payload
        return view_func(*args, **kwargs)

    return wrapper
