from datetime import datetime, timezone

from sqlalchemy import DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.conn import Base, engine


class Admin(Base):
    __tablename__ = "admins"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(40), nullable=False)
    username: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(),
        nullable=False,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
    role: Mapped[str] = mapped_column(
        String(40), nullable=False, server_default="admin"
    )
    admin_level: Mapped[int] = mapped_column(
        String(40), nullable=False, server_default="1"
    )
    is_active: Mapped[bool] = mapped_column(
        String(40), nullable=False, default=True, server_default=text("'true'")
    )
    last_login: Mapped[str] = mapped_column(
        String(50), nullable=True, server_default=text("'null'")
    )

    def __repr__(self):
        return f"Admin(id={self.id}, full_name={self.full_name}, username={self.username}, email={self.email}, role={self.role}, admin_level={self.admin_level})"


Base.metadata.create_all(bind=engine)
