# app/services/coupon.py
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exception_handler import db_exception_handler
from app.models.coupon import Coupon
from app.models.user import User
from app.schemas.coupon import (
    ApplyCouponResponse,
    CouponCreate,
    CouponResponse,
    CouponUpdate,
)


class CouponServices:
    def __init__(self, db: Session):
        self.db = db

    @db_exception_handler
    def create_coupon(self, coupon: CouponCreate) -> CouponResponse:
        """Create a new coupon"""
        # Check if coupon code already exists
        stmt = select(Coupon).where(Coupon.code == coupon.code)
        existing_coupon = self.db.execute(stmt).scalars().first()

        if existing_coupon:
            raise HTTPException(status_code=400, detail="Coupon code already exists")

        new_coupon = Coupon(
            code=coupon.code,
            activity=coupon.activity,
            discount_percentage=coupon.discount_percentage,
            can_used_up_to=coupon.can_used_up_to,
            expire_date=coupon.expire_date,
        )
        self.db.add(new_coupon)
        self.db.commit()
        self.db.refresh(new_coupon)
        return new_coupon

    @db_exception_handler
    def get_all_coupons(self, skip: int = 0, limit: int = 100) -> List[CouponResponse]:
        """Get all coupons with pagination"""
        stmt = select(Coupon).offset(skip).limit(limit)
        coupons = self.db.execute(stmt).scalars().all()
        return coupons

    @db_exception_handler
    def get_coupon_by_id(self, coupon_id: int) -> CouponResponse:
        """Get coupon by ID"""
        stmt = select(Coupon).where(Coupon.id == coupon_id)
        coupon = self.db.execute(stmt).scalars().first()

        if not coupon:
            raise HTTPException(status_code=404, detail="Coupon not found")

        return coupon

    @db_exception_handler
    def get_coupon_by_code(self, code: str) -> Optional[Coupon]:
        """Get coupon by code"""
        stmt = select(Coupon).where(Coupon.code == code)
        coupon = self.db.execute(stmt).scalars().first()
        return coupon

    @db_exception_handler
    def update_coupon(
        self, coupon_id: int, coupon_data: CouponUpdate
    ) -> CouponResponse:
        """Update a coupon"""
        stmt = select(Coupon).where(Coupon.id == coupon_id)
        coupon = self.db.execute(stmt).scalars().first()

        if not coupon:
            raise HTTPException(status_code=404, detail="Coupon not found")

        # Check if updating code and it already exists
        if coupon_data.code and coupon_data.code != coupon.code:
            stmt = select(Coupon).where(Coupon.code == coupon_data.code)
            existing_coupon = self.db.execute(stmt).scalars().first()
            if existing_coupon:
                raise HTTPException(
                    status_code=400, detail="Coupon code already exists"
                )

        update_data = coupon_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(coupon, key, value)

        self.db.commit()
        self.db.refresh(coupon)
        return coupon

    @db_exception_handler
    def delete_coupon(self, coupon_id: int):
        """Delete a coupon"""
        stmt = select(Coupon).where(Coupon.id == coupon_id)
        coupon = self.db.execute(stmt).scalars().first()

        if not coupon:
            raise HTTPException(status_code=404, detail="Coupon not found")

        self.db.delete(coupon)
        self.db.commit()
        return {"detail": "Coupon deleted successfully"}

    @db_exception_handler
    def apply_coupon(self, coupon_code: str, user_id: int) -> ApplyCouponResponse:
        """Apply a coupon to a user"""
        # Get coupon by code
        coupon = self.get_coupon_by_code(coupon_code)

        if not coupon:
            raise HTTPException(status_code=404, detail="Coupon not found")

        # Check if coupon is valid
        if not coupon.can_used:
            if not coupon.is_active:
                return ApplyCouponResponse(
                    success=False, message="Coupon is not active"
                )
            elif coupon.remaining <= 0:
                return ApplyCouponResponse(
                    success=False, message="Coupon usage limit reached"
                )
            elif coupon.expire_date and datetime.utcnow() > coupon.expire_date:
                return ApplyCouponResponse(success=False, message="Coupon has expired")

        # Get user
        user_stmt = select(User).where(User.id == user_id)
        user = self.db.execute(user_stmt).scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if user already used this coupon
        if user in coupon.users:
            return ApplyCouponResponse(
                success=False, message="You have already used this coupon"
            )

        # Apply coupon: add user to coupon's users list and increment used_count
        coupon.users.append(user)
        coupon.used_count += 1

        self.db.commit()
        self.db.refresh(coupon)

        return ApplyCouponResponse(
            success=True,
            message="Coupon applied successfully",
            coupon=coupon,
        )

    @db_exception_handler
    def get_coupon_usage_stats(self) -> dict:
        """Get statistics about coupon usage"""
        stmt = select(Coupon)
        coupons = self.db.execute(stmt).scalars().all()

        total_coupons = len(coupons)
        total_usage = sum(coupon.used_count for coupon in coupons)
        active_coupons = sum(1 for coupon in coupons if coupon.is_active)

        return {
            "total_coupons": total_coupons,
            "active_coupons": active_coupons,
            "total_usage": total_usage,
            "coupons": [
                {
                    "id": coupon.id,
                    "code": coupon.code,
                    "activity": coupon.activity,
                    "used_count": coupon.used_count,
                    "remaining": coupon.remaining,
                    "is_active": coupon.is_active,
                }
                for coupon in coupons
            ],
        }
