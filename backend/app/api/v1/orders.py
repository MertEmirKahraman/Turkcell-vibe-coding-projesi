from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from backend.app.core.security import get_current_shop_owner, get_current_user
from backend.app.db.session import get_db
from backend.app.models import (
    Order,
    OrderItem,
    OrderStatus,
    Product,
    Shop,
    SubscriptionPlan,
    Subscription,
    SubscriptionStatus,
    User,
    UserRole,
)
from backend.app.schemas.orders import (
    OrderCreateRequest,
    OrderStatusUpdateRequest,
    QRCodePayload,
)
from backend.app.services.orders import create_qr_payload, verify_qr_payload
from backend.app.services.subscriptions import get_active_subscription

router = APIRouter(prefix="/orders", tags=["orders"])

NEXT_ORDER_STATUS = {
    OrderStatus.PENDING: OrderStatus.ACCEPTED,
    OrderStatus.ACCEPTED: OrderStatus.PREPARING,
    OrderStatus.PREPARING: OrderStatus.READY,
    OrderStatus.READY: OrderStatus.DELIVERED,
}


def success(data: object) -> dict[str, object]:
    return {"success": True, "data": data, "error": None}


def order_response(order: Order, *, include_qr: bool) -> dict[str, object]:
    return {
        "id": order.id,
        "user_id": order.user_id,
        "shop_id": order.shop_id,
        "shop_name": order.shop.name,
        "status": order.status.value,
        "total_amount": float(order.total_amount),
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "items": [
            {
                "product_id": item.product_id,
                "product_name": item.product.name,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "customization": item.customization,
            }
            for item in order.items
        ],
        "qr_code": create_qr_payload(order) if include_qr else None,
    }


def get_order(db: Session, order_id: int) -> Order:
    order = db.scalar(
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.shop),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
    return order


def ensure_order_access(order: Order, user: User) -> None:
    is_shop_owner = (
        user.role == UserRole.SHOP_OWNER and order.shop.owner_id == user.id
    )
    if user.role != UserRole.ADMIN and order.user_id != user.id and not is_shop_owner:
        raise HTTPException(status_code=403, detail="Bu siparişi görüntüleme yetkiniz yok")


@router.post("")
def create_order(
    payload: OrderCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Sipariş yalnızca müşteri hesabıyla verilebilir")

    shop = db.get(Shop, payload.shop_id)
    if shop is None or not shop.is_active:
        raise HTTPException(status_code=404, detail="Dükkân bulunamadı veya aktif değil")
    product = db.scalar(
        select(Product).where(
            Product.id == payload.product_id,
            Product.shop_id == shop.id,
            Product.is_active.is_(True),
        )
    )
    if product is None:
        raise HTTPException(status_code=404, detail="Ürün bu dükkânın menüsünde bulunamadı")

    subscription = get_active_subscription(db, current_user.id)
    if subscription is None:
        raise HTTPException(
            status_code=403,
            detail="Aktif aboneliğiniz yok. Sipariş vermek için bir paket satın alın.",
        )

    if subscription.plan_type != SubscriptionPlan.UNLIMITED:
        now = datetime.now(timezone.utc)
        result = db.execute(
            update(Subscription)
            .where(
                Subscription.id == subscription.id,
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.expires_at > now,
                Subscription.remaining_credits > 0,
            )
            .values(
                remaining_credits=Subscription.remaining_credits - 1
            )
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Aboneliğinizin kahve hakkı kalmadı. Yeni dönem veya paket satın alın.",
            )

    order = Order(
        user_id=current_user.id,
        shop_id=shop.id,
        status=OrderStatus.PENDING,
        total_amount=product.price,
    )
    db.add(order)
    db.flush()
    db.add(
        OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=1,
            unit_price=product.price,
            customization={
                "size": payload.size,
                "sugar_level": payload.sugar_level,
                "milk_preference": payload.milk_preference,
                "extra_shots": payload.extra_shots,
            },
        )
    )
    db.commit()
    order = get_order(db, order.id)
    return success(order_response(order, include_qr=True))


@router.get("/history")
def order_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    orders = db.scalars(
        select(Order)
        .where(Order.user_id == current_user.id)
        .options(
            selectinload(Order.shop),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
        .order_by(Order.created_at.desc())
    ).all()
    return success([order_response(order, include_qr=True) for order in orders])


@router.get("/shop")
def shop_orders(
    order_status: OrderStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_shop_owner),
) -> dict[str, object]:
    query = (
        select(Order)
        .join(Shop, Order.shop_id == Shop.id)
        .options(
            selectinload(Order.shop),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
        .order_by(Order.created_at.desc())
    )
    if current_user.role != UserRole.ADMIN:
        query = query.where(Shop.owner_id == current_user.id)
    if order_status is not None:
        query = query.where(Order.status == order_status)
    orders = db.scalars(query).all()
    return success([order_response(order, include_qr=False) for order in orders])


@router.get("/{order_id}")
def get_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    order = get_order(db, order_id)
    ensure_order_access(order, current_user)
    return success(
        order_response(order, include_qr=order.user_id == current_user.id)
    )


@router.post("/{order_id}/verify-qr")
def verify_order_qr(
    order_id: int,
    payload: QRCodePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_shop_owner),
) -> dict[str, object]:
    order = get_order(db, order_id)
    if order.shop.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Bu dükkânın siparişlerini doğrulama yetkiniz yok")
    if order.status != OrderStatus.READY:
        raise HTTPException(status_code=409, detail="QR kod yalnızca hazır siparişte doğrulanabilir")
    if not verify_qr_payload(order, payload):
        raise HTTPException(status_code=400, detail="QR kod geçersiz veya siparişle eşleşmiyor")
    return success({"verified": True, "order_id": order.id})


@router.patch("/{order_id}/status")
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_shop_owner),
) -> dict[str, object]:
    order = get_order(db, order_id)
    if order.shop.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Bu dükkânın siparişlerini güncelleme yetkiniz yok")

    expected_status = NEXT_ORDER_STATUS.get(order.status)
    if payload.status != expected_status:
        next_name = expected_status.value if expected_status else "yok"
        raise HTTPException(
            status_code=409,
            detail=f"Geçersiz sipariş durumu geçişi. Beklenen sonraki durum: {next_name}",
        )
    if payload.status == OrderStatus.DELIVERED:
        raise HTTPException(
            status_code=409,
            detail="Teslimat için QR doğrulama endpoint'ini kullanın",
        )

    order.status = payload.status
    db.commit()
    db.refresh(order)
    order = get_order(db, order.id)
    return success(order_response(order, include_qr=False))


@router.post("/{order_id}/redeem")
def redeem_order(
    order_id: int,
    payload: QRCodePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_shop_owner),
) -> dict[str, object]:
    order = get_order(db, order_id)
    if order.shop.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Bu dükkânın siparişlerini teslim etme yetkiniz yok")
    if order.status != OrderStatus.READY:
        raise HTTPException(status_code=409, detail="Yalnızca hazır sipariş teslim edilebilir")
    if not verify_qr_payload(order, payload):
        raise HTTPException(status_code=400, detail="QR kod geçersiz veya siparişle eşleşmiyor")

    order.status = OrderStatus.DELIVERED
    db.commit()
    db.refresh(order)
    order = get_order(db, order.id)
    return success(order_response(order, include_qr=False))
