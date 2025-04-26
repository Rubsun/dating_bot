from dataclasses import dataclass

import toml


@dataclass
class RMQConfig:
    host: str
    port: int
    user: str
    password: str

    def __post_init__(self) -> None:
        self.uri = (
            f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/"
        )


@dataclass
class BotConfig:
    bot_token: str


@dataclass
class CeleryConfig:
    broker_url: str


@dataclass
class Config:
    rabbitmq: RMQConfig
    bot: BotConfig
    celery: CeleryConfig


def load_config(config_path: str) -> Config:
    with open(config_path, "r") as config_file:
        data = toml.load(config_file)
    return Config(
        rabbitmq=RMQConfig(**data["rmq"]),
        bot=BotConfig(**data["bot"]),
        celery=CeleryConfig(**data["celery"]),
    )
