from __future__ import annotations

from pathlib import Path

import yaml
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .models import EntryKind, ModelsFile
from .registry import RegistryStore, fingerprint
from .security import UserStore, get_or_create_secret

PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = PACKAGE_DIR / "web_assets" / "templates"
STATIC_DIR = PACKAGE_DIR / "web_assets" / "static"
REGISTRY_PATH = Path(".ai-management/registry.json")
USERS_PATH = Path(".ai-management/users.local.json")
SESSION_KEY_PATH = Path(".ai-management/session.local.key")
MODELS_PATH = Path("configs/models.example.yaml")

app = FastAPI(title="AI Management Hub")
app.add_middleware(SessionMiddleware, secret_key=get_or_create_secret(SESSION_KEY_PATH), same_site="lax")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATE_DIR)


def registry_store() -> RegistryStore:
    return RegistryStore(REGISTRY_PATH)


def user_store() -> UserStore:
    return UserStore(USERS_PATH)


def current_user(request: Request) -> dict[str, str] | None:
    return request.session.get("user")


def require_user(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return user


def load_models() -> ModelsFile:
    if not MODELS_PATH.exists():
        return ModelsFile()
    return ModelsFile.model_validate(yaml.safe_load(MODELS_PATH.read_text(encoding="utf-8")))


def registry_context() -> dict:
    registry = registry_store().load()
    skills = [entry for entry in registry.entries if entry.kind == EntryKind.SKILL]
    agents = [entry for entry in registry.entries if entry.kind == EntryKind.AGENT]
    duplicate_groups = registry_store().duplicate_groups()
    return {
        "registry": registry,
        "skills": skills,
        "agents": agents,
        "duplicate_groups": duplicate_groups,
    }


@app.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "has_users": bool(user_store().load().get("users")),
            "error": None,
        },
    )


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = user_store().authenticate(username, password)
    if not user:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request": request,
                "has_users": bool(user_store().load().get("users")),
                "error": "Anmeldung fehlgeschlagen.",
            },
            status_code=401,
        )
    request.session["user"] = user
    return RedirectResponse("/", status_code=303)


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@app.get("/")
def dashboard(request: Request):
    user = require_user(request)
    if not isinstance(user, dict):
        return user
    models = load_models()
    context = registry_context()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "user": user,
            "models": models.models,
            **context,
        },
    )


@app.get("/registry")
def registry(request: Request):
    user = require_user(request)
    if not isinstance(user, dict):
        return user
    return templates.TemplateResponse(
        request=request,
        name="registry.html",
        context={
            "request": request,
            "user": user,
            "candidate": None,
            "matches": [],
            "created": None,
            **registry_context(),
        },
    )


@app.post("/registry/check")
def check_registry(
    request: Request,
    kind: EntryKind = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
):
    user = require_user(request)
    if not isinstance(user, dict):
        return user
    tag_list = parse_tags(tags)
    matches = registry_store().find_similar(fingerprint(name, description, tag_list), kind=kind)
    return templates.TemplateResponse(
        request=request,
        name="registry.html",
        context={
            "request": request,
            "user": user,
            "candidate": {
                "kind": kind,
                "name": name,
                "description": description,
                "tags": tags,
            },
            "matches": matches,
            "created": None,
            **registry_context(),
        },
    )


@app.post("/registry/create")
def create_registry_entry(
    request: Request,
    kind: EntryKind = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
):
    user = require_user(request)
    if not isinstance(user, dict):
        return user
    entry, matches = registry_store().add_entry(kind, name, description, parse_tags(tags))
    return templates.TemplateResponse(
        request=request,
        name="registry.html",
        context={
            "request": request,
            "user": user,
            "candidate": None,
            "matches": matches,
            "created": entry,
            **registry_context(),
        },
    )


@app.get("/models")
def models(request: Request):
    user = require_user(request)
    if not isinstance(user, dict):
        return user
    parsed = load_models()
    return templates.TemplateResponse(
        request=request,
        name="models.html",
        context={
            "request": request,
            "user": user,
            "models": sorted(parsed.models, key=lambda item: item.priority, reverse=True),
            "routing": parsed.routing,
        },
    )


def parse_tags(value: str) -> list[str]:
    return [tag.strip() for tag in value.split(",") if tag.strip()]
