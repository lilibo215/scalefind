# Reddit API review package — scalefind

This document is the primary package for Reddit Developer Support / Responsible Builder Policy review.

Public source: *(set after GitHub publish — replace with repo URL)*  
Privacy policy: [`PRIVACY.md`](PRIVACY.md) *(raw / blob URL on GitHub after publish)*  
Data policy: [`DATA-POLICY.md`](DATA-POLICY.md)  
Security: [`SECURITY.md`](SECURITY.md)  
Architecture: [`ARCHITECTURE.md`](ARCHITECTURE.md)

## One-sentence purpose

**scalefind** is a **non-commercial**, **read-only**, **user-initiated** prototype that lets an operator search and view **publicly accessible** Reddit posts, comments, and subreddit metadata through the official Reddit API.

## What reviewers should verify in code

| Claim | Where to look |
|-------|----------------|
| Read-only HTTP (GET/HEAD only) | `app/reddit/client.py` — rejects non-GET; write method names forbidden |
| Tests fail if write helpers appear | `tests/test_readonly_and_security.py` |
| User-initiated only (no crawler/scheduler) | `app/api/routes.py`, `app/static/index.html`, no cron/worker modules |
| Reddit is the only external content source | `app/reddit/` package boundary |
| Credentials from env, never committed | `.env.example`, `.gitignore` excludes `.env` |
| Rate limits honored | `app/reddit/rate_limit.py` |
| Short local retention + deletion | `DATA_RETENTION_HOURS` (default 24), `DELETE /reddit/data/{id}`, `POST /reddit/data/expire` |
| No user profiling / no author enrichment | `DATA-POLICY.md`, `app/reddit/models.py` minimized fields |
| No AI training / no data resale | stated in README + PRIVACY + this file |

## Use case (paste into Reddit ticket)

**App name:** scalefind  

**Commercial?** No — prototype / evaluation only. Not a paid product, not a data marketplace, not an ads or lead-gen system.

**Access type:** OAuth client credentials (app-only) for **read** of public content. No posting, voting, messaging, moderation, or private-message access.

**What the app does:**
1. Operator enters an explicit search query (optional subreddit filter) in a local UI or HTTP API.
2. App calls Reddit OAuth API for search / subreddit about / post / comments.
3. Results are shown to the operator. Optionally cached in a **local SQLite** file with **24-hour** default expiry.
4. Operator can delete cached rows by id; expired rows are purged on startup and via an expire endpoint.

**What the app does not do:**
- Background crawling, continuous monitoring, or scheduled Reddit jobs
- Scraping outside the official API
- Writing to Reddit (submit, comment, vote, message, moderate, …)
- Building Redditor profiles or activity histories
- Selling, licensing, or sharing Reddit data with third parties
- Training or fine-tuning AI / ML models on Reddit content
- Inferring sensitive attributes about users
- Matching Reddit identities to off-platform identifiers

**Data accessed (public only):**
- Search listings (post id, title, body excerpt, subreddit, created time, permalink, score, comment count)
- Subreddit about (name, title, public description, subscribers)
- Single post + comments (depth/count limited; body excerpted)

**Subreddit scope:** Restricted by `config/subreddits.yaml` allowlist when populated. Prototype ships with placeholder names; production use should list only communities needed for the stated research task.

**Expected volume (prototype):** Low. Local interactive use. Default client budget ≈ **60 requests/minute** with backoff; expected real usage far below that (human-driven searches).

**User-Agent pattern:** `scalefind/0.1 by <reddit_username>` (configured via `REDDIT_USER_AGENT`).

**Redirect URI:** `http://localhost:8000/reddit/auth/callback` (local prototype; update if a public callback is ever added).

**Retention / deletion:** Local cache default **24 hours**. Explicit delete endpoints. No permanent warehouse, CRM, vector DB, or training corpus.

## Compliance statements

We intend to comply with:

- [Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy)
- [Developer Terms](https://redditinc.com/policies/developer-terms)
- Reddit Data API Terms / Public Content Policy as applicable

Specifically:

1. **Approval before use** — we will not call the Data API until Reddit grants access for this use case.
2. **Transparency** — this repository and documentation describe the real purpose and scope.
3. **No unapproved commercialization or AI training** — Reddit data is not sold, licensed, or used to train models.
4. **No privacy violations** — no sensitive-attribute inference, no re-identification, no off-platform identity matching.
5. **Respect rate limits** — client enforces local RPM + Reddit headers; no intentional circumvention.
6. **Scope minimization** — only read endpoints needed for search/view; allowlist for subreddits.

## How to run (for reviewers)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Reviewers: leave credentials empty to inspect UI + /health;
# or use sandbox credentials Reddit provides after approval.
uvicorn app.main:app --reload
```

- UI: http://localhost:8000  
- Health: http://localhost:8000/health (`read_only: true`)  
- OpenAPI: http://localhost:8000/docs  
- Tests: `pytest -q`

## Contact

Use the GitHub repository Issues after publish, or the email provided in the Reddit Developer Support ticket.
