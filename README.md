# scalefind

Read-only Reddit API research prototype (V0.1).

> **For Reddit reviewers:** start with **[REDDIT-REVIEW.md](REDDIT-REVIEW.md)** (use case, scope, volume, compliance checklist, code map).  
> Privacy policy: **[PRIVACY.md](PRIVACY.md)** · Data policy: **[DATA-POLICY.md](DATA-POLICY.md)**

## What this is

A small, standalone prototype that validates Reddit API connectivity for **user-initiated**, **read-only** retrieval of publicly accessible Reddit discussions.

It supports:

1. Reddit API authentication (environment-based OAuth client credentials)
2. Search of public Reddit content
3. Subreddit metadata lookup
4. Post retrieval
5. Comment retrieval (depth/count limited)
6. Rate-limit handling
7. Deletion of locally stored research data

## What this is not

- Not a commercial product or data marketplace
- Not a crawler or background monitor
- Not a user-profiling system
- Not an AI training pipeline
- Not a multi-source data platform

## Core principles

| Principle | Implementation |
|-----------|----------------|
| Reddit is the only external data source | All network I/O for content goes through `app/reddit/` |
| Read-only | Client rejects non-GET methods; tests fail if write helpers appear |
| User-initiated | Search/lookup only when an explicit request is made |
| No automated Reddit interaction | No schedulers, scrapers, or engagement bots |
| No user profiling | No profile storage, history building, or identity enrichment |
| No data resale | Local short-lived research storage only |
| No AI training | Data is not retained for model training |
| Data minimization | Only fields needed for research display |
| Data deletion | Explicit delete + configurable retention expiry (default 24h) |
| Rate limiting | Local budget + Reddit header awareness + capped exponential backoff |

## Responsible Builder Policy alignment

This prototype is intended to be used only **after** Reddit grants API access for the stated use case, and to comply with Reddit’s [Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy) and [Developer Terms](https://redditinc.com/policies/developer-terms): transparent purpose, minimized read scope, no unapproved commercialization or AI training, no privacy-invasive inference, and respect for rate limits. Details and a ticket-ready description are in [REDDIT-REVIEW.md](REDDIT-REVIEW.md).

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Reddit app credentials (after Reddit approval)
uvicorn app.main:app --reload
```

Open http://localhost:8000

## Configuration

See `.env.example`:

- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `REDDIT_USER_AGENT`
- `REDDIT_REDIRECT_URI`

Optional:

- `DATA_RETENTION_HOURS` (default `24`)
- `REDDIT_MAX_RETRIES` (default `3`)
- `REDDIT_RATE_LIMIT_REQUESTS_PER_MINUTE` (default `60`)

Subreddit allowlist: `config/subreddits.yaml`

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| GET | `/reddit/search?q=&subreddit=&limit=` | Search |
| GET | `/reddit/subreddit/{name}` | Subreddit info |
| GET | `/reddit/post/{id}` | Post |
| GET | `/reddit/post/{id}/comments` | Comments |
| DELETE | `/reddit/data/{id}` | Delete local data |
| POST | `/reddit/data/expire` | Delete expired local data |

## Tests

```bash
pytest -q
```

## Documentation

- [REDDIT-REVIEW.md](REDDIT-REVIEW.md) — Reddit API review package
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [DATA-POLICY.md](DATA-POLICY.md)
- [PRIVACY.md](PRIVACY.md)
- [SECURITY.md](SECURITY.md)
- [LICENSE](LICENSE)
