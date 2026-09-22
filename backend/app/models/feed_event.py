from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FeedEvent(Base):
    __tablename__ = "feed_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pond_id: Mapped[int] = mapped_column(ForeignKey("ponds.id"), nullable=False, index=True)
    fed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    feed_type: Mapped[str] = mapped_column(String(64), nullable=False)
    amount_kg: Mapped[float] = mapped_column(Float, nullable=False)
    operator_name: Mapped[str] = mapped_column(String(64), nullable=False)

    # 冲销凭证：本行作为某笔原投喂的负向冲销凭证时，reversal_of_id 指向原投喂。
    # 同一原投喂只许冲销一次（唯一约束）；凭证本身不允许再被冲销。
    reversal_of_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("feed_events.id"), unique=True, nullable=True, index=True
    )
    reversal_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    reversed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reversed_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    pond: Mapped["Pond"] = relationship("Pond", back_populates="feed_events")

    # 自引用关系：凭证 .original -> 原投喂；原投喂 .reversal -> 冲销凭证（None 表示未冲销）
    original: Mapped[Optional["FeedEvent"]] = relationship(
        "FeedEvent",
        remote_side=[id],
        foreign_keys=[reversal_of_id],
        back_populates="reversal",
    )
    reversal: Mapped[Optional["FeedEvent"]] = relationship(
        "FeedEvent",
        foreign_keys=[reversal_of_id],
        back_populates="original",
        uselist=False,
    )

    @property
    def is_reversed(self) -> bool:
        """原投喂是否已被冲销。"""
        return self.reversal is not None
