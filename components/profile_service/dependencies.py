from typing import Optional, Annotated

from fastapi import Request, Form, HTTPException
from pydantic import ValidationError

from components.profile_service.schemas import ProfileFormData
from components.profile_service.schemas import ProfileFormData as StarletteUploadFile


async def optional_file_upload(request: Request) -> Optional[StarletteUploadFile]:
    form = await request.form()
    file = form.get("photo")

    if isinstance(file, StarletteUploadFile):
        return file
    return None


async def validate_profile_form(
        age: Annotated[int, Form(...)],
        gender: Annotated[str, Form(...)],
        city: Annotated[str, Form(...)],
        telegram_id: Annotated[int, Form(...)],
        first_name: Annotated[str, Form(...)],
        last_name: Annotated[str, Form(...)],
        tg_username: Annotated[str, Form(...)],
        bio: Annotated[Optional[str], Form()] = None,
        photo_file_id: Annotated[Optional[str], Form()] = None,
) -> ProfileFormData:
    try:
        profile_data = ProfileFormData(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            tg_username=tg_username,
            bio=bio,
            age=age,
            gender=gender,
            city=city,
            photo_file_id=photo_file_id
        )
        return profile_data
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
