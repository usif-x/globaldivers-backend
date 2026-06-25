from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# Engine
db_url = settings.DATABASE_URL

# إصلاح الصيغة إذا كانت تبدأ بـ postgres:// وتحويلها إلى postgresql://
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# إنشاء المحرك باستخدام الرابط المعدل
engine = create_engine(db_url, echo=settings.DEBUG, pool_pre_ping=True)
# Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base Model
class Base(DeclarativeBase):
    pass


# Dependency (FastAPI style)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
