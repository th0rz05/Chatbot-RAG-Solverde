# Quick Start Guide - Solverde Chatbot v2.0

Get up and running in 5 minutes! ⚡

## Prerequisites

- Python 3.8+
- OpenAI API key

## Installation

### Step 1: Setup Environment

```bash
cd Chatbot-RAG-Solverde

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### Step 3: Configure API Key

```bash
# Copy template
cp .env.example .env

# Edit .env and add your OpenAI key
nano .env  # or use any text editor
```

Your `.env` should look like:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### Step 4: Start the Application

```bash
./start.sh
```

That's it! 🎉

## Access

- **Web Interface**: http://localhost:8080
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## First Test

1. Open http://localhost:8080
2. Click "Quanto tempo demora um levantamento?"
3. Watch the response stream in real-time!

## Common Commands

```bash
# Start everything
./start.sh

# Start manually (2 terminals needed)
cd backend && python api.py          # Terminal 1
cd frontend && python -m http.server 8080  # Terminal 2

# Stop
Ctrl+C (in each terminal)

# Check if running
curl http://localhost:8000/health
```

## Troubleshooting

### "Port already in use"

```bash
# Find and kill process on port 8000
lsof -i :8000
kill -9 <PID>

# Find and kill process on port 8080
lsof -i :8080
kill -9 <PID>
```

### "OPENAI_API_KEY not found"

Check your `.env` file:
```bash
cat .env
```

Make sure it contains: `OPENAI_API_KEY=sk-...`

### "No FAQs loaded"

```bash
# Check if FAQ file exists
ls docs/ajuda/perguntas_frequentes_completo.md

# If missing, create it or use the smaller one
ls docs/ajuda/perguntas_frequentes.md
```

## Next Steps

1. ✅ Read [README.md](README.md) for full documentation
2. ✅ Follow [TESTING_GUIDE.md](TESTING_GUIDE.md) to test all features
3. ✅ Review [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for technical details

## Support

- Check logs in terminal where you ran `./start.sh`
- Visit http://localhost:8000/docs for API documentation
- Review error messages in browser console (F12)

## File Structure

```
Chatbot-RAG-Solverde/
├── backend/           # API server
├── frontend/          # Web interface
├── docs/              # FAQ knowledge base
├── .env               # Your API key (create this!)
├── start.sh           # Startup script
└── README.md          # Full documentation
```

---

**Ready to chat!** 🚀

Visit http://localhost:8080 and start asking questions about Solverde.pt!
