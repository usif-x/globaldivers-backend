from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from app.core.cache import init_cache
from app.core.config import settings
from app.core.database import Base, engine
from app.core.init_superadmin import create_super_admin
from app.core.limiter import limiter
from app.models import *
from app.routes.all import routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_cache()
    yield


Base.metadata.create_all(bind=engine)


app = FastAPI(
    lifespan=lifespan,
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
)

templates = Jinja2Templates(directory="app/templates")
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    # Allow requests from any origin. Using a regex allows credentials to be
    # sent while matching all origins (browsers block '*' when credentials
    # are allowed). If you do NOT need credentials, you can alternatively
    # use allow_origins=["*"] and set allow_credentials=False.
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Rate limit exceeded, please wait and try again"},
    )


for route in routes:
    app.include_router(route)


@app.get("/", include_in_schema=False)
async def root(request: Request):
    return templates.TemplateResponse("forbidden.html", {"request": request})


@app.get("/document", include_in_schema=False)
async def redoc():
    return RedirectResponse(url="/docs")


@app.get("/documentation", include_in_schema=False)
async def docs():
    return RedirectResponse(url="/docs")


@app.get("/health", include_in_schema=False)
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": settings.APP_VERSION,
    }


if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).parent.parent
    STORAGE_DIR = PROJECT_ROOT / "storage"
    STORAGE_DIR.mkdir(exist_ok=True)
    create_super_admin()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
    )
