import toml
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    user: str
    password: str
    name: str
    host: str
    port: int

    def __post_init__(self) -> None:
        self.uri = (
            f"postgresql+asyncpg://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.name}"
        )


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
class Config:
    profile_service_url: str
    db: DatabaseConfig
    rabbitmq: RMQConfig


def load_config(config_path: str) -> Config:
    with open(config_path, "r") as config_file:
        data = toml.load(config_file)
    return Config(
        profile_service_url=data["profile_service_url"],
        db=DatabaseConfig(**data["db"]),
        rabbitmq=RMQConfig(**data["rmq"]),
    )
