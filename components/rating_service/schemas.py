from datetime import datetime
from pydantic import BaseModel, Field

class RatingBase(BaseModel):
    rating_score: float = Field(..., ge=0, le=100, example=85.5, description="Rating value between 0 and 100")


class RatingCreate(RatingBase):
    profile_telegram_id: int = Field(..., example=123456789)


class RatingResponse(RatingBase):
    profile_telegram_id: int
    last_calculated_at: datetime

    class Config:
        from_attributes = True
