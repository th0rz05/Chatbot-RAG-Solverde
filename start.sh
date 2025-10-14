#!/bin/bash

# Start Solverde Chatbot
# Inicia backend e frontend simultaneamente

echo "🚀 Starting Solverde Chatbot v2.0..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Create a .env file with: OPENAI_API_KEY=your-key"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -q -r backend/requirements.txt

echo ""
echo "📡 Starting backend API (port 8000)..."
cd backend
python api.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 3

# Start frontend
echo "🌐 Starting frontend (port 8080)..."
cd frontend
python3 -m http.server 8080 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Chatbot is running!"
echo "   Backend API:  http://localhost:8000"
echo "   Frontend UI:  http://localhost:8080"
echo "   API Docs:     http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✓ Services stopped"
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup INT

# Wait for processes
wait
