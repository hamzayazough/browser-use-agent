#!/bin/bash
# Quick start script for the prototype

set -e

echo "🚀 Starting Browser Agent Prototype"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from example..."
    cp .env.example .env
    echo "📝 Please edit .env with your API keys before running."
    exit 1
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
python -c "import fastapi, uvicorn, httpx, langchain_core" 2>/dev/null || {
    echo "❌ Dependencies not installed. Installing..."
    uv pip install -r requirements.txt
}

echo "✅ Dependencies ready"
echo ""

# Ask user what to run
echo "What would you like to run?"
echo "1) Server only"
echo "2) Client only"
echo "3) Both (in separate terminals)"
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "🌐 Starting server on http://localhost:8000"
        cd server && python main.py
        ;;
    2)
        read -p "Enter URL: " url
        read -p "Enter task: " task
        echo ""
        echo "🌐 Starting client..."
        cd local && python run.py --url "$url" --task "$task"
        ;;
    3)
        echo ""
        echo "Opening two terminals..."
        echo "Terminal 1: Server"
        echo "Terminal 2: Client"
        echo ""
        echo "Run these commands:"
        echo "  Terminal 1: cd server && python main.py"
        echo "  Terminal 2: cd local && python run.py --url YOUR_URL --task 'YOUR_TASK'"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
