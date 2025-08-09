from sqlalchemy.orm import relationship
from app.models import User, Invoice, Testimonial, Notification, Course

# Add relationships
User.posts = relationship("Post", back_populates="user", cascade="all, delete")
User.invoices = relationship("Invoice", back_populates="user", cascade="all, delete")
User.testimonials = relationship("Testimonial", back_populates="user", cascade="all, delete")
User.notifications = relationship("Notification", back_populates="user", cascade="all, delete")
User.subscribed_courses = relationship("Course", secondary="user_course_subscriptions", back_populates="subscribers", cascade="all, delete")
