from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import Base, SessionLocal, engine
from app.models import AgentStylePreset
from app.routers import analytics, images, metrics, posts, products, reminders, style_presets


settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    media_path = Path(settings.local_storage_dir)
    media_path.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=media_path), name="media")

    app.include_router(style_presets.router, prefix=settings.api_prefix)
    app.include_router(posts.router, prefix=settings.api_prefix)
    app.include_router(products.router, prefix=settings.api_prefix)
    app.include_router(images.router, prefix=settings.api_prefix)
    app.include_router(metrics.router, prefix=settings.api_prefix)
    app.include_router(reminders.router, prefix=settings.api_prefix)
    app.include_router(analytics.router, prefix=settings.api_prefix)

    @app.on_event("startup")
    def on_startup() -> None:
        Base.metadata.create_all(bind=engine)
        seed_style_presets()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "env": settings.app_env}

    return app


def seed_style_presets() -> None:
    defaults = [
        {
            "preset_type": "image",
            "name": "干净测评风",
            "description": "保留商品真实信息，背景更干净，适合小红书测评封面。",
            "prompt_template": "保持商品包装文字和形状真实，清理背景，主体清晰，预留封面文字空间。",
            "default_params": {"aspect_ratio": "3:4", "quality": "high", "keep_product_original": True},
        },
        {
            "preset_type": "copy",
            "name": "真实吐槽测评风",
            "description": "像普通用户做真实记录，允许轻微吐槽，不写广告腔。",
            "prompt_template": "基于用户真实感受写小红书笔记，不编造体验，结构包含优缺点、适合人群和评论引导。",
            "default_params": {"title_count": 5, "tone": "真实直观", "max_length": 600},
        },
    ]
    with SessionLocal() as db:
        exists = db.scalar(select(AgentStylePreset.id).where(AgentStylePreset.is_system_default.is_(True)))
        if exists:
            return
        for preset in defaults:
            db.add(AgentStylePreset(**preset, is_system_default=True, is_active=True))
        db.commit()


app = create_app()

