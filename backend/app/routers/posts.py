from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.db.session import get_db
from app.models import Post, Product, Reminder
from app.schemas import PostCreate, PostRead, PostUpdate
from app.services.agent import agent_service

router = APIRouter(prefix="/posts", tags=["posts"])


def post_query():
    return select(Post).options(selectinload(Post.products).selectinload(Product.images))


@router.post("", response_model=PostRead)
def create_post(payload: PostCreate, db: Session = Depends(get_db)) -> Post:
    post = Post(
        image_style_preset_id=payload.image_style_preset_id,
        image_custom_prompt=payload.image_custom_prompt,
        image_custom_params=payload.image_custom_params,
        copy_style_preset_id=payload.copy_style_preset_id,
        copy_custom_prompt=payload.copy_custom_prompt,
        copy_custom_params=payload.copy_custom_params,
    )
    for product_payload in payload.products:
        post.products.append(Product(**product_payload.model_dump()))
    db.add(post)
    db.commit()
    return get_post(post.id, db)


@router.get("", response_model=list[PostRead])
def list_posts(db: Session = Depends(get_db), status: str | None = None) -> list[Post]:
    stmt = post_query()
    if status:
        stmt = stmt.where(Post.status == status)
    stmt = stmt.order_by(Post.created_at.desc())
    return list(db.scalars(stmt).unique().all())


@router.get("/{post_id}", response_model=PostRead)
def get_post(post_id: str, db: Session = Depends(get_db)) -> Post:
    post = db.scalars(post_query().where(Post.id == post_id)).unique().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.patch("/{post_id}", response_model=PostRead)
def update_post(post_id: str, payload: PostUpdate, db: Session = Depends(get_db)) -> Post:
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(post, key, value)
    db.commit()
    return get_post(post_id, db)


@router.delete("/{post_id}")
def delete_post(post_id: str, db: Session = Depends(get_db)) -> dict[str, bool]:
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(post)
    db.commit()
    return {"ok": True}


@router.post("/{post_id}/generate-copy", response_model=PostRead)
def generate_copy(post_id: str, db: Session = Depends(get_db)) -> Post:
    post = db.scalars(select(Post).options(selectinload(Post.products)).where(Post.id == post_id)).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    result = agent_service.generate_copy(post)
    post.selected_title = result["selected_title"]
    post.title_options = result["title_options"]
    post.content = result["content"]
    post.cover_text = result["cover_text"]
    post.tags = result["tags"]
    post.comment_guide = result["comment_guide"]
    post.recommendation_level = result["recommendation_level"]
    for product_result in result["product_copy_results"]:
        product = next((item for item in post.products if item.id == product_result["product_id"]), None)
        if product:
            product.agent_summary = product_result["agent_summary"]
            product.agent_recommendation = product_result["agent_recommendation"]
            product.agent_detail = product_result
    db.commit()
    return get_post(post_id, db)


@router.post("/{post_id}/regenerate-copy", response_model=PostRead)
def regenerate_copy(post_id: str, db: Session = Depends(get_db)) -> Post:
    return generate_copy(post_id, db)


@router.post("/{post_id}/mark-published", response_model=PostRead)
def mark_published(post_id: str, db: Session = Depends(get_db)) -> Post:
    settings = get_settings()
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    now = datetime.utcnow()
    post.status = "published"
    post.published_at = now
    reminder = Reminder(
        post_id=post.id,
        remind_at=now + timedelta(days=settings.reminder_days_after_publish),
        message=f"《{post.selected_title or '未命名帖子'}》已发布 {settings.reminder_days_after_publish} 天，请录入数据。",
    )
    db.add(reminder)
    db.commit()
    return get_post(post_id, db)


@router.post("/{post_id}/mark-analyzed", response_model=PostRead)
def mark_analyzed(post_id: str, db: Session = Depends(get_db)) -> Post:
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.status = "analyzed"
    post.analyzed_at = datetime.utcnow()
    db.commit()
    return get_post(post_id, db)

