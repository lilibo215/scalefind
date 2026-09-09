"""Reddit package public surface — read-only modules only."""

from app.reddit.auth import CredentialError, fetch_app_only_token, require_credentials
from app.reddit.client import FORBIDDEN_WRITE_METHOD_NAMES, RedditAPIError, RedditClient
from app.reddit.comment import get_comments
from app.reddit.deletion import delete_expired_data, delete_post_data, delete_search_result
from app.reddit.post import get_post
from app.reddit.rate_limit import RateLimiter
from app.reddit.search import search
from app.reddit.subreddit import get_subreddit, is_allowed, load_allowlist

__all__ = [
    "CredentialError",
    "FORBIDDEN_WRITE_METHOD_NAMES",
    "RateLimiter",
    "RedditAPIError",
    "RedditClient",
    "delete_expired_data",
    "delete_post_data",
    "delete_search_result",
    "fetch_app_only_token",
    "get_comments",
    "get_post",
    "get_subreddit",
    "is_allowed",
    "load_allowlist",
    "require_credentials",
    "search",
]
