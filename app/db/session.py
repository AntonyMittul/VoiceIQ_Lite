import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Base


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./voiceiq.db")


def create_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    url = database_url or get_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    session = create_session_factory()()
    try:
        yield session
    finally:
        session.close()

