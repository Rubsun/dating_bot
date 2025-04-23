from fastapi import HTTPException, APIRouter

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute

from components.profile_service.minio_utils import MinIOClient
from components.profile_service.repositories import ProfileRepository
from components.profile_service.schemas import ProfileRequest

router = APIRouter(route_class=DishkaRoute)


@router.post("/profiles")
async def create_profile(
        profile_request: ProfileRequest,  # Accept data in the request body
        profile_repo: FromDishka[ProfileRepository],
        s3_client: FromDishka[MinIOClient],
):
    # Validate gender (Redundant because it's validated in Pydantic, but included as an example)
    if profile_request.gender not in ["Male", "Female", "Other"]:
        raise HTTPException(status_code=400, detail="Invalid gender value")

    # For simplicity, the file handling is omitted. In production, you might upload the photo separately and update the profile with a file path.
    photo = profile_request.photo  # Assuming the client provides the path/filename

    # Save the photo to a specific folder (mocked here)
    photo_file_name = f"{profile_request.first_name}_{profile_request.last_name}"
    photo_url = s3_client.upload_file(photo, photo_file_name)

    # Use the repository to save the profile in the database
    new_profile = await profile_repo.create_profile(
        telegram_id=profile_request.telegram_id,
        first_name=profile_request.first_name,
        last_name=profile_request.last_name,
        bio=profile_request.bio,
        age=profile_request.age,
        gender=profile_request.gender,
        city=profile_request.city,
        photo_path=photo_url,
    )

    return {"message": "Profile created successfully", "profile": {
        "id": new_profile.id,
        "first_name": new_profile.first_name,
        "last_name": new_profile.last_name,
        "bio": new_profile.bio,
        "age": new_profile.age,
        "gender": new_profile.gender,
        "city": new_profile.city,
        "photo_path": new_profile.photo_path
    }}


@router.get("/profiles/{profile_id}")
async def get_profile(profile_id: int, profile_repo: FromDishka[ProfileRepository]):
    """
    Endpoint to fetch a profile by its ID.
    """
    profile = await profile_repo.get_profile_by_id(profile_id)

    if profile is None:
        raise HTTPException(
            status_code=404, detail=f"Profile with ID {profile_id} not found"
        )

    return {
        "id": profile.id,
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "bio": profile.bio,
        "age": profile.age,
        "gender": profile.gender,
        "city": profile.city,
        "photo_path": profile.photo_path,
    }


@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: int, profile_repo: FromDishka[ProfileRepository]):
    """
    Endpoint to delete a profile by its ID.
    """
    success = await profile_repo.delete_profile_by_id(profile_id)

    if not success:
        raise HTTPException(
            status_code=404, detail=f"Profile with ID {profile_id} not found"
        )
    return {"message": f"Profile with ID {profile_id} was successfully deleted"}
