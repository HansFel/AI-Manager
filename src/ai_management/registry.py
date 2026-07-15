from __future__ import annotations

import json
import re
import uuid
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

from .models import EntryKind, Registry, RegistryEntry

STOP_WORDS = {
    "a",
    "ai",
    "an",
    "and",
    "der",
    "die",
    "das",
    "for",
    "fuer",
    "in",
    "of",
    "the",
    "to",
    "und",
}


def normalize_text(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", " ", value.lower())
    tokens = [token for token in cleaned.split() if token not in STOP_WORDS]
    return " ".join(sorted(tokens))


def fingerprint(name: str, description: str = "", tags: list[str] | None = None) -> str:
    parts = [name, description, " ".join(tags or [])]
    return normalize_text(" ".join(parts))


def similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


class RegistryStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> Registry:
        if not self.path.exists():
            return Registry()
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return Registry.model_validate(raw)

    def save(self, registry: Registry) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = registry.model_dump(mode="json")
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def init(self) -> bool:
        if self.path.exists():
            return False
        self.save(Registry())
        return True

    def add_entry(
        self,
        kind: EntryKind,
        name: str,
        description: str = "",
        tags: list[str] | None = None,
        metadata: dict | None = None,
    ) -> tuple[RegistryEntry, list[tuple[RegistryEntry, float]]]:
        registry = self.load()
        fp = fingerprint(name, description, tags)
        matches = self.find_similar(fp, kind=kind, registry=registry)
        entry = RegistryEntry(
            id=str(uuid.uuid4()),
            kind=kind,
            name=name,
            description=description,
            tags=tags or [],
            fingerprint=fp,
            metadata=metadata or {},
        )
        registry.entries.append(entry)
        self.save(registry)
        return entry, matches

    def find_similar(
        self,
        fp: str,
        kind: EntryKind | None = None,
        registry: Registry | None = None,
        threshold: float = 0.72,
    ) -> list[tuple[RegistryEntry, float]]:
        registry = registry or self.load()
        matches: list[tuple[RegistryEntry, float]] = []
        for entry in registry.entries:
            if kind and entry.kind != kind:
                continue
            score = similarity(fp, entry.fingerprint)
            if score >= threshold:
                matches.append((entry, score))
        return sorted(matches, key=lambda item: item[1], reverse=True)

    def duplicate_groups(self, threshold: float = 0.78) -> list[list[tuple[RegistryEntry, float]]]:
        registry = self.load()
        by_kind: dict[EntryKind, list[RegistryEntry]] = defaultdict(list)
        for entry in registry.entries:
            by_kind[entry.kind].append(entry)

        groups: list[list[tuple[RegistryEntry, float]]] = []
        seen: set[str] = set()
        for entries in by_kind.values():
            for entry in entries:
                if entry.id in seen:
                    continue
                group = [(entry, 1.0)]
                for other in entries:
                    if other.id == entry.id:
                        continue
                    score = similarity(entry.fingerprint, other.fingerprint)
                    if score >= threshold:
                        group.append((other, score))
                if len(group) > 1:
                    for grouped_entry, _ in group:
                        seen.add(grouped_entry.id)
                    groups.append(sorted(group, key=lambda item: item[1], reverse=True))
        return groups
