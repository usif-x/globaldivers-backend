# app/services/price_calculator.py
"""
Price calculator service for invoices.
Handles all pricing logic including base price calculation and discount application.
"""

from datetime import datetime
from typing import Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.coupon import Coupon
from app.models.course import Course
from app.models.trip import Trip


class PriceCalculator:
    """
    Utility class for calculating invoice amounts based on activity type,
    participants, and applicable discounts.
    """

    @staticmethod
    def calculate_trip_price(
        db: Session,
        trip_id: int,
        adults: int,
        children: int,
        coupon_code: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Tuple[float, float, Optional[dict]]:
        """
        Calculate the total price for a trip booking.

        Returns:
            Tuple[float, float, Optional[dict]]:
                - total_price: Final amount after all discounts
                - discount_amount: Total discount applied
                - discount_info: Dictionary with discount breakdown

        Raises:
            HTTPException: If trip not found, invalid participants, or invalid coupon
        """
        # 1. Validate and fetch trip
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trip with ID {trip_id} not found",
            )

        # 2. Validate participant counts
        if adults < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 1 adult is required for a trip booking",
            )

        if not trip.child_allowed and children > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Trip '{trip.name}' does not allow children",
            )

        total_participants = adults + children
        if total_participants > trip.maxim_person:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Trip '{trip.name}' allows maximum {trip.maxim_person} participants, but {total_participants} were requested",
            )

        # 3. Calculate base price (before any discounts)
        base_price = (adults * trip.adult_price) + (children * trip.child_price)

        # 4. Calculate group discount (built-in discount on trip)
        group_discount_amount = 0.0
        group_discount_info = None

        if trip.has_discount:
            # Check if discount applies based on minimum people requirement
            discount_applies = False

            if trip.discount_always_available:
                # Discount is always available
                discount_applies = True
            elif trip.discount_requires_min_people and trip.discount_min_people:
                # Discount only applies if minimum people is met
                if total_participants >= trip.discount_min_people:
                    discount_applies = True

            if discount_applies and trip.discount_percentage:
                group_discount_amount = (base_price * trip.discount_percentage) / 100
                group_discount_info = {
                    "type": "group_discount",
                    "percentage": trip.discount_percentage,
                    "amount": group_discount_amount,
                    "applied_because": (
                        "always available"
                        if trip.discount_always_available
                        else f"minimum {trip.discount_min_people} people required"
                    ),
                }

        # 5. Calculate promo code discount (if applicable)
        promo_discount_amount = 0.0
        promo_discount_info = None
        coupon_obj = None

        if coupon_code:
            coupon_obj = db.query(Coupon).filter(Coupon.code == coupon_code).first()

            if not coupon_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Coupon code '{coupon_code}' not found",
                )

            # Validate coupon
            PriceCalculator._validate_coupon(coupon_obj, user_id, "trip")

            # Apply coupon discount to the price after group discount
            price_after_group_discount = base_price - group_discount_amount
            promo_discount_amount = (
                price_after_group_discount * coupon_obj.discount_percentage
            ) / 100
            promo_discount_info = {
                "type": "promo_code",
                "code": coupon_code,
                "percentage": coupon_obj.discount_percentage,
                "amount": promo_discount_amount,
            }

        # 6. Calculate final price
        total_discount = group_discount_amount + promo_discount_amount
        final_price = base_price - total_discount

        # Ensure final price is not negative
        if final_price < 0:
            final_price = 0.0

        discount_info = {
            "base_price": base_price,
            "total_discount": total_discount,
            "group_discount": group_discount_info,
            "promo_discount": promo_discount_info,
            "final_price": final_price,
            "coupon_code": coupon_code,
        }

        return final_price, total_discount, discount_info, coupon_obj

    @staticmethod
    def calculate_course_price(
        db: Session,
        course_id: int,
        coupon_code: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Tuple[float, float, Optional[dict]]:
        """
        Calculate the total price for a course booking.

        Returns:
            Tuple[float, float, Optional[dict]]:
                - total_price: Final amount after all discounts
                - discount_amount: Total discount applied
                - discount_info: Dictionary with discount breakdown

        Raises:
            HTTPException: If course not found or invalid coupon
        """
        # 1. Validate and fetch course
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found",
            )

        if not course.price_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Course '{course.name}' pricing is not available",
            )

        # 2. Base price
        base_price = course.price

        # 3. Calculate group discount (built-in discount on course)
        group_discount_amount = 0.0
        group_discount_info = None

        if course.has_discount:
            discount_applies = False

            if course.discount_always_available:
                discount_applies = True
            elif course.discount_requires_min_people and course.discount_min_people:
                # For courses, min people might not apply in same way as trips
                # This is a placeholder - adjust based on your business logic
                discount_applies = True

            if discount_applies and course.discount_percentage:
                group_discount_amount = (base_price * course.discount_percentage) / 100
                group_discount_info = {
                    "type": "group_discount",
                    "percentage": course.discount_percentage,
                    "amount": group_discount_amount,
                }

        # 4. Calculate promo code discount
        promo_discount_amount = 0.0
        promo_discount_info = None
        coupon_obj = None

        if coupon_code:
            coupon_obj = db.query(Coupon).filter(Coupon.code == coupon_code).first()

            if not coupon_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Coupon code '{coupon_code}' not found",
                )

            PriceCalculator._validate_coupon(coupon_obj, user_id, "course")

            price_after_group_discount = base_price - group_discount_amount
            promo_discount_amount = (
                price_after_group_discount * coupon_obj.discount_percentage
            ) / 100
            promo_discount_info = {
                "type": "promo_code",
                "code": coupon_code,
                "percentage": coupon_obj.discount_percentage,
                "amount": promo_discount_amount,
            }

        # 5. Calculate final price
        total_discount = group_discount_amount + promo_discount_amount
        final_price = base_price - total_discount

        if final_price < 0:
            final_price = 0.0

        discount_info = {
            "base_price": base_price,
            "total_discount": total_discount,
            "group_discount": group_discount_info,
            "promo_discount": promo_discount_info,
            "final_price": final_price,
            "coupon_code": coupon_code,
        }

        return final_price, total_discount, discount_info, coupon_obj

    @staticmethod
    def _validate_coupon(
        coupon: Coupon, user_id: Optional[int] = None, activity_type: str = "all"
    ) -> None:
        """
        Validate that a coupon is applicable.

        Raises:
            HTTPException: If coupon is invalid or cannot be used
        """
        # Check if coupon is active
        if not coupon.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This coupon code is no longer active",
            )

        # Check if coupon has been used up
        if coupon.can_used_up_to > 0 and coupon.used_count >= coupon.can_used_up_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This coupon code has reached its usage limit",
            )

        # Check if coupon has expired
        if coupon.expire_date and datetime.utcnow() > coupon.expire_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This coupon code has expired",
            )

        # Check if coupon applies to this activity type
        if coupon.activity != "all" and coupon.activity != activity_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This coupon code is not valid for {activity_type} bookings",
            )

    @staticmethod
    def verify_amount_matches_calculation(
        calculated_amount: float, submitted_amount: float, tolerance: float = 1.0
    ) -> bool:
        """
        Verify that the submitted amount matches the backend-calculated amount.
        Uses a tolerance (default 1.0) to account for floating-point rounding
        and different rounding strategies between frontend and backend.

        Returns:
            bool: True if amounts match within tolerance, False otherwise
        """
        return abs(calculated_amount - submitted_amount) <= tolerance
