from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FeedEventCreate(BaseModel):
    pond_id: int = Field(..., alias="pondId")
    fed_at: datetime = Field(..., alias="fedAt")
    feed_type: str = Field(..., min_length=1, max_length=64, alias="feedType")
    amount_kg: float = Field(..., gt=0, alias="amountKg")
    operator_name: str = Field(..., min_length=1, max_length=64, alias="operatorName")

    model_config = ConfigDict(populate_by_name=True)


class FeedEventReverse(BaseModel):
    """冲销请求：只需填写原因。冲销千克由服务端取自原投喂，保证完全相等。"""

    reversal_reason: str = Field(..., min_length=6, max_length=200, alias="reason")

    model_config = ConfigDict(populate_by_name=True)


class FeedEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    pond_id: int = Field(serialization_alias="pondId")
    fed_at: datetime = Field(serialization_alias="fedAt")
    feed_type: str = Field(serialization_alias="feedType")
    amount_kg: float = Field(serialization_alias="amountKg")
    operator_name: str = Field(serialization_alias="operatorName")

    # 冲销凭证字段：普通投喂行为空；冲销凭证行携带原投喂编号 / 冲销千克(=负的原量) / 原因 / 冲销时刻 / 操作人
    reversal_of_id: Optional[int] = Field(default=None, serialization_alias="reversalOfId")
    reversal_reason: Optional[str] = Field(default=None, serialization_alias="reversalReason")
    reversed_at: Optional[datetime] = Field(default=None, serialization_alias="reversedAt")
    reversed_by: Optional[str] = Field(default=None, serialization_alias="reversedBy")
    is_reversed: bool = Field(default=False, serialization_alias="isReversed")
