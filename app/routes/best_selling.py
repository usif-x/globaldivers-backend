from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.models.best_selling import ItemType
from app.schemas.best_selling import (
    BestSellingCreate,
    BestSellingListResponse,
    BestSellingResponse,
    BestSellingUpdate,
)
from app.services.best_selling import BestSellingService

best_selling_routes = APIRouter(prefix="/best-selling", tags=["best-selling"])


@best_selling_routes.post(
    "/",
    response_model=BestSellingResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
def create_best_selling(
    best_selling_data: BestSellingCreate, db: Session = Depends(get_db)
):
    """Create a new best selling item"""
    try:
        best_selling = BestSellingService.create_best_selling(db, best_selling_data)
        return best_selling
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@best_selling_routes.get("/", response_model=BestSellingListResponse)
def get_all_best_selling(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    item_type: Optional[ItemType] = Query(None, description="Filter by item type"),
    db: Session = Depends(get_db),
):
    """Get all best selling items with pagination"""
    skip = (page - 1) * per_page

    items, total = BestSellingService.get_all_best_selling(
        db, skip=skip, limit=per_page, item_type=item_type
    )

    total_pages = ceil(total / per_page)

    return BestSellingListResponse(
        items=items, total=total, page=page, per_page=per_page, total_pages=total_pages
    )


@best_selling_routes.get("/courses", response_model=list[BestSellingResponse])
def get_best_selling_courses(
    limit: int = Query(10, ge=1, le=50, description="Number of courses to return"),
    db: Session = Depends(get_db),
):
    """Get best selling courses"""
    courses = BestSellingService.get_best_selling_courses(db, limit=limit)
    return courses


@best_selling_routes.get("/trips", response_model=list[BestSellingResponse])
def get_best_selling_trips(
    limit: int = Query(10, ge=1, le=50, description="Number of trips to return"),
    db: Session = Depends(get_db),
):
    """Get best selling trips"""
    trips = BestSellingService.get_best_selling_trips(db, limit=limit)
    return trips


@best_selling_routes.get("/{best_selling_id}", response_model=BestSellingResponse)
def get_best_selling_by_id(best_selling_id: int, db: Session = Depends(get_db)):
    """Get a specific best selling item by ID"""
    best_selling = BestSellingService.get_best_selling_by_id(db, best_selling_id)

    if not best_selling:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Best selling item with id {best_selling_id} not found",
        )

    return best_selling


@best_selling_routes.put(
    "/{best_selling_id}",
    response_model=BestSellingResponse,
    dependencies=[Depends(get_current_admin)],
)
def update_best_selling(
    best_selling_id: int,
    best_selling_update: BestSellingUpdate,
    db: Session = Depends(get_db),
):
    """Update a best selling item"""
    try:
        best_selling = BestSellingService.update_best_selling(
            db, best_selling_id, best_selling_update
        )

        if not best_selling:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Best selling item with id {best_selling_id} not found",
            )

        return best_selling
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@best_selling_routes.delete(
    "/{best_selling_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_admin)],
)
def delete_best_selling(best_selling_id: int, db: Session = Depends(get_db)):
    """Delete a best selling item"""
    success = BestSellingService.delete_best_selling(db, best_selling_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Best selling item with id {best_selling_id} not found",
        )


@best_selling_routes.post(
    "/reorder",
    response_model=list[BestSellingResponse],
    dependencies=[Depends(get_current_admin)],
)
def reorder_rankings(
    item_type: Optional[ItemType] = Query(
        None, description="Reorder specific item type only"
    ),
    db: Session = Depends(get_db),
):
    """Reorder rankings to ensure sequential numbering"""
    try:
        items = BestSellingService.reorder_rankings(db, item_type=item_type)
        return items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
