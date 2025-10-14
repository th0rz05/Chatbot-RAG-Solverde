# Response Length Guide - Balancing Detail & Conciseness

## Philosophy

**Goal**: Provide **complete, helpful information** while avoiding unnecessary verbosity.

**Rule of Thumb**:
- Simple question = Concise answer
- Complex question = Detailed explanation
- **Always err on the side of being helpful** rather than being brief

## Updated System Prompt

### Rule #9: Response Structure Adapted to Complexity

```
**Para perguntas SIMPLES** (ex: "Qual o mínimo?"):
   - Resposta direta em 1-2 frases curtas
   - Exemplo: "O depósito mínimo é 10€. Isto aplica-se a todos os métodos de pagamento."

**Para perguntas COMPLEXAS** (ex: "Como fazer levantamento?"):
   - Explica com DETALHE suficiente para o utilizador entender completamente
   - Usa listas numeradas para processos
   - Inclui contexto relevante (porquês, exceções, avisos)
   - Exemplo: explica passo-a-passo + menciona prazos + avisos importantes

**Para perguntas com MÚLTIPLAS OPÇÕES** (ex: "Que métodos tem?"):
   - Lista TODAS as opções disponíveis
   - Adiciona breves explicações quando útil (ex: prazos diferentes por método)
   - Menciona diferenças importantes

**REGRA GERAL**: É melhor dar informação COMPLETA e CLARA do que ser demasiado breve e deixar dúvidas.
```

## Examples Added to Prompt

### Exemplo 1: Detailed Response (Complex Question)

**Question**: "Quanto tempo demora o levantamento?"

