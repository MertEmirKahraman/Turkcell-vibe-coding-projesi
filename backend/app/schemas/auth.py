from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.models import UserRole


class RegisterRequest(BaseModel):
    phone_number: str = Field(min_length=10, max_length=15)
    full_name: str | None = Field(default=None, max_length=100)
    email: str | None = None
    preferences: dict[str, object] | None = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        digits = "".join(character for character in value if character.isdigit())
        if len(digits) not in (10, 11):
            raise ValueError("GSM numarası 10 veya 11 haneli olmalı")
        return digits


class PhoneRequest(BaseModel):
    phone_number: str = Field(min_length=10, max_length=15)

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        digits = "".join(character for character in value if character.isdigit())
        if len(digits) not in (10, 11):
            raise ValueError("GSM numarası 10 veya 11 haneli olmalı")
        return digits


class VerifyOTPRequest(PhoneRequest):
    otp_code: str = Field(pattern=r"^\d{4}$")


class RefreshRequest(BaseModel):
    refresh_token: str


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=100)
    email: str | None = None
    preferences: dict[str, object] | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    phone_number: str
    full_name: str | None
    email: str | None
    role: UserRole
    preferences: dict[str, object] | None
    phone_verified: bool
    profile_completed: bool = False
