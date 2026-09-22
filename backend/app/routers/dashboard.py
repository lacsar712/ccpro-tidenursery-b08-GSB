from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

from app.auth import get_current_user
from app.database import get_db
from app.models.feed_event import FeedEvent
from app.models.pond import Pond
from app.models.user import User
from app.models.water_sample import WaterSample
from app.schemas.dashboard import DashboardStats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    pond_total = db.query(func.count(Pond.id)).scalar() or 0
    quarantine_count = (
        db.query(func.count(Pond.id)).filter(Pond.status == "quarantine").scalar() or 0
    )
    samples_last_24h = (
        db.query(func.count(WaterSample.id))
        .filter(WaterSample.sampled_at >= now - timedelta(hours=24))
        .scalar()
        or 0
    )
    # 近 7 日投喂千克按“有效投喂”口径：冲销凭证行与已被冲销的原投喂均不计入
    # （与投喂页“仅有效投喂”的合计完全一致，已冲销部分被全额扣除）。
    voucher = aliased(FeedEvent)
    feed_kg_last_7d = (
        db.query(func.coalesce(func.sum(FeedEvent.amount_kg), 0.0))
        .outerjoin(voucher, voucher.reversal_of_id == FeedEvent.id)
        .filter(
            FeedEvent.fed_at >= now - timedelta(days=7),
            FeedEvent.reversal_of_id.is_(None),
            voucher.id.is_(None),
        )
        .scalar()
        or 0.0
    )
    return DashboardStats(
        pond_total=pond_total,
        quarantine_count=quarantine_count,
        samples_last_24h=samples_last_24h,
        feed_kg_last_7d=float(feed_kg_last_7d),
    )
