# Smart Scheduler - CrewAI Project

A CrewAI-powered application for processing course syllabi and generating study plans.

## Project Structure

```
CrewAI/
├── .gitignore
├── pyproject.toml
├── README.md
├── .env
├── src/
│   └── smart_scheduler/
│       ├── __init__.py
│       ├── main.py          # Flask application entry point
│       ├── crew.py          # Crew definition and configuration
│       ├── tools/
│       │   ├── __init__.py
│       │   └── n8n_tool.py  # Custom tool for n8n webhook integration
│       └── config/
│           ├── agents.yaml   # Agent configurations
│           └── tasks.yaml    # Task configurations
└── tests/
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

Or using the project:
```bash
pip install -e .
```

## Configuration

1. Create a `.env` file in the CrewAI directory:
```env
N8N_WEBHOOK_URL=https://your-n8n-domain.com/webhook/upload_syllabus
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

### Running the Flask Application

```bash
python src/smart_scheduler/main.py
```

The application will start on `http://localhost:5001`

### API Endpoints

- `POST /upload` - Upload a syllabus PDF file
- `GET /health` - Health check endpoint

### Using CrewAI Directly

You can also use the CrewAI crew directly:

```python
from src.smart_scheduler.crew import create_crew

crew = create_crew()
result = crew.kickoff()
```

## Development

Run tests:
```bash
pytest
```

## License

MIT

