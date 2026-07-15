from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any

HASH_NAME = "pbkdf2_sha256"
ITERATIONS = 240_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return "$".join(
        [
            HASH_NAME,
            str(ITERATIONS),
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(digest).decode("ascii"),
        ]
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        name, iterations, salt, digest = encoded.split("$", 3)
        if name != HASH_NAME:
            return False
        expected = base64.b64decode(digest.encode("ascii"))
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            base64.b64decode(salt.encode("ascii")),
            int(iterations),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


class UserStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "users": []}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def upsert_user(self, username: str, password: str, role: str = "admin") -> bool:
        payload = self.load()
        users = payload.setdefault("users", [])
        encoded = hash_password(password)
        for user in users:
            if user["username"].lower() == username.lower():
                user["password_hash"] = encoded
                user["role"] = role
                self.save(payload)
                return False
        users.append({"username": username, "password_hash": encoded, "role": role})
        self.save(payload)
        return True

    def authenticate(self, username: str, password: str) -> dict[str, str] | None:
        for user in self.load().get("users", []):
            if user["username"].lower() == username.lower() and verify_password(
                password, user.get("password_hash", "")
            ):
                return {"username": user["username"], "role": user.get("role", "user")}
        return None


def get_or_create_secret(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    path.parent.mkdir(parents=True, exist_ok=True)
    secret = base64.urlsafe_b64encode(os.urandom(48)).decode("ascii")
    path.write_text(secret, encoding="utf-8")
    return secret
