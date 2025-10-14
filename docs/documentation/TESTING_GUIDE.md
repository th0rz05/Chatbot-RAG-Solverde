# Testing Guide - Solverde Chatbot v2.0

This guide helps you test all the new features and verify everything is working correctly.

## Pre-Testing Checklist

- [ ] `.env` file created with `OPENAI_API_KEY`
- [ ] Dependencies installed: `pip install -r backend/requirements.txt`
- [ ] FAQ file exists: `docs/ajuda/perguntas_frequentes_completo.md`
- [ ] Ports 8000 and 8080 are available

## Phase 1: Enhanced RAG System

### Test 1: Hybrid Search Quality

**Objective**: Verify that the chatbot finds relevant FAQs using both semantic and keyword matching.

**Test Cases**:

1. **Exact Match**:
   - Question: "Quanto tempo demora um levantamento?"
   - Expected: Should find and reference the FAQ about withdrawal times
   - Success: ✅ Mentions "Levantamentos Flash" and specific timeframes

2. **Paraphrased Question**:
   - Question: "Demora muito para receber o dinheiro?"
   - Expected: Should still find withdrawal timing FAQ
   - Success: ✅ Understands it's about withdrawals and provides timing info

3. **Keyword-Heavy Question**:
   - Question: "IBAN comprovativo validação"
   - Expected: Should find IBAN validation FAQ
   - Success: ✅ Matches based on keywords even without full sentence

4. **Vague Question (Should Ask for Clarification)**:
   - Question: "Não recebi"
   - Expected: Should ask what wasn't received (withdrawal, bonus, etc.)
   - Success: ✅ Asks clarifying questions

5. **Multi-FAQ Question**:
   - Question: "Como usar free spins e bónus?"
   - Expected: Should combine info from both FAQs
   - Success: ✅ Provides info about both features

### Test 2: Context Awareness

**Objective**: Verify conversation memory works correctly.

**Conversation Flow**:

```
User: Como usar free spins?
Bot: [Explains free spins process]

User: E onde fica essa área?
Bot: [Should remember "essa área" refers to free spins area - "Os Meus Bónus"]

User: Quanto tempo demora?
Bot: [Should understand this is a new topic and ask "tempo de quê?"]
```

**Success Criteria**:
- ✅ Remembers context within same topic
- ✅ Asks clarification when topic changes
- ✅ Doesn't repeat information already given

### Test 3: Few-Shot Learning

**Objective**: Verify the chatbot follows the few-shot examples in the system prompt.

**Test Cases**:

1. **Direct Answer Style**:
   - Question: "Qual o limite de levantamento diário?"
   - Expected: Clear, direct answer: "100.000€"
   - Success: ✅ Concise and specific

2. **Step-by-Step Style**:
   - Question: "Como instalar a app?"
   - Expected: Numbered list of steps
   - Success: ✅ Uses numbered format

3. **Empathy + Clarification**:
   - Question: "Não recebi o meu dinheiro"
   - Expected: Shows empathy, then asks clarifying questions
   - Success: ✅ Tone is understanding and helpful

### Test 4: Knowledge Boundaries

**Objective**: Verify chatbot admits when it doesn't know.

**Test Cases**:

1. **Out-of-Scope Question**:
   - Question: "Qual o melhor jogo para ganhar?"
   - Expected: Should say it doesn't have that info and suggest contacting support
   - Success: ✅ Doesn't invent answers

2. **Partial Information**:
   - Question: "Como funciona o programa VIP?"
   - Expected: If not in FAQs, should admit and redirect to support
   - Success: ✅ Honest about limitations

## Phase 2: Streaming Responses

### Test 5: Real-Time Streaming

**Objective**: Verify responses stream token-by-token smoothly.

**Visual Test**:
1. Open http://localhost:8080
2. Ask any question
3. Observe:
   - ✅ Response appears word-by-word (not all at once)
   - ✅ No stuttering or lag
   - ✅ Smooth typing animation
   - ✅ Typing indicator shows before response
   - ✅ Typing indicator hides when complete

**Performance Test**:
```bash
# Backend logs should show streaming working
time curl -N http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","message":"Quanto tempo demora um levantamento?"}'
```

**Success Criteria**:
- ✅ First token within 500ms
- ✅ Smooth continuous stream (no breaks)
- ✅ Proper SSE format: `data: {JSON}\n\n`
- ✅ Stream ends with `{"type":"done"}`

