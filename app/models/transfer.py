from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.fee import FeeAppliesTo, FeeType


class TransferZone(Base):
    __tablename__ = "transfer_zones"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    region: Mapped[str] = mapped_column(String(100), nullable=True)

    trip_transfer_fees: Mapped[list["TripTransferFee"]] = relationship(
        "TripTransferFee", back_populates="zone"
    )


class TripTransferFee(Base):
    __tablename__ = "trip_transfer_fees"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), nullable=False
    )
    zone_id: Mapped[int] = mapped_column(
        ForeignKey("transfer_zones.id", ondelete="CASCADE"), nullable=False
    )
    fee_type: Mapped[FeeType] = mapped_column(
        SAEnum(FeeType, name="fee_type_enum"), nullable=False, default=FeeType.fixed
    )
    price: Mapped[float] = mapped_column(Float, nullable=False)
    applies_to: Mapped[FeeAppliesTo] = mapped_column(
        SAEnum(FeeAppliesTo, name="fee_applies_to_enum"),
        nullable=False,
        default=FeeAppliesTo.per_person,
    )

    trip: Mapped["Trip"] = relationship("Trip", back_populates="transfer_fees")
    zone: Mapped["TransferZone"] = relationship(
        "TransferZone", back_populates="trip_transfer_fees"
    )
