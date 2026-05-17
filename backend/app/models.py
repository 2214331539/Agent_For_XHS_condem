from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.session import Base


def new_uuid() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Post(Base, TimestampMixin):
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    selected_title: Mapped[str | None] = mapped_column(Text)
    title_options: Mapped[list[str]] = mapped_column(JSON, default=list)
    content: Mapped[str | None] = mapped_column(Text)
    cover_text: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    comment_guide: Mapped[str | None] = mapped_column(Text)
    recommendation_level: Mapped[str | None] = mapped_column(String(80))

    image_style_preset_id: Mapped[str | None] = mapped_column(ForeignKey("agent_style_presets.id", ondelete="SET NULL"))
    image_custom_prompt: Mapped[str | None] = mapped_column(Text)
    image_custom_params: Mapped[dict] = mapped_column(JSON, default=dict)
    copy_style_preset_id: Mapped[str | None] = mapped_column(ForeignKey("agent_style_presets.id", ondelete="SET NULL"))
    copy_custom_prompt: Mapped[str | None] = mapped_column(Text)
    copy_custom_params: Mapped[dict] = mapped_column(JSON, default=dict)

    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime)

    products: Mapped[list["Product"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    metrics: Mapped[list["PostMetric"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="post", cascade="all, delete-orphan")


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    product_name: Mapped[str] = mapped_column(String(255))
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    user_impression: Mapped[str] = mapped_column(Text)
    agent_summary: Mapped[str | None] = mapped_column(Text)
    agent_recommendation: Mapped[str | None] = mapped_column(String(80))
    agent_detail: Mapped[dict] = mapped_column(JSON, default=dict)

    post: Mapped[Post] = relationship(back_populates="products")
    images: Mapped[list["CardImage"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class CardImage(Base, TimestampMixin):
    __tablename__ = "card_images"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    card_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    source_image_id: Mapped[str | None] = mapped_column(ForeignKey("card_images.id", ondelete="SET NULL"))
    image_type: Mapped[str] = mapped_column(String(50), default="original")
    object_key: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    final_sort_order: Mapped[int | None] = mapped_column(Integer)
    is_selected_for_post: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_description: Mapped[str | None] = mapped_column(Text)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    file_size: Mapped[int | None] = mapped_column(Integer)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)

    product: Mapped[Product] = relationship(back_populates="images")


class ImageProcessingJob(Base, TimestampMixin):
    __tablename__ = "image_processing_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    card_id: Mapped[str | None] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    source_image_id: Mapped[str] = mapped_column(ForeignKey("card_images.id", ondelete="CASCADE"))
    result_image_id: Mapped[str | None] = mapped_column(ForeignKey("card_images.id", ondelete="SET NULL"))
    style_preset_id: Mapped[str | None] = mapped_column(ForeignKey("agent_style_presets.id", ondelete="SET NULL"))
    custom_prompt: Mapped[str | None] = mapped_column(Text)
    processing_params: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)


class PostMetric(Base):
    __tablename__ = "post_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    views: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    collects: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    followers_gained: Mapped[int] = mapped_column(Integer, default=0)
    interaction_rate: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)
    collect_rate: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)
    follower_rate: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)
    analysis_result: Mapped[str | None] = mapped_column(Text)
    analysis_json: Mapped[dict] = mapped_column(JSON, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    post: Mapped[Post] = relationship(back_populates="metrics")


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    remind_type: Mapped[str] = mapped_column(String(50), default="metrics_input")
    remind_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    post: Mapped[Post] = relationship(back_populates="reminders")


class AgentStylePreset(Base, TimestampMixin):
    __tablename__ = "agent_style_presets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    preset_type: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    prompt_template: Mapped[str] = mapped_column(Text)
    default_params: Mapped[dict] = mapped_column(JSON, default=dict)
    is_system_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

