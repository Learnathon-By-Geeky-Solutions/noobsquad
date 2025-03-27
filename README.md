# UHub - University Community Platform

## Team Members

- RaadShahamat (Team Leader)
- hmfahad308
- AnishRoy50

## Mentor

- shakil-shahan

## Project Name

- UHub - University Community Platform

## Project Description

UHub is a full-stack social and educational platform tailored specifically for university students. It enhances academic collaboration, social connectivity, and peer-to-peer engagement through real-time chat, group discussions, research matching, and community building tools.

With features like direct messaging, friend suggestions based on academic interests, real-time notifications, and a research collaboration hub, UHub offers a modern and seamless digital university experience. The platform is powered by FastAPI and PostgreSQL on the backend, and React with Vite on the frontend.

### Key Features
- 🔹 Real-time one-to-one chat system with WebSocket support
- 🔹 AI-powered research matching
- 🔹 Profile personalization and friend suggestions
- 🔹 Academic and social feed
- 🔹 Secure authentication and role-based access

## Tech Stack

- **Frontend**: React, Vite, Tailwind CSS
- **Backend**: FastAPI, PostgreSQL, SQLAlchemy, WebSockets
- **Database**: PostgreSQL
- **Authentication**: JWT
- **State Management**: Context API

## Getting Started

1. Clone the repository
   ```bash
   git clone https://github.com/noobsquad/uhub.git
   cd uhub
   ```
2. Install frontend & backend dependencies
   ```bash
   cd frontend && npm install
   cd ../backend && pip install -r requirements.txt
   ```
3. Setup environment variables (`.env`) in both frontend and backend
4. Start development servers
   ```bash
   # Backend
   uvicorn main:app --reload

   # Frontend (in another terminal)
   npm run dev
   ```

## Development Guidelines

1. Create feature-specific branches
2. Make small, atomic commits
3. Use descriptive commit messages
4. Push changes and create a pull request for code review

## Resources

- 📄 [Project Documentation](docs/)
- ⚙️ [Development Setup](docs/setup.md)
- 🤝 [Contributing Guidelines](CONTRIBUTING.md)

---
Made with 💙 by Team NoobSquad
