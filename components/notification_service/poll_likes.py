import asyncio

import msgpack
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import httpx

from celery import Celery
from celery.schedules import schedule
import aio_pika
from aio_pika.exchange import ExchangeType

from components.notification_service.config import Config, DEFAULT_PROFILE_PHOTO_ID
from components.notification_service.di import setup_di

# Initialize Celery
app = Celery('project')
app.config_from_object('components.notification_service.celeryconfig')

# Configure beat schedule
app.conf.beat_schedule = {
    'run-my-task-every-hour': {
        'task': 'components.notification_service.poll_likes.minutely_poll_likes_task',
        'schedule': schedule(run_every=60),  # Runs at the start of every hour
    },
}

app.conf.timezone = 'UTC'


def run_async(coro):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


container = setup_di()

@app.task
def minutely_poll_likes_task():
    # Your task logic here
    async def inner():
        cfg = await container.get(Config)
        bot = await container.get(Bot)
        connection = await aio_pika.connect_robust(cfg.rabbitmq.uri)

        async with connection:
            # Create a channel
            channel: aio_pika.abc.AbstractChannel = await connection.channel()

            # Declare the queue
            exchange = await channel.declare_exchange("likes", ExchangeType.DIRECT)
            queue: aio_pika.abc.AbstractQueue = await channel.declare_queue("likes")

            await queue.bind(exchange)

            # Get the message count
            queue_state = await queue.declare()  # Re-declare to get message count
            message_count = queue_state.message_count
            print(f"Queue has {message_count} messages")

            if message_count == 0:
                print("Queue is empty, exiting")
                return

            # Set QoS to prefetch messages (optional, adjust as needed)
            await channel.set_qos(prefetch_count=1)

            # Iterate over messages
            messages_processed = 0
            async for message in queue.iterator():
                async with message.process():
                    like_dct = msgpack.unpackb(message.body)
                    liker_id = like_dct["liker_id"]
                    liked_id = like_dct["liked_id"]

                    async with httpx.AsyncClient() as client:
                        liker_profile_resp = await client.get(f"{cfg.profile_service_url}/profiles/{liker_id}")
                        liker_data = liker_profile_resp.json()

                    text = (
                        f"❤️Поздравляем, y вас лайк!\n\n"
                        f"<b>{liker_data['first_name']} {liker_data.get('last_name', '')}, {liker_data['age']}</b>, {liker_data['city']}\n"
                        f"Пол: {'М' if liker_data['gender'] == 'male' else 'Ж'}\n\n"
                        f"{'О себе: ' + liker_data.get('bio') if liker_data.get('bio') != '' else 'Нет описания'}"
                    )

                    await bot.send_photo(
                        chat_id=liked_id,
                        photo=liker_data['photo_file_id'] if liker_data['photo_file_id'] != 'None' else DEFAULT_PROFILE_PHOTO_ID,
                        caption=text,
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(text='Показать юзернейм',
                                                      callback_data=f'show_username:{liker_data["tg_username"]}')],
                            ]
                        )
                    )
                    messages_processed += 1
                    # Stop after processing all initial messages
                    if messages_processed >= message_count:
                        break

            print("Finished processing all messages")
    return run_async(inner())
