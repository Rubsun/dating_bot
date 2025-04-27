from datetime import datetime
from typing import Optional

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import HTTPException, APIRouter, Depends, UploadFile

from components.profile_service.dependencies import validate_profile_form
from components.profile_service.minio_utils import MinIOClient
from components.profile_service.repositories import ProfileRepository
from components.profile_service.schemas import ProfileFormData

router = APIRouter(route_class=DishkaRoute)


@router.post("/profiles")
async def create_profile(
        profile_repo: FromDishka[ProfileRepository],
        s3_client: FromDishka[MinIOClient],
        photos: Optional[list[UploadFile]] = None,
        profile_data: ProfileFormData = Depends(validate_profile_form),
):
    photo_url = None
    if photos:
        for photo in photos:
            print("Photo:", photo)
            if photo.content_type not in ["image/jpeg", "image/png", "image/gif"]:
                raise HTTPException(status_code=400, detail="Invalid file type. Only JPG, PNG, GIF allowed.")

            photo_file_name = f"{profile_data.telegram_id}_{profile_data.first_name}_{profile_data.last_name}_{datetime.now()}"
            photo_bytes = await photo.read()

            try:
                photo_url = s3_client.upload_file(photo_bytes, photo_file_name)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to upload photo: {e}")
            finally:
                await photo.close()

    try:
        new_profile = await profile_repo.create_profile(
            telegram_id=profile_data.telegram_id,
            first_name=profile_data.first_name,
            last_name=profile_data.last_name,
            tg_username=profile_data.tg_username,
            bio=profile_data.bio,
            age=profile_data.age,
            gender=profile_data.gender,
            city=profile_data.city,
            photo_path=photo_url,
            photo_file_ids=profile_data.photo_file_ids
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create profile in database: {e}")

    return {
        "message": "Profile created successfully",
        "profile": {
            "id": new_profile.id,
            "telegram_id": profile_data.telegram_id,
            "first_name": new_profile.first_name,
            "last_name": new_profile.last_name,
            "tg_username": new_profile.tg_username,
            "bio": new_profile.bio,
            "age": new_profile.age,
            "gender": new_profile.gender,
            "city": new_profile.city,
            "photo_path": new_profile.photo_path,
            "photo_file_ids": new_profile.photo_file_ids
        }
    }


@router.get("/profiles/{profile_id}")
async def get_profile(profile_id: int, profile_repo: FromDishka[ProfileRepository]):
    profile = await profile_repo.get_profile_by_id(profile_id)

    if profile is None:
        raise HTTPException(
            status_code=404, detail=f"Profile with ID {profile_id} not found"
        )

    return {
        "id": profile.id,
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "tg_username": profile.tg_username,
        "bio": profile.bio,
        "age": profile.age,
        "gender": profile.gender,
        "city": profile.city,
        "photo_path": profile.photo_path,
        "photo_file_ids": profile.photo_file_ids,
    }


@router.post("/many-profiles")
async def get_many_profiles(
        profile_ids: list[int],
        profile_repo: FromDishka[ProfileRepository],
):
    profiles = await profile_repo.get_profiles_by_ids(profile_ids)

    return [
        {
            "id": profile.id,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "tg_username": profile.tg_username,
            "bio": profile.bio,
            "age": profile.age,
            "gender": profile.gender,
            "city": profile.city,
            "photo_path": profile.photo_path,
            "photo_file_ids": profile.photo_file_ids,
        }
        for profile in profiles
    ]


@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: int, profile_repo: FromDishka[ProfileRepository]):
    success = await profile_repo.delete_profile_by_id(profile_id)

    if not success:
        raise HTTPException(
            status_code=404, detail=f"Profile with ID {profile_id} not found"
        )
    return {"message": f"Profile with ID {profile_id} was successfully deleted"}
