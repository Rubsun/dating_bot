import os

from dishka import Provider, Scope, make_async_container, provide
from redis.asyncio import Redis

from components.api_gateway.config import Config, load_config


def config_provider() -> Provider:
    provider = Provider()

    cfg_path = os.getenv('API_GATEWAY_CONFIG_PATH',
                         './components/api_gateway/configs/app.toml')
    provider.provide(lambda: load_config(cfg_path),
                     scope=Scope.APP, provides=Config)

    return provider


class RedisProvider(Provider):
    @provide(scope=Scope.APP)
    def get_redis_client(self, cfg: Config) -> Redis:
        return Redis.from_url(cfg.redis.uri)


def setup_di():
    return make_async_container(
        config_provider(),
        RedisProvider()
    )
