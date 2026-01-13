# Prototype: Multi-Agent Browser Automation System

This prototype implements a distributed browser automation system with two specialized AI agents:
- **Navigation Agent**: Makes decisions on what actions to take
- **UX Specialist Agent**: Analyzes pages and provides feedback

## Architecture

```
Local Machine                    Cloud Server
┌────────────┐                  ┌─────────────────┐
│   Browser  │ ◄──────────────► │ Navigation Agent│
│  (Client)  │   HTTP/JSON      │        +        │
│            │                  │  UX Specialist  │
└────────────┘                  └─────────────────┘
```

## Project Structure

```
prototype/
├── local/              # Local browser client
│   ├── client.py       # Browser controller
│   └── run.py          # CLI entry point
├── server/             # Cloud server
│   ├── main.py         # FastAPI server
│   ├── navigation_agent.py
│   ├── ux_specialist.py
│   └── feedback_storage.py
└── shared/             # Shared models
    └── models.py       # Pydantic models
```

## Quick Start

### 1. Set Up Virtual Environment

```bash
(browser-use) hamza@Hamzas-MacBook-Pro prototype % python3 local/run.py --url "http://localhost:3000" --task "find the Terms of Service page"
✓ Browser started (headless=False)

🎯 Task: find the Terms of Service page
🌐 Starting URL: http://localhost:3000

🚀 Navigating to: http://localhost:3000
✓ Page loaded: http://localhost:3000/ - Title: TutorFroggy - AI-Powered Learning for Kids

============================================================
Step 1/50
============================================================
📸 Capturing browser state...
   Title: TutorFroggy - AI-Powered Learning for Kids
   DOM elements: 0
🚀 Sending to server...

💡 UX Feedback:
   Recommendation: The site has consistently failed to load content across the root domain, '/terms-of-service', '/signin', and now the current empty state. The site is fundamentally broken or inaccessible. Conclude that the Terms of Service cannot be found on this domain and stop further navigation attempts.
   Confidence: 1.00
   Issues: The page is completely empty, rendering no content, which makes the site unusable., Lack of any interactive elements (links, buttons) prevents navigation., The page title ('TutorFroggy - AI-Powered Learning for Kids') suggests a functional site, but the empty content contradicts this, creating user confusion and frustration., The consistent failure to load content across multiple attempted URLs indicates a fundamental technical failure or inaccessibility, completely blocking the task.

🎬 Action: done
   Reasoning: The site has consistently failed to load content across multiple attempts and common URLs (root, /terms-of-service, /terms, /signin). The UX specialist strongly recommends concluding that the site is fundamentally broken or inaccessible at this address. Since the task cannot be completed due to technical failure of the target website, the agent must stop and mark the task as complete (failed).

✅ Task completed!
   Step 1 completed
INFO     [BrowserSession] 📢 on_BrowserStopEvent - Calling reset() (force=False, keep_alive=None)
INFO     [BrowserSession] [SessionManager] Cleared all owned data (targets, sessions, mappings)
INFO     [BrowserSession] ✅ Browser session reset complete
INFO     [BrowserSession] ✅ Browser session reset complete
✓ Browser stopped
(browser-use) hamza@Hamzas-MacBook-Pro prototype % cd prototype

# Create a virtual environment using uv (recommended)
uv venv --python 3.11

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
# .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install all required packages
uv pip install -r requirements.txt
```

### 3. Set Up Environment

```bash
# Create .env file in prototype/
cat > .env << EOF
# Choose your LLM provider
BROWSER_USE_API_KEY=your-key-here
# or
OPENAI_API_KEY=your-key-here
# or
ANTHROPIC_API_KEY=your-key-here
EOF
```

### 4. Start the Server

```bash
# Start the cloud server (make sure venv is activated)
cd server
python main.py

# Server will run on http://localhost:8000
```

### 5. Run the Client

