from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from components.profile_service.models import Profile


class ProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_profile(
            self,
            telegram_id: int,
            first_name: str,
            last_name: str,
            tg_username: str,
            bio: str,
            age: int,
            gender: str,
            city: str,
            photo_path: str,
            photo_file_id: str
    ) -> Profile:
        # Create a new Profile object
        new_profile = Profile(
            id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            tg_username=tg_username,
            bio=bio,
            age=age,
            gender=gender,
            city=city,
            photo_path=photo_path,
            photo_file_id=photo_file_id,
        )
        self.db.add(new_profile)
        await self.db.commit()
        await self.db.refresh(new_profile)  # Refresh to get the updated instance
        return new_profile

    async def get_profile_by_id(self, profile_id: int) -> Profile:
        """Fetch a Profile by its ID."""
        result = await self.db.execute(select(Profile).where(Profile.id == profile_id))
        return result.scalars().first()

    async def delete_profile_by_id(self, profile_id: int) -> bool:
        """Delete a Profile by its ID."""
        result = await self.db.execute(select(Profile).where(Profile.id == profile_id))
        profile = result.scalars().first()

        # If profile does not exist, return False
        if not profile:
            return False

        await self.db.delete(profile)
        await self.db.commit()
        return True

    async def get_next_profile(self, viewer_id: int, offset: int = 0) -> Optional[Profile]:
        """
        Возвращает первую попавшуюся анкету, не совпадающую с viewer_id.
        TODO: Добавить фильтрацию уже просмотренных анкет.
        """
        result = await self.db.execute(
            select(Profile).where(Profile.id != viewer_id).offset(offset).limit(1)
        )
        return result.scalars().first()
