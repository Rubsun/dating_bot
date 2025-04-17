from components.matching_service.services import MatchingServicer
import asyncio
import logging

import grpc.aio
from dishka.integrations.grpcio import DishkaAioInterceptor

from components.matching_service.config import Config
from components.matching_service.di import setup_di
from components.protos import matching_pb2_grpc

logging.basicConfig(level=logging.INFO)


async def serve():
    container = setup_di()
    server = grpc.aio.server(interceptors=[DishkaAioInterceptor(container)])

    cfg = await container.get(Config)
    service = await container.get(MatchingServicer)

    matching_pb2_grpc.add_MatchingServicer_to_server(service, server)

    server.add_insecure_port(f"{cfg.grpc.uri}")
    await server.start()
    logging.info(f"Matching Service started")

    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt. Gracefully stopping...")
        await server.stop(5)  # 5 секунд на graceful shutdown


if __name__ == '__main__':
    asyncio.run(serve())
