# ConvertoAI

A simple FastAPI backend paired with a static frontend for a conversational commerce demo.

## Project structure

- `backend/` - FastAPI application and Python dependency manifest
- `frontend/` - Static HTML chat interface

## Requirements

- Python 3.11+ recommended
- `pip` package manager
- A valid Google GenAI API key or credential configuration

## Setup

1. Create a virtual environment in the `backend` folder:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and set your API key:

```powershell
copy .env.example .env
```

Update `.env` with your actual Google GenAI key:

```text
GOOGLE_API_KEY=your_google_api_key_here
```

## Run the backend

From the `backend` folder:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Open the frontend

Open `frontend/index.html` in your browser. The UI sends chat requests to the backend at `http://127.0.0.1:8000/chat`.

> If you prefer a local static server, use a browser extension or simple static server for `frontend/`.

## Notes

- The backend expects environment variables loaded from `.env`.
- The frontend is a static HTML page and does not require a build step.
- The current implementation uses the Google GenAI client and a mock inventory database.
