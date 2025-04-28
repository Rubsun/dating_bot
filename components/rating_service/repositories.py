from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from datetime import datetime
from components.rating_service.models import ProfileRating, ProfileStats


class ProfileRatingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_rating(
            self,
            profile_telegram_id: int,
            rating_score: float
    ) -> ProfileRating:

        new_rating = ProfileRating(
            profile_telegram_id=profile_telegram_id,
            rating_score=rating_score,
            last_calculated_at=datetime.now()
        )

        self.db.add(new_rating)
        await self.db.commit()
        await self.db.refresh(new_rating)
        return new_rating

    async def get_rating_by_profile_id(self, profile_id: int) -> ProfileRating:
        result = await self.db.execute(
            select(ProfileRating)
            .where(ProfileRating.profile_telegram_id == profile_id)
        )

        return result.scalars().first()

    async def update_rating(
            self,
            profile_id: int,
            new_rating: float
    ) -> ProfileRating:

        rating = await self.get_rating_by_profile_id(profile_id)

        if not rating:
            return await self.create_rating(profile_id, new_rating)

        rating.rating_score = new_rating
        rating.last_calculated_at = datetime.now()

        await self.db.commit()
        await self.db.refresh(rating)
        return rating

    async def delete_rating(self, profile_id: int) -> bool:
        result = await self.db.execute(
            delete(ProfileRating)
            .where(ProfileRating.profile_telegram_id == profile_id)
        )

        await self.db.commit()
        return result.rowcount > 0

    async def get_top_ratings(self, limit: int = 10) -> list[ProfileRating]:
        result = await self.db.execute(
            select(ProfileRating)
            .order_by(ProfileRating.rating_score.desc())
            .limit(limit)
        )

        ratings = result.scalars().all()

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
        stats.refs_count = stats.refs_count + 1 if stats.refs_count else 1

        await self.db.commit()
        await self.db.refresh(stats)

        print('Zdravo')

        return