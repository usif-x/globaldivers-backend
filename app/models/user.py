from app.db.conn import Base,engine
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, text, Integer
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .testimonial import Testimonial


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True, unique=True)
    full_name: Mapped[str] = mapped_column(String(40),nullable=False)
    password: Mapped[str] = mapped_column(String(100),nullable=False)
    email: Mapped[str] = mapped_column(String(100),nullable=False,unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(),nullable=False, default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(),nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    role: Mapped[str] = mapped_column(String(40),nullable=False, default="user", server_default=text("'user'"))
    is_active: Mapped[bool] = mapped_column(String(40),nullable=False, default=True, server_default=text("'true'"))
    is_blocked: Mapped[bool] = mapped_column(String(40),nullable=False, default=False, server_default=text("'false'"))
    last_login: Mapped[str] = mapped_column(String(50), nullable=True)
    testimonial: Mapped[list["Testimonial"]] = relationship(back_populates="user")
    

    

    def __repr__(self) -> str:
        
        return f"<User(id: {self.id}, name: {self.full_name})>"
    

Base.metadata.create_all(bind=engine)


