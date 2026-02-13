# Eval Methodology

## Goal
Quantify whether the agent is useful and safe compared to baseline manual workflow.

## Procedure
1. Run fixed benchmark repositories and tasks.
2. Capture latency, CI pass, human acceptance, and regression events.
3. Compare model and prompt versions on identical task set.

## Reporting
Maintain monthly table in `packages/evals/metrics.csv` and summarize trends in release notes.