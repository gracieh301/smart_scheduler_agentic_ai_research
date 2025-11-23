# Study Plan Generator

A web application that analyzes course syllabi and produces optimized weekly learning schedules with focused study sessions and spaced repetition reviews.

## Features

- **Syllabus Upload**: Upload PDF syllabi directly to N8N webhook for processing
- **RAG-based Analysis**: Uses vector embeddings (ChromaDB) for semantic search of syllabus content
- **AI-Powered Planning**: CrewAI agents generate optimized study plans with RAG
- **Spaced Repetition**: Automatically schedules review sessions at optimal intervals
- **Web Interface**: Streamlit UI for easy interaction
- **N8N Integration**: Syllabus processing handled by N8N workflows

## Project Structure

```
project/
├── backend/
│   ├── app.py              # Flask entry point
│   ├── crew/
│   │   ├── supervisor.py   # Supervisor agent
│   │   ├── agents.py       # Study Planner, Explanation/Tutor, and Parsing agents
│   │   ├── tools.py        # Database + VectorDB + n8n webhook tools
│   │   └── crew.py         # Crew configuration (tasks + agents + process)
│   ├── db/
│   │   ├── models.py       # SQLAlchemy models
│   │   └── plan_ops.py     # read/write plan helpers for tools
│   └── vector/
│       └── rag.py          # Embeddings + vector DB setup for syllabus PDFs
│
└── streamlit/
    ├── app.py              # UI for students to upload syllabus & generate plans
    └── api_client.py       # Calls Flask endpoints
```

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

1. **Clone the repository** (or navigate to the project directory)

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   The main dependencies include:
   - Flask (backend API)
   - Streamlit (frontend UI)
   - CrewAI (AI agent framework)
   - ChromaDB (vector database)
   - sentence-transformers (embeddings)
   - SQLAlchemy (database ORM)
   - PyPDF2 (PDF processing)

3. **Set up environment variables**:
   
   Create a `.env` file in the project root with the following variables:
   
   ```env
   # LLM Provider Configuration
   # Set LLM_PROVIDER to "openai" (default), "groq", or "mistral"
   LLM_PROVIDER=openai
   
   # OpenAI Configuration (required if LLM_PROVIDER=openai)
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4
   
   # Groq Configuration (required if LLM_PROVIDER=groq)
   # Get your API key from: https://console.groq.com/
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_MODEL=llama-3.1-70b-versatile
   # Other Groq models: "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma-7b-it"
   
   # Mistral Configuration (required if LLM_PROVIDER=mistral)
   # Get your API key from: https://console.mistral.ai/
   MISTRAL_API_KEY=your_mistral_api_key_here
   MISTRAL_MODEL=mistral-large-latest
   # Other Mistral models: "mistral-medium-latest", "mistral-small-latest", "pixtral-12b-2409"
   
   # Required: N8N webhook URL for syllabus uploads
   N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/your-webhook-id
   
   # Optional: Database URL (defaults to SQLite)
   DATABASE_URL=sqlite:///backend/study_planner.db
   
   # Optional: ChromaDB persistence directory
   CHROMA_PERSIST_DIR=backend/chroma_db
   
   # Optional: Flask configuration
   FLASK_PORT=5000
   FLASK_DEBUG=False
   
   # Optional: Backend URL for Streamlit
   BACKEND_URL=http://localhost:5000
   ```

## Running the Application

### Backend (Flask API)

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Run the Flask app**:
   ```bash
   python app.py
   ```

   Or use Flask directly:
   ```bash
   flask run
   ```

   The backend will start on `http://localhost:5000` (or the port specified in `FLASK_PORT`).

3. **Verify the backend is running**:
   ```bash
   curl http://localhost:5000/health
   ```

### Frontend (Streamlit UI)

1. **Open a new terminal** (keep the backend running)

2. **Navigate to the streamlit directory**:
   ```bash
   cd streamlit
   ```

