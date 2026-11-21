from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.core.settings import settings
from backend.app.db.session import get_db
from backend.app.models import User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


def create_token(
    user: User,
    token_type: Literal["access", "refresh"],
) -> str:
    now = datetime.now(timezone.utc)
    lifetime = (
        timedelta(minutes=settings.access_token_minutes)
        if token_type == "access"
        else timedelta(days=settings.refresh_token_days)
    )
    payload = {
        "sub": str(user.id),
        "phone_number": user.phone_number,
        "role": user.role.value,
        "token_type": token_type,
        "iat": now,
        "exp": now + lifetime,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Bearer token gerekli")

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("token_type") != "access":
            raise HTTPException(status_code=401, detail="Geçersiz erişim tokenı")
        user_id = int(payload["sub"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Geçersiz veya süresi dolmuş token")
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Geçersiz token içeriği")

    user = db.get(User, user_id)
    if user is None or not user.phone_verified:
        raise HTTPException(status_code=401, detail="Kullanıcı doğrulanmamış")
    return user


def get_current_shop_owner(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in (UserRole.SHOP_OWNER, UserRole.ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Bu işlem için dükkân sahibi yetkisi gerekli",
        )
    return current_user
