from typing import Optional, Annotated

from fastapi import UploadFile, Request, Form, HTTPException
from pydantic import ValidationError

from components.profile_service.schemas import ProfileFormData
from components.profile_service.schemas import ProfileFormData as StarletteUploadFile


async def optional_file_upload(request: Request) -> Optional[list[StarletteUploadFile]]:
    form = await request.form()
    files = form.get("photos")

    if isinstance(files, list):
        return files
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
        photo_file_ids: Annotated[Optional[list[str]], Form()] = None,
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
            photo_file_ids=eval(photo_file_ids[0]) if photo_file_ids else None
        )
        return profile_data
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())