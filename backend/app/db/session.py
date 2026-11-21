from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.core.settings import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    from backend.app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    if settings.database_url.startswith("sqlite"):
        inspector = inspect(engine)
        if "users" in inspector.get_table_names():
            user_columns = {column["name"] for column in inspector.get_columns("users")}
            if "password_hash" not in user_columns:
                with engine.begin() as connection:
                    connection.execute(
                        text(
                            "ALTER TABLE users "
                            "ADD COLUMN password_hash VARCHAR(255)"
                        )
                    )
            inspector = inspect(engine)
            user_columns = {column["name"] for column in inspector.get_columns("users")}
            if "phone_verified" not in user_columns:
                with engine.begin() as connection:
                    connection.execute(
                        text(
                            "ALTER TABLE users "
                            "ADD COLUMN phone_verified BOOLEAN NOT NULL DEFAULT 0"
                        )
                    )
        inspector = inspect(engine)
        if "order_items" in inspector.get_table_names():
            item_columns = {
                column["name"] for column in inspector.get_columns("order_items")
            }
            if "customization" not in item_columns:
                with engine.begin() as connection:
                    connection.execute(
                        text("ALTER TABLE order_items ADD COLUMN customization JSON")
                    )


def get_db() -> Generator[Session, None, None]:
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()