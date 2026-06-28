import enum

from sqlalchemy import Boolean
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FeeType(str, enum.Enum):
    fixed = "fixed"
    percentage = "percentage"


class FeeAppliesTo(str, enum.Enum):
    per_booking = "per_booking"
    per_person = "per_person"
    per_adult = "per_adult"
    per_child = "per_child"


class TripFee(Base):
    __tablename__ = "trip_fees"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    fee_type: Mapped[FeeType] = mapped_column(
        SAEnum(FeeType, name="fee_type_enum"), nullable=False, default=FeeType.fixed
    )
    value: Mapped[float] = mapped_column(Float, nullable=False)
    applies_to: Mapped[FeeAppliesTo] = mapped_column(
        SAEnum(FeeAppliesTo, name="fee_applies_to_enum"),
        nullable=False,
        default=FeeAppliesTo.per_person,
    )
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_included_in_price: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=True)

    trip: Mapped["Trip"] = relationship("Trip", back_populates="fees")
