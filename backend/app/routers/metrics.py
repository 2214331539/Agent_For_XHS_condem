from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import Post, PostMetric, Product
from app.schemas import MetricCreate, MetricRead
from app.services.agent import agent_service

router = APIRouter(prefix="/posts/{post_id}", tags=["metrics"])


def calculate_rates(payload: MetricCreate) -> dict[str, Decimal]:
    if payload.views <= 0:
        return {"interaction_rate": Decimal("0"), "collect_rate": Decimal("0"), "follower_rate": Decimal("0")}
    views = Decimal(payload.views)
    return {
        "interaction_rate": Decimal(payload.likes + payload.collects + payload.comments) / views,
        "collect_rate": Decimal(payload.collects) / views,
        "follower_rate": Decimal(payload.followers_gained) / views,
    }


@router.post("/metrics", response_model=MetricRead)
def create_metric(post_id: str, payload: MetricCreate, db: Session = Depends(get_db)) -> PostMetric:
    post = db.scalars(select(Post).options(selectinload(Post.products).selectinload(Product.images)).where(Post.id == post_id)).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    rates = calculate_rates(payload)
    metric = PostMetric(
        post_id=post_id,
        views=payload.views,
        likes=payload.likes,
        collects=payload.collects,
        comments=payload.comments,
        followers_gained=payload.followers_gained,
        **rates,
    )
    if payload.analyze:
        analysis = agent_service.analyze_metrics(post, {**payload.model_dump(), **rates})
        metric.analysis_result = analysis["text"]
        metric.analysis_json = analysis
        post.status = "analyzed"
        post.analyzed_at = datetime.utcnow()
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


@router.get("/metrics", response_model=list[MetricRead])
def list_metrics(post_id: str, db: Session = Depends(get_db)) -> list[PostMetric]:
    stmt = select(PostMetric).where(PostMetric.post_id == post_id).order_by(PostMetric.recorded_at.desc())
    return list(db.scalars(stmt).all())


@router.post("/analyze", response_model=MetricRead)
def analyze_latest_metric(post_id: str, db: Session = Depends(get_db)) -> PostMetric:
    post = db.scalars(select(Post).where(Post.id == post_id)).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    metric = db.scalars(select(PostMetric).where(PostMetric.post_id == post_id).order_by(PostMetric.recorded_at.desc())).first()
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    analysis = agent_service.analyze_metrics(
        post,
        {
            "views": metric.views,
            "interaction_rate": metric.interaction_rate,
            "collect_rate": metric.collect_rate,
            "follower_rate": metric.follower_rate,
        },
    )
    metric.analysis_result = analysis["text"]
    metric.analysis_json = analysis
    post.status = "analyzed"
    post.analyzed_at = datetime.utcnow()
    db.commit()
    db.refresh(metric)
    return metric


@router.get("/analysis", response_model=MetricRead)
def get_analysis(post_id: str, db: Session = Depends(get_db)) -> PostMetric:
    metric = db.scalars(
        select(PostMetric)
        .where(PostMetric.post_id == post_id, PostMetric.analysis_result.is_not(None))
        .order_by(PostMetric.recorded_at.desc())
    ).first()
    if not metric:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return metric

