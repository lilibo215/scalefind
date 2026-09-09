# Privacy Policy — scalefind

**Effective date:** 2026-09-09  
**Applies to:** the open-source `scalefind` prototype in this repository  
**Public copy:** https://github.com/lilibo215/scalefind/blob/main/PRIVACY.md

This policy describes how the **scalefind** application handles Reddit data and operator information when the software is run. It is written for Reddit API review and for anyone who operates a local instance.

## Summary

scalefind is a **non-commercial**, **read-only**, **user-initiated**, **localhost-only** research prototype. It retrieves **publicly accessible** Reddit content only when an operator explicitly requests it. It does **not** build user profiles, does **not** sell data, and does **not** use Reddit content to train AI models.

## Who this software is for

The intended operator is a person running the prototype on **their own machine** (default bind `127.0.0.1`) to evaluate official Reddit API connectivity for search and read of public discussions. This submission does **not** describe a public multi-tenant hosted service.

## Commercial use

This prototype and privacy policy cover **non-commercial** evaluation only. Any future commercial product, paid offering, or commercialization of Reddit data would require:

1. a **separate** Reddit API / commercial application and Reddit’s written approval, and  
2. an updated privacy policy reflecting that different deployment and data practice.

Those future practices are **out of scope** for this document and for the current API access request.

## Data we access from Reddit

Only through the official Reddit API, after credentials are configured, using **app-only (client credentials)** authentication:

| Type | Examples of fields | Purpose |
|------|--------------------|---------|
| Search / posts | id, title, body excerpt, subreddit, created time, permalink, score, comment count | Display search results |
| Subreddit about | name, title, public description, subscribers | Display community metadata |
| Comments | id, body excerpt, post id, created time, permalink, score, depth | Display comment threads |

We do **not** request write scopes or perform submit, vote, comment, message, or moderation actions.  
We do **not** rely on a user OAuth Redirect URI / authorization-code callback for this prototype’s stated purpose.

## Data we do not collect

- Reddit account profiles or reconstructed user activity histories
- Email addresses, phone numbers, or payment data from Reddit users
- Private messages or non-public content
- Off-platform identity matches
- Inferred sensitive characteristics (health, politics, sexuality, etc.)
- Behavioral advertising profiles

Author usernames are not part of the minimized local research record schema.

## Local storage and retention

- Optional short-lived cache in a **local SQLite** file (`STORAGE_PATH`, default `data/research.db`) on the operator’s machine
- Default retention: **24 hours** (`DATA_RETENTION_HOURS`)
- Cached rows expire and can be deleted:
  - `DELETE /reddit/data/{id}`
  - `POST /reddit/data/expire`
  - expired purge also runs on application startup

This is not a permanent archive, warehouse, CRM, lead database, or training corpus.

## Sharing and sale

Local research data is **not** sold, licensed, or shared with third parties by this prototype. Network calls for content go only to Reddit’s API.

## AI / machine learning

Reddit content retrieved by this prototype is **not** retained for AI or ML model training or fine-tuning.

## Credentials and logging

- OAuth client id / secret and tokens are supplied via environment variables (see `.env.example`) and must not be committed to git
- Application logging is designed to redact secrets and tokens (see `SECURITY.md`)

## Children

This prototype is not directed at children and is not intended to process children’s data.

## Operator responsibilities

Anyone who runs this software must:

- keep Reddit credentials private
- use an accurate descriptive `REDDIT_USER_AGENT`
- respect Reddit Developer Terms, Responsible Builder Policy, rate limits, and applicable law
- keep the subreddit allowlist explicit and limited to the stated use case
- keep the default **localhost-only** posture unless they intentionally change bind settings and accept the corresponding responsibilities
- update this privacy policy if they deploy a modified, commercial, or publicly hosted version with different data practices
- obtain **separate** Reddit approval before any commercial use

## Changes

Material changes to this policy will be reflected by updating this file in the public repository (with a revised effective date).

## Contact

- Prefer the public GitHub repository **Issues**: https://github.com/lilibo215/scalefind/issues  
- Or the contact email supplied in the Reddit Developer Support application for this app
