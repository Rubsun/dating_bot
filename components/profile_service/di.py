import os
from collections.abc import AsyncGenerator

from dishka import Provider, Scope, make_async_container, provide
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)

from components.profile_service.config import Config, load_config
from components.profile_service.models import Base, Profile  # noqa
from components.profile_service.repositories import ProfileRepository
from components.profile_service.minio_utils import MinIOClient


def config_provider() -> Provider:
    provider = Provider()

    cfg_path = os.getenv('PROFILE_SERVICE_CONFIG_PATH',
                         './components/profile_service/configs/app.toml')
    provider.provide(lambda: load_config(cfg_path),
                     scope=Scope.APP, provides=Config)
    return provider


class ProfileServiceProvider(Provider):
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
    async def get_repository(self, session: AsyncSession) -> ProfileRepository:
        return ProfileRepository(db=session)


    @provide(scope=Scope.APP)
    async def get_s3_client(self, cfg: Config) -> MinIOClient:
        return MinIOClient(
            bucket_name=cfg.s3.profile_photos_bucket,
            endpoint_url=cfg.s3.endpoint_url,
            access_key=cfg.s3.access_key,
            secret_key=cfg.s3.secret_key,
        )

def setup_di():
    return make_async_container(
        config_provider(),
        ProfileServiceProvider(),
    )
