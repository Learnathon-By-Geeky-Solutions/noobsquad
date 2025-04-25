from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.post import  Event, EventAttendee
from models.user import User
from database.session import SessionLocal
from schemas.eventAttendees import EventAttendeeCreate, EventAttendeeResponse
from api.v1.endpoints.Auth.auth import get_current_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ RSVP for an event
@router.post("/event/{event_id}/rsvp", response_model=EventAttendeeResponse)
def rsvp_event(
    event_id: int, 
    attendee_data: EventAttendeeCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")

    existing_attendance = db.query(EventAttendee).filter(
        EventAttendee.event_id == event_id, EventAttendee.user_id == current_user.id
    ).first()

    if existing_attendance:
        existing_attendance.status = attendee_data.status
    else:
        new_attendance = EventAttendee(
            event_id=event_id,
            user_id=current_user.id,
            status=attendee_data.status
        )
        db.add(new_attendance)

    db.commit()
    return existing_attendance if existing_attendance else new_attendance

# ✅ Get attendees of an event
@router.get("/event/{event_id}/attendees", response_model=list[EventAttendeeResponse])
def get_event_attendees(event_id: int, db: Session = Depends(get_db)):
    attendees = db.query(EventAttendee).filter(EventAttendee.event_id == event_id).all()
    return attendees

# ✅ Remove RSVP
@router.delete("/event/{event_id}/rsvp")
def remove_rsvp(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rsvp = db.query(EventAttendee).filter(EventAttendee.event_id == event_id, EventAttendee.user_id == current_user.id).first()

    if not rsvp:
        raise HTTPException(status_code=404, detail="You haven't RSVP'd for this event.")

    db.delete(rsvp)
    db.commit()
    return {"message": "RSVP removed successfully"}

@router.get("/event/{event_id}/my_rsvp/")
def get_user_rsvp_status(event_id: int, db: Session = Depends(get_db),current_user: User =Depends(get_current_user)):
    rsvp = db.query(EventAttendee).filter(EventAttendee.event_id == event_id, EventAttendee.user_id == current_user.id).first()
    return {"status": rsvp.status if rsvp else None}

@router.get("/posts/events/rsvp/counts/")
def get_rsvp_counts(event_id: int = Query(...), db: Session = Depends(get_db)):
    going_count = db.query(func.count()).filter(
        EventAttendee.event_id == event_id,
        EventAttendee.status == "going"
    ).scalar()

    interested_count = db.query(func.count()).filter(
        EventAttendee.event_id == event_id,
        EventAttendee.status == "interested"
    ).scalar()

    return {
        "going": going_count,
        "interested": interested_count
    }