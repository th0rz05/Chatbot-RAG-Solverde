"""
Solverde.pt FAQ Chatbot
Sistema conversacional inteligente com RAG usando ChromaDB
"""

import os
import re
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from typing import List, Dict, Optional
import uuid
import json


class FAQParser:
    """Parse FAQs do formato markdown fornecido"""
    
    @staticmethod
    def parse_faq_file(content: str) -> List[Dict]:
        """
        Parse o ficheiro de FAQs e extrai cada FAQ individual
        """
        faqs = []
        
        # Split por ## para separar cada FAQ
        sections = re.split(r'\n## ', content)
        
        for section in sections[1:]:  # Skip metadata inicial
            lines = section.strip().split('\n')
            if not lines:
                continue
            
            # Primeira linha é o título/pergunta principal
            title = lines[0].strip()
            
            # Procurar ID e fonte
            faq_id = None
            source = None
            question = None
            answer_lines = []
            
            in_answer = False
            
            for line in lines[1:]:
                if line.startswith('Fonte:'):
                    source = line.replace('Fonte:', '').strip()
                elif line.startswith('ID:'):
                    faq_id = line.replace('ID:', '').strip()
                elif line.startswith('Q:'):
                    question = line.replace('Q:', '').strip()
                    in_answer = False
                elif line.startswith('A:'):
                    answer_lines.append(line.replace('A:', '').strip())
                    in_answer = True
                elif in_answer and line.strip():
                    answer_lines.append(line.strip())
            
            if question and answer_lines:
                faqs.append({
                    'id': faq_id or str(uuid.uuid4()),
                    'title': title,
                    'question': question,
                    'answer': '\n'.join(answer_lines),
                    'source': source
                })
        
        return faqs


class SolverdeChatbot:
    """
    Chatbot conversacional para Solverde.pt
    Usa ChromaDB para RAG e OpenAI GPT-4 para conversa
    """
    
    def __init__(self, openai_api_key: str, persist_directory: str = "./chroma_db"):
        """
        Inicializa o chatbot
        
        Args:
            openai_api_key: Chave API da OpenAI
            persist_directory: Diretório para guardar a base de dados ChromaDB
        """
        self.client = OpenAI(api_key=openai_api_key)
        self.persist_directory = persist_directory
        
        # Inicializar ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Collection para as FAQs
        try:
            self.collection = self.chroma_client.get_collection(name="solverde_faqs")
            print(f"✓ Collection existente carregada ({self.collection.count()} FAQs)")
        except:
            self.collection = self.chroma_client.create_collection(
                name="solverde_faqs",
                metadata={"description": "Solverde.pt FAQs"}
            )
            print("✓ Nova collection criada")
        
        # Armazenar conversas ativas
        self.conversations: Dict[str, List[Dict]] = {}
    
    def load_faqs_from_file(self, file_path: str):
        """
        Carrega FAQs de um ficheiro markdown e adiciona ao ChromaDB
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        faqs = FAQParser.parse_faq_file(content)
        self.load_faqs(faqs)
    
    def load_faqs(self, faqs: List[Dict]):
        """
        Carrega lista de FAQs para o ChromaDB
        """
        if not faqs:
            print("⚠ Nenhuma FAQ para carregar")
            return
        
        # Preparar dados para ChromaDB
        ids = []
        documents = []
        metadatas = []
        
        for faq in faqs:
            # ID único
            ids.append(faq['id'])
            
            # Documento: combinação de pergunta + resposta para melhor retrieval
            doc_text = f"Pergunta: {faq['question']}\n\nResposta: {faq['answer']}"
            documents.append(doc_text)
            
            # Metadata
            metadatas.append({
                'question': faq['question'],
                'title': faq.get('title', ''),
                'source': faq.get('source', '')
            })
        
        # Adicionar ao ChromaDB (usa embeddings automáticos)
        try:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            print(f"✓ {len(faqs)} FAQs carregadas com sucesso!")
        except Exception as e:
            print(f"✗ Erro ao carregar FAQs: {e}")
    
    def _get_embeddings(self, text: str) -> List[float]:
        """
        Gera embeddings usando OpenAI
        """
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    def _search_relevant_faqs(self, query: str, conversation_history: List[Dict], n_results: int = 3) -> str:
        """
        Procura FAQs relevantes baseado na query e histórico de conversa
        """
        # Construir contexto da conversa para melhor retrieval
        context_parts = []
        
        # Últimas 3 mensagens do histórico
        if conversation_history:
            recent = conversation_history[-6:]  # últimas 3 trocas
            for msg in recent:
                context_parts.append(f"{msg['role']}: {msg['content']}")
        
        # Adicionar query atual
        context_parts.append(f"user: {query}")
        
        # Query combinada
        search_query = "\n".join(context_parts)
        
        # Procurar no ChromaDB
        results = self.collection.query(
            query_texts=[search_query],
            n_results=n_results
        )
        
        # Formatar resultados
        if not results['documents'] or not results['documents'][0]:
            return "Nenhuma FAQ relevante encontrada."
        
        faqs_context = "FAQs RELEVANTES:\n\n"
        
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
            faqs_context += f"FAQ {i}:\n"
            faqs_context += f"{doc}\n"
            if metadata.get('source'):
                faqs_context += f"Fonte: {metadata['source']}\n"
            faqs_context += "\n---\n\n"
        
        return faqs_context
    
    def _build_system_prompt(self, faqs_context: str) -> str:
        """
        Constrói o system prompt com instruções e contexto das FAQs
        """
        return f"""És um assistente virtual do Solverde.pt, especializado em ajudar utilizadores com questões sobre a plataforma.

