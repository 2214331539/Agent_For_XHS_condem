from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StylePresetBase(BaseModel):
    preset_type: str
    name: str
    description: str | None = None
    prompt_template: str
    default_params: dict[str, Any] = Field(default_factory=dict)
    is_system_default: bool = False
    is_active: bool = True


class StylePresetCreate(StylePresetBase):
    pass


class StylePresetRead(StylePresetBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class ImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    card_id: str
    source_image_id: str | None = None
    image_type: str
    object_key: str
    image_url: str
    sort_order: int
    final_sort_order: int | None = None
    is_selected_for_post: bool
    ai_description: str | None = None
    file_size: int | None = None
    mime_type: str | None = None
    created_at: datetime


class ProductBase(BaseModel):
    product_name: str
    price: Decimal | None = None
    user_impression: str
    sort_order: int = 0


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    product_name: str | None = None
    price: Decimal | None = None
    user_impression: str | None = None
    sort_order: int | None = None


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    post_id: str
    agent_summary: str | None = None
    agent_recommendation: str | None = None
    agent_detail: dict[str, Any] = Field(default_factory=dict)
    images: list[ImageRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PostCreate(BaseModel):
    image_style_preset_id: str | None = None
    image_custom_prompt: str | None = None
    image_custom_params: dict[str, Any] = Field(default_factory=dict)
    copy_style_preset_id: str | None = None
    copy_custom_prompt: str | None = None
    copy_custom_params: dict[str, Any] = Field(default_factory=dict)
    products: list[ProductCreate] = Field(default_factory=list)


class PostUpdate(BaseModel):
    status: str | None = None
    selected_title: str | None = None
    title_options: list[str] | None = None
    content: str | None = None
    cover_text: str | None = None
    tags: list[str] | None = None
    comment_guide: str | None = None
    recommendation_level: str | None = None


class PostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    selected_title: str | None = None
    title_options: list[str] = Field(default_factory=list)
    content: str | None = None
    cover_text: str | None = None
    tags: list[str] = Field(default_factory=list)
    comment_guide: str | None = None
    recommendation_level: str | None = None
    image_style_preset_id: str | None = None
    image_custom_prompt: str | None = None
    image_custom_params: dict[str, Any] = Field(default_factory=dict)
    copy_style_preset_id: str | None = None
    copy_custom_prompt: str | None = None
    copy_custom_params: dict[str, Any] = Field(default_factory=dict)
    published_at: datetime | None = None
    analyzed_at: datetime | None = None
    products: list[ProductRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class MetricCreate(BaseModel):
    views: int = Field(default=0, ge=0)
    likes: int = Field(default=0, ge=0)
    collects: int = Field(default=0, ge=0)
    comments: int = Field(default=0, ge=0)
    followers_gained: int = Field(default=0, ge=0)
    analyze: bool = False


class MetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    post_id: str
    views: int
    likes: int
    collects: int
    comments: int
    followers_gained: int
    interaction_rate: Decimal
    collect_rate: Decimal
    follower_rate: Decimal
    analysis_result: str | None = None
    analysis_json: dict[str, Any] = Field(default_factory=dict)
    recorded_at: datetime


class ReminderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    post_id: str
    remind_type: str
    remind_at: datetime
    status: str
    message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class ReminderUpdate(BaseModel):
    status: str | None = None
    message: str | None = None


class OverviewRead(BaseModel):
    draft_count: int
    pending_metrics_count: int
    published_this_week_count: int
    average_interaction_rate: float
    average_collect_rate: float
    best_post: dict[str, Any] | None
    next_suggestion: str

