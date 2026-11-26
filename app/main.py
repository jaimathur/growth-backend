from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.router import api_router
from .config import get_settings
from .db import close_pool, db_connection


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    close_pool()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Pennywise API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(api_router)

    @app.get("/api/v1/health", tags=["meta"])
    def health():
        try:
            with db_connection() as conn, conn.cursor() as cur:
                cur.execute("SELECT 1")
        except Exception:
            raise HTTPException(503, "database unavailable")
        return {"status": "ok"}

    return app


app = create_app()
