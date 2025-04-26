from dataclasses import dataclass

import toml


@dataclass
class BotConfig:
    bot_token: str


@dataclass
class Config:
    bot: BotConfig
    profile_service_url: str
    rating_service_url: str
    matching_service_url: str


def load_config(config_path: str) -> Config:
    with open(config_path, "r") as config_file:
        data = toml.load(config_file)
    return Config(
        bot=BotConfig(**data["bot"]),
        profile_service_url=data["profile_service_url"],
        rating_service_url=data["rating_service_url"],
        matching_service_url=data["matching_service_url"],
    )

