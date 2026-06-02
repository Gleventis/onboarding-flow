"""
Database connection handler
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from server.config import settings


class Database:
    """
    A db connection handler
    """

    def __init__(self, url: str) -> None:
        self.engine = create_engine(url=url)
        self.session_factory = sessionmaker(bind=self.engine)


db = Database(url=settings.database_url)


def get_onboarding_db() -> Generator[Session, None, None]:
    """
    Yield a database session for FastAPI dependency injection
    """
    session = db.session_factory()
    try:
        yield session
    finally:
        session.close()


if __name__ == "__main__":
    with db.session_factory() as session:
        print(f"Session created: {session}")