```bash
# In a new terminal, activate the venv again:
cd prototype
source .venv/bin/activate  # On macOS/Linux
# or .venv\Scripts\activate on Windows

# Run the browser client
cd local
python run.py --url "http://localhost:3000" --task "search for the cheapest product"

# Or with more options:
python run.py \
  --url "https://example.com" \
  --task "find the contact page and extract the email" \
  --server "http://localhost:8000" \
  --max-steps 30
```

## Usage Examples

### Basic Example
```bash
python local/run.py \
  --url "https://news.ycombinator.com" \
  --task "find the top post and click on it"
```

### With Custom Server
```bash
python local/run.py \
  --url "http://localhost:3000" \
  --task "search for the cheapest product" \
```

### Headless Mode
```bash
python local/run.py \
  --url "https://example.com" \
  --task "extract all product names" \
  --headless
```

## API Endpoints

### Server Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /navigate` - Main endpoint for navigation requests
- `GET /stats` - Get session statistics
- `GET /feedback` - Get all UX feedback
- `POST /reset` - Reset agents and clear history

### Example: Direct API Call

```python
import httpx

response = httpx.post(
    "http://localhost:8000/navigate",
    json={
        "task": "find the cheapest product",
        "state": {
            "url": "http://example.com",
            "title": "Example Page",
            "html": "<html>...</html>",
            "screenshot": "base64...",
            "dom_elements": [...],
            "viewport": {"width": 1280, "height": 720}
        },
        "step_number": 1
    }
)

action = response.json()["action"]
```

## Configuration

### Client Configuration

Edit `local/client.py` to customize:
- Browser window size
- Screenshot quality
- Timeout values
- DOM element filtering

### Server Configuration

Edit `server/main.py` to customize:
- LLM models (ChatBrowserUse, ChatOpenAI, etc.)
- Temperature settings
- CORS settings
- Feedback storage path

### Agent Configuration

**Navigation Agent** (`server/navigation_agent.py`):
- System prompt
- Decision-making logic
- History management

**UX Specialist** (`server/ux_specialist.py`):
- Analysis criteria
- Feedback format
- Confidence scoring

## Development

### Running Tests

```bash
# Test the server
curl http://localhost:8000/health

# Test a navigation request
curl -X POST http://localhost:8000/navigate \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

### Debugging

Enable verbose logging:

```python
# In server/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Adding New Actions

1. Add action type to `shared/models.py`:
```python
type: Literal["click", "input", "navigate", "your_new_action", ...]
```

2. Implement in `local/client.py`:
```python
elif action.type == "your_new_action":
    # Implementation
```

3. Update agent prompts to include the new action.

## Deployment

### Deploy Server to Cloud

```bash
# Using Docker
docker build -t browser-agent-server -f Dockerfile.server .
docker run -p 8000:8000 -e OPENAI_API_KEY=your-key browser-agent-server

# Or using cloud platforms (AWS, GCP, Azure)
# See deployment guides for FastAPI applications
```

### Environment Variables

```bash
# Server
BROWSER_USE_API_KEY=your-key
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Client
SERVER_URL=http://your-cloud-server.com:8000
```

## Limitations & Future Improvements

### Current Limitations
- HTTP-based communication (consider WebSockets for real-time)
- No authentication/authorization
- Single session only (no multi-user support)
- Limited error recovery

### Planned Improvements
- [ ] WebSocket support for real-time communication
- [ ] Session management for multiple concurrent users
- [ ] Authentication and API keys
- [ ] Persistent feedback storage (database)
- [ ] Agent fine-tuning based on feedback
- [ ] Visual feedback dashboard
- [ ] Recording and replay capabilities

## Troubleshooting

### Server won't start
- Check if port 8000 is available
- Verify API keys are set
- Check dependencies are installed with `uv pip install -r requirements.txt`

### Client can't connect
- Verify server is running: `curl http://localhost:8000/health`
- Check firewall settings
- Ensure correct server URL

### Actions fail to execute
- Check browser compatibility
- Verify DOM elements are correctly indexed
- Enable debug mode for detailed logs

## Contributing

Feel free to extend this prototype:
1. Add new agent types
2. Improve action parsing
3. Enhance feedback storage
4. Add monitoring and observability

## License

This prototype is part of the browser-use-agent project.
