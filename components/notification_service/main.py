import asyncio
import aio_pika
from aio_pika import connect, IncomingMessage, ExchangeType
from aiogram import Bot
import json

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


async def process_message(message: IncomingMessage):
    """Process messages received from the RabbitMQ queue."""
    async with message.process():
        try:
            # Decode and parse the incoming JSON message
            body = json.loads(message.body.decode())
            user1_id = body.get("user1_id")
            user2_id = body.get("user2_id")
            match_date = body.get("match_date")

            # Validate the message fields
            if not all([user1_id, user2_id, match_date]):
                raise ValueError("Message is missing required fields (user1_id, user2_id, match_date).")

            # Create and send customized Telegram messages for both users
            user1_message = f"You got a match with user {user2_id} on {match_date}."
            user2_message = f"You got a match with user {user1_id} on {match_date}."

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
        queue = await channel.declare_queue("matches")

        print('Consuming queue..')
        await queue.consume(process_message)
        await asyncio.Future()


if __name__ == "__main__":
    try:
        container = setup_di()
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Service stopped.")