# Chatbot-RAG-Solverde - Overview

## Project Summary

This project is an **intelligent FAQ chatbot** for Solverde.pt using **Retrieval-Augmented Generation (RAG)**. It provides natural, context-aware conversations to help users with questions about the Solverde.pt platform, powered by OpenAI's GPT-4 and ChromaDB for knowledge retrieval.

---

## Current Working Features

### 1. Core Chatbot System ([solverde_chatbot.py](solverde_chatbot.py))

#### FAQ Parser (`FAQParser` class)
- **Location**: [solverde_chatbot.py:16-68](solverde_chatbot.py#L16-L68)
- **Functionality**: Parses markdown FAQ files and extracts structured information
- **Extracts**: Questions, answers, titles, sources, and IDs from markdown format
- **Format Support**: Custom markdown structure with `## Title`, `Q:`, `A:`, `Fonte:`, `ID:` fields

#### Main Chatbot (`SolverdeChatbot` class)
- **Location**: [solverde_chatbot.py:71-324](solverde_chatbot.py#L71-L324)
- **Core Features**:
  - **Vector Database**: ChromaDB for persistent FAQ storage and semantic search
  - **Embeddings**: Automatic embedding generation via ChromaDB's default embeddings
  - **Conversation Management**: Multi-session support with conversation history (up to 20 messages per session)
  - **Smart Retrieval**: Context-aware FAQ search using conversation history (last 3 exchanges)
  - **Natural Responses**: GPT-4o powered conversational AI

#### Key Methods:
- `load_faqs_from_file()` - Loads FAQs from markdown files
- `load_faqs()` - Adds FAQs to ChromaDB vector store
- `chat()` - Main conversation method with RAG pipeline
- `_search_relevant_faqs()` - Semantic search with conversation context
- `_build_system_prompt()` - Dynamic prompt generation with retrieved FAQs
- `clear_conversation()` - Session management
- `export_conversation()` - Export chat history to JSON

#### Intelligent System Prompt
- **Location**: [solverde_chatbot.py:207-246](solverde_chatbot.py#L207-L246)
- **Features**:
  - Only answers based on retrieved FAQs (no hallucination)
  - Natural conversational flow with follow-up questions
  - Context-aware responses remembering conversation history
  - Professional Portuguese (Portugal) tone
  - Handles cases where information is not available

---

### 2. Terminal Interface ([terminal.py](terminal.py))

#### Interactive CLI (`TerminalChat` class)
- **Location**: [terminal.py:19-182](terminal.py#L19-L182)
- **Features**:
  - Clean, user-friendly terminal interface
  - Real-time chat with timestamp display
  - Command system for session management
  - Thinking indicator during processing
  - Error handling and recovery

#### Available Commands:
- `/sair` - Exit the chat
- `/limpar` - Clear conversation history
- `/novo` - Start new conversation session
- `/ajuda` - Show help message

#### Initialization Flow ([terminal.py:184-255](terminal.py#L184-L255)):
1. Loads `.env` file for API key
2. Validates OpenAI API key
3. Initializes chatbot with ChromaDB
4. Auto-loads FAQs from `docs/ajuda/perguntas_frequentes.md` if database is empty
5. Launches interactive chat session

---

### 3. Knowledge Base

#### FAQ Data
- **Location**: [docs/ajuda/perguntas_frequentes.md](docs/ajuda/perguntas_frequentes.md)
- **Content**: Currently contains 4 FAQs about:
  1. Withdrawal timing and processing
  2. Free spins usage
  3. IBAN proof validation
  4. Bonus usage

#### Vector Database
- **Location**: [chroma_db/](chroma_db/)
- **Type**: ChromaDB persistent storage
- **Contains**: Embeddings and metadata for all loaded FAQs
- **Automatic**: Uses ChromaDB's default embedding function

---

### 4. RAG Pipeline (How It Works)

```
User Question
     ↓
1. Add to conversation history
     ↓
2. Search ChromaDB for relevant FAQs (top 3)
   - Uses current question + last 6 messages as context
     ↓
3. Build system prompt with:
   - Instructions for natural conversation
   - Retrieved FAQ context
   - Guidelines for asking clarifying questions
     ↓
4. Send to GPT-4o with conversation history
     ↓
5. Return natural, context-aware response
     ↓
6. Store in conversation history
```

---

## Technical Stack

### Dependencies ([requirements.txt](requirements.txt))

- **chromadb** - Vector database
- **openai** - OpenAI API client
- **pyyaml** - YAML support
- **python-dotenv** - Environment variable management
- **ipython** - Interactive Python shell

### Models Used
- **LLM**: GPT-4o (configurable to GPT-4o-mini)
- **Embeddings**: ChromaDB default embeddings (sentence-transformers)
- **Vector Store**: ChromaDB with persistent storage

---

## Project Structure

```
Chatbot-RAG-Solverde/
├── solverde_chatbot.py       # Core chatbot logic & RAG system
├── terminal.py                # Terminal interface
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (API keys)
├── chroma_db/                 # ChromaDB persistent storage
│   ├── chroma.sqlite3        # Vector database
│   └── f75f0289.../          # Collection data
└── docs/
    └── ajuda/
        └── perguntas_frequentes.md  # FAQ knowledge base
```

---

## How to Use

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key in .env
echo "OPENAI_API_KEY=sk-..." > .env
```

### 2. Run the Chatbot
```bash
python terminal.py
```

### 3. Chat
- Ask questions naturally in Portuguese
- Use commands (`/sair`, `/limpar`, `/novo`, `/ajuda`)
- Get responses based on FAQ knowledge

---

## Key Features Implemented

✅ **RAG System**: Fully functional retrieval-augmented generation
✅ **Semantic Search**: Context-aware FAQ retrieval with ChromaDB
✅ **Conversation Memory**: Multi-turn conversations with history (20 messages)
✅ **Multi-Session Support**: Independent user sessions via session IDs
✅ **Natural Language**: Portuguese conversation with GPT-4o
✅ **FAQ Management**: Load and parse markdown FAQs
✅ **Persistent Storage**: ChromaDB saves FAQs between sessions
✅ **Terminal UI**: Clean, interactive command-line interface
✅ **Error Handling**: Graceful error recovery and user feedback
✅ **Context Awareness**: Uses conversation history for better retrieval
✅ **Export Functionality**: Save conversations to JSON

---

## Configuration Options

### In [solverde_chatbot.py](solverde_chatbot.py):
- **Model**: Change from `gpt-4o` to `gpt-4o-mini` ([line 285](solverde_chatbot.py#L285))
- **Temperature**: Adjust creativity (currently `0.7`) ([line 287](solverde_chatbot.py#L287))
- **Retrieval Count**: Number of FAQs retrieved (currently `3`) ([line 167](solverde_chatbot.py#L167))
- **History Limit**: Max conversation messages (currently `20`) ([line 302](solverde_chatbot.py#L302))
- **Context Window**: Messages used for retrieval (currently `6`) ([line 176](solverde_chatbot.py#L176))

### In [terminal.py](terminal.py):
- **FAQ Path**: Default location for FAQs ([line 219](terminal.py#L219))
- **Database Path**: ChromaDB storage location ([line 207](terminal.py#L207))


## Environment Variables

Required in `.env` file:
- `OPENAI_API_KEY` - Your OpenAI API key for GPT-4 and embeddings

---

## Summary

This is a **production-ready FAQ chatbot** with RAG capabilities that:
- Provides natural Portuguese conversations about Solverde.pt
- Uses semantic search to find relevant FAQs
- Maintains conversation context across multiple turns
- Runs in a clean terminal interface
- Persists knowledge in a vector database

The system is well-structured, documented, and ready for expansion with additional FAQs or features.
