from app.core.database import Base

from .admin import Admin
from .associations import user_course_subscriptions
from .best_selling import BestSelling
from .course import Course
from .course_content import CourseContent
from .dive_center import DiveCenter
from .gallery import Gallery
from .invoice import Invoice
from .notification import Notification
from .package import Package
from .setting import WebsiteSettings
from .testimonial import Testimonial
from .trip import Trip
from .user import User

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
    "WebsiteSettings",
    "Invoice",
    "Notification",
    "Gallery",
    "DiveCenter",
    "BestSelling",
]
