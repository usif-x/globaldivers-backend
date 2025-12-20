from .admin import admin_routes
from .analytics import analytics_routes
from .auth import auth_routes
from .best_selling import best_selling_routes
from .coupon import coupon_routes
from .course import course_routes
from .dive_center import dive_center_routes
from .divesites import divesites_routes
from .gallery import gallery_routes
from .invoice import router as invoice_routes
from .order import router as order_routes
from .package import package_routes
from .setting import setting_routes
from .testimonial import testimonial_routes
from .trip import trip_routes
from .upload import upload_routes
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
    invoice_routes,
    setting_routes,
    best_selling_routes,
    dive_center_routes,
    order_routes,
    upload_routes,
    coupon_routes,
]
