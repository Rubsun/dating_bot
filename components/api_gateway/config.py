from dataclasses import dataclass

import toml


@dataclass
class GrpcConfig:
    host: str
    port: int

    def __post_init__(self) -> None:
        self.uri = (
            f"{self.host}:{self.port}"
        )


@dataclass
class Config:
    grpc: GrpcConfig


def load_config(config_path: str) -> Config:
    with open(config_path, "r") as config_file:
        data = toml.load(config_file)
    return Config(
        grpc=GrpcConfig(**data["grpc"]),
    )
