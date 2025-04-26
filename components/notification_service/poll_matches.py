import asyncio
import aio_pika
import msgpack
from aio_pika import IncomingMessage, ExchangeType
from aiogram import Bot

from components.notification_service.config import Config
from components.notification_service.di import setup_di


async def send_telegram_message(user_id, text):
    """Send a message via Telegram directly to the user ID."""
    bot = await container.get(Bot)
    try:
        await bot.send_message(chat_id=user_id, text=text)
        print(f"Sent message to user {user_id}: {text}")
    except Exception as e:
        print(f"Error sending message to user {user_id}: {e}")


async def process_match_message(message: IncomingMessage):
    """Process messages received from the RabbitMQ queue."""
    async with message.process():
        try:
            # Decode and parse the incoming JSON message
            body = msgpack.unpackb(message.body)
            user1_id = body.get("user1_id")
            user2_id = body.get("user2_id")
            user1_username = body.get("user1_username")
            user2_username = body.get("user2_username")
            # match_date = body.get("match_date")

            # Validate the message fields
            if not all([user1_id, user2_id]):
                raise ValueError("Message is missing required fields (user1_id, user2_id, match_date).")

            # Create and send customized Telegram messages for both users
            user1_message = f"Поздравляем! У вас матч с @{user2_username}!"
            user2_message = f"Поздравляем! У вас матч с @{user1_username}!"

            await send_telegram_message(user1_id, user1_message)
            await send_telegram_message(user2_id, user2_message)

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