3. **Run the Streamlit app**:
   ```bash
   streamlit run app.py
   ```

   The UI will open in your browser at `http://localhost:8501`.

## Usage

1. **Upload a Syllabus**:
   - In the Streamlit UI, go to the "Upload Syllabus" tab
   - Select a PDF file of your course syllabus
   - Optionally enter the course name and code
   - Click "Upload Syllabus"
   - The file is sent directly to your N8N webhook
   - N8N workflow processes the PDF, extracts text, stores in database, and generates embeddings

2. **Generate a Study Plan**:
   - Go to the "Generate Plan" tab
   - Click "Generate Study Plan"
   - The Flask backend uses CrewAI agents with RAG to analyze the syllabus
   - Wait for the AI agents to create an optimized plan
   - View your weekly study schedule with focused sessions and spaced repetition reviews

## How It Works

1. **Syllabus Upload (via N8N)**:
   - PDF is sent directly to N8N webhook from Streamlit UI
   - N8N workflow processes the PDF:
     - Extracts text from PDF
     - Processes and structures the syllabus data
     - Returns JSON object with syllabus information
   - Flask backend receives N8N's JSON response and stores it in the database
   - The stored syllabus is then available for study plan generation

2. **Plan Generation (via Flask Backend + CrewAI)**:
   - Request sent to Flask backend `/generate_plan` endpoint
   - Supervisor agent receives the request
   - Study Planner agent uses RAG to retrieve relevant syllabus content from ChromaDB
   - Parsing agent extracts key information (topics, dates, assessments)
   - Study Planner agent creates optimized weekly schedules
   - Plan includes:
     - Focused study sessions for new material
     - Spaced repetition reviews (1 day, 3 days, 1 week, 3 weeks intervals)
   - Plan is saved to database
   - Optionally sent to n8n webhook for external integrations

## N8N Workflow Requirements

Your N8N workflow must return a JSON object with the following structure:

```json
{
  "Course Name": "Machine Learning",
  "Course Code": "CS101",
  "Class Times": ["Monday 10:00 AM", "Wednesday 2:00 PM"],
  "Lab Due Dates": ["2024-01-15", "2024-02-20"],
  "Midterm Date": "2024-03-10"
}
```

**Required fields:**
- `Course Name`: Name of the course (string)

**Optional fields:**
- `Course Code`: Course code (e.g., "CS101") (string)
- `Class Times`: Array of class meeting times (array of strings)
- `Lab Due Dates`: Array of lab assignment due dates (array of strings)
- `Midterm Date`: Date of the midterm exam (string)

**Note:** The `user_id` and `file_name` are automatically added by the application from the upload request, so you don't need to include them in N8N's response.

The Flask backend will:
1. Receive N8N's JSON response
2. Extract `Course Name` and `Course Code` for database storage
3. Create a formatted text version for RAG (includes Course Name, Course Code, Class Times, Lab Due Dates, Midterm Date)
4. Store both the structured data and formatted text in the database
5. Make it available for CrewAI agents to use when generating study plans

## Switching LLM Providers

The application supports **OpenAI**, **Groq**, and **Mistral** as LLM providers. This is useful when you run out of tokens or want to use a faster/cheaper alternative.

### Using OpenAI (Default)

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
```

### Using Groq

Groq offers fast inference with models like Llama 3.1 and Mixtral. Get your API key from [console.groq.com](https://console.groq.com/).

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile
```

**Available Groq Models:**
- `llama-3.1-70b-versatile` (default) - Best quality, slower
- `llama-3.1-8b-instant` - Fast, good quality
- `mixtral-8x7b-32768` - High quality, large context
- `gemma-7b-it` - Fast, efficient
- `llama-3.2-3b-preview` - Very fast, smaller model

