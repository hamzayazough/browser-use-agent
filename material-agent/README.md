# Curriculum Discovery API - Material Agent

FastAPI server for automated curriculum + materials pack building using Browser-Use agents.

## Prerequisites

- **Python 3.11 or higher** (required for browser-use)
- MongoDB running locally or accessible remotely
- OpenAI API key

## Setup

1. **Create virtual environment with Python 3.11+:**
```bash
python3.13 -m venv venv  # or python3.11, python3.12
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. **Environment is already configured:**
The `.env` file is already set up with:
- MongoDB connection
- OpenAI API key
- Browser-Use API key
- AWS S3 credentials

4. **Run the server:**
```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Quick Test

```bash
curl http://localhost:8000/health
```

## Project Structure

```
material-agent/
├── main.py                                      # FastAPI app entry point
├── config.py                                    # Settings and configuration
├── requirements.txt                             # Python dependencies
├── .env                                         # Environment variables (create from .env.example)
├── .env.example                                 # Example environment variables
├── curriculum-discovery-schema.json             # JSON Schema for validation
├── job1-curriculum-discovery-output.json        # Example Job 1 output
├── job2-topic-material-extraction-output.json   # Example Job 2 output
├── job3-validation-coverage-output.json         # Example Job 3 output
└── job4-publish-pack-output.json                # Example Job 4 output
```

## API Endpoints

### Health Check
- `GET /` - Basic health check
- `GET /health` - Detailed health status

### Coming Soon
- `POST /content-packs/discover` - Trigger curriculum discovery
- `GET /content-packs/{pack_id}` - Get content pack details
- `GET /jobs/{job_id}` - Get job status

## Environment Variables

All environment variables are configured in `.env`:

**Required:**
- `OPENAI_API_KEY` - For generating embeddings
- `MONGODB_URI` - MongoDB connection string

**Optional:**
- `BROWSER_USE_API_KEY` - For cloud browser automation (already configured)
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` - For S3 file storage (already configured)
- `PINECONE_API_KEY` - For production vector DB (alternative to MongoDB)
