from typing import Optional

from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from components.profile_service.models import Profile


class ProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        logger.debug(f"ProfileRepository initialized with db session: {db}")

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
            photo_file_ids: list[str]
    ) -> Profile:
        logger.info(f"Attempting to create profile for telegram_id: {telegram_id}")
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
            photo_file_ids=photo_file_ids,
        )
        try:
            self.db.add(new_profile)
            await self.db.commit()
            await self.db.refresh(new_profile)
            logger.info(f"Profile created successfully for telegram_id: {telegram_id}. Profile ID: {new_profile.id}")
            return new_profile
        except SQLAlchemyError as e:
            logger.exception(
                f"Database error during profile creation for telegram_id: {telegram_id}. Rolling back transaction. Error: {e}")
            await self.db.rollback()
            raise
        except Exception as e:
            logger.exception(f"Unexpected error during profile creation for telegram_id: {telegram_id}. Error: {e}")
            await self.db.rollback()
            raise

    async def get_profile_by_id(self, profile_id: int) -> Profile:
        """Fetch a Profile by its ID."""
        logger.info(f"Attempting to fetch profile by ID: {profile_id}")
        try:
            result = await self.db.execute(select(Profile).where(Profile.id == profile_id))
            profile = result.scalars().first()
            if profile:
                logger.info(f"Profile found for ID: {profile_id}")
                logger.debug(f"Profile data for ID {profile_id}: {profile.__dict__}")
            else:
                logger.warning(f"Profile not found for ID: {profile_id}")
            return profile
        except SQLAlchemyError as e:
            logger.exception(f"Database error while fetching profile ID: {profile_id}. Error: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error while fetching profile ID: {profile_id}. Error: {e}")
            raise

    async def get_profiles_by_ids(self, ids: list[int]):
        logger.info(f"Attempting to fetch profiles by IDs: {ids}")
        if not ids:
            logger.warning("get_profiles_by_ids called with empty list.")
            return []
        try:
            stmt = select(Profile).where(Profile.id.in_(ids))
            result = await self.db.execute(stmt)
            profiles = result.scalars().all()
            logger.info(f"Fetched {len(profiles)} profiles for {len(ids)} requested IDs.")
            logger.debug(f"Fetched profile IDs: {[p.id for p in profiles]}")
            return profiles
        except SQLAlchemyError as e:
            logger.exception(f"Database error while fetching profiles by IDs: {ids}. Error: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error while fetching profiles by IDs: {ids}. Error: {e}")
            raise

    async def delete_profile_by_id(self, profile_id: int) -> bool:
        """Delete a Profile by its ID."""
        logger.info(f"Attempting to delete profile by ID: {profile_id}")
        try:
            # Сначала получаем профиль, чтобы убедиться, что он существует
            result = await self.db.execute(select(Profile).where(Profile.id == profile_id))
            profile = result.scalars().first()

            if not profile:
                logger.warning(f"Profile not found for deletion with ID: {profile_id}")
                return False

            logger.info(f"Found profile ID {profile_id} for deletion. Proceeding.")
            await self.db.delete(profile)
            await self.db.commit()
            logger.info(f"Profile with ID {profile_id} deleted successfully.")
            return True
        except SQLAlchemyError as e:
            logger.exception(
                f"Database error during profile deletion for ID: {profile_id}. Rolling back transaction. Error: {e}")
            await self.db.rollback()
            raise
        except Exception as e:
            logger.exception(f"Unexpected error during profile deletion for ID: {profile_id}. Error: {e}")
            await self.db.rollback()
            raise
