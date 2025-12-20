# app/routes/coupon.py
from typing import List

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin, get_current_user
from app.schemas.coupon import (
    ApplyCouponRequest,
    ApplyCouponResponse,
    CouponCreate,
    CouponResponse,
    CouponUpdate,
)
from app.services.coupon import CouponServices

coupon_routes = APIRouter(prefix="/coupons", tags=["Coupon Endpoints"])


@coupon_routes.post(
    "/", response_model=CouponResponse, dependencies=[Depends(get_current_admin)]
)
async def create_coupon(
    coupon: CouponCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new coupon (Admin only).
    """
    return CouponServices(db).create_coupon(coupon)


@coupon_routes.get("/", response_model=List[CouponResponse])
async def get_all_coupons(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    Get all coupons with pagination.
    """
    return CouponServices(db).get_all_coupons(skip=skip, limit=limit)


@coupon_routes.get("/{coupon_id}", response_model=CouponResponse)
async def get_coupon_by_id(
    coupon_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    """
    Get a specific coupon by ID.
    """
    return CouponServices(db).get_coupon_by_id(coupon_id)


@coupon_routes.put(
    "/{coupon_id}",
    response_model=CouponResponse,
    dependencies=[Depends(get_current_admin)],
)
async def update_coupon(
    coupon_id: int = Path(..., ge=1),
    coupon: CouponUpdate = None,
    db: Session = Depends(get_db),
):
    """
    Update a coupon (Admin only).
    """
    return CouponServices(db).update_coupon(coupon_id, coupon)


@coupon_routes.delete("/{coupon_id}", dependencies=[Depends(get_current_admin)])
async def delete_coupon(
    coupon_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    """
    Delete a coupon (Admin only).
    """
    return CouponServices(db).delete_coupon(coupon_id)


@coupon_routes.post(
    "/apply",
    response_model=ApplyCouponResponse,
    dependencies=[Depends(get_current_user)],
)
async def apply_coupon(
    request: ApplyCouponRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Apply a coupon code to the current user.
    """
    return CouponServices(db).apply_coupon(request.code, current_user.id)


@coupon_routes.get("/stats/usage", dependencies=[Depends(get_current_admin)])
async def get_coupon_stats(
    db: Session = Depends(get_db),
):
    """
    Get coupon usage statistics (Admin only).
    """
    return CouponServices(db).get_coupon_usage_stats()
