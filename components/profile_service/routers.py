from typing import Optional

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import HTTPException, APIRouter, Depends, UploadFile
# --- Добавляем импорт logger ---
from loguru import logger

from components.profile_service.dependencies import validate_profile_form
from components.profile_service.minio_utils import MinIOClient
from components.profile_service.repositories import ProfileRepository
from components.profile_service.schemas import ProfileFormData

router = APIRouter(route_class=DishkaRoute)


@router.post("/profiles")
async def create_profile(
        profile_repo: FromDishka[ProfileRepository],
        s3_client: FromDishka[MinIOClient],
        photo: Optional[UploadFile] = None,
        profile_data: ProfileFormData = Depends(validate_profile_form),
):
    logger.info(f"Attempting to create profile for telegram_id: {profile_data.telegram_id}")
    logger.debug(f"Received profile data: {profile_data.model_dump()}")

    photo_url = None
    if photo:
        logger.info(f"Photo provided for telegram_id: {profile_data.telegram_id}. Content-type: {photo.content_type}")
        logger.debug(f"Photo details: filename='{photo.filename}', content_type='{photo.content_type}'")

        if photo.content_type not in ["image/jpeg", "image/png", "image/gif"]:
            logger.warning(
                f"Invalid photo file type '{photo.content_type}' for telegram_id: {profile_data.telegram_id}")
            raise HTTPException(status_code=400, detail="Invalid file type. Only JPG, PNG, GIF allowed.")

        photo_file_name = f"{profile_data.telegram_id}_{profile_data.first_name}_{profile_data.last_name}"
        logger.debug(f"Generated photo file name: {photo_file_name}")

        photo_bytes = await photo.read()
        logger.debug(f"Read {len(photo_bytes)} bytes from photo for telegram_id: {profile_data.telegram_id}")

        try:
            logger.info(f"Uploading photo to S3 for telegram_id: {profile_data.telegram_id} as {photo_file_name}")
            photo_url = s3_client.upload_file(photo_bytes, photo_file_name)
            logger.info(f"Photo uploaded successfully for telegram_id: {profile_data.telegram_id}. URL: {photo_url}")
        except Exception as e:
            logger.exception(f"Failed to upload photo for telegram_id: {profile_data.telegram_id}. Error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload photo: {e}")
        finally:
            await photo.close()
            logger.debug(f"Photo file closed for telegram_id: {profile_data.telegram_id}")

    try:
        logger.info(f"Creating profile entry in database for telegram_id: {profile_data.telegram_id}")
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
            photo_file_id=profile_data.photo_file_id
        )
        logger.info(
            f"Profile created successfully in database for telegram_id: {profile_data.telegram_id}. Profile ID: {new_profile.id}")
    except Exception as e:
        logger.exception(
            f"Failed to create profile in database for telegram_id: {profile_data.telegram_id}. Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create profile in database: {e}")

    logger.info(f"Profile creation process completed for telegram_id: {profile_data.telegram_id}")
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
            "photo_file_id": new_profile.photo_file_id
        }
    }


@router.get("/profiles/{profile_id}")
async def get_profile(profile_id: int, profile_repo: FromDishka[ProfileRepository]):
    logger.info(f"Attempting to retrieve profile with ID: {profile_id}")
    profile = await profile_repo.get_profile_by_id(profile_id)

    if profile is None:
        logger.warning(f"Profile with ID {profile_id} not found.")
        raise HTTPException(
            status_code=404, detail=f"Profile with ID {profile_id} not found"
        )

    logger.info(f"Profile with ID {profile_id} retrieved successfully.")
    logger.debug(f"Retrieved profile data for ID {profile_id}: {profile.__dict__}")
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
        "photo_file_id": profile.photo_file_id,
    }


@router.post("/many-profiles")
async def get_many_profiles(
        profile_ids: list[int],
        profile_repo: FromDishka[ProfileRepository],
):
    logger.info(f"Attempting to retrieve multiple profiles with IDs: {profile_ids}")
    if not profile_ids:
        logger.warning("Received empty list of profile IDs for get_many_profiles.")
        return []

    profiles = await profile_repo.get_profiles_by_ids(profile_ids)
    logger.info(f"Retrieved {len(profiles)} profiles out of {len(profile_ids)} requested IDs.")
    logger.debug(f"Retrieved profile IDs: {[p.id for p in profiles]}")

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
            "photo_file_id": profile.photo_file_id,
        }
        for profile in profiles
    ]


@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: int, profile_repo: FromDishka[ProfileRepository]):
    logger.info(f"Attempting to delete profile with ID: {profile_id}")
    success = await profile_repo.delete_profile_by_id(profile_id)

    if not success:
        logger.warning(f"Profile with ID {profile_id} not found for deletion.")
        raise HTTPException(
            status_code=404, detail=f"Profile with ID {profile_id} not found"
        )

    logger.info(f"Profile with ID {profile_id} was successfully deleted.")
    return {"message": f"Profile with ID {profile_id} was successfully deleted"}