**Note:** Model availability may change. Check [Groq's model documentation](https://console.groq.com/docs/models) for the latest list.

### Using Mistral

Mistral AI provides high-quality models with competitive pricing. Get your API key from [console.mistral.ai](https://console.mistral.ai/).

```env
LLM_PROVIDER=mistral
MISTRAL_API_KEY=your_mistral_api_key_here
MISTRAL_MODEL=mistral-large-latest
```

**Available Mistral Models:**
- `mistral-large-latest` (default) - Best quality, latest version
- `mistral-medium-latest` - Good balance of quality and speed
- `mistral-small-latest` - Fast, efficient
- `pixtral-12b-2409` - Multimodal, supports images
- `open-mistral-7b` - Open source, very fast

**Note:** Model availability may change. Check [Mistral's model documentation](https://docs.mistral.ai/capabilities/models/) for the latest list.

### Switching Providers

1. Update your `.env` file with the new `LLM_PROVIDER` and corresponding API key
2. Restart your Flask backend
3. The application will automatically use the new provider

**Note:** The system has automatic fallback - if your selected provider's API key is missing, it will try other available providers in order: Mistral → Groq → OpenAI.

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | No | `openai` | LLM provider: `"openai"`, `"groq"`, or `"mistral"` |
| `OPENAI_API_KEY` | Yes* | - | OpenAI API key (required if `LLM_PROVIDER=openai`) |
| `OPENAI_MODEL` | No | `gpt-4` | OpenAI model to use |
| `GROQ_API_KEY` | Yes* | - | Groq API key (required if `LLM_PROVIDER=groq`) |
| `GROQ_MODEL` | No | `llama-3.1-70b-versatile` | Groq model to use |
| `MISTRAL_API_KEY` | Yes* | - | Mistral API key (required if `LLM_PROVIDER=mistral`) |
| `MISTRAL_MODEL` | No | `mistral-large-latest` | Mistral model to use |
| `N8N_WEBHOOK_URL` | Yes | - | N8N webhook URL for syllabus uploads |
| `DATABASE_URL` | No | SQLite | Database connection URL |
| `CHROMA_PERSIST_DIR` | No | `backend/chroma_db` | ChromaDB storage directory |
| `FLASK_PORT` | No | `5000` | Flask server port |
| `FLASK_DEBUG` | No | `False` | Enable Flask debug mode |
| `BACKEND_URL` | No | `http://localhost:5000` | Backend API URL for Streamlit |

\* Required based on `LLM_PROVIDER` setting

## Troubleshooting

### Backend won't start
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify that `OPENAI_API_KEY` is set in your `.env` file
- Check that port 5000 (or your custom port) is not already in use

### PDF upload fails
- Ensure PyPDF2 is installed: `pip install PyPDF2`
- Verify the PDF is not corrupted or password-protected
- Check that the PDF contains extractable text (not just images)

### Plan generation fails
- Verify LLM API key is valid and has credits (OpenAI or Groq based on `LLM_PROVIDER`)
- Check backend logs for detailed error messages
- Ensure syllabus was uploaded successfully first
- If using Groq, verify `langchain-groq` is installed: `pip install langchain-groq`

### Vector DB errors
- Ensure ChromaDB is installed: `pip install chromadb`
- Check that the `CHROMA_PERSIST_DIR` directory is writable
- Try deleting the ChromaDB directory and re-uploading syllabi

## Development

### Project Structure Notes

- **Backend**: Flask REST API with CrewAI agents
- **Database**: SQLAlchemy ORM with SQLite (can be upgraded to PostgreSQL)
- **Vector DB**: ChromaDB for semantic search
- **Frontend**: Streamlit for simple, interactive UI

### Adding New Features

- **New Agents**: Add to `backend/crew/agents.py`
- **New Tools**: Add to `backend/crew/tools.py`
- **New API Endpoints**: Add to `backend/app.py`
- **UI Components**: Modify `streamlit/app.py`

## License

This project is provided as-is for educational and development purposes.

