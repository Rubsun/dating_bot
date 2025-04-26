import msgpack
from aio_pika import ExchangeType
from fastapi import APIRouter

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute

from components.matching_service.config import Config
from components.matching_service.repositories import LikeMatchRepository
from components.matching_service.schemas import LikeDislikePayload, UserMatch

import aio_pika

router = APIRouter(route_class=DishkaRoute)


@router.post("/match/check")
async def create_like(
        payload: LikeDislikePayload,
        matching_repo: FromDishka[LikeMatchRepository],
        cfg: FromDishka[Config],
):
    await matching_repo.create_like(
        rated_user_id=payload.rated_user_id,
        rater_user_id=payload.rater_user_id,
        like_type=payload.like_type,
   )

    is_match = await matching_repo.create_match(payload.rater_user_id, payload.rated_user_id, payload.rater_username, payload.rated_username)
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
            # Bind the queue to the default exchange
        return {"status": "ok"}
    else:
        return {"status": "error"}


@router.get("/profiles/next/{viewer_id}")
async def get_next_profile_to_view(
        viewer_id: int,
        matching_repo: FromDishka[LikeMatchRepository],
        offset: int = 0,
):
    profile = await matching_repo.get_next(viewer_id=viewer_id, offset=offset)

    if not profile:
        raise HTTPException(status_code=404, detail="No more profiles to view")

    return {
        "user_id": profile.id,
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "tg_username": profile.tg_username,
        "bio": profile.bio,
        "age": profile.age,
        "gender": profile.gender,
        "city": profile.city,
        "photo_path": profile.photo_path,
        "photo_file_id": profile.photo_file_id
    }


