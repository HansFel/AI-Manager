from __future__ import annotations

import os

import uvicorn

from .projects import ProjectStore
from .registry import RegistryStore
from .security import UserStore
from .web import PROJECTS_PATH, REGISTRY_PATH, USERS_PATH


def bootstrap() -> None:
    RegistryStore(REGISTRY_PATH).init()
    ProjectStore(PROJECTS_PATH).init()

    admin_password = os.getenv("AIM_BOOTSTRAP_ADMIN_PASSWORD")
    admin_user = os.getenv("AIM_BOOTSTRAP_ADMIN_USER", "admin")
    users = UserStore(USERS_PATH)
    if admin_password and not users.load().get("users"):
        users.upsert_user(username=admin_user, password=admin_password, role="admin")


def main() -> None:
    bootstrap()
    host = os.getenv("AIM_HOST", "0.0.0.0")
    port = int(os.getenv("AIM_PORT", "8765"))
    uvicorn.run("ai_management.web:app", host=host, port=port)


if __name__ == "__main__":
    main()
