from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from datetime import datetime

from components.matching_service.models import Like, Match


class LikeMatchRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_like(
        self,
        rater_user_id: int,
        rated_user_id: int,
        like_type: str = 'like'
    ) -> Like:
        new_like = Like(
            liker_telegram_id=rater_user_id,
            liked_telegram_id =rated_user_id,
            like_type=like_type,
            created_at=datetime.now()
        )
        self.db.add(new_like)
        await self.db.commit()
        await self.db.refresh(new_like)
        print(f"Пользователь {rater_user_id} лайкнул пользователя {rated_user_id}.")
        return new_like

    async def create_match(
            self,
            rater_user_id: int,
            rated_user_id: int,
            rater_username: str,
            rated_username: str,
    ) -> bool:
        mutual_like_result = await self.db.execute(
            select(Like).where(
                Like.liker_telegram_id == rated_user_id, # Ищем лайк от того, кого лайкнули
                Like.liked_telegram_id == rater_user_id   # На того, кто лайкнул сейчас
            )
        )
        mutual_like = mutual_like_result.scalars().first()
        print(mutual_like)

        if mutual_like:
            print(f"Взаимный лайк обнаружен между {rater_user_id} и {rated_user_id}!")

            # Определяем порядок ID для записи в таблицу matches
            user_id_to_username = {
                rater_user_id: rater_username,
                rated_user_id: rated_username,
            }

            user1 = min(rater_user_id, rated_user_id)
            user2 = max(rater_user_id, rated_user_id)

            # Проверяем, не существует ли уже запись о совпадении для этой пары
            # Используем асинхронный запрос
            existing_match_result = await self.db.execute(
                select(Match).where(
                    Match.user1_telegram_id == user1,
                    Match.user2_telegram_id == user2
                )
            )
            existing_match = existing_match_result.scalars().first()


            if not existing_match:
                # Создаем новую запись о совпадении
                new_match = Match(
                    user1_telegram_id=user1,
                    user2_telegram_id=user2,
                    user1_username=user_id_to_username[user1],
                    user2_username=user_id_to_username[user2],
                    matched_at=datetime.now()# Устанавливаем время совпадения
                )
                self.db.add(new_match)
                await self.db.commit() # Асинхронный коммит
                await self.db.refresh(new_match) # Refresh может не понадобиться

                print(f"Создана запись о совпадении между {user1} и {user2}.")
                return True # Произошло совпадение
            else:
                 print(f"Запись о совпадении между {user1} и {user2} уже существует.")
                 return False # Совпадение уже было зарегистрировано
        else:
            print(f"Взаимный лайк от пользователя {rated_user_id} не найден.")
            return False # Совпадения не произошло

    async def get_match(self, user1_id: int, user2_id: int) -> Match:
        user1 = min(user1_id, user2_id)
        user2 = max(user1_id, user2_id)

        match_result = await self.db.execute(
            select(Match).where(
                Match.user1_telegram_id == user1,
                Match.user2_telegram_id == user2
            )
        )
        return match_result.scalars().first()