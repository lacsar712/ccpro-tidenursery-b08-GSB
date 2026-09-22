from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FeedEventCreate(BaseModel):
    pond_id: int = Field(..., alias="pondId")
    fed_at: datetime = Field(..., alias="fedAt")
    feed_type: str = Field(..., min_length=1, max_length=64, alias="feedType")
    amount_kg: float = Field(..., gt=0, alias="amountKg")
    operator_name: str = Field(..., min_length=1, max_length=64, alias="operatorName")

    model_config = ConfigDict(populate_by_name=True)


class FeedReversalCreate(BaseModel):
    amount_kg: float = Field(..., gt=0, alias="amountKg")
    reason: str = Field(..., min_length=6, max_length=200, alias="reason")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("reason")
    @classmethod
    def reason_not_blank(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 6:
            raise ValueError("冲销原因至少 6 字")
        return v


class FeedReversalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    feed_event_id: int = Field(serialization_alias="feedEventId")
    amount_kg: float = Field(serialization_alias="amountKg")
    reason: str = Field(serialization_alias="reason")
    reversed_at: datetime = Field(serialization_alias="reversedAt")
    operator_name: str = Field(serialization_alias="operatorName")


class FeedEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    pond_id: int = Field(serialization_alias="pondId")
    fed_at: datetime = Field(serialization_alias="fedAt")
    feed_type: str = Field(serialization_alias="feedType")
    amount_kg: float = Field(serialization_alias="amountKg")
    operator_name: str = Field(serialization_alias="operatorName")
    reversal: Optional[FeedReversalOut] = Field(
        default=None, serialization_alias="reversal"
    )
