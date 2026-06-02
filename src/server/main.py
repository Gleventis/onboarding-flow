"""
Main module for the server
"""
import logging

from alembic.config import Config
from alembic import command
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from pathlib import Path
from server.config import settings
from server.routes import generic, applications

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -10s %(funcName) '
              '-5s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    startup and shutdown behavior
    currently runs alembic migrations to create the tables

    Args:
        app (FastAPI): the fastapi app
    """
    config_file_path = Path(__file__).resolve().parent.parent / "alembic.ini"

    almbc_config = Config(str(config_file_path))

    command.upgrade(almbc_config, "head")

    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan, version="0.1.0")


def configure() -> None:
    """
    configures the server
    """
    logging.basicConfig(level=settings.logging_level, format=LOG_FORMAT)

    app.include_router(generic.router, tags=['Generic'])
    app.include_router(applications.router, tags=['Application'])


if __name__ == '__main__':
    configure()
    uvicorn.run(app,
                host='0.0.0.0',
                port=8000)

else:
    configure()
