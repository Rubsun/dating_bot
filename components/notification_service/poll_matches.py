import asyncio
import aio_pika
import msgpack
from aio_pika import IncomingMessage, ExchangeType
from aiogram import Bot, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import httpx

from components.notification_service.config import Config, DEFAULT_PROFILE_PHOTO_ID
from components.notification_service.di import setup_di


async def send_match_messages(user1_id, user2_id):
    """Send a message via Telegram directly to the user ID."""
    cfg = await container.get(Config)
    bot = await container.get(Bot)

    async with httpx.AsyncClient() as client:
        get_user1_task = asyncio.create_task(client.get(f"{cfg.profile_service_url}/profiles/{user1_id}"))
        get_user2_task = asyncio.create_task(client.get(f"{cfg.profile_service_url}/profiles/{user2_id}"))

        user1_resp, user2_resp = await asyncio.gather(get_user1_task, get_user2_task)
        user1, user2 = user1_resp.json(), user2_resp.json()

    try:
        for user, user_id in zip([user1, user2], [user2_id, user1_id]):
            text = (
                f"🎉Поздравляем, y вас мэтч!\n\n"
                f"<b>{user['first_name']} {user.get('last_name', '')}, {user['age']}</b>, {user['city']}\n"
                f"Пол: {'М' if user['gender'] == 'male' else 'Ж'}\n\n"
                f"{'О себе: ' + user.get('bio') if user.get('bio') != '' else 'Нет описания'}"
            )
            user_profile_photos = user['photo_file_ids']

            if user_profile_photos in ('None', None) or len(user_profile_photos) <= 1:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=DEFAULT_PROFILE_PHOTO_ID if (user_profile_photos in (
                    'None', None) or len(user_profile_photos) == 0) else user['photo_file_ids'][0],
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text='Показать юзернейм',
                                                  callback_data=f'show_username:{user["id"]}')],
                        ]
                    )
                )
            else:
                await bot.send_media_group(
                    chat_id=user_id,
                    media=[
                        types.input_media_photo.InputMediaPhoto(
                            media=photo_id,
                            caption=text if (i == len(user_profile_photos) - 1) else None,
                            parse_mode="HTML" if (i == len(user_profile_photos) - 1) else None,
                        )
                        for i, photo_id in enumerate(user_profile_photos)
                    ],
                )
                await bot.send_message(chat_id=user_id, text='Меню', reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text='Показать юзернейм',
                                              callback_data=f'show_username:{user["tg_username"]}')],
                    ]
                ))

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