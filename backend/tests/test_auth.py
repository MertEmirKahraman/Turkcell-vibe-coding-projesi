from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_register_verify_profile_and_refresh() -> None:
    phone = "05559990001"

    register = client.post(
        "/api/v1/auth/register",
        json={"phone_number": phone, "full_name": "OTP Test Kullanıcısı"},
    )
    assert register.status_code == 200
    assert register.json()["data"]["otp_simulation"] == "1234"

    verified = client.post(
        "/api/v1/auth/verify-otp",
        json={"phone_number": phone, "otp_code": "1234"},
    )
    assert verified.status_code == 200
    payload = verified.json()["data"]
    assert payload["token_type"] == "bearer"
    assert payload["user"]["role"] == "CUSTOMER"
    assert payload["user"]["phone_verified"] is True

    headers = {"Authorization": f"Bearer {payload['access_token']}"}
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["data"]["profile_completed"] is True

    refreshed = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": payload["refresh_token"]},
    )
    assert refreshed.status_code == 200
    assert "access_token" in refreshed.json()["data"]


def test_wrong_otp_is_rejected() -> None:
    register = client.post(
        "/api/v1/auth/register",
        json={"phone_number": "05559990002"},
    )
    assert register.status_code == 200

    response = client.post(
        "/api/v1/auth/verify-otp",
        json={"phone_number": "05559990002", "otp_code": "1111"},
    )
    assert response.status_code == 400
