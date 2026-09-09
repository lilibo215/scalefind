"""Minimal read-only Reddit research API routes."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.config import Settings, get_settings
from app.reddit.auth import CredentialError
from app.reddit.client import RedditAPIError, RedditClient
from app.reddit.comment import get_comments
from app.reddit.deletion import delete_expired_data, delete_post_data
from app.reddit.post import get_post
from app.reddit.search import search as reddit_search
from app.reddit.subreddit import get_subreddit, is_allowed, load_allowlist
from app.storage.local import LocalStore

router = APIRouter()


@lru_cache
def get_store() -> LocalStore:
    settings = get_settings()
    return LocalStore(settings.storage_path)


@router.get("/health")
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> dict:
    return {
        "status": "ok",
        "service": "scalefind",
        "read_only": True,
        "credentials_configured": settings.credentials_present(),
    }


@router.get("/reddit/search")
async def search_endpoint(
    q: Annotated[str, Query(min_length=1, max_length=300)],
    subreddit: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=25)] = 10,
    settings: Annotated[Settings, Depends(get_settings)] = ...,
    store: Annotated[LocalStore, Depends(get_store)] = ...,
):
    allowlist = load_allowlist(settings.subreddit_allowlist_path)
    if subreddit and not is_allowed(subreddit, allowlist):
        raise HTTPException(status_code=403, detail="Subreddit is not on the allowlist")

    try:
        async with RedditClient(settings) as client:
            results = await reddit_search(client, q, subreddit=subreddit, limit=limit)
    except CredentialError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RedditAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code or 502, detail="Reddit API request failed"
        ) from exc

    for item in results:
        store.upsert(
            item.reddit_id,
            "search_result",
            item.model_dump(mode="json"),
            retention_hours=settings.data_retention_hours,
        )

    return {
        "query": q,
        "subreddit": subreddit,
        "count": len(results),
        "results": [r.model_dump(mode="json") for r in results],
    }


@router.get("/reddit/subreddit/{name}")
async def subreddit_endpoint(
    name: str,
    settings: Annotated[Settings, Depends(get_settings)],
):
    allowlist = load_allowlist(settings.subreddit_allowlist_path)
    if not is_allowed(name, allowlist):
        raise HTTPException(status_code=403, detail="Subreddit is not on the allowlist")
    try:
        async with RedditClient(settings) as client:
            info = await get_subreddit(client, name)
    except CredentialError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RedditAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code or 502, detail="Reddit API request failed"
        ) from exc
    return info.model_dump(mode="json")


@router.get("/reddit/post/{post_id}")
async def post_endpoint(
    post_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    store: Annotated[LocalStore, Depends(get_store)],
):
    try:
        async with RedditClient(settings) as client:
            post = await get_post(client, post_id)
    except CredentialError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RedditAPIError as exc:
        status = 404 if exc.category == "not_found" else (exc.status_code or 502)
        raise HTTPException(status_code=status, detail="Post retrieval failed") from exc

    store.upsert(
        post.reddit_id,
        "post",
        post.model_dump(mode="json"),
        retention_hours=settings.data_retention_hours,
    )
    return post.model_dump(mode="json")


@router.get("/reddit/post/{post_id}/comments")
async def comments_endpoint(
    post_id: str,
    subreddit: Annotated[str | None, Query(max_length=100)] = None,
    max_depth: Annotated[int, Query(ge=0, le=5)] = 2,
    max_count: Annotated[int, Query(ge=1, le=100)] = 50,
    settings: Annotated[Settings, Depends(get_settings)] = ...,
    store: Annotated[LocalStore, Depends(get_store)] = ...,
):
    try:
        async with RedditClient(settings) as client:
            comments = await get_comments(
                client,
                post_id,
                subreddit=subreddit,
                max_depth=max_depth,
                max_count=max_count,
            )
    except CredentialError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RedditAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code or 502, detail="Comment retrieval failed"
        ) from exc

    for c in comments:
        store.upsert(
            c.reddit_id,
            "comment",
            c.model_dump(mode="json"),
            retention_hours=settings.data_retention_hours,
        )
    return {
        "post_id": post_id,
        "count": len(comments),
        "comments": [c.model_dump(mode="json") for c in comments],
    }


@router.delete("/reddit/data/{reddit_id}")
async def delete_data_endpoint(
    reddit_id: str,
    store: Annotated[LocalStore, Depends(get_store)],
):
    try:
        deleted = delete_post_data(store, reddit_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"reddit_id": reddit_id, "deleted": deleted}


@router.post("/reddit/data/expire")
async def expire_data_endpoint(store: Annotated[LocalStore, Depends(get_store)]):
    deleted = delete_expired_data(store)
    return {"deleted": deleted}


@router.get("/reddit/auth/status")
async def auth_status(settings: Annotated[Settings, Depends(get_settings)]):
    """Safe credential presence check — never returns secrets."""
    return {
        "credentials_configured": settings.credentials_present(),
        "user_agent_set": bool(settings.reddit_user_agent.strip()),
        "redirect_uri": settings.reddit_redirect_uri,
    }
