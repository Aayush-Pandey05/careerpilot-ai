from sqlalchemy import create_engine

from alembic import context
from app.core.config import get_settings
from app.interview.models import InterviewSession

config = context.config
url = get_settings().database_url.get_secret_value()
metadata = InterviewSession.metadata
if context.is_offline_mode():
    context.configure(url=url, target_metadata=metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url, hide_parameters=True)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=metadata)
        with context.begin_transaction():
            context.run_migrations()
