from typing import Optional, List
from pydantic import BaseModel


class CreateTrip(BaseModel):
  name: str
  description: str
  images: List[str]
  is_image_list: bool = False
  adult_price: float
  child_price: float
  maxim_person: int
  has_discount: bool
  discount_percentage: float
  duration: int
  package_id: int
  included: List[str]
  not_included: List[str]
  terms_and_conditions: List[str]



class TripResponse(BaseModel):
  id: int
  name: str
  description: Optional[str] = None
  images: List[str]
  is_image_list: bool = False
  adult_price: float
  child_price: float
  maxim_person: int
  package_id: int
  has_discount: bool = False
  discount_percentage: Optional[int] = None
  included: Optional[List[str]] = None
  duration: Optional[int] = None
  not_included: Optional[List[str]] = None
  terms_and_conditions: Optional[List[str]]

  class Config:
    from_attributes = True



class UpdateTrip(BaseModel):
  name: Optional[str] = None
  description: Optional[str] = None
  images: Optional[List[str]] = None
  is_image_list: Optional[bool] = None
  adult_price: Optional[float] = None
  child_price: Optional[float] = None
  maxim_person: Optional[int] = None
  has_discount: Optional[bool] = None
  discount_percentage: Optional[int] = None
  duration: Optional[int] = None
  package_id: Optional[int] = None
  included: Optional[List[str]] = None
  not_included: Optional[List[str]] = None
  terms_and_conditions: Optional[List[str]] = None