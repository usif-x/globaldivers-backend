from app.db.conn import Base

from .associations import user_course_subscriptions

from .admin import Admin
from .course import Course
from .course_content import CourseContent
from .invoice import Invoice
from .package import Package
from .setting import WebsiteSettings
from .testimonial import Testimonial
from .trip import Trip
from .user import User
from .notification import Notification





# Make all models available at package level
__all__ = [
    # Association tables
    "user_course_subscriptions",

    # Models
    "User",
    "Testimonial",
    "Package",
    "Trip",
    "Invoice",
    "Notification",
    "Course",
    "CourseContent",
    "Admin",
    "WebsiteSettings"
]
