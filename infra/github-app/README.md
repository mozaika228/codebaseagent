# GitHub App Setup

Use a GitHub App for server-to-server PR creation.

## Required Environment Variables

- `GITHUB_APP_ID`
- `GITHUB_APP_INSTALLATION_ID`
- `GITHUB_APP_PRIVATE_KEY`

`GITHUB_APP_PRIVATE_KEY` must contain the PEM private key text.

## Minimal Permissions

- Repository permissions:
- `Contents: Read & write`
- `Pull requests: Read & write`
- `Metadata: Read-only`

## Event Subscriptions

For MVP PR creation flow, no webhook is strictly required.
If you later add async sync, subscribe to:

- `pull_request`
- `push`
- `installation_repositories`
