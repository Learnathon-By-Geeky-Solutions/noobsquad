from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.v1.endpoints.Auth.auth import get_current_user
from models.user import User
from database.session import SessionLocal
from sqlalchemy.orm import Session
from services.services import get_post_by_id

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.delete("/delete_post/{post_id}")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = get_post_by_id(db, post_id, current_user.id)
    db.delete(post)
    db.commit()
    return {"message": "Post deleted successfully"}