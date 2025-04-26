#all helper functions related to post, will be here
from sqlalchemy.orm import Session
from models.user import User
from models.post import Post
from core.connection_crud import get_connections
from crud.notification import create_notification

STATUS_404_ERROR = "Post not found"



def send_post_notifications(db: Session, user: User, post: Post):
    friends = get_connections(db, user.id)
    for friend in friends:
        friend_id = friend["friend_id"] if friend["user_id"] == user.id else friend["user_id"]
        create_notification(db=db, recipient_id=friend_id, actor_id=user.id, notif_type="new_post", post_id=post.id)
    db.commit()

