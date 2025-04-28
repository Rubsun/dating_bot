import httpx
from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import HTTPException, APIRouter
from loguru import logger

from components.rating_service.config import Config
from components.rating_service.repositories import ProfileRatingRepository

from components.rating_service.schemas import RatingCreate, RatingResponse, RatingBase, ProfileInfoCreate, \
    LikeDislikePayload, ProfileInfoUpdate, StatsInfo, MatchingPayload, ChatPayload
from components.rating_service.schemas import RatingResponse, RatingBase, ProfileInfoCreate, \
    LikeDislikePayload
from components.rating_service.services import RatingService, ProfileRatingCalculator

service = RatingService(ProfileRatingCalculator())
router = APIRouter(route_class=DishkaRoute)


@router.post("/ratings", response_model=RatingResponse)
async def create_rating(
        rating_data: ProfileInfoCreate,
        rating_repo: FromDishka[ProfileRatingRepository],
):
    telegram_id = rating_data.telegram_id
    logger.info(f"Attempting to create initial rating for telegram_id: {telegram_id}")
    logger.debug(f"Received profile info for initial rating: {rating_data.model_dump()}")

    profile = await rating_repo.get_rating_by_profile_id(telegram_id)
    if profile:
        logger.warning(f"Rating profile already exists for telegram_id: {telegram_id}")
        raise HTTPException(status_code=404, detail="Profile is already registered")

    logger.debug(f"Calculating initial rating for telegram_id: {telegram_id}")
    rating = await service.init_rating(rating_data)
    logger.info(f"Calculated initial rating for telegram_id {telegram_id}: {rating}")

    logger.debug(f"Creating rating entry in database for telegram_id: {telegram_id}")
    profile_rating = await rating_repo.create_rating(
        profile_telegram_id=rating_data.telegram_id,
        rating_score=rating
    )
    logger.info(
        f"Successfully created rating for telegram_id: {telegram_id}. DB ID: {profile_rating.profile_telegram_id}")

    return profile_rating


@router.put("/ratings", response_model=RatingResponse)
async def create_rating(
        rating_data: ProfileInfoCreate,
        rating_repo: FromDishka[ProfileRatingRepository],
        cfg: FromDishka[Config]
):
    telegram_id = rating_data.telegram_id
    logger.info(f"Attempting to update rating based on profile changes for telegram_id: {telegram_id}")

    profile = await rating_repo.get_rating_by_profile_id(telegram_id)
    if not profile:
        raise HTTPException(status_code=404, detail="No Profile")

    profile_service_url = f"{cfg.profile_service_url}/profiles/{telegram_id}"

    async with httpx.AsyncClient() as client:
        response = await client.get(profile_service_url)

        if response.status_code == 404:
            logger.error(
                f"Profile not found in Profile Service (URL: {profile_service_url}) but rating exists for telegram_id: {telegram_id}.")

        elif response.status_code == 200:
            answer = response.json()
            logger.debug(
                f"Received profile data from Profile Service for telegram_id {telegram_id}: {answer}")
            old_rating = profile.rating_score
            logger.debug(f"Calculating updated rating for telegram_id {telegram_id}. Old rating: {old_rating}")
            rating = service.update_rating(old_rating, answer)
            logger.info(f"Calculated updated rating for telegram_id {telegram_id}: {rating}")

            logger.debug(f"Updating rating entry in database for telegram_id: {telegram_id}")
            profile_rating = await rating_repo.update_rating(
                profile_id=rating_data.telegram_id,
                new_rating=rating
            )
            logger.info(f"Successfully updated rating for telegram_id: {telegram_id}")
            return profile_rating


@router.get("/ratings/{profile_id}", response_model=RatingResponse)
async def get_rating(
        profile_id: int,
        rating_repo: FromDishka[ProfileRatingRepository]
):
    logger.info(f"Attempting to get rating for profile_id: {profile_id}")
    rating = await rating_repo.get_rating_by_profile_id(profile_id)
    if not rating:
        logger.warning(f"Rating not found for profile_id: {profile_id}")
        raise HTTPException(status_code=404, detail="Rating not found")
    logger.info(f"Rating found for profile_id: {profile_id}. Rating score: {rating.rating_score}")
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
    logger.info(f"Attempting to delete rating for profile_id: {profile_id}")
    success = await rating_repo.delete_rating(profile_id)
    if not success:
        logger.warning(f"Rating not found for deletion attempt for profile_id: {profile_id}")
        raise HTTPException(status_code=404, detail="Rating not found")
    logger.info(f"Successfully deleted rating for profile_id: {profile_id}")
    return {"message": "Rating deleted successfully"}


