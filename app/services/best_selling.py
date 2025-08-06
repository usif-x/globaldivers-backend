from typing import List, Optional

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session, selectinload

from app.models.best_selling import BestSelling, ItemType
from app.models.course import Course
from app.models.trip import Trip
from app.schemas.best_selling import BestSellingCreate, BestSellingUpdate


class BestSellingService:
    @staticmethod
    def create_best_selling(
        db: Session, best_selling_data: BestSellingCreate
    ) -> BestSelling:
        # Set the appropriate foreign key based on item_type
        course_id = (
            best_selling_data.item_id
            if best_selling_data.item_type == ItemType.COURSE
            else None
        )
        trip_id = (
            best_selling_data.item_id
            if best_selling_data.item_type == ItemType.TRIP
            else None
        )

        # Check if item exists
        if best_selling_data.item_type == ItemType.COURSE:
            course = (
                db.query(Course).filter(Course.id == best_selling_data.item_id).first()
            )
            if not course:
                raise ValueError(
                    f"Course with id {best_selling_data.item_id} not found"
                )
        else:
            trip = db.query(Trip).filter(Trip.id == best_selling_data.item_id).first()
            if not trip:
                raise ValueError(f"Trip with id {best_selling_data.item_id} not found")

        # Check if ranking position is already taken
        existing = (
            db.query(BestSelling)
            .filter(BestSelling.ranking_position == best_selling_data.ranking_position)
            .first()
        )

        if existing:
            raise ValueError(
                f"Ranking position {best_selling_data.ranking_position} is already taken"
            )

        best_selling = BestSelling(
            item_type=best_selling_data.item_type,
            item_id=best_selling_data.item_id,
            ranking_position=best_selling_data.ranking_position,
            course_id=course_id,
            trip_id=trip_id,
        )

        db.add(best_selling)
        db.commit()
        db.refresh(best_selling)
        return best_selling

    @staticmethod
    def get_best_selling_by_id(
        db: Session, best_selling_id: int
    ) -> Optional[BestSelling]:
        return (
            db.query(BestSelling)
            .options(selectinload(BestSelling.course), selectinload(BestSelling.trip))
            .filter(BestSelling.id == best_selling_id)
            .first()
        )

    @staticmethod
    def get_all_best_selling(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        item_type: Optional[ItemType] = None,
    ) -> tuple[List[BestSelling], int]:
        query = db.query(BestSelling).options(
            selectinload(BestSelling.course), selectinload(BestSelling.trip)
        )

        if item_type:
            query = query.filter(BestSelling.item_type == item_type)

        # Order by ranking position
        query = query.order_by(BestSelling.ranking_position)

        total = query.count()
        items = query.offset(skip).limit(limit).all()

        return items, total

    @staticmethod
    def get_best_selling_courses(db: Session, limit: int = 10) -> List[BestSelling]:
        return (
            db.query(BestSelling)
            .options(selectinload(BestSelling.course))
            .filter(BestSelling.item_type == ItemType.COURSE)
            .order_by(BestSelling.ranking_position)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_best_selling_trips(db: Session, limit: int = 10) -> List[BestSelling]:
        return (
            db.query(BestSelling)
            .options(selectinload(BestSelling.trip))
            .filter(BestSelling.item_type == ItemType.TRIP)
            .order_by(BestSelling.ranking_position)
            .limit(limit)
            .all()
        )

    @staticmethod
    def update_best_selling(
        db: Session, best_selling_id: int, best_selling_update: BestSellingUpdate
    ) -> Optional[BestSelling]:
        best_selling = (
            db.query(BestSelling).filter(BestSelling.id == best_selling_id).first()
        )

        if not best_selling:
            return None

        update_data = best_selling_update.model_dump(exclude_unset=True)

        # Handle ranking position conflicts
        if "ranking_position" in update_data:
            existing = (
                db.query(BestSelling)
                .filter(
                    and_(
                        BestSelling.ranking_position == update_data["ranking_position"],
                        BestSelling.id != best_selling_id,
                    )
                )
                .first()
            )

            if existing:
                raise ValueError(
                    f"Ranking position {update_data['ranking_position']} is already taken"
                )

        # Handle item_type and item_id changes
        if "item_type" in update_data or "item_id" in update_data:
            item_type = update_data.get("item_type", best_selling.item_type)
            item_id = update_data.get("item_id", best_selling.item_id)

            # Verify the item exists
            if item_type == ItemType.COURSE:
                course = db.query(Course).filter(Course.id == item_id).first()
                if not course:
                    raise ValueError(f"Course with id {item_id} not found")
                update_data["course_id"] = item_id
                update_data["trip_id"] = None
            else:
                trip = db.query(Trip).filter(Trip.id == item_id).first()
                if not trip:
                    raise ValueError(f"Trip with id {item_id} not found")
                update_data["trip_id"] = item_id
                update_data["course_id"] = None

        for field, value in update_data.items():
            setattr(best_selling, field, value)

        db.commit()
        db.refresh(best_selling)
        return best_selling

    @staticmethod
    def delete_best_selling(db: Session, best_selling_id: int) -> bool:
        best_selling = (
            db.query(BestSelling).filter(BestSelling.id == best_selling_id).first()
        )

        if not best_selling:
            return False

        db.delete(best_selling)
        db.commit()
        return True

    @staticmethod
    def reorder_rankings(
        db: Session, item_type: Optional[ItemType] = None
    ) -> List[BestSelling]:
        """Reorder rankings to ensure sequential numbering (1, 2, 3, ...)"""
        query = db.query(BestSelling)

        if item_type:
            query = query.filter(BestSelling.item_type == item_type)

        items = query.order_by(BestSelling.ranking_position).all()

        for index, item in enumerate(items, 1):
            item.ranking_position = index

        db.commit()
        return items
