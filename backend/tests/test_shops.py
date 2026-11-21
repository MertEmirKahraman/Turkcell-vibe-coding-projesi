from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models import Product, Shop, User, UserRole

client = TestClient(app)
KIZILAY_LATITUDE = 39.919870
KIZILAY_LONGITUDE = 32.853241


def create_test_shops() -> tuple[int, str]:
    suffix = uuid4().hex
    with SessionLocal() as db:
        owner = User(
            phone_number=f"06{uuid4().int % 10**9:09d}",
            full_name="Dükkân Test Sahibi",
            role=UserRole.CUSTOMER,
            phone_verified=True,
        )
        db.add(owner)
        db.flush()
        near_shop = Shop(
            owner_id=owner.id,
            name=f"Test Kızılay {suffix}",
            address="Kızılay, Ankara",
            latitude=Decimal("39.919870"),
            longitude=Decimal("32.853241"),
            is_active=True,
        )
        farther_shop = Shop(
            owner_id=owner.id,
            name=f"Test Çankaya {suffix}",
            address="Çankaya, Ankara",
            latitude=Decimal("39.898330"),
            longitude=Decimal("32.864250"),
            is_active=True,
        )
        db.add_all([near_shop, farther_shop])
        db.flush()
        db.add_all([
            Product(
                shop_id=near_shop.id,
                name="Test Espresso",
                description="Espresso",
                price=Decimal("75.00"),
                stock_quantity=10,
                is_active=True,
            ),
            Product(
                shop_id=near_shop.id,
                name="Gizli Ürün",
                price=Decimal("1.00"),
                stock_quantity=0,
                is_active=False,
            ),
        ])
        db.commit()
        return near_shop.id, suffix


def remove_test_shops(suffix: str) -> None:
    with SessionLocal() as db:
        shops = db.query(Shop).filter(Shop.name.contains(suffix)).all()
        owner_ids = {shop.owner_id for shop in shops}
        for shop in shops:
            db.delete(shop)
        db.flush()
        for owner_id in owner_ids:
            owner = db.get(User, owner_id)
            if owner is not None:
                db.delete(owner)
        db.commit()


def test_shop_list_search_nearby_sorting_and_menu() -> None:
    near_shop_id, suffix = create_test_shops()
    try:
        listing = client.get("/api/v1/shops")
        assert listing.status_code == 200
        assert any(shop["name"].endswith(suffix) for shop in listing.json()["data"])

        nearby = client.get(
            "/api/v1/shops",
            params={
                "latitude": KIZILAY_LATITUDE,
                "longitude": KIZILAY_LONGITUDE,
                "radius_km": 1,
            },
        )
        nearby_shops = nearby.json()["data"]
        assert near_shop_id in [shop["id"] for shop in nearby_shops]
        assert [shop["distance_km"] for shop in nearby_shops] == sorted(
            shop["distance_km"] for shop in nearby_shops
        )
        assert nearby_shops[0]["distance_km"] == 0

        search = client.get("/api/v1/shops", params={"search": suffix})
        assert search.status_code == 200
        assert len(search.json()["data"]) == 2

        detail = client.get(f"/api/v1/shops/{near_shop_id}")
        assert detail.status_code == 200
        assert [item["name"] for item in detail.json()["data"]["menu"]] == [
            "Test Espresso"
        ]
    finally:
        remove_test_shops(suffix)


def test_coordinates_must_be_provided_together() -> None:
    response = client.get(
        "/api/v1/shops",
        params={"latitude": KIZILAY_LATITUDE},
    )

    assert response.status_code == 422
