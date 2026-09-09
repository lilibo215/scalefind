# Data Policy

## Purpose of data collection

This prototype collects only the minimum Reddit content fields needed to demonstrate **user-initiated**, **localhost-only**, **non-commercial** research retrieval and local deletion.

This policy supports Reddit Responsible Builder Policy expectations: no unapproved commercialization or AI training, no sensitive-attribute inference, no re-identification / off-platform identity matching, and retention limited to what is needed for the immediate task.

## Scope of this policy

| In scope (this prototype) | Out of scope |
|---------------------------|--------------|
| Non-commercial evaluation on the operator’s machine | Commercial products, paid offerings, or data monetization |
| App-only read of public content | User OAuth / Redirect URI login flows as a product feature |
| Short-lived local SQLite cache | Permanent warehouses, CRM / lead databases, training corpora |

**Future commercial use** would require a **separate** Reddit application and Reddit’s commercial / written approval path, plus a revised data policy. It is not covered by the current access request for this repository.

## Allowed fields

For posts / search results:

- `reddit_id`
- `title`
- `body` / short excerpt
- `subreddit`
- `created_at`
- `permalink`
- `score` (optional)
- `comment_count` (optional)

For comments:

- `reddit_id`
- `body` (excerpted)
- `post_id`
- `subreddit` (if present)
- `created_at`
- `permalink`
- `score` (optional)
- `depth`

For subreddits:

- name / display name
- title
- public description
- subscriber count
- existence / accessibility flags

## Prohibited collection

Do not collect or store:

- Reddit user profiles or user histories
- Email addresses or phone numbers
- External social profiles
- Inferred personal attributes
- Behavioral profiles
- Identity matches against non-Reddit systems

## Storage

- Local SQLite file only (`STORAGE_PATH`, default `data/research.db`), on the operator’s machine under the default **localhost-only** deployment
- Default retention: **24 hours** (`DATA_RETENTION_HOURS`)
- Not a permanent warehouse
- No vector database, embeddings store, CRM database, lead database, or opportunity database

## Deletion

- `delete_post_data(reddit_id)` — remove all local rows for an id
- `delete_search_result(reddit_id)` — remove search-result rows
- `delete_expired_data()` — remove rows past `expires_at`
- HTTP: `DELETE /reddit/data/{id}` and `POST /reddit/data/expire`

## External sources

Reddit is the only external data source.
