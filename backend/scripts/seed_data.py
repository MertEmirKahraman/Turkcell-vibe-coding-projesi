from datetime import datetime, timedelta, timezone
from decimal import Decimal

from pwdlib import PasswordHash
from sqlalchemy import select

from backend.app.db.session import init_db, SessionLocal
from backend.app.models import (
    Product,
    Shop,
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    User,
    UserRole,
)


SEED_PHONE = "05551234567"
SEED_PASSWORD = "Kahve123!"
SHOP_OWNER_PHONE = "05557654321"

SHOPS = [
    {
        "name": "KahveCell Kızılay",
        "address": "Meşrutiyet Mah., Kızılay, Çankaya/Ankara",
        "latitude": Decimal("39.919870"),
        "longitude": Decimal("32.853241"),
    },
    {
        "name": "KahveCell Çankaya",
        "address": "Yıldız Mah., Çankaya/Ankara",
        "latitude": Decimal("39.898330"),
        "longitude": Decimal("32.864250"),
    },
    {
        "name": "KahveCell Bahçelievler",
        "address": "Seyranbağları Mah., Bahçelievler, Çankaya/Ankara",
        "latitude": Decimal("39.932010"),
        "longitude": Decimal("32.827310"),
    },
    {
        "name": "KahveCell Çayyolu",
        "address": "Çayyolu Mah., Çankaya/Ankara",
        "latitude": Decimal("39.883920"),
        "longitude": Decimal("32.704160"),
    },
    {
        "name": "KahveCell Tunalı",
        "address": "Kavaklıdere Mah., Tunalı Hilmi Caddesi, Çankaya/Ankara",
        "latitude": Decimal("39.905690"),
        "longitude": Decimal("32.858520"),
    },
]

PRODUCTS = [
    ("Espresso", "Yoğun ve dengeli tek shot espresso", "75.00", 100),
    ("Cappuccino", "Espresso, buharlanmış süt ve süt köpüğü", "105.00", 100),
    ("Türk Kahvesi", "Geleneksel usulle pişirilmiş Türk kahvesi", "85.00", 100),
    ("Americano", "Espresso ve sıcak su", "95.00", 100),
    ("Latte", "Espresso ve bol sütlü yumuşak içim", "115.00", 100),
]


def main() -> None:
    init_db()
    password_hash = PasswordHash.recommended().hash(SEED_PASSWORD)
    now = datetime.now(timezone.utc)

    with SessionLocal() as session:
        user = session.scalar(
            select(User).where(User.phone_number == SEED_PHONE)
        )
        if user is None:
            user = User(
                phone_number=SEED_PHONE,
                full_name="Test Kullanıcısı",
                email="test@kahvecell.local",
                password_hash=password_hash,
                role=UserRole.CUSTOMER,
                phone_verified=True,
                preferences={
                    "coffee": "latte",
                    "allergens": [],
                    "size": "medium",
                },
                created_at=now,
            )
            session.add(user)
            session.flush()
        else:
            user.password_hash = password_hash
            user.full_name = "Test Kullanıcısı"
            user.email = "test@kahvecell.local"
            user.role = UserRole.CUSTOMER
            user.phone_verified = True

        shop_owner = session.scalar(
            select(User).where(User.phone_number == SHOP_OWNER_PHONE)
        )
        if shop_owner is None:
            shop_owner = User(
                phone_number=SHOP_OWNER_PHONE,
                full_name="Test Dükkân Sahibi",
                email="shopowner@kahvecell.local",
                role=UserRole.SHOP_OWNER,
                phone_verified=True,
            )
            session.add(shop_owner)
            session.flush()
        else:
            shop_owner.full_name = "Test Dükkân Sahibi"
            shop_owner.email = "shopowner@kahvecell.local"
            shop_owner.role = UserRole.SHOP_OWNER
            shop_owner.phone_verified = True

        subscription = session.scalar(
            select(Subscription).where(
                Subscription.user_id == user.id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
        )
        if subscription is None:
            session.add(
                Subscription(
                    user_id=user.id,
                    plan_type=SubscriptionPlan.STARTER,
                    remaining_credits=10,
                    status=SubscriptionStatus.ACTIVE,
                    started_at=now,
                    expires_at=now + timedelta(days=30),
                )
            )

        shop_count = 0
        product_count = 0
        for shop_data in SHOPS:
            shop = session.scalar(
                select(Shop).where(Shop.name == shop_data["name"])
            )
            if shop is None:
                shop = Shop(
                    owner_id=shop_owner.id,
                    name=shop_data["name"],
                    address=shop_data["address"],
                    latitude=shop_data["latitude"],
                    longitude=shop_data["longitude"],
                    is_active=True,
                    created_at=now,
                )
                session.add(shop)
                session.flush()
                shop_count += 1
            else:
                shop.owner_id = shop_owner.id

            for name, description, price, stock in PRODUCTS:
                product = session.scalar(
                    select(Product).where(
                        Product.shop_id == shop.id,
                        Product.name == name,
                    )
                )
                if product is None:
                    session.add(
                        Product(
                            shop_id=shop.id,
                            name=name,
                            description=description,
                            price=Decimal(price),
                            stock_quantity=stock,
                            is_active=True,
                        )
                    )
                    product_count += 1

        session.commit()

    print("Seed tamamlandı.")
    print(f"Test telefon: {SEED_PHONE}")
    print(f"Test şifre: {SEED_PASSWORD}")
    print(f"Eklenen dükkân: {shop_count}")
    print(f"Eklenen ürün: {product_count}")


if __name__ == "__main__":
    main()
