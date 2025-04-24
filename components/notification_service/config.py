from dataclasses import dataclass

import toml


@dataclass
class RMQConfig:
    host: str
    port: int

    def __post_init__(self) -> None:
        self.uri = (
            f"amqp://guest:guest@{self.host}:{self.port}/"
        )


@dataclass
class BotConfig:
    bot_token: str


@dataclass
class Config:
    rabbitmq: RMQConfig
    bot: BotConfig


def load_config(config_path: str) -> Config:
    with open(config_path, "r") as config_file:
        data = toml.load(config_file)
    return Config(
        rabbitmq=RMQConfig(**data["rmq"]),
        bot=BotConfig(**data["bot"]),
    )
