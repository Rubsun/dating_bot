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
    pool_size: int = 10

    @property
    def uri(self) -> str:
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/"

@dataclass
class Config:
    db: DatabaseConfig
    rmq: RMQConfig


def load_config(config_path: str) -> Config:
    with open(config_path, "r") as config_file:
        data = toml.load(config_file)
    return Config(
        db=DatabaseConfig(**data["db"]),
        rmq=RMQConfig(**data["rmq"]),
    )
