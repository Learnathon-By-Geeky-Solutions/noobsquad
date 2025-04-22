from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from collections import defaultdict
from models.user import User
from models.post import Post
from models.university import University
from schemas.university import UniversityPage, Member, UniversityPost, UniversityListResponse
from database.session import SessionLocal
from core.dependencies import get_db
from schemas.post import PostResponse
from services.services import extract_hashtags
from models.hashtag import post_hashtags


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


@router.get("/", response_model=List[UniversityListResponse])
def get_universities(limit_departments: int = 3, db: Session = Depends(get_db)):
    universities = db.query(University).all()

    result = []
    for uni in universities:
        dept_preview = uni.departments[:limit_departments]
        result.append({
            "id": uni.id,
            "name": uni.name,
            "departments": dept_preview,
            "has_more_departments": len(uni.departments) > limit_departments
        })

    return result

@router.get("/{university_id}/departments", response_model=List[str])
def get_all_departments(university_id: int, db: Session = Depends(get_db)):
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found")
    return university.departments


@router.get("/posts/university/{university_name}/department/{department_name}")
def get_post_ids_by_department(
    university_name: str,
    department_name: str,
    db: Session = Depends(get_db)
):
    try:
        hashtag = f"#{university_name.lower()}"

        # Get users in this university & department
        users = db.query(User).filter(
            User.university_name.ilike(university_name),
            User.department == department_name
        ).all()

        user_ids = [user.id for user in users]

        if not user_ids:
            return []

        # Get matching posts with the university hashtag
        posts = db.query(Post).filter(
            Post.user_id.in_(user_ids),
            Post.content.ilike(f"%{hashtag}%")
        ).order_by(Post.created_at.desc()).all()

        post_ids = [post.id for post in posts]

        return post_ids

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/posts/by-hashtag", response_model=List[int])
def get_posts_by_hashtag(db: Session = Depends(get_db)):
    # Step 1: Get the post_ids from post_hashtags table
    post_ids = db.query(post_hashtags.c.post_id).all()

    # Step 2: Flatten the list of tuples to get just the post ids
    post_ids = [post_id[0] for post_id in post_ids]

    # Step 3: Sort the post_ids by the created_at time from the posts table in descending order
    sorted_post_ids = db.query(Post.id).filter(Post.id.in_(post_ids))\
        .order_by(Post.created_at.desc()).all()

    # Step 4: Flatten the list of tuples to get just the post ids
    sorted_post_ids = [post[0] for post in sorted_post_ids]

    # Return the sorted list of post ids
    return sorted_post_ids


