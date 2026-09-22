from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from app.auth import get_current_user
from app.database import get_db
from app.models.feed_event import FeedEvent
from app.models.pond import Pond
from app.models.user import User
from app.schemas.feed_event import FeedEventCreate, FeedEventOut, FeedEventReverse

router = APIRouter(prefix="/api/feed-events", tags=["feed-events"])


@router.get("", response_model=List[FeedEventOut])
def list_events(
    pond_id: Optional[int] = Query(None, alias="pondId"),
    valid_only: bool = Query(False, alias="validOnly"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """投喂列表。默认返回全部行（原投喂 + 冲销凭证，已冲销原行带 isReversed 标记）；
    validOnly=true 时仅返回有效投喂：排除冲销凭证与已冲销的原投喂。
    """
    q = db.query(FeedEvent)
    if pond_id is not None:
        q = q.filter(FeedEvent.pond_id == pond_id)
    if valid_only:
        voucher = aliased(FeedEvent)
        q = q.outerjoin(voucher, voucher.reversal_of_id == FeedEvent.id).filter(
            FeedEvent.reversal_of_id.is_(None),  # 排除冲销凭证行
            voucher.id.is_(None),  # 排除已被凭证冲销的原投喂
        )
    return q.order_by(FeedEvent.fed_at.desc(), FeedEvent.id.desc()).all()


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
    "/{event_id}/reverse",
    response_model=FeedEventOut,
    status_code=status.HTTP_201_CREATED,
)
def reverse_event(
    event_id: int,
    payload: FeedEventReverse,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """错误投喂不允许物理删除，通过冲销凭证负向抵消。

    - 冲销千克由服务端取自原投喂（凭证 amount_kg = -原 amount_kg），必然完全相等；
    - 同一原投喂只许冲销一次（DB 唯一约束兜底）；
    - 冲销凭证本身不允许再被冲销；
    - 操作人取当前登录用户，冲销时刻由服务端记录。
    """
    original = db.get(FeedEvent, event_id)
    if not original:
        raise HTTPException(status_code=404, detail="投喂记录不存在")
    if original.reversal_of_id is not None:
        raise HTTPException(status_code=400, detail="冲销凭证不能再次冲销")
    if original.reversal is not None:
        raise HTTPException(status_code=400, detail="该投喂已冲销，不能重复冲销")

    now = datetime.now(timezone.utc)
    voucher = FeedEvent(
        pond_id=original.pond_id,
        fed_at=now,
        feed_type=original.feed_type,
        amount_kg=-original.amount_kg,
        operator_name=current_user.display_name,
        reversal_of_id=original.id,
        reversal_reason=payload.reversal_reason,
        reversed_at=now,
        reversed_by=current_user.display_name,
    )
    db.add(voucher)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="该投喂已冲销，不能重复冲销")
    db.refresh(voucher)
    return voucher
