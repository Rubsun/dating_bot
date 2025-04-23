import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from components.api_gateway.controllers.bot.handlers import router as handler_router

BOT_TOKEN = "7595911850:AAHs-6bjlqCrO_eqLC_eVu1L4HEW-2nv4M0"


async def start_polling():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())  # TODO Redis

    dp.include_router(handler_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(start_polling())
