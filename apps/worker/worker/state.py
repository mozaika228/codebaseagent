from __future__ import annotations

from typing import Literal, TypedDict


class TestResults(TypedDict):
    passed: bool
    summary: str


class AgentState(TypedDict, total=False):
    repoId: str
    commitSha: str
    analysisId: str
    proposalId: str
    changedFiles: list[str]
    patch: str
    testResults: TestResults
    riskLevel: Literal["low", "medium", "high"]
    prUrl: str
    errors: list[str]