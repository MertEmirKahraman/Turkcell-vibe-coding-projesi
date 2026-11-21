from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models import OrderStatus


class OrderCreateRequest(BaseModel):
    shop_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    size: Literal["S", "M", "L"] = "M"
    sugar_level: int = Field(default=0, ge=0, le=5)
    milk_preference: Literal["NONE", "WHOLE", "OAT", "LACTOSE_FREE"] = "WHOLE"
    extra_shots: int = Field(default=0, ge=0, le=3)


class OrderStatusUpdateRequest(BaseModel):
    status: OrderStatus


class QRCodePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str
    user_id: str
    shop_id: str
    created_at: datetime
    signature: str = Field(pattern=r"^[a-f0-9]{64}$")
