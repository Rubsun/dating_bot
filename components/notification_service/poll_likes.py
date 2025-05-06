import asyncio

import msgpack
import httpx
from aiogram import Bot, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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
            liked_likers = {}
            messages_processed = 0
            async for message in queue.iterator():
                async with message.process():
                    like_dct = msgpack.unpackb(message.body)
                    liked_id = like_dct["liked_id"]

                    if liked_likers.get(liked_id) is None:

                        liked_likers[liked_id] = []

                    liked_likers[liked_id].append(like_dct["liker_id"])
                    messages_processed += 1
                    # Stop after processing all initial messages
                    if messages_processed >= message_count:
                        break

            print("Finished processing all messages")

        for liked_id in liked_likers:
            likers = liked_likers[liked_id]

            async with httpx.AsyncClient() as client:
                existing_liked_user_matches_resp = await client.get(
                    cfg.matching_service_url + f'/matches/{liked_id}'
                )
                existing_liked_user_matches = existing_liked_user_matches_resp.json()

            print(existing_liked_user_matches)

            # clean up from existing matches
            for liked_user_match in existing_liked_user_matches:
                matched_id = liked_user_match['user_id']
                if matched_id in likers:
                    likers.remove(matched_id)

            if len(likers) > 0:
                await bot.send_message(
                    chat_id=liked_id,
                    text=f'Твоя анкета понравилась {len(likers)} чел.',
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[[InlineKeyboardButton(text='Посмотреть', callback_data=f'my_likers-{likers}')]]
                    )
                )
    return run_async(inner())
