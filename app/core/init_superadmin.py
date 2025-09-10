from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.admin import Admin
from app.core.config import settings  # استدعاء ملف الإعدادات
from .hashing import hash_password


def create_super_admin():
    db: Session = SessionLocal()
    try:
        name = settings.ADMIN_NAME
        username = settings.ADMIN_USERNAME
        email = settings.ADMIN_EMAIL
        default_password = settings.ADMIN_PASSWORD
        level = settings.ADMIN_LEVEL

        # تحقق إذا كان هناك Admin مسبقاً
        stmt = select(Admin).where(Admin.username == username)
        admin = db.execute(stmt).scalars().first()

        if admin:
            print(f"✅ Super Admin already exists. -> {username}:{default_password}")
            return

        print("🚀 Creating Super Admin...")
        new_admin = Admin(
            full_name=name,
            username=username,
            password=hash_password(default_password),
            email=email,
            admin_level=level,
        )
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        print(
            f"""
✅ Super Admin Created Successfully:
🧑 Name: {name}
👤 Username: {username}
📧 Email: {email}
🔐 Password: {default_password}
🔓 Level: {level} (Full Access)
"""
        )
    finally:
        db.close()
