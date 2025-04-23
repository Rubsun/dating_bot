from fastapi import HTTPException, APIRouter

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from components.rating_service.repositories import ProfileRatingRepository

from components.rating_service.schemas import RatingCreate, RatingResponse, RatingBase


router = APIRouter(route_class=DishkaRoute)


@router.post("/ratings", response_model=RatingResponse)
async def create_rating(
        rating_data: RatingCreate,
        rating_repo: FromDishka[ProfileRatingRepository],
):
    profile = await rating_repo.get_rating_by_profile_id(rating_data.profile_telegram_id)
    if profile:
        raise HTTPException(status_code=404, detail="Profile is already registered")

    rating = await rating_repo.create_rating(
        profile_telegram_id=rating_data.profile_telegram_id,
        rating_score=rating_data.rating_score
    )
    return rating


@router.get("/ratings/{profile_id}", response_model=RatingResponse)
async def get_rating(
        profile_id: int,
        rating_repo: FromDishka[ProfileRatingRepository]
):
    rating = await rating_repo.get_rating_by_profile_id(profile_id)
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    return rating


@router.put("/ratings/{profile_id}", response_model=RatingResponse)
async def update_rating(
        profile_id: int,
        rating_data: RatingBase,
        rating_repo: FromDishka[ProfileRatingRepository]
):
    updated = await rating_repo.update_rating(profile_id, rating_data.rating_score)
    if not updated:
        raise HTTPException(status_code=404, detail="Rating not found")
    return updated


@router.delete("/ratings/{profile_id}")
async def delete_rating(
        profile_id: int,
        rating_repo: FromDishka[ProfileRatingRepository]
):
    success = await rating_repo.delete_rating(profile_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rating not found")
    return {"message": "Rating deleted successfully"}


@router.get("/top", response_model=list[RatingResponse])
async def get_top_ratings(
        rating_repo: FromDishka[ProfileRatingRepository],
        limit: int = 10
):
    profiles = await rating_repo.get_top_ratings(limit)

    return profiles
