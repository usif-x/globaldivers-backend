from .admin import admin_routes
from .analytics import analytics_routes
from .auth import auth_routes
from .course import course_routes
from .divesites import divesites_routes
from .gallery import gallery_routes
from .invoice import invoice_routes
from .package import package_routes
from .payment import payment_routes
from .testimonial import testimonial_routes
from .trip import trip_routes
from .user import user_routes

routes = [
    auth_routes,
    user_routes,
    admin_routes,
    package_routes,
    trip_routes,
    testimonial_routes,
    course_routes,
    divesites_routes,
    analytics_routes,
    gallery_routes,
    payment_routes,
    invoice_routes,
]
