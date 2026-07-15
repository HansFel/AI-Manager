from __future__ import annotations

import os
from pathlib import Path

import yaml
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .models import EntryKind, ModelsFile
from .projects import ProjectStore
from .registry import RegistryStore, fingerprint
from .security import UserStore, get_or_create_secret

PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = PACKAGE_DIR / "web_assets" / "templates"
STATIC_DIR = PACKAGE_DIR / "web_assets" / "static"
DATA_DIR = Path(os.getenv("AIM_DATA_DIR", ".ai-management"))
REGISTRY_PATH = DATA_DIR / "registry.json"
PROJECTS_PATH = DATA_DIR / "projects.json"
USERS_PATH = DATA_DIR / "users.local.json"
SESSION_KEY_PATH = DATA_DIR / "session.local.key"
MODELS_PATH = Path("configs/models.example.yaml")

app = FastAPI(title="AI Management Hub")
app.add_middleware(SessionMiddleware, secret_key=get_or_create_secret(SESSION_KEY_PATH), same_site="lax")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATE_DIR)


def registry_store() -> RegistryStore:
    return RegistryStore(REGISTRY_PATH)


def user_store() -> UserStore:
    return UserStore(USERS_PATH)


def project_store() -> ProjectStore:
    return ProjectStore(PROJECTS_PATH)


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


def projects_context() -> dict:
    catalog = project_store().load()
    project_names = {project.id: project.name for project in catalog.projects}
    return {
        "catalog": catalog,
        "project_names": project_names,
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
    project_context = projects_context()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "user": user,
            "models": models.models,
            **project_context,
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


@app.get("/projects")
def projects(request: Request):
    user = require_user(request)
    if not isinstance(user, dict):
        return user
    return templates.TemplateResponse(
        request=request,
        name="projects.html",
        context={
            "request": request,
            "user": user,
            "created_project": None,
            "created_commonality": None,
            **projects_context(),
        },
    )


@app.post("/projects/create")
def create_project(
    request: Request,
    name: str = Form(...),
    repo_url: str = Form(""),
    local_path: str = Form(""),
    description: str = Form(""),
    tags: str = Form(""),
    owner: str = Form(""),
    status: str = Form("active"),
):
    user = require_user(request)
    if not isinstance(user, dict):
        return user
    entry = project_store().add_project(
        name=name,
        repo_url=repo_url,
        local_path=local_path,
        description=description,
        tags=parse_tags(tags),
        status=status,
        owner=owner,
    )
    return templates.TemplateResponse(
        request=request,
        name="projects.html",
        context={
            "request": request,
            "user": user,
            "created_project": entry,
            "created_commonality": None,
            **projects_context(),
        },
    )


@app.post("/projects/commonalities/create")
def create_commonality(
    request: Request,
    title: str = Form(...),
    category: str = Form("shared"),
    description: str = Form(""),
    project_ids: list[str] = Form([]),
    tags: str = Form(""),
):
    user = require_user(request)
    if not isinstance(user, dict):
        return user
    entry = project_store().add_commonality(
        title=title,
        category=category,
        description=description,
        project_ids=project_ids,
        tags=parse_tags(tags),
    )
    return templates.TemplateResponse(
        request=request,
        name="projects.html",
        context={
            "request": request,
            "user": user,
            "created_project": None,
            "created_commonality": entry,
            **projects_context(),
        },
    )


def parse_tags(value: str) -> list[str]:
    return [tag.strip() for tag in value.split(",") if tag.strip()]
