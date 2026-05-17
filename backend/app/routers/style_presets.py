from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AgentStylePreset
from app.schemas import StylePresetCreate, StylePresetRead

router = APIRouter(prefix="/style-presets", tags=["style-presets"])


@router.get("", response_model=list[StylePresetRead])
def list_style_presets(db: Session = Depends(get_db), preset_type: str | None = None) -> list[AgentStylePreset]:
    stmt = select(AgentStylePreset).where(AgentStylePreset.is_active.is_(True))
    if preset_type:
        stmt = stmt.where(AgentStylePreset.preset_type == preset_type)
    return list(db.scalars(stmt.order_by(AgentStylePreset.preset_type, AgentStylePreset.created_at)).all())


@router.get("/defaults", response_model=list[StylePresetRead])
def list_default_presets(db: Session = Depends(get_db)) -> list[AgentStylePreset]:
    stmt = select(AgentStylePreset).where(AgentStylePreset.is_system_default.is_(True), AgentStylePreset.is_active.is_(True))
    return list(db.scalars(stmt).all())


@router.post("", response_model=StylePresetRead)
def create_style_preset(payload: StylePresetCreate, db: Session = Depends(get_db)) -> AgentStylePreset:
    preset = AgentStylePreset(**payload.model_dump())
    db.add(preset)
    db.commit()
    db.refresh(preset)
    return preset


@router.get("/{preset_id}", response_model=StylePresetRead)
def get_style_preset(preset_id: str, db: Session = Depends(get_db)) -> AgentStylePreset:
    preset = db.get(AgentStylePreset, preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Style preset not found")
    return preset


@router.patch("/{preset_id}", response_model=StylePresetRead)
def update_style_preset(preset_id: str, payload: StylePresetCreate, db: Session = Depends(get_db)) -> AgentStylePreset:
    preset = db.get(AgentStylePreset, preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Style preset not found")
    for key, value in payload.model_dump().items():
        setattr(preset, key, value)
    db.commit()
    db.refresh(preset)
    return preset


@router.delete("/{preset_id}")
def delete_style_preset(preset_id: str, db: Session = Depends(get_db)) -> dict[str, bool]:
    preset = db.get(AgentStylePreset, preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Style preset not found")
    preset.is_active = False
    db.commit()
    return {"ok": True}

