from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Reminder
from app.schemas import ReminderRead, ReminderUpdate

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("", response_model=list[ReminderRead])
def list_reminders(db: Session = Depends(get_db), status: str | None = None) -> list[Reminder]:
    stmt = select(Reminder)
    if status:
        stmt = stmt.where(Reminder.status == status)
    return list(db.scalars(stmt.order_by(Reminder.remind_at.asc())).all())


@router.get("/pending", response_model=list[ReminderRead])
def list_pending_reminders(db: Session = Depends(get_db)) -> list[Reminder]:
    now = datetime.utcnow()
    stmt = select(Reminder).where(Reminder.status == "pending", Reminder.remind_at <= now).order_by(Reminder.remind_at.asc())
    return list(db.scalars(stmt).all())


@router.patch("/{reminder_id}", response_model=ReminderRead)
def update_reminder(reminder_id: str, payload: ReminderUpdate, db: Session = Depends(get_db)) -> Reminder:
    reminder = db.get(Reminder, reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(reminder, key, value)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.post("/{reminder_id}/done", response_model=ReminderRead)
def mark_done(reminder_id: str, db: Session = Depends(get_db)) -> Reminder:
    reminder = db.get(Reminder, reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    reminder.status = "done"
    reminder.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(reminder)
    return reminder


@router.post("/{reminder_id}/ignore", response_model=ReminderRead)
def ignore_reminder(reminder_id: str, db: Session = Depends(get_db)) -> Reminder:
    reminder = db.get(Reminder, reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    reminder.status = "ignored"
    reminder.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(reminder)
    return reminder

