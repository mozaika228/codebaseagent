# Contributing

## Scope

Contributions are welcome for:

- API stability and safety guardrails
- analysis quality and eval methodology
- frontend usability and observability
- CI reliability and test coverage

## Development flow

1. Create a branch from `main`
2. Make focused changes
3. Add or update tests
4. Run checks locally
5. Open a PR with rationale and risk notes

## Local checks

### API

```bash
cd apps/api
pip install -r requirements.txt
pytest tests -q --cov=app --cov-report=term
```

### Web

```bash
cd apps/web
pnpm install
pnpm typecheck
pnpm build
```

## PR checklist

- [ ] behavior change described
- [ ] tests added or updated
- [ ] no secret keys in code
- [ ] docs updated (README/docs/* when needed)
