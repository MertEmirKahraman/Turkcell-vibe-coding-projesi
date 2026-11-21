from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.security import create_token, get_current_user
from backend.app.core.settings import settings
from backend.app.db.session import get_db
from backend.app.models import OTPVerification, User, UserRole
from backend.app.schemas.auth import (
    PhoneRequest,
    ProfileUpdateRequest,
    RefreshRequest,
    RegisterRequest,
    UserResponse,
    VerifyOTPRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])
SIMULATED_OTP = "1234"


def success(data: object) -> dict[str, object]:
    return {"success": True, "data": data, "error": None}


def user_response(user: User) -> dict[str, object]:
    return {
        "id": user.id,
        "phone_number": user.phone_number,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role.value,
        "preferences": user.preferences,
        "phone_verified": user.phone_verified,
        "profile_completed": bool((user.full_name or "").strip()),
    }


def create_otp(db: Session, phone_number: str) -> OTPVerification:
    active_otps = db.scalars(
        select(OTPVerification).where(
            OTPVerification.phone_number == phone_number,
            OTPVerification.consumed.is_(False),
        )
    ).all()
    for otp in active_otps:
        otp.consumed = True

    otp = OTPVerification(
        phone_number=phone_number,
        code=SIMULATED_OTP,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    db.add(otp)
    db.commit()
    return otp


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    user = db.scalar(select(User).where(User.phone_number == payload.phone_number))
    if user is None:
        user = User(
            phone_number=payload.phone_number,
            full_name=payload.full_name or "",
            email=str(payload.email) if payload.email else None,
            role=UserRole.CUSTOMER,
            preferences=payload.preferences,
            phone_verified=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif payload.full_name or payload.email or payload.preferences:
        if payload.full_name:
            user.full_name = payload.full_name
        if payload.email:
            user.email = str(payload.email)
        if payload.preferences:
            user.preferences = payload.preferences
        db.commit()

    otp = create_otp(db, payload.phone_number)
    return success({
        "message": "OTP gönderildi",
        "phone_number": payload.phone_number,
        "otp_simulation": SIMULATED_OTP,
        "expires_at": otp.expires_at,
    })


@router.post("/login")
def login(payload: PhoneRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    user = db.scalar(select(User).where(User.phone_number == payload.phone_number))
    if user is None:
        raise HTTPException(status_code=404, detail="Bu GSM numarasıyla kayıtlı kullanıcı bulunamadı")

    otp = create_otp(db, payload.phone_number)
    return success({
        "message": "OTP gönderildi",
        "phone_number": payload.phone_number,
        "otp_simulation": SIMULATED_OTP,
        "expires_at": otp.expires_at,
    })


@router.post("/verify-otp")
def verify_otp(payload: VerifyOTPRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    otp = db.scalar(
        select(OTPVerification)
        .where(
            OTPVerification.phone_number == payload.phone_number,
            OTPVerification.code == payload.otp_code,
            OTPVerification.consumed.is_(False),
        )
        .order_by(OTPVerification.created_at.desc())
    )
    now = datetime.now(timezone.utc)
    if otp is None or otp.expires_at.replace(tzinfo=timezone.utc) <= now:
        raise HTTPException(status_code=400, detail="OTP geçersiz veya süresi dolmuş")

    otp.consumed = True
    user = db.scalar(select(User).where(User.phone_number == payload.phone_number))
    if user is None:
        db.commit()
        raise HTTPException(status_code=404, detail="Önce kayıt olmalısınız")

    user.phone_verified = True
    db.commit()
    db.refresh(user)

    return success({
        "access_token": create_token(user, "access"),
        "refresh_token": create_token(user, "refresh"),
        "token_type": "bearer",
        "user": user_response(user),
    })


@router.post("/refresh")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        claims = jwt.decode(
            payload.refresh_token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        if claims.get("token_type") != "refresh":
            raise HTTPException(status_code=401, detail="Geçersiz refresh token")
        user = db.get(User, int(claims["sub"]))
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Geçersiz veya süresi dolmuş refresh token")
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Geçersiz refresh token")

    if user is None or not user.phone_verified:
        raise HTTPException(status_code=401, detail="Kullanıcı doğrulanmamış")

    return success({
        "access_token": create_token(user, "access"),
        "refresh_token": create_token(user, "refresh"),
        "token_type": "bearer",
    })


@router.get("/me")
def me(
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    return success(user_response(current_user))


@router.patch("/me")
def update_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.email is not None:
        current_user.email = str(payload.email)
    if payload.preferences is not None:
        current_user.preferences = payload.preferences
    db.commit()
    db.refresh(current_user)
    return success(user_response(current_user))
