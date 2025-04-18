from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from collections import defaultdict
from models.user import User
from models.post import Post
from schemas.university import UniversityPage, Member, UniversityPost
from database.session import SessionLocal
from core.dependencies import get_db


router = APIRouter()



@router.get("/{university_name}", response_model=UniversityPage)
def get_university_info(university_name: str, db: Session = Depends(get_db)):
    try:
        # 1. Get all users from this university
        users = db.query(User).filter(User.university_name.ilike(university_name)).all()

        if not users:
            raise HTTPException(status_code=404, detail="University not found")

        total_members = len(users)

        # 2. Group users by department
        departments = defaultdict(list)
        user_ids = []
        for user in users:
            departments[user.department].append(Member(username=user.username, email=user.email))
            user_ids.append(user.id)

        # 3. Get posts by these users containing #university_name
        hashtag = f"#{university_name.lower()}"
        posts = db.query(Post).filter(
            Post.user_id.in_(user_ids),
            Post.content.ilike(f"%{hashtag}%")
        ).order_by(Post.created_at.desc()).all()

        post_ids = [post.id for post in posts]

        return UniversityPage(
            university=university_name,
            total_members=total_members,
            departments=departments,
            post_ids=post_ids
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
