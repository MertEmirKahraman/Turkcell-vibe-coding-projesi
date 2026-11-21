from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_user
from backend.app.db.session import get_db
from backend.app.models import PaymentTransaction, User
from backend.app.schemas.subscriptions import PaymentRequest
from backend.app.services.subscriptions import process_subscription_payment

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/history")
def payment_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    transactions = db.scalars(
        select(PaymentTransaction)
        .where(PaymentTransaction.user_id == current_user.id)
        .order_by(PaymentTransaction.created_at.desc())
    ).all()
    return {
        "success": True,
        "data": [
            {
                "transaction_id": transaction.transaction_id,
                "subscription_plan": transaction.plan_type.value,
                "amount": float(transaction.amount),
                "status": transaction.status,
                "timestamp": transaction.created_at,
                "subscription_id": transaction.subscription_id,
            }
            for transaction in transactions
        ],
        "error": None,
    }


@router.post("/process")
def process_payment(
    payload: PaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    result = process_subscription_payment(
        db,
        current_user,
        payload.subscription_plan,
        payload.card_number,
    )
    subscription = result.pop("subscription")
    if subscription is not None:
        result["subscription_id"] = subscription.id
    return {"success": True, "data": result, "error": None}
