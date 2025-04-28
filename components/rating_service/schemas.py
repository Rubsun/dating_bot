from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProfileInfoCreate(BaseModel):
    telegram_id: int = Field(..., example=12345678)
    first_name: str = Field(..., example="John")
    last_name: str = Field(..., example="Doe")
    bio: Optional[str] = Field(None, example="Software Developer")
    age: int = Field(..., example=30)
    gender: str = Field(
        ..., example="Male", description="Allowed values: Male, Female, Other"
    )
    city: str = Field(..., example="New York")
    photo_file_ids: Optional[list[str]] = Field(None, example="AgACAgUAAxkBAA...")


class ProfileInfoUpdate(BaseModel):
    telegram_id: int = Field(..., example=12345678)
    first_name: str = Field(..., example="John")
    last_name: str = Field(..., example="Doe")
    bio: Optional[str] = Field(None, example="Software Developer")
    rating: float = Field(..., example=1000)
    age: int = Field(..., example=30)
    gender: str = Field(
        ..., example="Male", description="Allowed values: Male, Female, Other"
    )
    city: str = Field(..., example="New York")
    photo_file_ids: Optional[list[str]] = Field(None, example="AgACAgUAAxkBAA...")


class RatingBase(BaseModel):
    rating_score: float = Field(..., example=85.5, description="Rating value between 0 and 100")


class RatingCreate(RatingBase):
    profile_telegram_id: int = Field(..., example=123456789)


class RatingResponse(RatingBase):
    profile_telegram_id: int
    last_calculated_at: datetime

    class Config:
        from_attributes = True


class LikeDislikePayload(BaseModel):
    rater_user_id: int
    rated_user_id: int


class StatsInfo(BaseModel):
    profile_telegram_id: int
    likes_givenL: int
    dislikes_given: int
    likes_received: int
    dislikes_received: int
    matches_count: int


class MatchingPayload(BaseModel):
    user1_id: int
    user2_id: int


class ChatPayload(BaseModel):
    watcher_id: int
    watched_id: int