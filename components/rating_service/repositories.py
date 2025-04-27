from datetime import datetime

from loguru import logger
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from components.rating_service.models import ProfileRating


class ProfileRatingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_rating(
            self,
            profile_telegram_id: int,
            rating_score: float
    ) -> ProfileRating:

        logger.info(
            f"Attempting to create rating entry for telegram_id: {profile_telegram_id} with score: {rating_score}")
        new_rating = ProfileRating(
            profile_telegram_id=profile_telegram_id,
            rating_score=rating_score,
            last_calculated_at=datetime.now()
        )
        logger.debug(f"Created ProfileRating object: {new_rating.__dict__}")

        self.db.add(new_rating)
        await self.db.commit()
        await self.db.refresh(new_rating)
        logger.info(f"Successfully created and committed rating entry for telegram_id: {profile_telegram_id}")

        return new_rating

    async def get_rating_by_profile_id(self, profile_id: int) -> ProfileRating:
        logger.info(f"Attempting to retrieve rating for profile_id: {profile_id}")
        result = await self.db.execute(
            select(ProfileRating)
            .where(ProfileRating.profile_telegram_id == profile_id)
        )
        rating = result.scalars().first()
        if rating:
            logger.info(f"Rating found for profile_id: {profile_id}. Score: {rating.rating_score}")
            logger.debug(f"Found rating details: {rating.__dict__}")
        else:
            logger.info(f"Rating not found for profile_id: {profile_id}")

        return rating

    async def update_rating(
            self,
            profile_id: int,
            new_rating: float
    ) -> ProfileRating:

        logger.info(f"Attempting to update rating for profile_id: {profile_id} to new score: {new_rating}")
        rating = await self.get_rating_by_profile_id(profile_id)

        if not rating:
            logger.warning(
                f"Rating not found for profile_id: {profile_id} during update attempt. Creating new rating instead.")
            return await self.create_rating(profile_id, new_rating)

        logger.debug(
            f"Found existing rating for profile_id {profile_id}. Current score: {rating.rating_score}. Proceeding with update.")
        rating.rating_score = new_rating
        rating.last_calculated_at = datetime.now()

        await self.db.commit()
        await self.db.refresh(rating)
        logger.info(f"Successfully updated and committed rating for profile_id: {profile_id}")
        return rating

    async def delete_rating(self, profile_id: int) -> bool:
        logger.info(f"Attempting to delete rating for profile_id: {profile_id}")
        result = await self.db.execute(
            delete(ProfileRating)
            .where(ProfileRating.profile_telegram_id == profile_id)
        )

        await self.db.commit()
        return result.rowcount > 0

    async def get_top_ratings(self, limit: int = 10) -> list[ProfileRating]:
        logger.info(f"Attempting to retrieve top {limit} ratings.")
        result = await self.db.execute(
            select(ProfileRating)
            .order_by(ProfileRating.rating_score.desc())
            .limit(limit)
        )

        ratings = result.scalars().all()
        logger.info(f"Successfully retrieved {len(ratings)} top ratings (limit was {limit}).")
        logger.debug(f"Top ratings retrieved: {[(r.profile_telegram_id, r.rating_score) for r in ratings]}")

        return ratings
