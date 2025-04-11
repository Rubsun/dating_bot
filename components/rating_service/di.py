import os
from collections.abc import AsyncGenerator

from dishka import Provider, Scope, make_async_container, provide
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from components.bot_gateway.config import Config, load_config
from components.bot_gateway.repositories.notification_repository import NotificationRepository
from components.bot_gateway.services.notification_service import (
    NotificationAnalyzer,
    NotificationGateway,
    NotificationService,
)


def config_provider() -> Provider:
    provider = Provider()

    cfg_path = os.getenv('DATING_BOT_CONFIG_PATH', './configs/app.toml')
    provider.provide(lambda: load_config(cfg_path), scope=Scope.APP, provides=Config)
    return provider


class RedisProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_redis_client(self, cfg: Config) -> Redis:
        return Redis.from_url(cfg.redis.uri)


class DatabaseProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_engine(self, cfg: Config) -> AsyncEngine:
        return create_async_engine(cfg.db.uri, echo=True)

    @provide(scope=Scope.APP)
    def get_sessionmaker(self, engine: AsyncEngine) -> async_sessionmaker:
        return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    async def get_session(
            self,
            sessionmaker: async_sessionmaker
    ) -> AsyncGenerator[AsyncSession, None, None]:
        async with sessionmaker() as session:
            yield session


class NotificationProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_notification_gateway(self, session: AsyncSession) -> NotificationGateway:
        return NotificationRepository(session)

    @provide(scope=Scope.REQUEST)
    def get_notification_service(
            self,
            repository: NotificationGateway,
            notification_analyzer: NotificationAnalyzer,
    ) -> NotificationService:
        return NotificationService(repository, notification_analyzer)


def setup_di():
    return make_async_container(
        config_provider(),
        DatabaseProvider(),
        NotificationProvider(),
        RedisProvider()
    )