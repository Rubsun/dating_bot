import httpx
import msgpack
from aio_pika import ExchangeType
from fastapi import APIRouter, HTTPException

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from geoalchemy2.shape import to_shape

from components.matching_service.config import Config
from components.matching_service.repositories import LikeMatchRepository
from components.matching_service.schemas import LikeDislikePayload, UserMatch, UserInfo, UserInfoResponse


import aio_pika

router = APIRouter(route_class=DishkaRoute)


@router.post("/match/check", tags=["matching"])
async def create_like(
        payload: LikeDislikePayload,
        matching_repo: FromDishka[LikeMatchRepository],
        cfg: FromDishka[Config],
):

    check_like = await matching_repo.get_like_by_users_id(payload.rater_user_id, payload.rated_user_id)
    if check_like:
        raise HTTPException(status_code=404, detail="Like has already created")

    await matching_repo.create_like(
        rated_user_id=payload.rated_user_id,
        rater_user_id=payload.rater_user_id,
        like_type=payload.like_type,
   )

    if payload.like_type == "like":
        check_match = await matching_repo.get_match_by_users_id(payload.rater_user_id, payload.rated_user_id)
        if check_match:
            raise HTTPException(status_code=404, detail="Match has already created")

        is_match = await matching_repo.is_match(payload.rater_user_id, payload.rated_user_id, payload.rater_username, payload.rated_username)
        if is_match:
            match = await matching_repo.get_match(payload.rater_user_id, payload.rated_user_id)
            print('-----------------------', match)

            connection = await aio_pika.connect_robust(cfg.rabbitmq.uri)
            async with connection:
                routing_key = "matches"
                channel = await connection.channel()
                exchange = await channel.declare_exchange('matches', ExchangeType.DIRECT)
                queue = await channel.declare_queue('matches')
                await queue.bind(exchange, routing_key)

                await exchange.publish(
                    aio_pika.Message(
                        msgpack.packb(
                            UserMatch(
                                user1_id=match.user1_telegram_id,
                                user2_id=match.user2_telegram_id,
                                user1_username=match.user1_username,
                                user2_username=match.user2_username,
                                # match_data=match.matched_at
                            )
                        )
                    ),
                    routing_key=routing_key
                )
            return {"match":
                        {"matcher1": match.user1_telegram_id,
                        "matcher2": match.user2_telegram_id}
                    }
        return {"status": "half-match"}
    return {"status": "no-match"}


@router.post("/users/info", tags=["users"])
async def create_preferences(
    info: UserInfo,
    matching_repo: FromDishka[LikeMatchRepository]
) -> UserInfoResponse:

    created = await matching_repo.get_info_by_user_id(info.user_id)
    if created:
        raise HTTPException(status_code=404, detail="Info has already created")
    new_info = await matching_repo.create_info(**info.model_dump())

    point = to_shape(new_info.location)
    return UserInfoResponse(
        user_id=new_info.user_id,
        age=new_info.age,
        gender=new_info.gender,
        rating=new_info.rating,
        preferred_gender=new_info.preferred_gender,
        preferred_min_age=new_info.preferred_min_age,
        preferred_max_age=new_info.preferred_max_age,
        longitude=point.x,
        latitude=point.y
    )

@router.put("/users/info", tags=["users"])
async def update_preferences(
        info: UserInfo,
        matching_repo: FromDishka[LikeMatchRepository],
) -> UserInfoResponse:

    updated = await matching_repo.get_info_by_user_id(info.user_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Info not found")

    new_info = await matching_repo.update_info(**info.model_dump())

    point = to_shape(new_info.location)
    return UserInfoResponse(
        user_id=new_info.user_id,
        age=new_info.age,
        gender=new_info.gender,
        rating=new_info.rating,
        preferred_gender=new_info.preferred_gender,
        preferred_min_age=new_info.preferred_min_age,
        preferred_max_age=new_info.preferred_max_age,
        longitude=point.x,
        latitude=point.y
    )


@router.get("/match/profiles/{viewer_id}", tags=["matching"])
async def get_next_profile_to_view(
        viewer_id: int,
        matching_repo: FromDishka[LikeMatchRepository],
        cfg: FromDishka[Config],
        offset: int = 0,
        limit: int = 50
):

    profile = await matching_repo.find_matching_users(user_id=viewer_id, offset=offset, limit=limit)

    params = {
        "profile_ids": profile
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{cfg.profile_service_url}/many-profiles", params=params)
        if response.status_code == 200:
            print('Zdravo')
        elif response.status_code == 404:
            print('Fimoz')

    if not profile:
        raise HTTPException(status_code=404, detail="No more profiles to view")

    return profile

    # return {
    #     "user_id": profile.id,
    #     "first_name": profile.first_name,
    #     "last_name": profile.last_name,
    #     "tg_username": profile.tg_username,
    #     "bio": profile.bio,
    #     "age": profile.age,
    #     "gender": profile.gender,
    #     "city": profile.city,
    #     "photo_path": profile.photo_path,
    #     "photo_file_id": profile.photo_file_id
    # }


