from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import router
from app.core.config import get_settings
from app.services.llm_service import configure_tracing


@asynccontextmanager
async def lifespan(app):
    configure_tracing(get_settings())  # Set privacy before upload preflight can be traced.
    yield


app = FastAPI(title="CareerPilot AI", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)
app.include_router(router)


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Database unavailable. Start PostgreSQL, check DATABASE_URL and run alembic upgrade head."
        },
    )


@app.exception_handler(Exception)
async def service_error(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500, content={"detail": "The operation failed. Verify backend configuration and retry."}
    )
