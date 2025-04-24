from datetime import datetime
from typing import TypedDict

from pydantic import BaseModel, Field


class LikeDislikePayload(BaseModel):
    rater_user_id: int
    rated_user_id: int
    like_type: str

class UserMatch(TypedDict):
    user1_id: int
    user2_id: int
    # match_data: datetime