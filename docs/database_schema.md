# UConnect Database Schema

```mermaid
erDiagram
    User {
        int id PK
        string username
        string email
        string hashed_password
        bool is_active
        bool is_verified
        string profile_picture
        string university_name FK
        string department
        string fields_of_interest
        bool profile_completed
    }

    University {
        int id PK
        string name
        string[] departments
        int total_members
    }

    Post {
        int id PK
        int user_id FK
        text content
        enum post_type
        datetime created_at
        int like_count
    }

    Event {
        int id PK
        int post_id FK
        int user_id FK
        string title
        text description
        datetime event_datetime
        string location
        string image_url
    }

    Message {
        int id PK
        int sender_id FK
        int receiver_id FK
        string content
        string file_url
        enum message_type
        datetime timestamp
        bool is_read
    }

    ResearchPaper {
        int id PK
        string title
        string author
        string research_field
        text file_path
        int uploader_id FK
        datetime created_at
    }

    ResearchCollaboration {
        int id PK
        string title
        string research_field
        text details
        int creator_id FK
    }

    Comment {
        int id PK
        int user_id FK
        int post_id FK
        int parent_id FK
        text content
        datetime created_at
        int like_count
    }

    Like {
        int id PK
        int user_id FK
        int post_id FK
        int comment_id FK
        datetime created_at
    }

    Share {
        int id PK
        int user_id FK
        int post_id FK
        string share_token
        datetime created_at
    }

    Notification {
        int id PK
        int user_id FK
        int actor_id FK
        string type
        int post_id FK
        bool is_read
        datetime created_at
    }

    Hashtag {
        int id PK
        string name
        int usage_count
    }

    Connection {
        int id PK
        int user_id FK
        int friend_id FK
        enum status
    }

    CollaborationRequest {
        int id PK
        int research_id FK
        int requester_id FK
        text message
        enum status
    }

    User ||--o{ Post : "creates"
    User ||--o{ Event : "creates"
    User ||--o{ Comment : "writes"
    User ||--o{ Like : "gives"
    User ||--o{ Share : "shares"
    User ||--o{ ResearchPaper : "uploads"
    User ||--o{ ResearchCollaboration : "creates"
    User ||--o{ Message : "sends"
    User ||--o{ Message : "receives"
    User ||--o{ Notification : "receives"
    User ||--o{ Notification : "triggers"
    User ||--o{ Connection : "initiates"
    User ||--o{ CollaborationRequest : "sends"

    Post ||--o{ Comment : "has"
    Post ||--o{ Like : "receives"
    Post ||--o{ Share : "has"
    Post ||--o{ Notification : "generates"
    Post ||--o{ Hashtag : "contains"
    Post ||--o| Event : "has"

    Comment ||--o{ Comment : "has replies"
    Comment ||--o{ Like : "receives"

    ResearchCollaboration ||--o{ CollaborationRequest : "receives"
    ResearchCollaboration }|--|| User : "has collaborators"

    University ||--o{ User : "has members"
```

## Diagram Overview

This ER diagram represents the database schema for UConnect, a university-focused social platform. Here are the key relationships:

### Core Entities
- **User**: Central entity with profile information and university affiliation
- **Post**: Main content type that can include text, media, or events
- **Event**: Special type of post for university events
- **Message**: Enables direct communication between users

### Academic Features
- **ResearchPaper**: For sharing academic papers
- **ResearchCollaboration**: For finding research partners
- **University**: Maintains list of universities and departments

### Social Features
- **Comment**: Nested comment system
- **Like**: For posts and comments
- **Share**: Post sharing system
- **Connection**: Friend/connection system
- **Notification**: Activity notifications
- **Hashtag**: For categorizing posts

### Key Relationships
1. Users can create multiple posts, comments, likes, etc.
2. Posts can have multiple comments, likes, and shares
3. Comments can have nested replies
4. Research collaborations can have multiple requests
5. Messages connect two users (sender and receiver)
6. Users can have multiple connections (friends)
