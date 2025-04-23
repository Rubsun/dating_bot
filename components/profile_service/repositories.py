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
            bio: str,
            age: int,
            gender: str,
            city: str,
            photo_path: str
    ) -> Profile:
        # Create a new Profile object
        new_profile = Profile(
            id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            bio=bio,
            age=age,
            gender=gender,
            city=city,
            photo_path=photo_path,
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
