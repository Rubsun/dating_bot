from datetime import datetime

from loguru import logger
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from datetime import datetime
from components.rating_service.models import ProfileRating, ProfileStats
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

    async def get_stats_by_profile_id(self, profile_id: int) -> ProfileStats:
        result = await self.db.execute(
            select(ProfileStats)
            .where(ProfileStats.profile_telegram_id == profile_id)
        )

        return result.scalars().first()

    async def create_stats(
            self,
            profile_telegram_id,
            likes_given,
            dislikes_given,
            likes_received,
            dislikes_received,
            matches_count
    ) -> ProfileStats:
        new_stats = ProfileStats(
            profile_telegram_id=profile_telegram_id,
            likes_given=likes_given,
            dislikes_given=dislikes_given,
            likes_received=likes_received,
            dislikes_received=dislikes_received,
            matches_count=matches_count
        )

        self.db.add(new_stats)
        await self.db.commit()
        await self.db.refresh(new_stats)
        return new_stats

    async def update_stats(
            self,
            profile_telegram_id,
            likes_given,
            dislikes_given,
            likes_received,
            dislikes_received,
            matches_count
    ) -> ProfileStats:

        stats = await self.get_stats_by_profile_id(profile_telegram_id)
        if stats:
            stats.likes_given = likes_given
            stats.dislikes_given = dislikes_given
            stats.likes_received = likes_received
            stats.dislikes_received = dislikes_received
            stats.matches_count = matches_count

            await self.db.commit()
            await self.db.refresh(stats)
            return stats

    async def add_chat(self, user_id):
        stats = await self.get_stats_by_profile_id(user_id)
        stats.chats_count = stats.chats_count + 1 if stats.chats_count else 1

        await self.db.commit()
        await self.db.refresh(stats)

        print('Zdravo')

        return

    async def add_ref(self, user_id):
        stats = await self.get_stats_by_profile_id(user_id)
        if not stats:
            stats = ProfileStats(refs_count=0)
            self.db.add(stats)

        stats.refs_count = stats.refs_count + 1 if stats.refs_count else 1

        await self.db.commit()
        await self.db.refresh(stats)

        print('Zdravo')
        return