### Test 6: Error Handling During Streaming

**Test Cases**:

1. **Backend Restart During Stream**:
   - Start a question
   - Restart backend mid-response
   - Expected: Frontend shows error message gracefully
   - Success: ✅ No crash, clear error message

2. **Network Interruption**:
   - Simulate slow network
   - Expected: Stream continues when connection resumes
   - Success: ✅ Resilient to network issues

## Phase 3: Web Interface

### Test 7: UI/UX Functionality

**Test Checklist**:

- ✅ **Welcome Screen**:
  - Shows on first load
  - Suggested questions are clickable
  - Clicking suggestion sends that question

- ✅ **Message Display**:
  - User messages: Right side, purple gradient
  - Bot messages: Left side, gray background
  - Icons show correctly (user/robot)

- ✅ **Input Field**:
  - Enter key sends message
  - Button click sends message
  - Input clears after sending
  - Input disabled during processing
  - Focus returns after response

- ✅ **New Chat Button**:
  - Asks for confirmation if messages exist
  - Clears all messages
  - Shows welcome screen again
  - Generates new session ID

- ✅ **Scrolling**:
  - Auto-scrolls to bottom on new message
  - Scroll bar appears when needed
  - Smooth scroll animation

### Test 8: Markdown Rendering

**Test Cases**:

1. **Bold Text**:
   - Question: "Preciso de comprovativo de IBAN?"
   - Expected: Response includes bold keywords in green
   - Success: ✅ `**texto**` renders as bold

2. **Lists**:
   - Question: "Passos para usar free spins?"
   - Expected: Numbered list renders correctly
   - Success: ✅ Proper list formatting

3. **Links**:
   - If FAQ has links, they should be clickable
   - Success: ✅ Links are underlined and clickable

### Test 9: Mobile Responsiveness

**Test on Mobile Device or Narrow Browser**:

- ✅ Layout adjusts to screen width
- ✅ Message bubbles don't overflow
- ✅ Input field remains usable
- ✅ Buttons are tap-friendly (not too small)
- ✅ Scrolling works smoothly

**Responsive Breakpoints**:
- Desktop (>768px): Full layout with sidebar
- Mobile (<768px): Stacked layout

### Test 10: Cross-Browser Compatibility

**Test on Multiple Browsers**:

| Browser | Version | Streaming | UI | Result |
|---------|---------|-----------|-----|--------|
| Chrome | Latest | ✅ | ✅ | ✅ |
| Firefox | Latest | ✅ | ✅ | ✅ |
| Safari | Latest | ✅ | ✅ | ✅ |
| Edge | Latest | ✅ | ✅ | ✅ |

## Integration Tests

### Test 11: Full Conversation Flow

**Complete User Journey**:

```
1. Open http://localhost:8080
   ✅ Welcome screen loads

2. Click "Quanto tempo demora um levantamento?"
   ✅ Question appears in chat
   ✅ Typing indicator shows
   ✅ Response streams smoothly
   ✅ Response is accurate

3. Follow-up: "E para cartão de crédito?"
   ✅ Bot remembers context (levantamento)
   ✅ Provides specific info about credit card

4. New topic: "Como usar bónus?"
   ✅ Bot switches topic smoothly
   ✅ Provides bonus usage instructions

5. Vague question: "Não funciona"
   ✅ Bot asks what doesn't work
   ✅ Clarifying questions are relevant

6. Click "Nova Conversa"
   ✅ Confirmation dialog shows
   ✅ Chat clears after confirmation
   ✅ Welcome screen returns
```

### Test 12: Session Management

**Test Multiple Sessions**:

1. Open two browser tabs
2. Chat in Tab 1: Ask about levantamentos
3. Chat in Tab 2: Ask about bónus
4. Return to Tab 1: Continue levantamentos topic
5. Expected: Each tab maintains its own conversation history
6. Success: ✅ Independent sessions work correctly

### Test 13: API Endpoints

**Backend API Tests**:

```bash
# 1. Health Check
curl http://localhost:8000/health
# Expected: status=healthy, faq_count>0

# 2. Chat (non-streaming)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test1","message":"Olá"}'
# Expected: JSON response with message

# 3. Clear Session
curl -X POST http://localhost:8000/api/sessions/clear \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test1"}'
# Expected: {"status":"cleared"}

# 4. Get History
curl http://localhost:8000/api/sessions/test1/history
# Expected: Empty history after clear

# 5. Stats
curl http://localhost:8000/api/stats
# Expected: System statistics
```

