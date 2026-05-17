from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import CardImage, ImageProcessingJob, Post, Product
from app.schemas import ImageRead
from app.services.storage import storage_service

router = APIRouter(tags=["images"])


@router.post("/products/{product_id}/images", response_model=ImageRead)
async def upload_image(product_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)) -> CardImage:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    saved = await storage_service.save_upload(file, f"xhs/original/{product_id}")
    image = CardImage(
        card_id=product_id,
        image_type="original",
        object_key=str(saved["object_key"]),
        image_url=str(saved["image_url"]),
        file_size=saved["file_size"],
        mime_type=str(saved["mime_type"] or ""),
        sort_order=len(product.images),
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


@router.get("/products/{product_id}/images", response_model=list[ImageRead])
def list_product_images(product_id: str, db: Session = Depends(get_db)) -> list[CardImage]:
    stmt = select(CardImage).where(CardImage.card_id == product_id, CardImage.is_deleted.is_(False)).order_by(CardImage.sort_order)
    return list(db.scalars(stmt).all())


@router.get("/images/{image_id}", response_model=ImageRead)
def get_image(image_id: str, db: Session = Depends(get_db)) -> CardImage:
    image = db.get(CardImage, image_id)
    if not image or image.is_deleted:
        raise HTTPException(status_code=404, detail="Image not found")
    return image


@router.patch("/images/{image_id}", response_model=ImageRead)
def update_image(image_id: str, payload: dict, db: Session = Depends(get_db)) -> CardImage:
    image = db.get(CardImage, image_id)
    if not image or image.is_deleted:
        raise HTTPException(status_code=404, detail="Image not found")
    for key in ["sort_order", "final_sort_order", "is_selected_for_post", "ai_description"]:
        if key in payload:
            setattr(image, key, payload[key])
    db.commit()
    db.refresh(image)
    return image


@router.delete("/images/{image_id}")
def delete_image(image_id: str, db: Session = Depends(get_db)) -> dict[str, bool]:
    image = db.get(CardImage, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image.is_deleted = True
    image.deleted_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


@router.post("/images/{image_id}/process", response_model=ImageRead)
def process_image(image_id: str, db: Session = Depends(get_db)) -> CardImage:
    source = db.get(CardImage, image_id)
    if not source or source.is_deleted:
        raise HTTPException(status_code=404, detail="Image not found")
    product = db.get(Product, source.card_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    post = db.get(Post, product.post_id)

    job = ImageProcessingJob(
        post_id=product.post_id,
        card_id=product.id,
        source_image_id=source.id,
        status="completed",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        custom_prompt=post.image_custom_prompt if post else None,
        processing_params={
            "provider": "image_style_agent",
            "style_instruction": post.image_custom_prompt if post else None,
            "note": "The original upload is retained until an external image generation provider is configured.",
        },
    )
    processed = CardImage(
        card_id=product.id,
        source_image_id=source.id,
        image_type="processed",
        object_key=source.object_key,
        image_url=source.image_url,
        sort_order=source.sort_order,
        final_sort_order=source.final_sort_order,
        is_selected_for_post=True,
        ai_description="主体清晰，适合作为测评图片；图片处理风格已记录到处理任务，外部图片生成服务接入后可直接使用。",
        file_size=source.file_size,
        mime_type=source.mime_type,
    )
    db.add(processed)
    db.flush()
    job.result_image_id = processed.id
    db.add(job)
    db.commit()
    db.refresh(processed)
    return processed
