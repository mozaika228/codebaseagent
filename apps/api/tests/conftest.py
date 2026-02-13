from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

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
