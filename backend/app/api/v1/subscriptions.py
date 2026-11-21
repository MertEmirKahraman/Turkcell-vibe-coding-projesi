from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_user
from backend.app.db.session import get_db
from backend.app.models import PaymentTransaction, Subscription, SubscriptionStatus, User
from backend.app.schemas.subscriptions import PLAN_DETAILS, SubscriptionChangeRequest
from backend.app.services.subscriptions import get_active_subscription

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


def success(data: object) -> dict[str, object]:
    return {"success": True, "data": data, "error": None}


def subscription_response(subscription: Subscription) -> dict[str, object]:
    details = PLAN_DETAILS[subscription.plan_type]
    return {
        "id": subscription.id,
        "plan_type": subscription.plan_type.value,
        "plan_name": details["name"],
        "monthly_price": float(details["monthly_price"]),
        "monthly_credits": details["monthly_credits"],
        "remaining_credits": (
            None if details["monthly_credits"] is None
            else subscription.remaining_credits
        ),
        "guest_credits": details["guest_credits"],
        "priority": details["priority"],
        "status": subscription.status.value,
        "started_at": subscription.started_at,
        "expires_at": subscription.expires_at,
    }


@router.get("/plans")
def list_plans() -> dict[str, object]:
    plans = [
        {
            "plan_type": plan.value,
            **details,
            "monthly_price": float(details["monthly_price"]),
        }
        for plan, details in PLAN_DETAILS.items()
    ]
    return success(plans)


@router.get("/me")
def get_my_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    subscription = get_active_subscription(db, current_user.id)
    if subscription is None:
        return success({"active": False, "subscription": None})
    return success(
        {"active": True, "subscription": subscription_response(subscription)}
    )


@router.patch("/me")
def change_subscription(
    payload: SubscriptionChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    active = get_active_subscription(db, current_user.id)
    if active is None:
        raise HTTPException(
            status_code=404,
            detail="Aktif abonelik bulunamadı; önce paket satın alın",
        )
    if active.plan_type == payload.subscription_plan:
        raise HTTPException(status_code=409, detail="Bu paket zaten aktif")

    from backend.app.services.subscriptions import process_subscription_payment

    payment = process_subscription_payment(
        db,
        current_user,
        payload.subscription_plan,
        payload.card_number,
    )
    if payment["status"] == "FAILED":
        return success({
            "payment": {key: value for key, value in payment.items() if key != "subscription"},
            "subscription_changed": False,
        })
    subscription = payment["subscription"]
    return success({
        "payment": {key: value for key, value in payment.items() if key != "subscription"},
        "subscription_changed": True,
        "subscription": subscription_response(subscription),
    })


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def cancel_subscription(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    subscription = get_active_subscription(db, current_user.id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="Aktif abonelik bulunamadı")
    subscription.status = SubscriptionStatus.CANCELLED
    db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT
