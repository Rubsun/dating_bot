import os

import grpc
from dishka import Provider, Scope, make_async_container, provide

from components.api_gateway.config import Config, load_config
from common.protos import matching_pb2_grpc



def config_provider() -> Provider:
    provider = Provider()

    cfg_path = os.getenv('DATING_SERVICE_CONFIG_PATH',
                         './components/api_gateway/configs/app.toml')
    provider.provide(lambda: load_config(cfg_path),
                     scope=Scope.APP, provides=Config)
    return provider


class GrpcClientProvider(Provider):
    @provide(scope=Scope.SESSION)
    async def get_grpc_channel(self, cfg: Config) -> grpc.Channel:
        return grpc.aio.insecure_channel(cfg.grpc.uri)

    @provide(scope=Scope.SESSION)
    async def get_matching_stub(self, channel: grpc.Channel) -> matching_pb2_grpc.MatchingStub:
        return matching_pb2_grpc.MatchingStub(channel)

    # @provide(scope=Scope.APP)
    # async def cleanup_grpc(
    #     self,
    #     channel: grpc.Channel,
    # ) -> AsyncGenerator[None, None]:
    #     try:
    #         yield
    #     finally:
    #         logger.info("Closing gRPC channel")
    #         channel.close()


def setup_di():
    return make_async_container(
        config_provider(),
        GrpcClientProvider()
    )
