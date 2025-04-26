import asyncio
import aio_pika
import msgpack
from aio_pika import IncomingMessage, ExchangeType
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import httpx

from components.notification_service.config import Config
from components.notification_service.di import setup_di

DEFAULT_PROFILE_PHOTO_ID = "AgACAgIAAxkBAAPTaAz10wpbJ5qbrlZN8D9l857jUTUAAizuMRtF92hIMO4aSv2p4J8BAAMCAANtAAM2BA"


async def send_match_messages(user1_id, user2_id):
    """Send a message via Telegram directly to the user ID."""
    cfg = await container.get(Config)
    bot = await container.get(Bot)

    async with httpx.AsyncClient() as client:
        get_user1_task = asyncio.create_task(client.get(f"{cfg.profile_service_url}/profiles/{user1_id}"))
        get_user2_task = asyncio.create_task(client.get(f"{cfg.profile_service_url}/profiles/{user2_id}"))

        user1_resp, user2_resp = await asyncio.gather(get_user1_task, get_user2_task)
        user1, user2 = user1_resp.json(), user2_resp.json()

    text1 = (
        f"Поздравляем, y вас мэтч!\n\n"
        f"<b>{user2['first_name']} {user2.get('last_name', '')}, {user2['age']}</b>, {user2['city']}\n"
        f"Пол: {'М' if user2['gender'] == 'male' else 'Ж'}\n\n"
        f"{'О себе: ' + user2.get('bio') if user2.get('bio') != '' else 'Нет описания'}"
    )
    text2 = (
        f"Поздравляем, y вас мэтч!\n\n"
        f"<b>{user1['first_name']} {user1.get('last_name', '')}, {user1['age']}</b>, {user1['city']}\n"
        f"Пол: {'М' if user1['gender'] == 'male' else 'Ж'}\n\n"
        f"{'О себе: ' + user1.get('bio') if user1.get('bio') != '' else 'Нет описания'}"
    )
    try:
        await bot.send_photo(
            chat_id=user1_id,
            photo=user2['photo_file_id'] if user2['photo_file_id'] != 'None' else DEFAULT_PROFILE_PHOTO_ID,
            caption=text1,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text='Показать юзернейм', callback_data=f'show_username:{user2["tg_username"]}')],
                ]
            )
        )
        await bot.send_photo(
            chat_id=user2_id,
            photo=user1['photo_file_id'] if user1['photo_file_id'] != 'None' else DEFAULT_PROFILE_PHOTO_ID,
            caption=text2,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text='Показать юзернейм',
                                          callback_data=f'show_username:{user1["tg_username"]}')],
                ]
            )
        )
    except Exception as e:
        print(f"Error sending message to users {user1_id}, {user2_id}: {e}")


async def process_match_message(message: IncomingMessage):
    """Process messages received from the RabbitMQ queue."""
    async with message.process():
        try:
            # Decode and parse the incoming JSON message
            body = msgpack.unpackb(message.body)
            user1_id = body.get("user1_id")
            user2_id = body.get("user2_id")
            # match_date = body.get("match_date")

            # Validate the message fields
            if not all([user1_id, user2_id]):
                raise ValueError("Message is missing required fields (user1_id, user2_id, match_date).")

            await send_match_messages(user1_id, user2_id)
        except Exception as e:
            print(f"Error processing message: {e}")


async def main():
    # Establish connection to RabbitMQ
    cfg = await container.get(Config)
    connection = await aio_pika.connect_robust(cfg.rabbitmq.uri)
    async with connection:
        channel = await connection.channel()

        # Declare the "matches" queue
        exchange = await channel.declare_exchange("matches", ExchangeType.DIRECT)
        queue = await channel.declare_queue("matches")

        # Bind the queue to the default exchange
        await queue.bind(exchange)

        print('Consuming queue..')
        await queue.consume(process_match_message)
        await asyncio.Future()


if __name__ == "__main__":
    try:
        container = setup_di()
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Service stopped.")