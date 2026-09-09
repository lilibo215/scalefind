# Security

## Secrets

- Credentials come from environment variables (see `.env.example`)
- Never hardcode `REDDIT_CLIENT_SECRET` or tokens
- `.gitignore` excludes `.env`, local DBs, and virtualenvs — do not commit secrets to GitHub
- Application fails safely when credentials are missing (`CredentialError` → HTTP 503)

## Logging

Logs must never contain:

- OAuth client secret
- access token
- refresh token
- authorization code

`app/logging_utils.py` provides redaction helpers and a logging filter. Prefer logging request id, endpoint/path, status, latency, and rate-limit state.

## Request safety

- HTTP timeouts (`REDDIT_REQUEST_TIMEOUT_SECONDS`)
- Finite retries (`REDDIT_MAX_RETRIES`, hard-capped)
- Central rate limiting (`app/reddit/rate_limit.py`)
- Input validation on query parameters and path ids
- Safe API error messages (no credential leakage)

## Read-only enforcement

- `RedditClient.request` allows only `GET` / `HEAD`
- Forbidden write method names are listed and tested
- Tests fail if write-operation methods are introduced on the client module

## Subreddit allowlist

`config/subreddits.yaml` restricts which communities can be queried through the API when populated. Use placeholder names for initial testing; change explicitly as needed.
