# Architecture

## Overview

`scalefind` is a small FastAPI application with an isolated Reddit API package. There is no multi-source abstraction and no commercial domain models.

```
scalefind
│
├── app/main.py              # FastAPI app + static UI
├── app/config.py            # Environment settings
├── app/logging_utils.py     # Credential-safe logging
├── app/api/routes.py        # HTTP endpoints
├── app/storage/local.py     # Minimal SQLite research cache
├── app/static/index.html    # Single research UI
│
└── app/reddit/              # ALL Reddit API access
    ├── auth.py
    ├── client.py            # Read-only HTTP client
    ├── search.py
    ├── subreddit.py
    ├── post.py
    ├── comment.py
    ├── rate_limit.py
    ├── deletion.py
    └── models.py            # Minimized research records
```

## Module responsibilities

| Module | Responsibility |
|--------|----------------|
| Authentication | Client-credentials OAuth via env vars; fail closed if missing |
| Reddit client | Central GET-only requests; retries; no write API surface |
| Search | User-initiated search → normalized post records |
| Subreddit | Explicit lookup + allowlist check |
| Post | Single-post retrieval by id |
| Comment | Comment tree walk with max depth/count |
| Rate limiter | Local RPM budget, header parsing, exponential backoff, finite retries |
| Deletion | Delete by id / search result / expired retention |
| Storage | Short-lived local SQLite only |
| API | Thin HTTP layer over Reddit modules |
| Frontend | One search page; read-only banner |

## Data flow

1. User submits a query in the UI (or calls an API endpoint).
2. API validates input and allowlist (when a subreddit is specified).
3. `RedditClient` authenticates (if needed) and performs a GET request.
4. Rate limiter gates the request and interprets Reddit rate-limit headers.
5. Response is normalized to minimized research records.
6. Optional local cache write with expiry (`DATA_RETENTION_HOURS`).
7. User may delete cached records; expired records are removed on startup and via `/reddit/data/expire`.

## Explicit non-goals

- Background crawlers / continuous monitors
- Write operations (submit, comment, vote, message, moderate, …)
- CRM / lead / opportunity / sales models
- External data source adapters
- Vector / embedding warehouses
- User identity enrichment

## Extensibility note

If a write endpoint is added to `RedditClient`, `tests/test_readonly_and_security.py` is designed to fail.
