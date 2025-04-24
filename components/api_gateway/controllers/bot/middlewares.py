from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message


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
            return await event.answer(text='Для использования бота необходимо выставить username')
        return await handler(event, data)
