"""
Test Anti-Hallucination Measures
Quick script to verify the chatbot doesn't invent information
"""

import os
from dotenv import load_dotenv
from solverde_chatbot_enhanced import SolverdeChatbot

# Load environment
load_dotenv()

# Initialize chatbot
print("🚀 Initializing chatbot...")
chatbot = SolverdeChatbot(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    persist_directory="./chroma_db"
)

# Load FAQs if needed
if chatbot.collection.count() == 0:
    print("📁 Loading FAQs...")
    chatbot.load_faqs_from_file("docs/ajuda/perguntas_frequentes_completo.md")

print(f"✅ Chatbot ready with {chatbot.collection.count()} documents\n")

# Test cases
test_cases = [
    {
        "name": "Payment Methods (should list only available)",
        "question": "Que métodos de pagamento tem?",
        "expected_keywords": ["Visa", "Mastercard", "MB Way", "Multibanco", "PayPal", "Neteller", "Skrill"],
        "forbidden_keywords": ["Apple Pay", "Google Pay", "Revolut"]  # Not in FAQs
    },
    {
        "name": "Pix (should say NO clearly)",
        "question": "Tem Pix?",
        "expected_keywords": ["Não", "não aceita"],
        "forbidden_keywords": ["talvez", "possivelmente", "atualmente não encontrei"]
    },
    {
        "name": "Bitcoin (should say NO clearly)",
        "question": "Posso depositar com Bitcoin?",
        "expected_keywords": ["Não", "não aceita", "criptomoeda"],
        "forbidden_keywords": ["talvez", "possivelmente"]
    },
    {
        "name": "Best game to win (should admit it doesn't know)",
        "question": "Qual o melhor jogo para ganhar?",
        "expected_keywords": ["Não encontrei", "suporte@solverde.pt"],
        "forbidden_keywords": ["slots", "blackjack", "RTP", "estratégia", "volatilidade", "margem da casa"]
    },
    {
        "name": "VIP Program (should admit it doesn't know)",
        "question": "Como funciona o programa VIP?",
        "expected_keywords": ["Não encontrei", "suporte@solverde.pt"],
        "forbidden_keywords": ["níveis", "pontos", "benefícios exclusivos"]
    },
    {
        "name": "Minimum deposit (should say 10€)",
        "question": "Qual o depósito mínimo?",
        "expected_keywords": ["10€", "10 euros"],
        "forbidden_keywords": ["5€", "20€"]
    },
    {
        "name": "Minimum withdrawal (should say 20€)",
        "question": "Qual o levantamento mínimo?",
        "expected_keywords": ["20€", "20 euros"],
        "forbidden_keywords": ["10€", "30€"]
    }
]

# Run tests
session_id = "test_session"
results = []

print("=" * 70)
print("TESTING ANTI-HALLUCINATION MEASURES")
print("=" * 70)
print()

for i, test in enumerate(test_cases, 1):
    print(f"Test {i}/{len(test_cases)}: {test['name']}")
    print(f"Question: {test['question']}")
    print("-" * 70)

    # Get response
    response = chatbot.chat(session_id, test['question'])
    print(f"Response:\n{response}\n")

    # Check expected keywords
    passed_expected = all(
        keyword.lower() in response.lower()
        for keyword in test.get('expected_keywords', [])
    )

    # Check forbidden keywords (should NOT appear)
    passed_forbidden = not any(
        keyword.lower() in response.lower()
        for keyword in test.get('forbidden_keywords', [])
    )

    # Overall pass/fail
    passed = passed_expected and passed_forbidden

    # Results
    status = "✅ PASS" if passed else "❌ FAIL"
    results.append({
        "test": test['name'],
        "passed": passed,
        "expected_ok": passed_expected,
        "forbidden_ok": passed_forbidden
    })

    print(f"Status: {status}")

    if not passed_expected:
        missing = [kw for kw in test.get('expected_keywords', [])
                   if kw.lower() not in response.lower()]
        print(f"  ⚠️  Missing expected keywords: {missing}")

    if not passed_forbidden:
        found = [kw for kw in test.get('forbidden_keywords', [])
                 if kw.lower() in response.lower()]
        print(f"  ⚠️  Found forbidden keywords (hallucination!): {found}")

    print()
    print("=" * 70)
    print()

    # Clear conversation for next test
    chatbot.clear_conversation(session_id)

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

total = len(results)
passed = sum(1 for r in results if r['passed'])
failed = total - passed

print(f"Total tests: {total}")
print(f"Passed: {passed} ✅")
print(f"Failed: {failed} ❌")
print(f"Success rate: {(passed/total)*100:.1f}%")
print()

if failed > 0:
    print("Failed tests:")
    for r in results:
        if not r['passed']:
            print(f"  - {r['test']}")
            if not r['expected_ok']:
                print(f"    (missing expected keywords)")
            if not r['forbidden_ok']:
                print(f"    (HALLUCINATION DETECTED - used forbidden keywords)")

print("\n" + "=" * 70)

# Final verdict
if failed == 0:
    print("🎉 ALL TESTS PASSED! Anti-hallucination measures working correctly.")
else:
    print(f"⚠️  {failed} test(s) failed. Review system prompt and FAQs.")

print("=" * 70)
