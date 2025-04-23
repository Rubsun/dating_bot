from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from components.profile_service.routers import \
    router as matching_router
from components.profile_service.di import setup_di


@asynccontextmanager
async def lifespan(app_: FastAPI) -> AsyncGenerator[None, None]:
    yield

    await app_.container.close()


def create_app(ioc_container: AsyncContainer):
    application = FastAPI(title="Dating Bot Profile Service",
                          version="1.0.0", lifespan=lifespan)

    setup_dishka(container=ioc_container, app=application)
    application.container = ioc_container

    application.include_router(matching_router, prefix="/api/v1")

    @application.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return application


container = setup_di()
app = create_app(container)
