# Smart Scheduler Flask API Documentation

## Overview

The Flask backend provides REST endpoints for the Smart Scheduler application. All business logic runs in the backend - the frontend only makes API calls.

## Base URL

```
http://localhost:5000
```

## Endpoints

### 1. POST `/chat`

Forward chat message to CrewAI and return reply.

**Request Body:**
```json
{
    "message": "User's message or question",
    "user_id": "user123"
}
```

**Response (Success):**
```json
{
    "success": true,
    "response": "Agent's response text",
    "user_id": "user123"
}
```

**Response (Error):**
```json
{
    "success": false,
    "error": "Error message"
}
```

**Status Codes:**
- `200`: Success
- `400`: Bad request (missing fields)
- `500`: Server error
- `503`: CrewAI not available

**Example:**
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Generate a study plan", "user_id": "user123"}'
```

---

### 2. POST `/upload_syllabus`

Store uploaded syllabus PDF and extract topics using CrewAI.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Fields:
  - `file` (required): PDF file
  - `user_id` (optional): User identifier (defaults to "default_user")
  - `course_name` (optional): Course name (defaults to filename)

**Response (Success):**
```json
{
    "success": true,
    "syllabus_id": 123,
    "message": "Syllabus uploaded and stored successfully",
    "course_name": "Introduction to Machine Learning",
    "user_id": "user123"
}
```

**Response (Error):**
```json
{
    "success": false,
    "error": "Error message"
}
```

**Status Codes:**
- `200`: Success
- `400`: Bad request (no file, extraction failed)
- `500`: Server error

**Example:**
```bash
curl -X POST http://localhost:5000/upload_syllabus \
  -F "file=@syllabus.pdf" \
  -F "user_id=user123" \
  -F "course_name=Machine Learning"
```

**What it does:**
1. Extracts text from PDF
2. Saves syllabus to database
3. Stores in vector database for RAG
4. Uses CrewAI to extract topics, due dates, and workload

---

### 3. GET `/plan`

Return study plan for a user.

**Query Parameters:**
- `user_id` (required): User identifier

**Response (Success):**
```json
{
    "success": true,
    "plan": {
        "plan_id": 123,
        "user_id": "user123",
        "sessions": [
            {
                "session_id": 456,
                "topic": "Neural Networks",
                "session_type": "focused",
                "scheduled_start": "2024-01-15T09:00:00",
                "scheduled_end": "2024-01-15T10:00:00",
                "duration_minutes": 60,
                "priority": 3,
                "status": "scheduled"
            }
        ],
        "plan_data": {...}
    }
}
```

**Response (No Plan):**
```json
{
    "success": false,
    "error": "No study plan found for this user",
    "plan": null
}
```

**Status Codes:**
- `200`: Success
- `400`: Bad request (missing user_id)
- `404`: No plan found
- `500`: Server error

**Example:**
```bash
curl "http://localhost:5000/plan?user_id=user123"
```

---

### 4. POST `/update_mastery`

Update mastery level after a study session.

**Request Body:**
```json
{
    "user_id": "user123",
    "topic": "Neural Networks",
    "mastery_level": 0.7,
    "session_id": 456,
    "confidence_score": 0.8,
    "notes": "Understood backpropagation well"
}
```

**Required Fields:**
- `user_id`: User identifier
- `topic`: Topic name
- `mastery_level`: Number between 0.0 and 1.0

**Optional Fields:**
- `session_id`: Study session ID
- `confidence_score`: Number between 0.0 and 1.0
- `notes`: Text notes about the session

**Response (Success):**
```json
{
    "success": true,
    "record_id": 789,
    "message": "Mastery level updated successfully"
}
```

**Response (Error):**
```json
{
    "success": false,
    "error": "Error message"
}
```

**Status Codes:**
- `200`: Success
- `400`: Bad request (missing/invalid fields)
- `500`: Server error

**Example:**
```bash
curl -X POST http://localhost:5000/update_mastery \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "topic": "Neural Networks",
    "mastery_level": 0.7,
    "confidence_score": 0.8
  }'
```

---

### 5. GET `/health`

Health check endpoint.

**Response:**
```json
{
    "status": "healthy",
    "crewai_available": true
}
```

**Status Code:** `200`

**Example:**
```bash
curl http://localhost:5000/health
```

---

### 6. POST `/upload` (Legacy)

Legacy endpoint for file upload to n8n webhook. Kept for backward compatibility.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Field: `file` (required)

**Response:**
```json
{
    "status": "success",
    "n8n_response": "..."
}
```

---

## Error Handling

All endpoints return consistent error responses:

```json
{
    "success": false,
    "error": "Human-readable error message"
}
```

## CORS

CORS is enabled for all endpoints to allow frontend access.

## Environment Variables

- `FLASK_PORT`: Port to run Flask on (default: 5000)
- `FLASK_DEBUG`: Enable debug mode (default: False)
- `N8N_WEBHOOK_URL`: n8n webhook URL for calendar integration
- `DATABASE_URL`: Database connection string (optional, defaults to SQLite)
- `OPENAI_API_KEY`: OpenAI API key (optional, for OpenAI embeddings)

## Testing

Run the test script to verify all endpoints:

```bash
python backend/test_endpoints.py
```

Make sure the Flask server is running first:

```bash
python backend/app.py
```

## Architecture Notes

- All business logic runs in the backend
- Frontend only makes API calls - no logic in frontend
- CrewAI agents are called via `run_crew()` function
- Database operations use SQLAlchemy models
- RAG system uses ChromaDB for vector storage
- Scheduling timestamps are computed by backend utilities

