from math import asin, cos, radians, sin, sqrt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.session import get_db
from backend.app.models import Shop

router = APIRouter(prefix="/shops", tags=["shops"])
EARTH_RADIUS_KM = 6371.0088


def success(data: object) -> dict[str, object]:
    return {"success": True, "data": data, "error": None}


def distance_in_km(
    latitude: float,
    longitude: float,
    shop_latitude: float,
    shop_longitude: float,
) -> float:
    latitude_delta = radians(shop_latitude - latitude)
    longitude_delta = radians(shop_longitude - longitude)
    a = (
        sin(latitude_delta / 2) ** 2
        + cos(radians(latitude))
        * cos(radians(shop_latitude))
        * sin(longitude_delta / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * asin(sqrt(min(1.0, a)))


def shop_summary(shop: Shop, distance_km: float | None) -> dict[str, object]:
    return {
        "id": shop.id,
        "name": shop.name,
        "address": shop.address,
        "latitude": float(shop.latitude) if shop.latitude is not None else None,
        "longitude": float(shop.longitude) if shop.longitude is not None else None,
        "is_active": shop.is_active,
        "distance_km": round(distance_km, 2) if distance_km is not None else None,
    }


@router.get("")
def list_shops(
    search: str | None = Query(default=None, min_length=1, max_length=100),
    latitude: float | None = Query(default=None, ge=-90, le=90),
    longitude: float | None = Query(default=None, ge=-180, le=180),
    radius_km: float | None = Query(default=None, gt=0, le=500),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if (latitude is None) != (longitude is None):
        raise HTTPException(
            status_code=422,
            detail="latitude ve longitude birlikte gönderilmelidir",
        )
    if radius_km is not None and latitude is None:
        raise HTTPException(
            status_code=422,
            detail="radius_km kullanmak için latitude ve longitude gereklidir",
        )

    shops = db.scalars(
        select(Shop)
        .where(Shop.is_active.is_(True))
        .options(selectinload(Shop.products))
        .order_by(Shop.id)
    ).all()
    query = search.strip().casefold() if search else None
    result: list[tuple[Shop, float | None]] = []
    for shop in shops:
        if query and query not in f"{shop.name} {shop.address or ''}".casefold():
            continue

        distance = None
        if latitude is not None and longitude is not None:
            if shop.latitude is None or shop.longitude is None:
                continue
            distance = distance_in_km(
                latitude,
                longitude,
                float(shop.latitude),
                float(shop.longitude),
            )
            if radius_km is not None and distance > radius_km:
                continue
        result.append((shop, distance))

    if latitude is not None and longitude is not None:
        result.sort(key=lambda item: item[1] if item[1] is not None else float("inf"))

    return success(
        [
            {
                **shop_summary(shop, distance),
                "product_count": sum(product.is_active for product in shop.products),
            }
            for shop, distance in result
        ]
    )


@router.get("/{shop_id}")
def get_shop_detail(
    shop_id: int,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    shop = db.scalar(
        select(Shop)
        .where(Shop.id == shop_id, Shop.is_active.is_(True))
        .options(selectinload(Shop.products))
    )
    if shop is None:
        raise HTTPException(status_code=404, detail="Dükkân bulunamadı")

    products = [
        {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": float(product.price),
        }
        for product in shop.products
        if product.is_active
    ]
    return success({**shop_summary(shop, None), "menu": products})
