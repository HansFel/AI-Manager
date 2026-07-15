from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EntryKind(StrEnum):
    AGENT = "agent"
    SKILL = "skill"


class RegistryEntry(BaseModel):
    id: str
    kind: EntryKind
    name: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    fingerprint: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)


class Registry(BaseModel):
    version: int = 1
    entries: list[RegistryEntry] = Field(default_factory=list)


class ModelConfig(BaseModel):
    id: str
    provider: str
    display_name: str
    roles: list[str] = Field(default_factory=list)
    priority: int = 0
    enabled: bool = True


class ModelsFile(BaseModel):
    models: list[ModelConfig] = Field(default_factory=list)
    routing: dict[str, Any] = Field(default_factory=dict)


class ProjectEntry(BaseModel):
    id: str
    name: str
    repo_url: str = ""
    local_path: str = ""
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    status: str = "active"
    owner: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)


class CommonalityEntry(BaseModel):
    id: str
    title: str
    category: str = "shared"
    description: str = ""
    project_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProjectCatalog(BaseModel):
    version: int = 1
    projects: list[ProjectEntry] = Field(default_factory=list)
    commonalities: list[CommonalityEntry] = Field(default_factory=list)
