import aio_pika
import httpx
import msgpack
from aio_pika import ExchangeType
from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, HTTPException
from geoalchemy2.shape import to_shape
from loguru import logger

from components.matching_service.config import Config
from components.matching_service.repositories import LikeMatchRepository
from components.matching_service.schemas import LikeDislikePayload, UserMatch, UserInfoCreate, UserInfoUpdate, \
    UserInfoResponse, UserLike

router = APIRouter(route_class=DishkaRoute)


@router.post("/match/check", tags=["matching"])
async def create_like(
        payload: LikeDislikePayload,
        matching_repo: FromDishka[LikeMatchRepository],
        cfg: FromDishka[Config],
):
    logger.info(
        f"Received /match/check request: rater={payload.rater_user_id}, rated={payload.rated_user_id}, type={payload.like_type}")

    check_like = await matching_repo.get_like_by_users_id(payload.rater_user_id, payload.rated_user_id)
    if check_like:
        raise HTTPException(status_code=404, detail="Like has already created")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=f"{cfg.rating_service_url}/ratings/{payload.rated_user_id}"
        )

        rating = response.json()
        await matching_repo.update_rating(rating['profile_telegram_id'], rating['rating_score'])

    like = await matching_repo.create_like(
        rated_user_id=payload.rated_user_id,
        rater_user_id=payload.rater_user_id,
        like_type=payload.like_type,
    )

    if payload.like_type == "like":
        logger.info(f"Processing 'like' from {payload.rater_user_id} to {payload.rated_user_id}")

        connection = await aio_pika.connect_robust(cfg.rabbitmq.uri)
        async with connection:
            routing_key = "likes"
            channel = await connection.channel()
            exchange = await channel.declare_exchange('likes', ExchangeType.DIRECT)
            queue = await channel.declare_queue('likes')
            await queue.bind(exchange, routing_key)

            await exchange.publish(
                aio_pika.Message(
                    msgpack.packb(
                        UserLike(
                            liker_id=like.liker_telegram_id,
                            liked_id=like.liked_telegram_id,
                            like_date=str(like.created_at)
                        )
                    )
                ),
                routing_key=routing_key
            )

        check_match = await matching_repo.get_match_by_users_id(payload.rater_user_id, payload.rated_user_id)
        if check_match:
            logger.warning(
                f"Match already exists between {payload.rater_user_id} and {payload.rated_user_id}. Like processed, but no new match created.")

            raise HTTPException(status_code=404, detail="Match has already created")

        logger.debug(f"Checking if a new match is formed between {payload.rater_user_id} and {payload.rated_user_id}")
        is_match = await matching_repo.is_match(payload.rater_user_id, payload.rated_user_id, payload.rater_username,
                                                payload.rated_username)
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
                            )
                        )
                    ),
                    routing_key=routing_key
                )
            return {
                "match":
                    {
                        "matcher1": match.user1_telegram_id,
                        "matcher2": match.user2_telegram_id
                    }
            }
        return {"status": "half-match"}
    return {"status": "no-match"}


@router.post("/users/info", tags=["users"])
async def create_preferences(
        info: UserInfoCreate,
        matching_repo: FromDishka[LikeMatchRepository]
) -> UserInfoResponse:
    logger.info(f"Received POST /users/info request for user_id: {info.user_id}")
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


@router.put("/users/info/{user_id}", tags=["users"])
async def update_preferences(
        user_id: int,
        info: UserInfoUpdate,
        matching_repo: FromDishka[LikeMatchRepository],
) -> UserInfoResponse:
    logger.info(f"Received PUT /users/info/{user_id} request.")
    logger.debug(f"Update data for user_id {user_id}: {info.model_dump(exclude_unset=True)}")

    updated = await matching_repo.get_info_by_user_id(user_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Info not found")

    new_info = await matching_repo.update_info(user_id=user_id, **info.model_dump())

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
    logger.info(f"Received GET /match/profiles/{viewer_id} request with offset={offset}, limit={limit}")
    profile_ids = await matching_repo.find_matching_users(user_id=viewer_id, offset=offset, limit=limit)
    if not profile_ids:
        raise HTTPException(status_code=404, detail="No more profiles to view")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            url=f"{cfg.profile_service_url}/many-profiles", json=profile_ids
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f'Fimoz: {response.json()}')

    profiles = response.json()
    return profiles
