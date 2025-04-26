from datetime import datetime
from typing import TypedDict

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