INSTRUÇÕES IMPORTANTES:

1. **CONHECIMENTO**: Responde APENAS com base nas FAQs fornecidas abaixo. Se a informação não estiver nas FAQs, diz claramente que não tens essa informação específica e sugere contactar o suporte.

2. **CONVERSA NATURAL**: Mantém uma conversa natural, amigável e profissional. Não precisas de dar toda a informação de uma vez - podes fazer perguntas para esclarecer e ajudar melhor.

3. **PEDIR INFORMAÇÃO**: Quando percebes que precisas de mais detalhes para dar uma resposta precisa (ex: qual o banco, método de pagamento, tempo de espera, etc.), pergunta de forma natural e clara. Exemplos:
   - "Para te poder ajudar melhor, podes dizer-me qual é o teu banco?"
   - "Que método de levantamento utilizaste? (transferência bancária, MB Way, cartão, etc.)"
   - "Há quantos dias fizeste o pedido de levantamento?"

4. **SER ESPECÍFICO**: As FAQs muitas vezes têm informação que varia (ex: prazos diferentes por banco, horários específicos). Quando isso acontece, pergunta o necessário para dar a resposta exata para o caso do utilizador.

5. **CONTEXTO**: Lembra-te do que foi dito anteriormente na conversa. Se o utilizador já te deu informação, usa-a sem voltar a perguntar.

6. **TOM**: Usa português de Portugal, com um tom profissional mas acessível. Evita ser demasiado formal ou frio. Mostra empatia quando apropriado.

7. **QUANDO NÃO SABES**: Se a pergunta não está coberta nas FAQs, responde honestamente:
   "Não encontrei informação específica sobre isso nas nossas FAQs. Para te ajudar melhor, podes:
   - Contactar o suporte através do email suporte@solverde.pt
   - Usar o chat ao vivo no site Solverde.pt
   - Ligar para a nossa linha de apoio"

8. **NÃO INVENTES**: Nunca inventes ou assumes informação que não está explicitamente nas FAQs. É melhor admitir que não sabes do que dar informação incorreta.

9. **SAUDAÇÕES**: Responde a cumprimentos de forma amigável e natural, mas mantém o foco em ajudar com as questões do utilizador.

---

{faqs_context}

---

Agora ajuda o utilizador da melhor forma possível, lembrando-te sempre de todo o contexto da conversa."""
    
    def chat(self, session_id: str, user_message: str) -> str:
        """
        Processa uma mensagem do utilizador e retorna a resposta
        
        Args:
            session_id: ID único da sessão/utilizador
            user_message: Mensagem do utilizador
            
        Returns:
            Resposta do assistente
        """
        # Criar ou recuperar conversa
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        conversation = self.conversations[session_id]
        
        # 1. Procurar FAQs relevantes
        faqs_context = self._search_relevant_faqs(user_message, conversation)
        
        # 2. Construir system prompt
        system_prompt = self._build_system_prompt(faqs_context)
        
        # 3. Adicionar mensagem do user ao histórico
        conversation.append({
            "role": "user",
            "content": user_message
        })
        
        # 4. Preparar mensagens para o GPT
        messages = [
            {"role": "system", "content": system_prompt}
        ] + conversation
        
        # 5. Chamar GPT
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Usa gpt-4o-mini se quiseres mais barato
                messages=messages,
                temperature=0.7
            )
            
            assistant_message = response.choices[0].message.content
            
        except Exception as e:
            assistant_message = f"Desculpa, ocorreu um erro ao processar a tua mensagem. Por favor, tenta novamente. (Erro: {str(e)})"
        
        # 6. Adicionar resposta ao histórico
        conversation.append({
            "role": "assistant",
            "content": assistant_message
        })
        
        # 7. Limitar tamanho do histórico (últimas 20 mensagens)
        if len(conversation) > 20:
            conversation = conversation[-20:]
            self.conversations[session_id] = conversation
        
        return assistant_message
    
    def clear_conversation(self, session_id: str):
        """Limpa o histórico de uma conversa"""
        if session_id in self.conversations:
            del self.conversations[session_id]
            print(f"✓ Conversa {session_id} limpa")
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Retorna o histórico de uma conversa"""
        return self.conversations.get(session_id, [])
    
    def export_conversation(self, session_id: str, file_path: str):
        """Exporta conversa para ficheiro JSON"""
        history = self.get_conversation_history(session_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"✓ Conversa exportada para {file_path}")
