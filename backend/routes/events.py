from fastapi import APIRouter, Depends, HTTPException, Request, Body, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, List
from schemas.post import  EventResponse
from models.user import User
from database.session import SessionLocal
from core.dependencies import get_db
from api.v1.endpoints.auth import get_current_user

from models.post import Event

router = APIRouter()

@router.get("/events/grouped-by-time", response_model=Dict[str, List[int]])
def get_grouped_event_ids(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    in_7_days = now + timedelta(days=7)
    in_30_days = now + timedelta(days=30)
    in_1_year = now + timedelta(days=365)

    events_within_7_days = (
        db.query(Event.id)
        .filter(Event.event_datetime >= now, Event.event_datetime <= in_7_days)
        .all()
    )

    events_within_30_days = (
        db.query(Event.id)
        .filter(Event.event_datetime > in_7_days, Event.event_datetime <= in_30_days)
        .all()
    )

    events_within_year = (
        db.query(Event.id)
        .filter(Event.event_datetime > in_30_days, Event.event_datetime <= in_1_year)
        .all()
    )

    return {
        "within_7_days": [e.id for e in events_within_7_days],
        "within_30_days": [e.id for e in events_within_30_days],
        "within_year": [e.id for e in events_within_year],
    }

@router.get("/events/by-ids/paginated", response_model=List[EventResponse])
async def get_paginated_events_by_ids(
    request: Request,
    event_ids: List[int] = Query(...),
    offset: int = Query(0),
    limit: int = Query(4),  # Initial load = 4, then client sets 12 or more
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Safely slice the event IDs list
    paged_ids = event_ids[offset : offset + limit]

    if not paged_ids:
        return []

    events = db.query(Event).filter(Event.id.in_(paged_ids)).all()

    return events