@router.get("/top", response_model=list[RatingResponse])
async def get_top_ratings(
        rating_repo: FromDishka[ProfileRatingRepository],
        limit: int = 10
):
    logger.info(f"Attempting to get top {limit} ratings.")
    profiles = await rating_repo.get_top_ratings(limit)
    logger.info(f"Retrieved {len(profiles)} top profiles.")
    logger.debug(f"Top profile IDs and ratings: {[(p.profile_telegram_id, p.rating_score) for p in profiles]}")

    return profiles


@router.post("/ratings/like")
async def rate_like(
        payload: LikeDislikePayload,
        rating_repo: FromDishka[ProfileRatingRepository]
):
    rater_rating = await rating_repo.get_rating_by_profile_id(payload.rater_user_id)
    rated_rating = await rating_repo.get_rating_by_profile_id(payload.rated_user_id)
    logger.info(
        f"Processing 'like' from rater_id {rater_rating.profile_telegram_id} to rated_id {rated_rating.profile_telegram_id}")
    logger.debug(f"Like payload: {payload.model_dump()}")

    rating = await service.add_like(rater_rating.rating_score, rated_rating.rating_score)
    await rating_repo.update_rating(payload.rated_user_id, rated_rating.rating_score + rating)
    logger.info(f"Successfully updated rating for rated_id {rated_rating.profile_telegram_id} after like.")
    return


@router.post("/ratings/dislike")
async def rate_dislike(
        payload: LikeDislikePayload,
        rating_repo: FromDishka[ProfileRatingRepository]
):
    rater_rating = await rating_repo.get_rating_by_profile_id(payload.rater_user_id)
    rated_rating = await rating_repo.get_rating_by_profile_id(payload.rated_user_id)
    logger.info(
        f"Processing 'dislike' from rater_id {rater_rating.profile_telegram_id} to rated_id {rated_rating.profile_telegram_id}")
    logger.debug(f"Dislike payload: {payload.model_dump()}")

    rating = await service.add_dislike(rater_rating.rating_score, rated_rating.rating_score)
    await rating_repo.update_rating(payload.rated_user_id, rated_rating.rating_score + rating)
    logger.info(f"Successfully updated rating for rated_id {rated_rating.profile_telegram_id} after dislike.")
    return


@router.post("/stats/info/{profile_id}", tags=["stats"])
async def stat_info(
        profile_id: int,
        rating_repo: FromDishka[ProfileRatingRepository],
        cfg: FromDishka[Config]
):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{cfg.matching_service_url}/match/stats/{profile_id}")
        stats = response.json()

    stats_info = await rating_repo.get_stats_by_profile_id(profile_id)
    if not stats_info:
        profile_stats = await rating_repo.create_stats(profile_id, **stats)

    else:
        profile_stats = await rating_repo.update_stats(profile_id, **stats)

    return profile_stats

@router.post("/stats/match", tags=["stats"])
async def note_match(
        payload: MatchingPayload
):
    await service.fimoz()
    print(payload.user1_id, payload.user2_id)
    return

@router.post("/stats/chat", tags=["stats"])
async def note_chat(
        payload: ChatPayload,
        rating_repo: FromDishka[ProfileRatingRepository]
):
    await service.fimoz()
    await rating_repo.add_chat(payload.watched_id)

    return

@router.post("/stats/ref/{user_id}", tags=["stats"])
async def note_ref(
    user_id: int,
    rating_repo: FromDishka[ProfileRatingRepository]
):
    await service.fimoz()
    await rating_repo.add_ref(user_id)

    return

@router.get("/stats/{user_id}", tags=["stats"])
async def get_stat(
        user_id: int,
        rating_repo: FromDishka[ProfileRatingRepository]
):
    stats = await rating_repo.get_stats_by_profile_id(user_id)
    return stats