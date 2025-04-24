from functools import partial
from typing import AsyncGenerator

import aio_pika
from aio_pika import Connection
from aio_pika.abc import AbstractRobustConnection, AbstractChannel
from aio_pika.pool import Pool

from learn_anything.api_gateway.adapters.rmq.config import RMQConfig
from learn_anything.api_gateway.adapters.logger import logger


async def get_channel(connection_pool: Pool[Connection]) -> AsyncGenerator[AbstractChannel, None]:
    async with connection_pool.acquire() as connection:
        yield await connection.channel()


async def get_connection_pool(rmq_cfg: RMQConfig) -> Pool[Connection]:
    return Pool(partial(_get_connection, rmq_cfg), max_size=rmq_cfg.pool_size)


async def _get_connection(rmq_cfg: RMQConfig) -> AbstractRobustConnection:
    try:
        return await aio_pika.connect_robust(rmq_cfg.uri)
    except Exception as e:
        logger.exception(e)
        exit(1)