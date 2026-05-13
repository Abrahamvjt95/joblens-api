# JobLens API

Serverless tech job search engine backend. An AWS Lambda ETL pipeline aggregates real listings from four public job APIs, normalises and indexes them into Amazon OpenSearch, and exposes a search + autocomplete REST API via API Gateway.

## Architecture

```
EventBridge (daily cron)
    └── Orchestrator Lambda (fan-out)
            ├── Fetcher Lambda × 4  (Adzuna · TheMuse · Remotive · Arbeitnow)
            │       └── raw JSON → S3 (joblens-raw)
            ├── Normalizer Lambda
            │       └── normalised JSON → S3 (joblens-normalized)
            └── Indexer Lambda
                    └── bulk index → Amazon OpenSearch

API Gateway
    ├── GET /jobs/search        → Search Lambda (full-text + faceted filters)
    ├── GET /jobs/autocomplete  → Search Lambda (prefix suggestions)
    └── GET /health             → Health Lambda
```

## Tech stack

- **Python 3.11** · AWS Lambda
- **AWS SAM** — IaC and deployment
- **Amazon OpenSearch Service** (t3.small, eu-west-1)
- **Amazon S3** — ETL event backbone
- **Amazon EventBridge** — daily cron trigger
- **API Gateway** — HTTP API with CORS

## Data sources

| Source | Region | ~Volume |
|--------|--------|---------|
| Adzuna | GB · DE · FR · NL · US · IT · AT | 700 |
| TheMuse | US startups | 150 |
| Remotive | Worldwide (remote-only) | 20 |
| Arbeitnow | DE / EU | 50 |

Total: **~993 indexed jobs**, refreshed daily via EventBridge cron.

## Project structure

```
lambdas/
├── shared/       # Models, OpenSearch client, S3 utils
├── fetchers/     # One module per source
├── normalizer/   # Salary parser, stack extractor, per-source normalizers
├── search/       # Query builder, search + autocomplete handler
├── indexer/      # Bulk indexer to OpenSearch
├── orchestrator/ # Fan-out Lambda
└── health/       # Health check endpoint
scripts/          # Index setup, manual seeding helpers
tests/            # pytest — 75 tests
template.yaml     # SAM IaC
```

## Local development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Build and deploy (requires Python 3.11)
export PATH="/opt/homebrew/opt/python@3.11/bin:$PATH"
sam build
sam deploy
```

## Environment variables

Set via SAM template / Lambda console:

| Variable | Description |
|----------|-------------|
| `OPENSEARCH_HOST` | OpenSearch domain endpoint |
| `OPENSEARCH_USER` / `OPENSEARCH_PASSWORD` | HTTP basic auth credentials |
| `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` | Adzuna API credentials |
| `S3_BUCKET_RAW` / `S3_BUCKET_NORMALIZED` | S3 bucket names |
| `ADZUNA_COUNTRIES` | Comma-separated country codes (default `gb,de,fr,nl,us,it,at`) |
| `ADZUNA_PAGES` | Pages per country (default `5`) |
| `ARBEITNOW_PAGES` | Pages to fetch (default `8`) |

## Live demo

Frontend: [https://joblens-frontend-psi.vercel.app](https://joblens-frontend-psi.vercel.app)  
Frontend repo: [github.com/Abrahamvjt95/joblens-frontend](https://github.com/Abrahamvjt95/joblens-frontend)
