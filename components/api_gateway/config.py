from dataclasses import dataclass

import toml


@dataclass
class BotConfig:
    bot_token: str


@dataclass
class Config:
    bot: BotConfig


def load_config(config_path: str) -> Config:
    with open(config_path, "r") as config_file:
        data = toml.load(config_file)
    return Config(
        bot=BotConfig(**data["bot"]),
    )
