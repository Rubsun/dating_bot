import os
from dishka import Provider, Scope, make_async_container

from components.api_gateway.config import Config, load_config



def config_provider() -> Provider:
    provider = Provider()

    cfg_path = os.getenv('DATING_SERVICE_CONFIG_PATH',
                         './components/api_gateway/configs/app.toml')
    provider.provide(lambda: load_config(cfg_path),
                     scope=Scope.APP, provides=Config)
    return provider



def setup_di():
    return make_async_container(
        config_provider(),
    )
