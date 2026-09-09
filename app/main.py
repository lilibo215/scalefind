"""FastAPI application entrypoint for scalefind."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import get_settings
from app.logging_utils import configure_logging
from app.reddit.deletion import delete_expired_data
from app.storage.local import LocalStore

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    settings = get_settings()
    store = LocalStore(settings.storage_path)
    delete_expired_data(store)
    yield


app = FastAPI(
    title="scalefind",
    version="0.1.0",
    description="Read-only Reddit research prototype",
    lifespan=lifespan,
)
app.include_router(router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
