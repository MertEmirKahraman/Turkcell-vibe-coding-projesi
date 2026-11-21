from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from backend.app.models import SubscriptionPlan


class PaymentRequest(BaseModel):
    subscription_plan: SubscriptionPlan
    card_number: str = Field(min_length=16, max_length=23)

    @field_validator("card_number")
    @classmethod
    def normalize_card_number(cls, value: str) -> str:
        normalized = value.replace("-", "").replace(" ", "")
        if not normalized.isdigit() or len(normalized) != 16:
            raise ValueError("Kart numarası 16 haneli olmalı")
        return normalized


class SubscriptionChangeRequest(PaymentRequest):
    pass


class PaymentStatus(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


PLAN_DETAILS = {
    SubscriptionPlan.STARTER: {
        "name": "Starter",
        "monthly_price": Decimal("89.99"),
        "monthly_credits": 10,
        "guest_credits": 0,
        "priority": False,
        "validity_days": 30,
    },
    SubscriptionPlan.PREMIUM: {
        "name": "Premium",
        "monthly_price": Decimal("149.99"),
        "monthly_credits": 20,
        "guest_credits": 2,
        "priority": False,
        "validity_days": 30,
    },
    SubscriptionPlan.UNLIMITED: {
        "name": "Unlimited",
        "monthly_price": Decimal("249.99"),
        "monthly_credits": None,
        "guest_credits": 5,
        "priority": True,
        "validity_days": 30,
    },
}
