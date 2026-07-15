from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .models import CommonalityEntry, ProjectCatalog, ProjectEntry


class ProjectStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> ProjectCatalog:
        if not self.path.exists():
            return ProjectCatalog()
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return ProjectCatalog.model_validate(raw)

    def save(self, catalog: ProjectCatalog) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = catalog.model_dump(mode="json")
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def init(self) -> bool:
        if self.path.exists():
            return False
        self.save(ProjectCatalog())
        return True

    def add_project(
        self,
        name: str,
        repo_url: str = "",
        local_path: str = "",
        description: str = "",
        tags: list[str] | None = None,
        status: str = "active",
        owner: str = "",
    ) -> ProjectEntry:
        catalog = self.load()
        now = datetime.now(timezone.utc).isoformat()
        entry = ProjectEntry(
            id=str(uuid.uuid4()),
            name=name,
            repo_url=repo_url,
            local_path=local_path,
            description=description,
            tags=tags or [],
            status=status,
            owner=owner,
            created_at=now,
            updated_at=now,
        )
        catalog.projects.append(entry)
        self.save(catalog)
        return entry

    def add_commonality(
        self,
        title: str,
        category: str = "shared",
        description: str = "",
        project_ids: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> CommonalityEntry:
        catalog = self.load()
        now = datetime.now(timezone.utc).isoformat()
        entry = CommonalityEntry(
            id=str(uuid.uuid4()),
            title=title,
            category=category,
            description=description,
            project_ids=project_ids or [],
            tags=tags or [],
            created_at=now,
            updated_at=now,
        )
        catalog.commonalities.append(entry)
        self.save(catalog)
        return entry

    def project_name_map(self) -> dict[str, str]:
        return {project.id: project.name for project in self.load().projects}
