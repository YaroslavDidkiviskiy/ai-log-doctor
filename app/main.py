import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import create_tables
from app.routers import web, uploads, incidents

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    create_tables()
    yield


app = FastAPI(
    title="AI Log Doctor",
    description="AI-powered log incident analyzer",
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(web.router)
app.include_router(uploads.router)
app.include_router(incidents.router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
