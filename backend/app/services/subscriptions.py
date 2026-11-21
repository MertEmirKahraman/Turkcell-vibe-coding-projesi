from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import (
    PaymentTransaction,
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    User,
)
from backend.app.schemas.subscriptions import PLAN_DETAILS

PAYMENT_SUCCESS_CARD = "4242424242424242"
PAYMENT_FAILURE_CARD = "4000000000000002"


def get_active_subscription(db: Session, user_id: int) -> Subscription | None:
    now = datetime.now(timezone.utc)
    return db.scalar(
        select(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.expires_at > now,
        )
        .order_by(Subscription.started_at.desc())
    )


def process_subscription_payment(
    db: Session,
    user: User,
    plan: SubscriptionPlan,
    card_number: str,
) -> dict[str, object]:
    transaction_id = str(uuid4())
    amount = PLAN_DETAILS[plan]["monthly_price"]
    payment_succeeded = card_number == PAYMENT_SUCCESS_CARD
    subscription: Subscription | None = None

    if payment_succeeded:
        now = datetime.now(timezone.utc)
        existing = get_active_subscription(db, user.id)
        if existing is not None:
            existing.status = SubscriptionStatus.CANCELLED

        plan_details = PLAN_DETAILS[plan]
        subscription = Subscription(
            user_id=user.id,
            plan_type=plan,
            remaining_credits=plan_details["monthly_credits"] or 0,
            status=SubscriptionStatus.ACTIVE,
            started_at=now,
            expires_at=now + timedelta(days=plan_details["validity_days"]),
        )
        db.add(subscription)
        db.flush()

    transaction = PaymentTransaction(
        transaction_id=transaction_id,
        user_id=user.id,
        subscription_id=subscription.id if subscription else None,
        plan_type=plan,
        amount=amount,
        status="SUCCEEDED" if payment_succeeded else "FAILED",
    )
    db.add(transaction)
    db.commit()
    if subscription is not None:
        db.refresh(subscription)

    return {
        "status": transaction.status,
        "transaction_id": transaction.transaction_id,
        "subscription_plan": plan.value,
        "amount": float(amount),
        "timestamp": transaction.created_at,
        "subscription": subscription,
    }
