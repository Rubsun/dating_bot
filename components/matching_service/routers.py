import msgpack
from aio_pika import ExchangeType
from fastapi import HTTPException, APIRouter

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute

from components.matching_service.config import Config
from components.matching_service.repositories import LikeMatchRepository
from components.matching_service.schemas import LikeDislikePayload, UserMatch

import aio_pika

router = APIRouter(route_class=DishkaRoute)


@router.post("/match/like")
async def create_like(
        payload: LikeDislikePayload,
        matching_repo: FromDishka[LikeMatchRepository],
        cfg: FromDishka[Config],
):
    await matching_repo.create_like(**payload.model_dump())

    is_match = await matching_repo.create_match(payload.rater_user_id, payload.rated_user_id)
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
