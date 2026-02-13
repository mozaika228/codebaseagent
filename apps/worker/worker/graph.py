from __future__ import annotations

from .state import AgentState


class WorkerGraph:
    """MVP orchestration scaffold matching the planned LangGraph node sequence."""

    def run(self, state: AgentState) -> AgentState:
        state = self.ingest_repo(state)
        state = self.build_code_map(state)
        state = self.summarize_architecture(state)
        state = self.select_safe_refactor(state)

        if state.get("riskLevel") == "high":
            state.setdefault("errors", []).append("High risk refactor blocked")
            return state

        state = self.generate_patch(state)
        state = self.static_review(state)
        state = self.run_sandbox_tests(state)

        if not state.get("testResults", {}).get("passed", False):
            state.setdefault("errors", []).append("Tests failed; PR generation skipped")
            return state

        state = self.create_pr_draft(state)
        return self.finalize_report(state)

    def ingest_repo(self, state: AgentState) -> AgentState:
        return state

    def build_code_map(self, state: AgentState) -> AgentState:
        return state

    def summarize_architecture(self, state: AgentState) -> AgentState:
        state["analysisId"] = "a_demo"
        return state

    def select_safe_refactor(self, state: AgentState) -> AgentState:
        state["proposalId"] = "p_demo"
        state["riskLevel"] = "low"
        state["changedFiles"] = ["src/api/user.ts", "src/core/validate.ts"]
        return state

    def generate_patch(self, state: AgentState) -> AgentState:
        state["patch"] = "diff --git a/src/api/user.ts b/src/api/user.ts"
        return state

    def static_review(self, state: AgentState) -> AgentState:
        return state

    def run_sandbox_tests(self, state: AgentState) -> AgentState:
        state["testResults"] = {"passed": True, "summary": "pytest: 42 passed"}
        return state

    def create_pr_draft(self, state: AgentState) -> AgentState:
        state["prUrl"] = "https://github.com/example/repo/pull/42"
        return state

    def finalize_report(self, state: AgentState) -> AgentState:
        state.setdefault("errors", [])
        return state