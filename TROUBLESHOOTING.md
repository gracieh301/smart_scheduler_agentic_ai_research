# Troubleshooting Guide

## Common Issues and Solutions

### 1. Import Errors

#### Issue: `ModuleNotFoundError: No module named 'crewai_tools'`
**Solution:**
```bash
pip install crewai-tools
```

#### Issue: `ModuleNotFoundError: No module named 'flask_cors'`
**Solution:**
```bash
pip install flask-cors
```

#### Issue: `ModuleNotFoundError: No module named 'chromadb'`
**Solution:**
```bash
pip install chromadb
```

#### Issue: `ModuleNotFoundError: No module named 'sentence_transformers'`
**Solution:**
```bash
pip install sentence-transformers
```

### 2. Database Issues

#### Issue: `sqlite3.OperationalError: unable to open database file`
**Solution:**
- Ensure the `backend` directory exists and is writable
- Check that the database path in `backend/db/models.py` is correct
- The default path is `backend/study_planner.db`

#### Issue: `AttributeError: 'NoneType' object has no attribute 'query'`
**Solution:**
- Make sure `init_db()` is called before using the database
- Check that database models are properly imported

### 3. Vector Database Issues

#### Issue: `chromadb.errors.InvalidCollectionException`
**Solution:**
- Delete the `backend/chroma_db` directory and restart
- The collection will be recreated automatically

#### Issue: `OSError: [Errno 13] Permission denied: 'chroma_db'`
**Solution:**
- Check file permissions on the `backend/chroma_db` directory
- Ensure the directory is writable

### 4. CrewAI Issues

#### Issue: `ValueError: OPENAI_API_KEY environment variable is required`
**Solution:**
- Create a `.env` file in the project root
- Add: `OPENAI_API_KEY=your_api_key_here`
- Or set it as an environment variable:
  ```bash
  # Windows PowerShell
  $env:OPENAI_API_KEY="your_api_key_here"
  
  # Linux/Mac
  export OPENAI_API_KEY="your_api_key_here"
  ```

#### Issue: `AttributeError: 'Agent' object has no attribute 'tools'`
**Solution:**
- Ensure you're using the correct version of CrewAI
- Update: `pip install --upgrade crewai crewai-tools`

### 5. PDF Processing Issues

#### Issue: `ImportError: PyPDF2 package required for PDF processing`
**Solution:**
```bash
pip install PyPDF2
```

#### Issue: PDF text extraction returns empty string
**Solution:**
- The PDF might be image-based (scanned document)
- Try using OCR tools or ensure the PDF has selectable text
- Check that the PDF is not corrupted

### 6. Port Already in Use

#### Issue: `OSError: [Errno 48] Address already in use` or `Port 5000 is already in use`
**Solution:**
- Change the port in `.env`: `FLASK_PORT=5001`
- Or kill the process using port 5000:
  ```bash
  # Windows
  netstat -ano | findstr :5000
  taskkill /PID <PID> /F
  
  # Linux/Mac
  lsof -ti:5000 | xargs kill
  ```

### 7. Import Path Issues

#### Issue: `ModuleNotFoundError: No module named 'db'` or `No module named 'vector'`
**Solution:**
- Make sure you're running from the `backend` directory:
  ```bash
  cd backend
  python app.py
  ```
- Or ensure the backend directory is in your Python path
- Check that `__init__.py` files exist in `backend/db/`, `backend/vector/`, and `backend/crew/`

### 8. Environment Variable Issues

#### Issue: Environment variables not loading
**Solution:**
- Ensure `.env` file is in the project root (same level as `backend/` and `streamlit/`)
- Check that `python-dotenv` is installed: `pip install python-dotenv`
- Verify `.env` file format (no spaces around `=`, no quotes needed):
  ```
  OPENAI_API_KEY=sk-...
  FLASK_PORT=5000
  ```

## Quick Diagnostic Commands

### Check if all dependencies are installed:
```bash
pip list | grep -E "crewai|flask|chromadb|sentence-transformers|PyPDF2|sqlalchemy"
```

### Test database connection:
```python
from backend.db.models import init_db
init_db()
print("Database OK")
```

### Test vector DB:
```python
from backend.vector.rag import get_collection
collection = get_collection()
print(f"Collection OK: {collection.name}")
```

### Test CrewAI import:
```python
from crewai import Agent, Crew, Task
print("CrewAI OK")
```

## Getting Help

If you encounter an error:

1. **Check the error message** - It usually tells you what's missing
2. **Verify dependencies** - Run `pip install -r requirements.txt`
3. **Check environment variables** - Ensure `.env` file exists and has `OPENAI_API_KEY`
4. **Check file structure** - Ensure all `__init__.py` files exist
5. **Run from correct directory** - Start backend from `backend/` directory

## Common Error Messages and Fixes

| Error | Likely Cause | Fix |
|-------|--------------|-----|
| `No module named 'X'` | Missing package | `pip install X` |
| `OPENAI_API_KEY required` | Missing API key | Add to `.env` file |
| `Port already in use` | Another process using port | Change port or kill process |
| `Database locked` | SQLite file locked | Close other connections |
| `Permission denied` | File permissions | Check directory permissions |
| `Collection not found` | ChromaDB issue | Delete `chroma_db` folder and restart |

