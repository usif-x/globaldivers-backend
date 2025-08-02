from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from app.core.init_superadmin import create_super_admin
from app.core.limiter import limiter
from app.db.conn import Base, engine
from app.models.admin import Admin
from app.models.course import Course
from app.models.invoice import Invoice
from app.models.package import Package
from app.models.testimonial import Testimonial
from app.models.trip import Trip
from app.models.user import User
from app.routes.all import routes

Base.metadata.create_all(bind=engine)


app = FastAPI(
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


@app.get("/invoices/1")
async def invoice():
    return {
        "id": "inv_123",
        "invoice_number": "INV-001",
        "status": "paid",
        "total_amount": 1250.00,
        "currency": "USD",
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "created_at": "2024-01-15",
        "due_date": "2024-02-15",
        "items": [{"name": "Web Development", "quantity": 1, "rate": 1000.00}],
    }


@app.get("/users/me/invoices")
async def invoices():
    return [
        {
            "id": "INV-2023-001",
            "issue_date": "2023-10-26T10:00:00Z",
            "amount": 149.99,
            "status": "paid",
            "download_url": "/mock/invoice-001.pdf",
        },
        {
            "id": "INV-2023-002",
            "issue_date": "2023-09-15T14:30:00Z",
            "amount": 49.50,
            "status": "paid",
            "download_url": "/mock/invoice-002.pdf",
        },
        {
            "id": "INV-2023-003",
            "issue_date": "2023-10-28T09:00:00Z",
            "amount": 299.00,
            "status": "pending",
            "download_url": "/mock/invoice-003.pdf",
        },
        {
            "id": "INV-2023-004",
            "issue_date": "2023-08-01T11:00:00Z",
            "amount": 75.00,
            "status": "paid",
            "download_url": "/mock/invoice-004.pdf",
        },
        {
            "id": "INV-2023-005",
            "issue_date": "2023-10-20T18:00:00Z",
            "amount": 1200.00,
            "status": "overdue",
            "download_url": "/mock/invoice-005.pdf",
        },
        {
            "id": "INV-2023-006",
            "issue_date": "2023-07-25T12:00:00Z",
            "amount": 35.00,
            "status": "paid",
            "download_url": "/mock/invoice-006.pdf",
        },
        {
            "id": "INV-2023-007",
            "issue_date": "2023-06-10T16:45:00Z",
            "amount": 89.99,
            "status": "paid",
            "download_url": "/mock/invoice-007.pdf",
        },
    ]


@app.get("/users/me/courses")
async def courses():
    return [
        {
            "id": "course-101",
            "title": "Advanced React Patterns",
            "slug": "advanced-react-patterns",
            "description": "Deep dive into hooks, context, performance optimization, and state management strategies for large-scale React applications.",
            "thumbnail_url": "https://images.unsplash.com/photo-1633356122544-f134324a6cee?q=80&w=800",
            "progress": 75,
        },
        {
            "id": "course-102",
            "title": "Next.js 14: The Full Course",
            "slug": "nextjs-14-full-course",
            "description": "Master the app router, server components, data fetching, and deployment with the latest version of Next.js.",
            "thumbnail_url": "https://images.unsplash.com/photo-1607703703578-2ebe383b9878?q=80&w=800",
            "progress": 20,
        },
        {
            "id": "course-103",
            "title": "Tailwind CSS from Scratch",
            "slug": "tailwind-css-from-scratch",
            "description": "Learn how to build beautiful, custom designs without leaving your HTML. Covers utility-first fundamentals, responsive design, and customization.",
            "thumbnail_url": "https://images.unsplash.com/photo-1617042375876-a13e36732a04?q=80&w=800",
            "progress": 100,
        },
        {
            "id": "course-104",
            "title": "Introduction to TypeScript",
            "slug": "intro-to-typescript",
            "description": "Add static types to your JavaScript to eliminate bugs and build more robust, maintainable applications.",
            "thumbnail_url": "https://images.unsplash.com/photo-1596328607689-92b519b5a325?q=80&w=800",
            "progress": 0,
        },
    ]


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
