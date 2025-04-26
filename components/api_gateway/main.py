import asyncio
import logging
from redis.asyncio import Redis

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.redis import RedisStorage
from dishka.integrations.aiogram import (
    setup_dishka,
)

from components.api_gateway.config import Config
from components.api_gateway.controllers.bot.handlers import router as handler_router
from components.api_gateway.controllers.bot.middlewares import CheckUsernameMiddleware
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
        ]
    )

    dp = Dispatcher(storage=RedisStorage(Redis.from_url(cfg.redis.uri)))
    setup_dishka(container=container, router=dp, auto_inject=True)
    dp.message.middleware(CheckUsernameMiddleware())
    dp.include_router(handler_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.info("Запуск бота...")
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_polling())

