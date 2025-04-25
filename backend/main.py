from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.session import engine, Base
from api.v1.endpoints import connections, chat
from api.v1.endpoints.Research import SearchPaper,CurrentPaper,PostResearch,Collaboration,UploadPaper
from api.v1.endpoints.Auth import auth, OTP, Password
from routes import profile, notification, group, user, topuni, events
from routes.PostManagement import PostCreation, PostUpdating, PostDeletion, PostFetch
from routes.PostReaction import PostComment,PostLike,PostShare,EventAttendee
from fastapi.staticfiles import StaticFiles
from api.v1.endpoints import search
from api.v1.endpoints.chatbot import huggingface



app = FastAPI()
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/uploads/profile_pictures", StaticFiles(directory="uploads/profile_pictures"), name="uploads")
app.mount("/uploads/media", StaticFiles(directory="uploads/media"), name="media")
app.mount("/uploads/document", StaticFiles(directory="uploads/document"), name="document")
app.mount("/uploads/event_images", StaticFiles(directory="uploads/event_images"), name="event_images") 
app.mount("/uploads/research_papers", StaticFiles(directory="uploads/research_papers"), name="research_papers")


# ✅ Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Adjust for your frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# ✅ Create tables
Base.metadata.create_all(bind=engine)

# ✅ Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(OTP.router, prefix="/auth", tags=["Authentication"])
app.include_router(Password.router, prefix="/auth", tags=["Authentication"])
app.include_router(profile.router, prefix="/profile", tags=["User Profile"])
app.include_router(PostCreation.router,prefix="/posts", tags=["Posts"])
app.include_router(PostUpdating.router,prefix="/posts", tags=["Posts"])
app.include_router(PostDeletion.router,prefix="/posts", tags=["Posts"])
app.include_router(PostFetch.router,prefix="/posts", tags=["Posts"])
app.include_router(PostLike.router, prefix="/interactions", tags=["Post Interactions"])
app.include_router(PostShare.router, prefix="/interactions", tags=["Post Interactions"])
app.include_router(PostComment.router, prefix="/interactions", tags=["Post Interactions"])
app.include_router(EventAttendee.router, prefix="/interactions", tags=["Post Interactions"])
app.include_router(connections.router, prefix="/connections", tags=["Connections"])
app.include_router(Collaboration.router, prefix="/research", tags=["Research"])
app.include_router(CurrentPaper.router, prefix="/research", tags=["Research"])
app.include_router(PostResearch.router, prefix="/research", tags=["Research"])
app.include_router(SearchPaper.router, prefix="/research", tags=["Research"])
app.include_router(UploadPaper.router, prefix="/research", tags=["Research"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(notification.router, prefix="/notifications", tags=["Notifications"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(huggingface.router, prefix="/chatbot", tags=["Chatbot"])
app.include_router(group.router, prefix="/universities", tags=["University Groups"])
app.include_router(user.router, prefix="/user", tags=["Username"])
app.include_router(topuni.router, prefix="/top", tags=["Top Uni"])
app.include_router(events.router, prefix="/top", tags=["Events"])
