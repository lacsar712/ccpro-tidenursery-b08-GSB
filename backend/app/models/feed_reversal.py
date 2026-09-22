from datetime import datetime

from sqlalchemy import String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FeedReversal(Base):
    """冲销凭证：负向抵消一笔错误投喂，原投喂记录保留不删除。"""

    __tablename__ = "feed_reversals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    feed_event_id: Mapped[int] = mapped_column(
        ForeignKey("feed_events.id"), nullable=False, unique=True, index=True
    )
    amount_kg: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    reversed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    operator_name: Mapped[str] = mapped_column(String(64), nullable=False)

    feed_event: Mapped["FeedEvent"] = relationship("FeedEvent", back_populates="reversal")
