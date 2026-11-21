from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)
SUCCESS_CARD = "4242-4242-4242-4242"
FAILURE_CARD = "4000-0000-0000-0002"


def register_and_authorize() -> tuple[str, str]:
    phone = f"0555{uuid4().int % 10**7:07d}"
    registered = client.post(
        "/api/v1/auth/register",
        json={"phone_number": phone, "full_name": "Abonelik Testi"},
    )
    assert registered.status_code == 200
    verified = client.post(
        "/api/v1/auth/verify-otp",
        json={"phone_number": phone, "otp_code": "1234"},
    )
    assert verified.status_code == 200
    return phone, verified.json()["data"]["access_token"]


def test_plans_payment_upgrade_cancel_and_failed_payment() -> None:
    _, token = register_and_authorize()
    headers = {"Authorization": f"Bearer {token}"}

    plans = client.get("/api/v1/subscriptions/plans")
    assert plans.status_code == 200
    plan_data = plans.json()["data"]
    assert [plan["monthly_price"] for plan in plan_data] == [89.99, 149.99, 249.99]

    failed = client.post(
        "/api/v1/payments/process",
        headers=headers,
        json={
            "subscription_plan": "STARTER",
            "card_number": FAILURE_CARD,
        },
    )
    assert failed.status_code == 200
    assert failed.json()["data"]["status"] == "FAILED"
    assert client.get("/api/v1/subscriptions/me", headers=headers).json()["data"] == {
        "active": False,
        "subscription": None,
    }

    purchased = client.post(
        "/api/v1/payments/process",
        headers=headers,
        json={
            "subscription_plan": "STARTER",
            "card_number": SUCCESS_CARD,
        },
    )
    assert purchased.status_code == 200
    payment = purchased.json()["data"]
    assert payment["status"] == "SUCCEEDED"
    assert payment["amount"] == 89.99
    assert payment["subscription_id"] is not None

    active = client.get("/api/v1/subscriptions/me", headers=headers).json()["data"]
    assert active["active"] is True
    assert active["subscription"]["remaining_credits"] == 10

    upgraded = client.patch(
        "/api/v1/subscriptions/me",
        headers=headers,
        json={
            "subscription_plan": "PREMIUM",
            "card_number": SUCCESS_CARD,
        },
    )
    assert upgraded.status_code == 200
    assert upgraded.json()["data"]["subscription"]["plan_type"] == "PREMIUM"
    assert upgraded.json()["data"]["subscription"]["remaining_credits"] == 20

    cancelled = client.delete("/api/v1/subscriptions/me", headers=headers)
    assert cancelled.status_code == 204
    assert client.get("/api/v1/subscriptions/me", headers=headers).json()["data"] == {
        "active": False,
        "subscription": None,
    }
    history = client.get("/api/v1/payments/history", headers=headers)
    assert history.status_code == 200
    assert [payment["status"] for payment in history.json()["data"]] == [
        "SUCCEEDED",
        "SUCCEEDED",
        "FAILED",
    ]
