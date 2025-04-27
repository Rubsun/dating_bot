from datetime import datetime
from typing import TypedDict
from geoalchemy2.shape import to_shape

from pydantic import BaseModel, Field


class LikeDislikePayload(BaseModel):
    rater_user_id: int
    rated_user_id: int
    rater_username: str
    rated_username: str
    like_type: str

class UserMatch(TypedDict):
    user1_id: int
    user2_id: int
    user1_username: str
    user2_username: str
    # match_date: datetime

class UserInfoCreate(BaseModel):
    user_id: int
    age: int
    gender: str
    rating: float
    preferred_gender: str
    preferred_min_age: int
    preferred_max_age: int
    latitude: float
    longitude: float


class UserInfoUpdate(BaseModel):
    age: int | None = None
    gender: str | None = None
    rating: float | None = None
    preferred_gender: str | None = None
    preferred_min_age: int | None = None
    preferred_max_age: int | None = None
    latitude: float | None = None
    longitude: float | None = None


class UserInfoResponse(BaseModel):
    user_id: int
    age: int | None
    gender: str | None
    rating: float | None
    preferred_gender: str | None
    preferred_min_age: int | None
    preferred_max_age: int | None
    longitude: float | None
    latitude: float | None


class UserLike(TypedDict):
    liker_id: int
    liked_id: int
    like_date: str