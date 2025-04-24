from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LikeDislikePayload(BaseModel):
    rater_user_id: int
    rated_user_id: int
    like_type: str