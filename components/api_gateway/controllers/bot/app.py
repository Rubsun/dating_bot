import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from components.api_gateway.controllers.bot.handlers import router as handler_router

BOT_TOKEN = "7066916393:AAFOAZtmf__xt9Fl-XSM9GpTQvddn98skkI"

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
)

async def start_polling():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())  # TODO Redis

    dp.include_router(handler_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.info("Запуск бота...")
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_polling())
