from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models.feed_event import FeedEvent
from app.models.feed_reversal import FeedReversal
from app.models.pond import Pond
from app.models.user import User
from app.schemas.feed_event import FeedEventCreate, FeedEventOut, FeedReversalCreate

router = APIRouter(prefix="/api/feed-events", tags=["feed-events"])


@router.get("", response_model=List[FeedEventOut])
def list_events(
    pond_id: Optional[int] = Query(None, alias="pondId"),
    valid_only: bool = Query(False, alias="validOnly"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    # 默认列表保留全部原始行（含已冲销）；validOnly=true 时仅返回未冲销的有效投喂。
    q = db.query(FeedEvent).options(selectinload(FeedEvent.reversal))
    if pond_id is not None:
        q = q.filter(FeedEvent.pond_id == pond_id)
    if valid_only:
        q = q.outerjoin(FeedReversal, FeedReversal.feed_event_id == FeedEvent.id).filter(
            FeedReversal.id.is_(None)
        )
    return q.order_by(FeedEvent.fed_at.desc()).all()


@router.post("", response_model=FeedEventOut, status_code=status.HTTP_201_CREATED)
def create_event(
    payload: FeedEventCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    pond = db.query(Pond).filter(Pond.id == payload.pond_id).first()
    if not pond:
        raise HTTPException(status_code=400, detail="塘口不存在")
    item = FeedEvent(
        pond_id=payload.pond_id,
        fed_at=payload.fed_at,
        feed_type=payload.feed_type,
        amount_kg=payload.amount_kg,
        operator_name=payload.operator_name,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post(
    "/{event_id}/reversal",
    response_model=FeedEventOut,
    status_code=status.HTTP_201_CREATED,
)
def reverse_event(
    event_id: int,
    payload: FeedReversalCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # 投喂不允许物理删除，错误记录以冲销凭证负向抵消。
    item = (
        db.query(FeedEvent)
        .options(selectinload(FeedEvent.reversal))
        .filter(FeedEvent.id == event_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="投喂记录不存在")
    if item.reversal is not None:
        raise HTTPException(status_code=400, detail="该投喂已冲销，不能重复冲销")
    if payload.amount_kg != item.amount_kg:
        raise HTTPException(status_code=400, detail="冲销千克必须等于原投喂千克")
    reversal = FeedReversal(
        feed_event_id=item.id,
        amount_kg=payload.amount_kg,
        reason=payload.reason,
        reversed_at=datetime.now(timezone.utc),
        operator_name=user.display_name,
    )
    db.add(reversal)
    db.commit()
    db.refresh(item)
    return item
