from pydantic import BaseModel, Field
from typing import Optional


class ProfileRequest(BaseModel):
    telegram_id: int = Field(..., example=12345678)
    first_name: str = Field(..., max_length=100, example="John")
    last_name: str = Field(..., max_length=100, example="Doe")
    bio: Optional[str] = Field(None, max_length=300, example="Software Developer")
    age: int = Field(..., ge=0, le=150, example=30)
    gender: str = Field(
        ..., example="Male", description="Allowed values: Male, Female, Other"
    )
    city: str = Field(..., max_length=100, example="New York")
    photo: bytes = Field(..., description='photo content')
