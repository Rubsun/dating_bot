from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

class ProfileInfo(BaseModel):
    telegram_id: int = Field(..., example=12345678)
    first_name: str = Field(..., max_length=100, example="John")
    last_name: str = Field(..., max_length=100, example="Doe")
    bio: Optional[str] = Field(None, max_length=300, example="Software Developer")
    age: int = Field(..., ge=0, le=150, example=30)
    gender: str = Field(
        ..., example="Male", description="Allowed values: Male, Female, Other"
    )
    city: str = Field(..., max_length=100, example="New York")
    photo: Optional[bytes] = Field(..., description='photo content')


class RatingBase(BaseModel):
    rating_score: float = Field(..., ge=0, le=100, example=85.5, description="Rating value between 0 and 100")


class RatingCreate(RatingBase):
    profile_telegram_id: int = Field(..., example=123456789)


class RatingResponse(RatingBase):
    profile_telegram_id: int
    last_calculated_at: datetime

    class Config:
        from_attributes = True
