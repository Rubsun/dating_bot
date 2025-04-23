import os
from collections.abc import AsyncGenerator

from dishka import Provider, Scope, make_async_container, provide
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)

from components.rating_service.config import Config, load_config
from components.rating_service.models import Base, ProfileRating  # noqa
from components.rating_service.repositories import ProfileRatingRepository


def config_provider() -> Provider:
    provider = Provider()

    cfg_path = os.getenv('RATING_SERVICE_CONFIG_PATH',
                         './components/rating_service/configs/app.toml')
    provider.provide(lambda: load_config(cfg_path),
                     scope=Scope.APP, provides=Config)
    return provider


class RatingServiceProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_engine(self, cfg: Config) -> AsyncEngine:
        return create_async_engine(cfg.db.uri, echo=True)

    @provide(scope=Scope.APP)
    async def get_sessionmaker(self, engine: AsyncEngine) -> async_sessionmaker:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    async def get_session(
            self,
            sessionmaker: async_sessionmaker
    ) -> AsyncGenerator[AsyncSession, None, None]:
        async with sessionmaker() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    async def get_repository(self, session: AsyncSession) -> ProfileRatingRepository:
        return ProfileRatingRepository(db=session)


def setup_di():
    return make_async_container(
        config_provider(),
        RatingServiceProvider(),
    )
