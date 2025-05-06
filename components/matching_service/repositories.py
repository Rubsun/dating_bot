from geoalchemy2 import WKTElement
from geoalchemy2.functions import ST_Distance, ST_DWithin
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, func, case, delete
from datetime import datetime

from components.matching_service.models import Like, Match, UserInfo


class LikeMatchRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_like_by_users_id(self, liker_id: int, liked_id: int) -> Like:
        result = await self.db.execute(
            select(Like)
            .where(
                and_(
                    Like.liker_telegram_id == liker_id,
                    Like.liked_telegram_id == liked_id
                )
            )
        )
        return result.scalars().first()

    async def create_like(
            self,
            rater_user_id: int,
            rated_user_id: int,
            like_type: str = 'like'
    ) -> Like:

        new_like = Like(
            liker_telegram_id=rater_user_id,
            liked_telegram_id=rated_user_id,
            like_type=like_type,
            created_at=datetime.now()
        )

        self.db.add(new_like)
        await self.db.commit()
        await self.db.refresh(new_like)
        print(f"Пользователь {rater_user_id} лайкнул пользователя {rated_user_id}.")
        return new_like

    async def get_match_by_users_id(self, user1_id: int, user2_id) -> Match:
        user1_id = min(user1_id, user2_id)
        user2_id = max(user2_id, user1_id)
        result = await self.db.execute(
            select(Match)
            .where(
                and_(Match.user1_telegram_id == user1_id,
                     Match.user2_telegram_id == user2_id
                     )
            )
        )
        return result.scalars().first()

    async def is_match(
            self,
            rater_user_id: int,
            rated_user_id: int,
            rater_username: str,
            rated_username: str,
    ) -> bool:
        mutual_like_result = await self.db.execute(
            select(Like).where(
                Like.liker_telegram_id == rated_user_id,
                Like.liked_telegram_id == rater_user_id
            )
        )
        mutual_like = mutual_like_result.scalars().first()
        print(mutual_like)

        if mutual_like:
            print(f"Взаимный лайк обнаружен между {rater_user_id} и {rated_user_id}!")

            user_id_to_username = {
                rater_user_id: rater_username,
                rated_user_id: rated_username,
            }

            user1 = min(rater_user_id, rated_user_id)
            user2 = max(rater_user_id, rated_user_id)

            existing_match_result = await self.db.execute(
                select(Match).where(
                    Match.user1_telegram_id == user1,
                    Match.user2_telegram_id == user2
                )
            )
            existing_match = existing_match_result.scalars().first()

            if not existing_match:
                new_match = Match(
                    user1_telegram_id=user1,
                    user2_telegram_id=user2,
                    user1_username=user_id_to_username[user1],
                    user2_username=user_id_to_username[user2],
                    matched_at=datetime.now()
                )
                self.db.add(new_match)
                await self.db.commit()
                await self.db.refresh(new_match)

                print(f"Создана запись о совпадении между {user1} и {user2}.")
                return True
            else:
                print(f"Запись о совпадении между {user1} и {user2} уже существует.")
                return False
        else:
            print(f"Взаимный лайк от пользователя {rated_user_id} не найден.")
            return False

    async def get_info_by_user_id(self, user_id: int) -> UserInfo:
        result = await self.db.execute(
            select(UserInfo)
            .where(UserInfo.user_id == user_id)
        )
        return result.scalars().first()

    async def create_info(
            self,
            user_id: int,
            age: int,
            gender: str,
            rating: float,
            preferred_gender: str,
            preferred_min_age: int,
            preferred_max_age: int,
            latitude: float,
            longitude: float
    ) -> UserInfo:

        info = UserInfo(
            user_id=user_id,
            age=age,
            gender=gender,
            rating=rating,
            preferred_gender=preferred_gender,
            preferred_min_age=preferred_min_age,
            preferred_max_age=preferred_max_age,
            location=f"POINT({longitude} {latitude})"
        )

        self.db.add(info)
        await self.db.commit()
        print(f"Создалися preference для {user_id}")
        await self.db.refresh(info)

        return info

    async def update_info(
            self,
            user_id: int,
            age: int | None = None,
            gender: str | None = None,
            rating: float | None = None,
            preferred_gender: str | None = None,
            preferred_min_age: int | None = None,
            preferred_max_age: int | None = None,
            latitude: float | None = None,
            longitude: float | None = None,
    ) -> UserInfo:

        stmt = select(UserInfo).where(UserInfo.user_id == user_id)
        result = await self.db.execute(stmt)
        info = result.scalar_one_or_none()

        info.age = age if age else info.age
        info.gender = gender if gender else info.gender
        info.rating = rating if rating else info.rating
        info.preferred_gender = preferred_gender if preferred_gender else info.preferred_gender
        info.preferred_min_age = preferred_min_age if preferred_min_age else info.preferred_min_age
        info.preferred_max_age = preferred_max_age if preferred_max_age else info.preferred_max_age
        info.location = f"POINT({longitude} {latitude})" if longitude and latitude else info.location

        await self.db.commit()
        await self.db.refresh(info)

        return info

    # async def get_profiles(self, viewer_id: int, offset: int = 0, limit: int = 50) -> Optional[Profile]:
    #     result = await self.db.execute(
    #         select(Profile).where(Profile.id != viewer_id).offset(offset).limit(limit)
    #     )
    #     return result.scalars().first()
    #
    #
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

    async def get_user_match(self, user_id: int) -> list[dict]:
        matches = await self.db.execute(
            select(Match).where(
                or_(
                    Match.user1_telegram_id == user_id,
                    Match.user2_telegram_id == user_id
                )
            )
        )
        matches = matches.scalars().all()

        result = []
        for match in matches:
            if match.user1_telegram_id == user_id:
                partner_data = {
                    "username": match.user2_username,
                    "user_id": match.user2_telegram_id,
                    "matched_at": match.matched_at
                }
            else:
                partner_data = {
                    "username": match.user1_username,
                    "user_id": match.user1_telegram_id,
                    "matched_at": match.matched_at
                }
            result.append(partner_data)

        return result

    async def find_matching_users(
            self,
            user_id: int,
            offset: int = 0,
            limit: int = 50
    ) -> list[int]:
        initial_radius_km = 20
        max_radius_km = 100
        radius_step_km = 20
        min_profiles = 50

        user_query = select(
            UserInfo.preferred_gender,
            UserInfo.preferred_min_age,
            UserInfo.preferred_max_age,
            func.ST_X(UserInfo.location).label('longitude'),
            func.ST_Y(UserInfo.location).label('latitude')
        ).where(UserInfo.user_id == user_id)

        user = (await self.db.execute(user_query)).first()

        if not user or user.longitude is None or user.latitude is None:
            return []

        user_point = WKTElement(f'SRID=4326;POINT({user.longitude} {user.latitude})', extended=True)

        matched_query = select(
            case(
                (Match.user1_telegram_id == user_id, Match.user2_telegram_id),
                else_=Match.user1_telegram_id
            )
        ).where(
            or_(
                Match.user1_telegram_id == user_id,
                Match.user2_telegram_id == user_id
            )
        )

        matched_users_list = (await self.db.execute(matched_query)).all()
        matched_users = {row[0] for row in matched_users_list}

        matched_users.add(user_id)

        found_users = []
        current_radius = initial_radius_km

        while current_radius <= max_radius_km:
            query = (
                select(
                    UserInfo.user_id,
                    ST_Distance(
                        UserInfo.location,
                        user_point,
                        use_spheroid=True
                    ).label('distance'),
                    UserInfo.rating
                )
                .where(
                    and_(
                        UserInfo.user_id != user_id,
                        UserInfo.user_id.not_in(matched_users),
                        ST_DWithin(
                            UserInfo.location,
                            user_point,
                            current_radius * 0.01,
                            use_spheroid=True
                        ),
                        or_(
                            UserInfo.gender == user.preferred_gender,
                            user.preferred_gender == "any"
                        ),
                        UserInfo.age.between(
                            user.preferred_min_age,
                            user.preferred_max_age
                        )
                    )
                )
                .order_by('distance', UserInfo.rating)
                .limit(min_profiles * 2)
            )

            result = await self.db.execute(query)
            batch = result.all()

            new_users = [
                (row.user_id, row.distance, row.rating)
                for row in batch
                if row.user_id not in {u[0] for u in found_users}
            ]

            found_users.extend(new_users)
            current_radius += radius_step_km

        sorted_users = sorted(
            found_users,
            key=lambda x: (x[1], -x[2])
        )

        return [u[0] for u in sorted_users][offset:offset + limit]

    async def update_rating(self, user_id, new_rating):
        stmt = select(UserInfo).where(UserInfo.user_id == user_id)
        result = await self.db.execute(stmt)
        info = result.scalar_one_or_none()

        info.rating = new_rating if new_rating else info.rating

        await self.db.commit()
        await self.db.refresh(info)

        return info

    async def get_stats(self, user_id):
        likes_given_query = select(func.count()).where(
            Like.liker_telegram_id == user_id,
            Like.like_type == 'like'
        )
        likes_given = await self.db.scalar(likes_given_query)

        likes_received_query = select(func.count()).where(
            Like.liked_telegram_id == user_id,
            Like.like_type == 'like'
        )
        likes_received = await self.db.scalar(likes_received_query)

        dislikes_given_query = select(func.count()).where(
            Like.liker_telegram_id == user_id,
            Like.like_type == 'dislike'
        )
        dislikes_given = await self.db.scalar(dislikes_given_query)

        dislikes_received_query = select(func.count()).where(
            Like.liked_telegram_id == user_id,
            Like.like_type == 'dislike'
        )
        dislikes_received = await self.db.scalar(dislikes_received_query)

        matches_query = select(func.count()).where(
            or_(
                Match.user1_telegram_id == user_id,
                Match.user2_telegram_id == user_id
            )
        )
        matches_count = await self.db.scalar(matches_query)

        return {
            "likes_given": likes_given or 0,
            "dislikes_given": dislikes_given or 0,
            "likes_received": likes_received or 0,
            "dislikes_received": dislikes_received or 0,
            "matches_count": matches_count or 0
        }

    async def check_dislike(self, user_id):
        query = (
            select(Like)
            .where(
                or_(
                    and_(
                        Like.liker_telegram_id == user_id,
                        Like.like_type == 'dislike'
                    ),
                    and_(
                        Like.liked_telegram_id == user_id,
                        Like.like_type == 'dislike'
                    )
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def delete_like(self, user_id):
        async with self.db.begin() as conn:
            stmt = delete(Like).where(Like.liker_telegram_id == user_id)

            result = await conn.execute(stmt)

            return result.rowcount