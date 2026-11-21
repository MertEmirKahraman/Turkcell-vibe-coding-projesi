from sqlalchemy import inspect

from backend.app.db.session import engine
from backend.app.main import app


def test_database_tables_are_created_on_startup() -> None:
    from fastapi.testclient import TestClient

    with TestClient(app):
        table_names = set(inspect(engine).get_table_names())

    assert {
        "users",
        "subscriptions",
        "shops",
        "products",
        "orders",
        "order_items",
    }.issubset(table_names)
