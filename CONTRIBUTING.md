# Contributing

Thanks for contributing to `atlassian-sprint-review-summary`.

```mermaid
flowchart LR
  Dev[Contributor] --> Setup[poetry install]
  Setup --> Checks[format lint test sam validate]
  Checks --> PR[Open Pull Request]
```

## Development Setup

```bash
poetry install
```

## Quality Checks

Run before opening a PR:

```bash
poetry run poe format
poetry run poe lint
poetry run poe test
sam validate --region eu-central-1
```

## Pull Request Guidelines

- Keep changes focused and small.
- Update docs when behavior or configuration changes.
- Add or update tests for logic changes.
- Avoid committing secrets, credentials, or personal IDs.
