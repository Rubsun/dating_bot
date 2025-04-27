from typing import Optional

from pydantic import BaseModel, Field
from pydantic.v1 import validator


class ProfileFormData(BaseModel):
    telegram_id: int = Field(..., example=12345678)
    first_name: str = Field(..., max_length=100, example="John")
    last_name: str = Field(..., max_length=100, example="Doe")
    tg_username: str = Field(..., max_length=100, example="johndoe21")
    bio: Optional[str] = Field(None, max_length=300, example="Software Developer")
    age: int = Field(..., ge=0, le=150, example=30)
    gender: str = Field(..., example="Male", description="Allowed values: Male, Female, Other")
    city: str = Field(..., max_length=100, example="New York")
    photo_file_id: Optional[str] = Field(None, example="AgACAgUAAxkBAA...")

    @validator('gender')
    def validate_gender(cls, v):
        if v not in ["Male", "Female", "Other"]:
            raise ValueError("Invalid gender value. Allowed: Male, Female, Other")
        return v
