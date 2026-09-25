# CDN Traffic Scheduler

A small FastAPI service that chooses a healthy CDN endpoint using latency, availability, current load, and cost. The endpoint data is synthetic so the project can be run locally without access to a real CDN provider.

## What it demonstrates

- Multi-endpoint traffic selection
- Health-aware failover
- Latency, reliability, load, and cost scoring
- Estimated egress cost for a request
- REST APIs, tests, Docker, and GitHub Actions CI

## Run

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs.

```bash
curl -X POST http://127.0.0.1:8000/v1/schedule \\
  -H 'Content-Type: application/json' \\
  -d '{"region":"us-west","size_gb":2}'
```

## Test

```bash
pytest -q
```

## Resume description

> Built a health-aware CDN traffic scheduler that ranks synthetic endpoints by latency, availability, load, and egress cost; added failover handling, REST APIs, Docker deployment, and automated tests.

