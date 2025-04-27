import asyncio
import json
import logging
from datetime import datetime
from functools import partial
from typing import Any

from redis.asyncio import Redis

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.redis import RedisStorage
from dishka.integrations.aiogram import (
    setup_dishka,
)

from components.api_gateway.config import Config
from components.api_gateway.controllers.bot.handlers import router as handler_router
from components.api_gateway.controllers.bot.middlewares import CheckUsernameMiddleware, RateLimitMiddleware, \
    MediaGroupMiddleware
from components.api_gateway.di import setup_di

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
)

async def start_polling():
    container = setup_di()
    cfg = await container.get(Config)

    bot = Bot(token=cfg.bot.bot_token)
    await bot.delete_webhook()

    await bot.set_my_commands(
        commands=[
            types.BotCommand(command='start', description='Начать работу с ботом'),
            types.BotCommand(command='view', description='Смотреть анкеты'),
            types.BotCommand(command='profile', description='Мой профиль'),
            types.BotCommand(command='referral', description='Реферальная система'),
        ]
    )

    redis = await container.get(Redis)
    dp = Dispatcher(storage=RedisStorage(redis, json_dumps=partial(json.dumps, cls=DTOJSONEncoder)))
    setup_dishka(container=container, router=dp, auto_inject=True)
    dp.message.middleware(CheckUsernameMiddleware())

    rate_limit_middleware = RateLimitMiddleware(ioc_container=container)
    dp.callback_query.outer_middleware(rate_limit_middleware)
    dp.message.outer_middleware(rate_limit_middleware)
    dp.message.middleware(MediaGroupMiddleware())

    dp.include_router(handler_router)

    await dp.start_polling(bot)


class DTOJSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


if __name__ == "__main__":
    logging.info("Запуск бота...")
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_polling())