**Response Style**: DETAILED (because it's a common, important question with multiple variables)

```
Graças aos Levantamentos Flash, agora podes levantar os teus ganhos de forma imediata na Solverde.pt! 🎉

**Prazos por método de levantamento:**

- **Levantamentos Flash (≥20€)**: Creditados de forma imediata! Basta teres a conta validada...

- **Levantamentos inferiores a 20€**: Podem demorar até 2 dias úteis

- **Transferência bancária**: Geralmente 2 dias úteis, podendo chegar até 72 horas...

- **Carteiras digitais** (PayPal, Neteller, Skrill): Maioritariamente imediato...

- **Cartão VISA**: Entre 2 a 4 dias úteis

**Importante**: Alguns bancos têm restrições em certos horários:
- Crédito Agrícola: 00h00 - 02h00
- ActivoBank/Millennium: 21h00 - 05h00
...

Já fizeste o teu pedido de levantamento? Qual método estás a usar?
```

**Why detailed?**
- ✅ Multiple variables (method, amount, bank, time)
- ✅ Important information (money!)
- ✅ Users need complete picture to understand their situation
- ✅ Prevents follow-up questions

**Length**: ~200 words ✅ (appropriate for complexity)

### Exemplo 6: Concise Response (Simple Question)

**Question**: "Qual o depósito mínimo?"

**Response Style**: CONCISE (because it's straightforward)

```
O depósito mínimo na Solverde.pt é de **10€**. Este valor aplica-se a todos os métodos de pagamento disponíveis (Multibanco, MB Way, cartão, transferência bancária, PayPal, Neteller, Skrill).

Se precisares de ajuda para fazer um depósito, posso explicar o processo!
```

**Why concise?**
- ✅ Simple factual answer (one number)
- ✅ Quick clarification about applicability
- ✅ Offer to help more if needed

**Length**: ~40 words ✅ (appropriate for simplicity)

## Decision Tree: How Long Should the Answer Be?

```
Is the question simple (one fact)?
├─ YES → Concise (1-3 sentences)
│        Example: "Qual o mínimo?" → "10€, aplica-se a todos os métodos."
│
└─ NO → Is it complex (multiple parts, process, or important)?
    ├─ YES → Detailed (organize with headings, lists, examples)
    │        Example: "Como fazer levantamento?" → Step-by-step + prazos + avisos
    │
    └─ MAYBE → Does it have multiple options?
              └─ YES → Complete list with brief explanations
                       Example: "Que métodos tem?" → List all 7 + note about differences
```

## When to Be DETAILED

### 1. Money-Related Questions
- Withdrawals, deposits, limits, fees
- **Why**: Users need complete info to avoid issues
- **Example**: "Quanto tempo demora levantamento?" → Detailed breakdown by method

### 2. Multi-Step Processes
- Account verification, document upload, bonus activation
- **Why**: Users need to complete all steps correctly
- **Example**: "Como usar free spins?" → Step 1, 2, 3... with screenshots locations

### 3. Multiple Options/Variables
- Payment methods, bank restrictions, timeframes
- **Why**: Users need to know ALL options and differences
- **Example**: "Que bancos têm restrições?" → List all with specific hours

### 4. Important Warnings/Exceptions
- Account suspension reasons, document rejection, restrictions
- **Why**: Users need to avoid problems
- **Example**: "Porque rejeitaram meu IBAN?" → List all common reasons

## When to Be CONCISE

### 1. Simple Factual Questions
- Minimum amounts, limits, yes/no questions
- **Why**: One fact = one answer
- **Example**: "Depósito mínimo?" → "10€"

### 2. Clarification Requests
- When asking user for more info
- **Why**: Keep conversation flowing
- **Example**: "Que banco usas?" → Short list of options

### 3. "I Don't Know" Responses
- When info not in FAQs
- **Why**: Be honest, redirect quickly
- **Example**: "Melhor jogo?" → "Não encontrei essa info. Contacta suporte@solverde.pt"

## Length Guidelines by Question Type

| Question Type | Target Length | Example |
|---------------|---------------|---------|
| **Simple fact** | 20-50 words | "Qual o mínimo?" |
| **Yes/No + context** | 50-100 words | "Tem Pix?" |
| **How-to (simple)** | 100-150 words | "Como validar cartão?" |
| **How-to (complex)** | 150-250 words | "Como fazer levantamento?" |
| **Multiple options** | 100-200 words | "Que métodos tem?" |
| **Troubleshooting** | 150-300 words | "Porque não recebi levantamento?" |

## Before vs After Comparison

### Question: "Que métodos de pagamento tem?"

**Before** (too concise - missing context):
```
Temos Visa, Mastercard, MB Way, Multibanco, PayPal, Neteller e Skrill.
```
❌ Problem: No distinction between deposit/withdrawal, no context

**After** (appropriate detail):
```
Na Solverde.pt, dispomos dos seguintes métodos de pagamento:

**Para Depósitos:**
- Transferência Bancária (SEPA)
- Cartão de Crédito/Débito (Visa, Mastercard)
- MB Way
- Multibanco
- PayPal
- Neteller
- Skrill

**Para Levantamentos:**
- Transferência Bancária (SEPA)
- Cartão de Crédito/Débito (Visa, Mastercard)
- PayPal
- Neteller
- Skrill

**Importante**: Os levantamentos devem ser feitos pelo mesmo método usado no depósito, sempre que possível.

Qual método estavas a pensar usar?
```
✅ Complete: Shows both deposit & withdrawal
✅ Clear: Organized with headings
✅ Helpful: Mentions important rule + asks follow-up

## Red Flags (Too Brief)

❌ **User has to ask follow-up** for basic context
   - "Qual o prazo?" → "2 dias" (which method? which bank?)

❌ **Missing important exceptions**
   - "Levantamento imediato" (forgot to mention bank restrictions)

❌ **List without context**
   - Just lists options without explaining differences

## Green Flags (Right Amount of Detail)

✅ **User can take action** without asking more
   - Has all info needed to complete task

✅ **Organized clearly** with headings/lists
   - Easy to scan and find relevant part

✅ **Includes "why" when helpful**
   - "Precisas validar conta porque..." (context helps understanding)

✅ **Ends with helpful question**
   - "Qual método estás a usar?" (keeps conversation going)

## Special Case: Payment Method Questions

These deserve **extra detail** because:
- Users are dealing with their money
- Different methods have different rules
- Prevents frustration and support tickets

**Template for payment questions**:
```markdown
[Direct answer to question]

**Available methods:**
[Complete list with categories if applicable]

**Important notes:**
[Any restrictions, rules, or timeframes]

[Helpful follow-up question]
```

## Implementation Notes

### System Prompt Changes

1. **Rule #9 expanded** from 4 lines to 15 lines
2. **Added explicit guidelines** for simple vs complex
3. **Added "REGRA GERAL"** emphasizing helpfulness over brevity

### Few-Shot Examples

1. **Example 1 enhanced** to show detailed response (was ~80 words, now ~200 words)
2. **Example 6 added** to show concise response for simple question

### Key Phrase Added

> "É melhor dar informação COMPLETA e CLARA do que ser demasiado breve e deixar dúvidas. O utilizador veio buscar ajuda - dá-lhe informação suficiente para resolver o problema!"

**Why this works**:
- Emphasizes user's goal (solve problem)
- Permission to be thorough
- Discourages over-optimization for brevity

## Testing

### Test Cases

**Simple questions** (should be concise):
1. "Qual o mínimo?" → ~40 words ✅
2. "Tem Pix?" → ~60 words ✅
3. "Idade mínima?" → ~30 words ✅

**Complex questions** (should be detailed):
1. "Quanto tempo levantamento?" → ~200 words ✅
2. "Como validar IBAN?" → ~150 words ✅
3. "Que métodos tem?" → ~120 words ✅

**Process questions** (should be step-by-step):
1. "Como usar free spins?" → ~150 words with numbered steps ✅
2. "Como enviar documentos?" → ~100 words with steps ✅

## User Feedback Signals

### Good (Right Length)

User feedback like:
- "Thanks, that explained everything!"
- "Perfect, I understand now"
- "Very clear explanation"

### Too Short

User feedback like:
- "But which method?"
- "What about [obvious follow-up]?"
- "Can you explain more?"

### Too Long (Rare)

User feedback like:
- "Too much information"
- "Can you summarize?"
- "Just tell me the answer"

## Maintenance

### Monthly Review

Check conversation logs:
1. Count follow-up questions (high = too concise)
2. Check where users say "too much" (rare, but note it)
3. Identify topics where users consistently ask for more detail

### Adjustment

If users frequently ask follow-ups on a topic:
→ Add that detail proactively to the FAQ response

If users say "too long" on a topic:
→ Front-load the direct answer, put details after

## Summary

**Core Principle**:
> The goal is **helpfulness**, not brevity. Give users enough information to solve their problem without needing to ask follow-ups.

**Three Levels**:
1. **Simple** (20-50 words): Direct facts
2. **Standard** (100-150 words): Most explanations
3. **Detailed** (150-300 words): Complex processes, money topics, troubleshooting

**When in doubt**: Go for the **more detailed** explanation. It's better to give complete info than leave the user confused! 🎯
