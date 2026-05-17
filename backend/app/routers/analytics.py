from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Post, PostMetric, Reminder
from app.schemas import OverviewRead

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=OverviewRead)
def overview(db: Session = Depends(get_db)) -> OverviewRead:
    week_start = datetime.utcnow() - timedelta(days=7)
    draft_count = db.scalar(select(func.count(Post.id)).where(Post.status == "draft")) or 0
    pending_metrics_count = (
        db.scalar(select(func.count(Reminder.id)).where(Reminder.status == "pending", Reminder.remind_at <= datetime.utcnow())) or 0
    )
    published_this_week_count = (
        db.scalar(select(func.count(Post.id)).where(Post.published_at.is_not(None), Post.published_at >= week_start)) or 0
    )
    avg_interaction = db.scalar(select(func.avg(PostMetric.interaction_rate))) or 0
    avg_collect = db.scalar(select(func.avg(PostMetric.collect_rate))) or 0

    best_metric = db.scalars(select(PostMetric).order_by(PostMetric.interaction_rate.desc()).limit(1)).first()
    best_post = None
    if best_metric:
        post = db.get(Post, best_metric.post_id)
        best_post = {
            "post_id": best_metric.post_id,
            "title": post.selected_title if post else "未命名帖子",
            "views": best_metric.views,
            "likes": best_metric.likes,
            "collects": best_metric.collects,
            "comments": best_metric.comments,
            "followers_gained": best_metric.followers_gained,
            "interaction_rate": float(best_metric.interaction_rate),
            "collect_rate": float(best_metric.collect_rate),
        }

    return OverviewRead(
        draft_count=draft_count,
        pending_metrics_count=pending_metrics_count,
        published_this_week_count=published_this_week_count,
        average_interaction_rate=float(avg_interaction or 0),
        average_collect_rate=float(avg_collect or 0),
        best_post=best_post,
        next_suggestion="优先处理到期数据录入；若草稿超过 2 篇，先发布最完整的一篇，再准备下一期 3-5 个产品横评。",
    )

