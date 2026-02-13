from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

# Ensure tests can import `app` package both locally and in CI.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.store import store


@pytest.fixture(autouse=True)
def clear_store() -> Generator[None, None, None]:
    store.repos.clear()
    store.analyses.clear()
    store.proposals.clear()
    store.runs.clear()
    yield
    store.repos.clear()
    store.analyses.clear()
    store.proposals.clear()
    store.runs.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
