from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from backend.app.core.security import create_token
from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models import (
    Order,
    OrderItem,
    OrderStatus,
    Product,
    Shop,
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    User,
    UserRole,
)

client = TestClient(app)


def create_order_fixture(
    *,
    with_subscription: bool = True,
    plan: SubscriptionPlan = SubscriptionPlan.STARTER,
    credits: int = 1,
) -> dict[str, int | str]:
    with SessionLocal() as db:
        customer = User(
            phone_number=f"09{uuid4().int % 10**9:09d}",
            full_name="Sipariş Test Müşterisi",
            role=UserRole.CUSTOMER,
            phone_verified=True,
        )
        owner = User(
            phone_number=f"08{uuid4().int % 10**9:09d}",
            full_name="Sipariş Test Dükkân Sahibi",
            role=UserRole.SHOP_OWNER,
            phone_verified=True,
        )
        db.add_all([customer, owner])
        db.flush()
        shop = Shop(
            owner_id=owner.id,
            name=f"Sipariş Test Dükkânı {uuid4().hex}",
            address="Kızılay, Ankara",
            latitude=39.919870,
            longitude=32.853241,
            is_active=True,
        )
        db.add(shop)
        db.flush()
        product = Product(
            shop_id=shop.id,
            name="Test Cappuccino",
            description="Cappuccino",
            price=100,
            stock_quantity=20,
            is_active=True,
        )
        db.add(product)
        if with_subscription:
            now = datetime.now(timezone.utc)
            db.add(
                Subscription(
                    user_id=customer.id,
                    plan_type=plan,
                    remaining_credits=credits,
                    status=SubscriptionStatus.ACTIVE,
                    started_at=now,
                    expires_at=now + timedelta(days=30),
                )
            )
        db.commit()
        return {
            "customer_id": customer.id,
            "owner_id": owner.id,
            "shop_id": shop.id,
            "product_id": product.id,
            "customer_token": create_token(customer, "access"),
            "owner_token": create_token(owner, "access"),
        }


def cleanup_order_fixture(fixture: dict[str, int | str]) -> None:
    with SessionLocal() as db:
        order_ids = select(Order.id).where(Order.shop_id == fixture["shop_id"])
        db.execute(delete(OrderItem).where(OrderItem.order_id.in_(order_ids)))
        db.execute(delete(Order).where(Order.shop_id == fixture["shop_id"]))
        db.execute(
            delete(Subscription).where(Subscription.user_id == fixture["customer_id"])
        )
        db.execute(delete(Product).where(Product.shop_id == fixture["shop_id"]))
        db.execute(delete(Shop).where(Shop.id == fixture["shop_id"]))
        db.execute(
            delete(User).where(User.id.in_([fixture["customer_id"], fixture["owner_id"]]))
        )
        db.commit()


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_order_credits_qr_and_shop_owner_status_flow() -> None:
    fixture = create_order_fixture()
    customer_headers = auth_header(str(fixture["customer_token"]))
    owner_headers = auth_header(str(fixture["owner_token"]))
    try:
        created = client.post(
            "/api/v1/orders",
            headers=customer_headers,
            json={
                "shop_id": fixture["shop_id"],
                "product_id": fixture["product_id"],
                "size": "L",
                "sugar_level": 2,
                "milk_preference": "OAT",
                "extra_shots": 1,
            },
        )
        assert created.status_code == 200
        order = created.json()["data"]
        order_id = order["id"]
        qr = order["qr_code"]
        assert order["status"] == "PENDING"
        assert set(qr) == {
            "order_id",
            "user_id",
            "shop_id",
            "created_at",
            "signature",
        }
        assert len(qr["signature"]) == 64
        assert order["items"][0]["customization"] == {
            "size": "L",
            "sugar_level": 2,
            "milk_preference": "OAT",
            "extra_shots": 1,
        }

        with SessionLocal() as db:
            subscription = db.scalar(
                select(Subscription).where(
                    Subscription.user_id == fixture["customer_id"]
                )
            )
            assert subscription is not None
            assert subscription.remaining_credits == 0

        history = client.get("/api/v1/orders/history", headers=customer_headers)
        assert history.status_code == 200
        assert history.json()["data"][0]["id"] == order_id

        shop_orders = client.get("/api/v1/orders/shop", headers=owner_headers)
        assert shop_orders.status_code == 200
        assert shop_orders.json()["data"][0]["id"] == order_id
        assert shop_orders.json()["data"][0]["qr_code"] is None

        for next_status in ("ACCEPTED", "PREPARING", "READY"):
            updated = client.patch(
                f"/api/v1/orders/{order_id}/status",
                headers=owner_headers,
                json={"status": next_status},
            )
            assert updated.status_code == 200
            assert updated.json()["data"]["status"] == next_status

        forged_qr = {**qr, "signature": "0" * 64}
        invalid = client.post(
            f"/api/v1/orders/{order_id}/verify-qr",
            headers=owner_headers,
            json=forged_qr,
        )
        assert invalid.status_code == 400

        verified = client.post(
            f"/api/v1/orders/{order_id}/verify-qr",
            headers=owner_headers,
            json=qr,
        )
        assert verified.status_code == 200
        assert verified.json()["data"]["verified"] is True

        delivered = client.post(
            f"/api/v1/orders/{order_id}/redeem",
            headers=owner_headers,
            json=qr,
        )
        assert delivered.status_code == 200
        assert delivered.json()["data"]["status"] == "DELIVERED"
        assert client.get(
            f"/api/v1/orders/{order_id}", headers=customer_headers
        ).json()["data"]["status"] == "DELIVERED"

        no_credits = client.post(
            "/api/v1/orders",
            headers=customer_headers,
            json={
                "shop_id": fixture["shop_id"],
                "product_id": fixture["product_id"],
            },
        )
        assert no_credits.status_code == 409
        assert "kahve hakkı kalmadı" in no_credits.json()["error"]["message"]
    finally:
        cleanup_order_fixture(fixture)


def test_order_requires_active_subscription_and_unlimited_does_not_decrement() -> None:
    no_subscription = create_order_fixture(with_subscription=False)
    unlimited = create_order_fixture(
        plan=SubscriptionPlan.UNLIMITED,
        credits=0,
    )
    try:
        no_subscription_response = client.post(
            "/api/v1/orders",
            headers=auth_header(str(no_subscription["customer_token"])),
            json={
                "shop_id": no_subscription["shop_id"],
                "product_id": no_subscription["product_id"],
            },
        )
        assert no_subscription_response.status_code == 403
        assert "Aktif aboneliğiniz yok" in no_subscription_response.json()["error"]["message"]

        unlimited_response = client.post(
            "/api/v1/orders",
            headers=auth_header(str(unlimited["customer_token"])),
            json={
                "shop_id": unlimited["shop_id"],
                "product_id": unlimited["product_id"],
            },
        )
        assert unlimited_response.status_code == 200
        with SessionLocal() as db:
            subscription = db.scalar(
                select(Subscription).where(
                    Subscription.user_id == unlimited["customer_id"]
                )
            )
            assert subscription is not None
            assert subscription.remaining_credits == 0
    finally:
        cleanup_order_fixture(no_subscription)
        cleanup_order_fixture(unlimited)
