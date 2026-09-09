# scalefind

Non-commercial, **read-only** Reddit API prototype (v0.1).

An operator explicitly searches or looks up **public** Reddit content through the official API. Nothing runs in the background. Nothing is written back to Reddit.

**Reddit reviewers:** see [REDDIT-REVIEW.md](REDDIT-REVIEW.md) first.  
**Privacy:** [PRIVACY.md](PRIVACY.md) · **Data:** [DATA-POLICY.md](DATA-POLICY.md) · **Security:** [SECURITY.md](SECURITY.md)

---

## Features

- OAuth client-credentials auth (env-based; fails closed if missing)
- Public search, subreddit about, post, and comment retrieval
- Comment depth / count limits
- Local rate limiting + Reddit header awareness + capped backoff
- Short-lived local SQLite cache (default **24h**) with explicit delete / expire
- Single-page research UI at `/`

## Non-goals

| Not this | Why it matters |
|----------|----------------|
| Commercial product / data marketplace | No resale or licensing of Reddit data |
| Crawler / scheduler / monitor | Only user-initiated requests |
| Write actions (post, vote, message, mod…) | Client allows GET/HEAD only; tests enforce it |
| User profiling / identity enrichment | Minimized fields; no author history store |
| AI / ML training corpus | Data not retained for training |
| Multi-source platform | Reddit is the only external content source |

## Compliance

Intended use is only **after** Reddit grants API access for this use case, under the [Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy) and [Developer Terms](https://redditinc.com/policies/developer-terms).

Ticket-ready description, volume estimates, and a code checklist live in [REDDIT-REVIEW.md](REDDIT-REVIEW.md).

## Requirements

- Python **3.11+**
- Reddit OAuth app credentials (after approval)

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

```env
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=scalefind/0.1 by your_reddit_username
REDDIT_REDIRECT_URI=http://localhost:8000/reddit/auth/callback
```

```bash
uvicorn app.main:app --reload
```

| URL | Purpose |
|-----|---------|
| http://localhost:8000 | Research UI |
| http://localhost:8000/health | Liveness (`read_only: true`) |
| http://localhost:8000/docs | OpenAPI |

Without credentials, `/health` still works; Reddit endpoints return **503**.

## Configuration

| Variable | Default | Notes |
|----------|---------|--------|
| `REDDIT_CLIENT_ID` | _(empty)_ | Required for API calls |
| `REDDIT_CLIENT_SECRET` | _(empty)_ | Required for API calls |
| `REDDIT_USER_AGENT` | `scalefind/0.1` | Use a descriptive UA including your Reddit username |
| `REDDIT_REDIRECT_URI` | `http://localhost:8000/reddit/auth/callback` | Local prototype |
| `REDDIT_REQUEST_TIMEOUT_SECONDS` | `15` | HTTP timeout |
| `REDDIT_MAX_RETRIES` | `3` | Hard-capped retries |
| `REDDIT_RATE_LIMIT_REQUESTS_PER_MINUTE` | `60` | Local budget |
| `DATA_RETENTION_HOURS` | `24` | Local cache TTL |
| `STORAGE_PATH` | `data/research.db` | SQLite path |
| `SUBREDDIT_ALLOWLIST_PATH` | `config/subreddits.yaml` | Allowed communities |

Secrets stay in `.env` (gitignored). Never commit client secrets or tokens.

## API

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness |
| `GET` | `/reddit/search?q=&subreddit=&limit=` | Search (`limit` 1–25) |
| `GET` | `/reddit/subreddit/{name}` | Subreddit metadata |
| `GET` | `/reddit/post/{id}` | Single post |
| `GET` | `/reddit/post/{id}/comments` | Comments (limited) |
| `DELETE` | `/reddit/data/{id}` | Delete local cache row(s) |
| `POST` | `/reddit/data/expire` | Purge expired local rows |

## Project layout

```
scalefind/
├── app/
│   ├── main.py              # FastAPI entry + static UI
│   ├── config.py            # Settings from env
│   ├── api/routes.py        # HTTP endpoints
│   ├── storage/local.py     # Short-lived SQLite cache
│   ├── static/index.html    # Research UI
│   └── reddit/              # ALL Reddit network I/O
│       ├── client.py        # Read-only HTTP client
│       ├── auth.py
│       ├── search.py / post.py / comment.py / subreddit.py
│       ├── rate_limit.py
│       ├── deletion.py
│       └── models.py
├── config/subreddits.yaml   # Subreddit allowlist
├── tests/
└── REDDIT-REVIEW.md         # API review package
```

## Tests

```bash
pytest -q
```

Read-only and secret-redaction checks: `tests/test_readonly_and_security.py`.

## Documentation

| Doc | Contents |
|-----|----------|
| [REDDIT-REVIEW.md](REDDIT-REVIEW.md) | Reddit review package / ticket text |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Module map and data flow |
| [DATA-POLICY.md](DATA-POLICY.md) | Allowed / prohibited fields, retention |
| [PRIVACY.md](PRIVACY.md) | Privacy policy |
| [SECURITY.md](SECURITY.md) | Secrets, logging, request safety |
| [LICENSE](LICENSE) | MIT |

## License

MIT — see [LICENSE](LICENSE).
