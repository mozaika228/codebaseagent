from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class InMemoryStore:
    repos: dict[str, dict[str, Any]] = field(default_factory=dict)
    analyses: dict[str, dict[str, Any]] = field(default_factory=dict)
    proposals: dict[str, dict[str, Any]] = field(default_factory=dict)
    runs: dict[str, dict[str, Any]] = field(default_factory=dict)


store = InMemoryStore()