## Performance Tests

### Test 14: Load Testing

**Concurrent Users**:

```bash
# Install Apache Bench (optional)
brew install ab  # macOS
# or
apt-get install apache2-utils  # Linux

# Test 10 concurrent users, 100 requests total
ab -n 100 -c 10 -T 'application/json' \
  -p request.json \
  http://localhost:8000/api/chat

# request.json contains:
# {"session_id":"load-test","message":"Quanto tempo demora?"}
```

**Success Criteria**:
- ✅ All requests complete successfully
- ✅ Average response time < 2 seconds
- ✅ No errors or timeouts

### Test 15: Memory Usage

**Monitor Resources**:

```bash
# Check backend memory usage
ps aux | grep "python.*api.py"

# Monitor in real-time
watch -n 1 'ps aux | grep "python.*api.py"'
```

**Success Criteria**:
- ✅ Memory usage stable (no leaks)
- ✅ Under 1GB RAM for backend
- ✅ CPU usage reasonable (<50% idle, <90% under load)

## Quality Assurance Checklist

### Functionality
- [ ] All FAQ topics are covered
- [ ] Hybrid search finds relevant FAQs
- [ ] Context awareness works across turns
- [ ] Clarifying questions are asked when needed
- [ ] Admits when information is not available

### Performance
- [ ] First token latency < 500ms
- [ ] Streaming is smooth (no stuttering)
- [ ] Page load time < 2 seconds
- [ ] Supports 10+ concurrent users

### UX/UI
- [ ] Interface is intuitive
- [ ] Buttons and inputs work correctly
- [ ] Mobile responsive
- [ ] Cross-browser compatible
- [ ] Error messages are clear

### Reliability
- [ ] No crashes or freezes
- [ ] Graceful error handling
- [ ] Sessions are independent
- [ ] Data persists correctly

### Security
- [ ] API key not exposed in frontend
- [ ] Input sanitization works
- [ ] CORS configured correctly
- [ ] No sensitive data in logs

## Common Issues & Fixes

### Issue: "API não acessível"
**Fix**: Check if backend is running on port 8000
```bash
lsof -i :8000
# If not running: cd backend && python api.py
```

### Issue: Streaming doesn't work
**Fix**: Check browser console for CORS errors
- Verify CORS settings in `backend/api.py`
- Ensure frontend URL is in `allow_origins`

### Issue: "Nenhuma FAQ encontrada"
**Fix**: FAQs not loaded
```bash
# Check if FAQ file exists
ls docs/ajuda/perguntas_frequentes_completo.md

# Manually load
python
>>> from solverde_chatbot_enhanced import SolverdeChatbot
>>> bot = SolverdeChatbot(api_key="your-key")
>>> bot.load_faqs_from_file("docs/ajuda/perguntas_frequentes_completo.md")
```

### Issue: High OpenAI costs
**Fix**: Switch to cheaper models
```bash
# In .env:
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini
```

## Test Results Template

Use this template to document your test results:

```markdown
# Test Results - [Date]

## Environment
- Python Version:
- OpenAI Models:
- Browser:
- OS:

## Phase 1: Enhanced RAG
- [ ] Hybrid search: PASS/FAIL
- [ ] Context awareness: PASS/FAIL
- [ ] Few-shot learning: PASS/FAIL
- [ ] Knowledge boundaries: PASS/FAIL

## Phase 2: Streaming
- [ ] Real-time streaming: PASS/FAIL
- [ ] Error handling: PASS/FAIL

## Phase 3: Web Interface
- [ ] UI functionality: PASS/FAIL
- [ ] Markdown rendering: PASS/FAIL
- [ ] Mobile responsive: PASS/FAIL
- [ ] Cross-browser: PASS/FAIL

## Integration Tests
- [ ] Full conversation flow: PASS/FAIL
- [ ] Session management: PASS/FAIL
- [ ] API endpoints: PASS/FAIL

## Performance Tests
- [ ] Load testing: PASS/FAIL
- [ ] Memory usage: PASS/FAIL

## Notes
[Any observations or issues found]

## Overall Result
✅ PASS / ❌ FAIL
```

---

**Happy Testing! 🚀**

If all tests pass, your Solverde Chatbot v2.0 is production-ready!
