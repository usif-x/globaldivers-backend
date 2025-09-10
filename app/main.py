import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from app.core.cache import init_cache
from app.core.init_superadmin import create_super_admin
from app.core.limiter import limiter
from app.core.database import Base, engine
from app.models import *
from app.routes.all import routes
from limits.storage import RedisStorage
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_cache()
    yield


Base.metadata.create_all(bind=engine)


app = FastAPI(
    lifespan=lifespan,
    title="global divers app backend",
    description="global divers app backend server using ( fastapi, sqlalchemy, alembic, mysql )",
    version="1.0.0",
)


app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
storage = RedisStorage(str(settings.DB_REDIS_URI))

limiter._storage = storage

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Rate limit exceeded, please wait one minute and try again"},
    )


for route in routes:
    app.include_router(route)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


PROJECT_ROOT = Path(__file__).parent.parent
STORAGE_DIR = PROJECT_ROOT / "storage"

print(f"📁 Current working directory: {os.getcwd()}")
print(f"📁 Main.py location: {Path(__file__).absolute()}")
print(f"📁 Project root: {PROJECT_ROOT.absolute()}")
print(f"📁 Storage directory: {STORAGE_DIR.absolute()}")
print(f"📁 Storage exists: {STORAGE_DIR.exists()}")
print(f"📁 Storage is directory: {STORAGE_DIR.is_dir()}")

# List files in storage (if it exists)
if STORAGE_DIR.exists():
    files = list(STORAGE_DIR.iterdir())
    print(f"📁 Files in storage: {[f.name for f in files]}")
else:
    print("❌ Storage directory doesn't exist!")

# Ensure storage directory exists
STORAGE_DIR.mkdir(exist_ok=True)

# Mount with absolute path
app.mount("/storage", StaticFiles(directory=str(STORAGE_DIR)), name="storage")


# Add a test endpoint to check storage mounting
@app.get("/test-storage")
async def test_storage():
    return {
        "storage_path": str(STORAGE_DIR.absolute()),
        "storage_exists": STORAGE_DIR.exists(),
        "files_count": len(list(STORAGE_DIR.iterdir())) if STORAGE_DIR.exists() else 0,
        "files": (
            [f.name for f in STORAGE_DIR.iterdir()] if STORAGE_DIR.exists() else []
        ),
    }


@app.get("/", include_in_schema=False)
async def root():
    return HTMLResponse(content="""
    <!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>403 Forbidden</title>
  <style>
    body {
      background-color: black;
      color: #333;
      font-family: Arial, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
    }
    h1 {
      font-size: 5rem;
      margin: 0;
      color: #dc3545;
    }
    p {
      color: white;
      font-size: 1.2rem;
      margin: 10px 0 20px;
    }
  </style>
</head>
<body>
  <h1>403</h1>
  <p>Forbidden – You don’t have permission to access this page.</p>
</body>
</html>
""")


@app.get("/document", include_in_schema=False)
async def redoc():
    return RedirectResponse(url="/docs")


@app.get("/documentation", include_in_schema=False)
async def docs():
    return RedirectResponse(url="/docs")

@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}


create_super_admin()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
    )

