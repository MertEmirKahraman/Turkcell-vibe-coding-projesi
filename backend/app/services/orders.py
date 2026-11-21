import hashlib
import hmac
import json
from datetime import datetime, timezone

from backend.app.core.settings import settings
from backend.app.models import Order
from backend.app.schemas.orders import QRCodePayload


def qr_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


def qr_unsigned_payload(order: Order) -> dict[str, str]:
    return {
        "order_id": str(order.id),
        "user_id": str(order.user_id),
        "shop_id": str(order.shop_id),
        "created_at": qr_timestamp(order.created_at),
    }


def qr_signature(payload: dict[str, str]) -> str:
    canonical_payload = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hmac.new(
        settings.qr_signing_secret.encode("utf-8"),
        canonical_payload,
        hashlib.sha256,
    ).hexdigest()


def create_qr_payload(order: Order) -> dict[str, str]:
    payload = qr_unsigned_payload(order)
    return {
        **payload,
        "signature": qr_signature(payload),
    }


def verify_qr_payload(order: Order, qr_payload: QRCodePayload) -> bool:
    unsigned_payload = {
        "order_id": qr_payload.order_id,
        "user_id": qr_payload.user_id,
        "shop_id": qr_payload.shop_id,
        "created_at": qr_timestamp(qr_payload.created_at),
    }
    expected_signature = qr_signature(unsigned_payload)
    return (
        hmac.compare_digest(qr_payload.signature, expected_signature)
        and unsigned_payload == qr_unsigned_payload(order)
    )
