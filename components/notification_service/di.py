import os
from aiogram import Bot
from dishka import Provider, Scope, make_async_container

from components.notification_service.config import Config, load_config

def notification_service_provider() -> Provider:
    provider = Provider()

    cfg_path = os.getenv('NOTIFICATION_SERVICE_CONFIG_PATH', './components/notification_service/configs/app.toml')
    cfg = load_config(cfg_path)

    provider.provide(lambda: cfg,
                     scope=Scope.APP, provides=Config)
    provider.provide(lambda: Bot(token=cfg.bot.bot_token),
                     scope=Scope.APP, provides=Bot)
    return provider




def setup_di():
    return make_async_container(
        notification_service_provider(),
    )
