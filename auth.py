"""
JWT auth for the admin dashboard/API. The original project has no
mention of access control at all — anyone on the network could open the
dashboard and export attendance data. This adds a minimal login endpoint
and a decorator to protect routes.
"""
from __future__ import annotations

import datetime as dt
import functools
import hashlib
import hmac

import jwt
from flask import request, jsonify, g

from config import Config


def hash_password(password: str, salt: str = "fras-static-salt") -> str:
    """
    Simple salted SHA-256 for the single local admin account. For a
    multi-user system, swap this for passlib/bcrypt — kept dependency-light
    here since there's exactly one credential to manage.
    """
    return hashlib.sha256((salt + password).encode()).hexdigest()


def verify_password(password: str, expected_hash: str) -> bool:
    return hmac.compare_digest(hash_password(password), expected_hash or "")


def issue_token(username: str) -> str:
    payload = {
        "sub": username,
        "iat": dt.datetime.utcnow(),
        "exp": dt.datetime.utcnow() + Config.JWT_EXPIRY,
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "") if auth_header else request.cookies.get("fras_token")
        if not token:
            return jsonify({"error": "Authentication required"}), 401
        try:
            payload = decode_token(token)
            g.user = payload["sub"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Session expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return view(*args, **kwargs)
    return wrapped
