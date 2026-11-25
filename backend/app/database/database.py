from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine():
    return create_engine(
        get_settings().database_url.get_secret_value(),
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
        hide_parameters=True,
    )


def get_session():
    with sessionmaker(get_engine(), expire_on_commit=False)() as session:
        yield session
