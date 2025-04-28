import time
from contextlib import suppress
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message
from dishka import AsyncContainer
from redis.asyncio import Redis


class CheckUsernameMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.counter = 0

    async def __call__(
            self,
            handler,
            event: Message,
            data: dict[str, Any]
    ) -> Any:
        if not event.from_user.username:
            return await event.answer(text='Для использования бота необходимо выставить username в настройках')
        return await handler(event, data)


# Максимум 100 запросов в минуту от одного клиента
RATE_LIMIT = 100
TIME_WINDOW = 60


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, ioc_container: AsyncContainer):
        self._ioc_container = ioc_container
        self._cache = {}

    async def __call__(
            self,
            handler,
            event: Message,
            data: dict[str, Any]
    ) -> Any:
        redis_client = await self._ioc_container.get(Redis)

        user_id = event.from_user.id
        redis_key = f"ratelimit:{user_id}"

        try:
            current_count = await redis_client.get(redis_key)
            if not current_count:
                await redis_client.setex(redis_key, RATE_LIMIT, 1)
                return await handler(event, data)

            current_count = await redis_client.incr(redis_key)
            print(f"{redis_key}: {current_count}")

            if int(current_count) > RATE_LIMIT:
                if not self._cache.get(redis_key):
                    self._cache[redis_key] = time.time()

                await event.answer(
                    f'Слишком много запросов. Прошу, передохни еще {TIME_WINDOW - (time.time() - self._cache[redis_key])} сек.')
                return
            with suppress(KeyError):
                del self._cache[redis_key]

            return await handler(event, data)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")


from typing import Dict, Any, Awaitable, Callable
from asyncio import sleep



class MediaGroupMiddleware(BaseMiddleware):
    def __init__(self):
        self._memo = {}

    @staticmethod
    def _get_content(msg: Message):
        if msg.photo:
            return msg.photo[-1]
        return getattr(msg, msg.content_type)

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ):
        media_group_id, content = event.media_group_id, self._get_content(event)
        if media_group_id:
            if not self._memo.get(media_group_id):
                self._memo[media_group_id] = {
                    "media_group": list(),
                    "handled": False
                }
            self._memo[media_group_id]["media_group"].append(content)
            await sleep(0.4)  # giving time to get and process other media

            if not self._memo[media_group_id]["handled"]:
                self._memo[media_group_id]["handled"] = True

                data["media_group"] = self._memo[media_group_id]["media_group"]
                return await handler(event, data)
            return
        if self._memo:
            self._memo.clear()
        return await handler(event, data)
