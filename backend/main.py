from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.session import engine, Base
from api.v1.endpoints import auth, connections, research, chat
from routes import profile
from routes import post
from routes import postReaction


app = FastAPI()

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
app.include_router(profile.router, prefix="/profile", tags=["User Profile"])
app.include_router(post.router,prefix="/posts", tags=["Posts"])
app.include_router(postReaction.router, prefix="/interactions", tags=["Post Interactions"])
app.include_router(connections.router, prefix="/connections", tags=["Connections"])
app.include_router(research.router, prefix="/research", tags=["Research"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])

