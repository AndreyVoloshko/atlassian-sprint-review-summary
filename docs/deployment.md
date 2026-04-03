# Deployment Guide

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| AWS SAM CLI | >= 1.100 | [Install guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) |
| AWS CLI | >= 2.0 | [Install guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) |
| Python | >= 3.12 | [python.org](https://www.python.org/downloads/) |
| Poetry | >= 1.8 | [Poetry docs](https://python-poetry.org/docs/) |

You also need:

- AWS credentials configured (`aws configure` or environment variables)
- Amazon Bedrock model access enabled in `eu-central-1` (see below)

## Enable Bedrock Model Access

1. Open the [Amazon Bedrock console](https://console.aws.amazon.com/bedrock/) in **eu-central-1**
2. Go to **Model access** in the left navigation
3. Click **Manage model access**
4. Enable **Amazon Nova Micro** (or your preferred model)
5. Save — Amazon-owned models are usually granted instantly

## First Deployment

```bash
sam build
sam deploy --guided
```

The guided wizard will ask for parameter values. Press Enter to accept defaults, or override:

| Parameter | Default | What to set |
|-----------|---------|-------------|
| Stack name | — | `atlassian-sprint-review-summary` |
| Region | — | `eu-central-1` |
| `StageName` | `prod` | `prod` |
| `BedrockModelId` | `eu.amazon.nova-micro-v1:0` | Keep default for cheapest |
| `AuthMode` | `api-key` | `api-key` for simple setup, `forge-jwt` for Forge apps |
| Confirm changeset | — | `y` |

After deployment, SAM prints the stack outputs including your API endpoint.

## Subsequent Deployments

```bash
sam build && sam deploy
```

SAM reads saved config from `samconfig.toml`.

## Dev Environment Deployment

```bash
sam build && sam deploy --config-env dev
```

This uses the `[dev]` profile in `samconfig.toml` — no auth, debug logging.

## Retrieve Your API Key

After deploying with `AuthMode=api-key`:

```bash
# Get stack outputs (includes API ID)
aws cloudformation describe-stacks \
  --stack-name atlassian-sprint-review-summary \
  --region eu-central-1 \
  --query 'Stacks[0].Outputs' \
  --output table

# List all API keys with values
aws apigateway get-api-keys \
  --include-values \
  --region eu-central-1 \
  --output table
```

Or find the key in the [API Gateway Console](https://console.aws.amazon.com/apigateway/) → atlassian-sprint-review-summary → API Keys.

## Verify Deployment

```bash
# Health check (no auth required)
curl https://<API_ID>.execute-api.eu-central-1.amazonaws.com/prod/health

# Generate a summary
curl -X POST https://<API_ID>.execute-api.eu-central-1.amazonaws.com/prod/summarize \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <FORGE_INVOCATION_TOKEN>" \
  -d @events/summarize.json
```

If your deployment uses `AuthMode=api-key`, call with `x-api-key: <YOUR_KEY>` instead.

## Override Parameters at Deploy Time

```bash
sam deploy --parameter-overrides \
  BedrockModelId="eu.amazon.nova-lite-v1:0" \
  AuthMode="forge-jwt" \
  ForgeAppId="ari:cloud:ecosystem::app/YOUR_APP_ID"
```

To override generation parameters like `temperature`, `max_tokens`, or `top_p`, update `config.yaml` (or pass per-request `model_params` in the API payload).

## Tear Down

```bash
sam delete --stack-name atlassian-sprint-review-summary
```

This removes all AWS resources created by the stack.

## Local Development

```bash
poetry install

# Run tests
poetry run pytest tests/ -v

# Local invoke (requires AWS credentials with Bedrock access)
sam local invoke SummarizeFunction -e events/summarize.json

# Local API (starts a local API Gateway)
sam local start-api
```

### Script Shortcuts

The project uses npm-style tasks via Poetry (`poethepoet`) defined in `pyproject.toml`:

```bash
poetry run poe test       # pytest tests/ -v
poetry run poe lint       # ruff check src tests
poetry run poe format     # ruff format src tests
poetry run poe invoke     # sam local invoke SummarizeFunction -e events/summarize.json
poetry run poe start-api  # sam local start-api
poetry run poe build      # sam build
poetry run poe deploy     # sam deploy
poetry run poe deploy-dev # sam deploy --config-env dev
```

## CI/CD

The project is structured for straightforward CI:

```bash
sam build
sam validate
pytest tests/ -v
sam deploy --no-confirm-changeset
```
