from __future__ import annotations

from .graph import WorkerGraph
from .state import AgentState


def main() -> None:
    state: AgentState = {
        "repoId": "r_demo",
        "commitSha": "abc123",
        "changedFiles": [],
        "errors": [],
    }
    result = WorkerGraph().run(state)
    print("Worker run complete")
    print(result)


if __name__ == "__main__":
    main()