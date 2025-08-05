import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from app.core.cache import init_cache
from app.core.init_superadmin import create_super_admin
from app.core.limiter import limiter
from app.db.conn import Base, engine
from app.models.admin import Admin
from app.models.course import Course
from app.models.gallery import Gallery
from app.models.invoice import Invoice
from app.models.package import Package
from app.models.testimonial import Testimonial
from app.models.trip import Trip
from app.models.user import User
from app.routes.all import routes

# Get project root directory (parent of 'app' folder)


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


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": f"Rate limit exceeded, please wait one minute and try again"
        },
    )


for route in routes:
    app.include_router(route)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
    return RedirectResponse(url="https://globaldivers.vercel.app/")  # Frontend URL


@app.get("/document", include_in_schema=False)
async def redoc():
    return RedirectResponse(url="/docs")


@app.get("/documentation", include_in_schema=False)
async def docs():
    return RedirectResponse(url="/docs")


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}


@app.get("/users/me/notifications")
async def notifications():
    return [
        {
            "id": "uuid-notif-1",
            "type": "new_invoice",
            "message": "Your invoice #INV-2023-003 for the 'Next.js 14' course is ready.",
            "link": "/profile?tab=invoices",
            "is_read": False,
            "created_at": "2023-10-28T09:01:00Z",
        },
        {
            "id": "uuid-notif-2",
            "type": "course_update",
            "message": "A new module, 'Advanced Caching Strategies', has been added to 'Next.js 14: The Full Course'.",
            "link": "/courses/nextjs-14-full-course",
            "is_read": False,
            "created_at": "2023-10-27T15:30:00Z",
        },
        {
            "id": "uuid-notif-3",
            "type": "payment_success",
            "message": "Your payment of $149.99 for 'Advanced React Patterns' was successful.",
            "link": "/payment/success?order_id=ORD-12345",
            "is_read": True,
            "created_at": "2023-10-26T10:05:00Z",
        },
        {
            "id": "uuid-notif-4",
            "type": "new_message",
            "message": "You have a new message from your instructor, Jane Doe.",
            "link": "/messages/jane-doe",
            "is_read": False,
            "created_at": "2023-10-28T11:20:00Z",
        },
        {
            "id": "uuid-notif-5",
            "type": "default",
            "message": "Welcome to our platform! We're glad to have you here.",
            "link": "/dashboard",
            "is_read": True,
            "created_at": "2023-10-25T08:00:00Z",
        },
        {
            "id": "uuid-notif-6",
            "type": "course_update",
            "message": "You've completed 'Tailwind CSS from Scratch'! Congratulations!",
            "link": "/profile?tab=courses",
            "is_read": True,
            "created_at": "2023-10-20T12:00:00Z",
        },
    ]


create_super_admin()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
