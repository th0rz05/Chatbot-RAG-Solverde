"""
Solverde.pt Enhanced FAQ Chatbot
Sistema conversacional inteligente com RAG avançado usando ChromaDB e OpenAI
Versão 2.0 - Com hybrid search, embeddings melhorados e streaming
"""

import os
import re
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from openai import OpenAI
from typing import List, Dict, Optional, AsyncIterator
import uuid
import json
from collections import Counter
import math


class FAQParser:
    """Parse FAQs do formato markdown melhorado"""

    @staticmethod
    def parse_faq_file(content: str) -> List[Dict]:
        """
        Parse o ficheiro de FAQs completo e extrai cada FAQ individual
        Suporta o novo formato com categorias, palavras-chave e metadata
        """
        faqs = []

        # Split por ### para separar cada FAQ (novo formato)
        sections = re.split(r'\n### ', content)

        for section in sections[1:]:  # Skip header
            lines = section.strip().split('\n')
            if not lines:
                continue

            # Primeira linha é o título/pergunta principal
            title = lines[0].strip()

            faq_data = {
                'id': str(uuid.uuid4()),
                'title': title,
                'question': '',
                'answer': '',
                'category': '',
                'keywords': '',
                'source': ''
            }

            # Parse metadata e conteúdo
            in_answer = False
            answer_lines = []

            for line in lines[1:]:
                line = line.strip()
                if not line or line.startswith('---'):
                    continue

                if line.startswith('**Categoria**:'):
                    faq_data['category'] = line.replace('**Categoria**:', '').strip()
                elif line.startswith('**Fonte**:'):
                    faq_data['source'] = line.replace('**Fonte**:', '').strip()
                elif line.startswith('**Pergunta**:'):
                    faq_data['question'] = line.replace('**Pergunta**:', '').strip()
                    in_answer = False
                elif line.startswith('**Resposta**:'):
                    in_answer = True
                    # Primeira linha da resposta
                    answer_start = line.replace('**Resposta**:', '').strip()
                    if answer_start:
                        answer_lines.append(answer_start)
                elif line.startswith('**Palavras-chave**:'):
                    faq_data['keywords'] = line.replace('**Palavras-chave**:', '').strip()
                    in_answer = False
                elif in_answer:
                    answer_lines.append(line)

            faq_data['answer'] = '\n'.join(answer_lines)

            if faq_data['question'] and faq_data['answer']:
                faqs.append(faq_data)

        return faqs


class SolverdeChatbot:
    """
    Chatbot conversacional avançado para Solverde.pt
    Features:
    - Hybrid search (semantic + keyword)
    - OpenAI embeddings (text-embedding-3-large)
    - Enhanced prompt engineering
    - Streaming support
    - Smart context management
    """

    def __init__(
        self,
        openai_api_key: str,
        persist_directory: str = "./chroma_db",
        embedding_model: str = "text-embedding-3-large",
        llm_model: str = "gpt-4o",
        temperature: float = 0.7,
        max_context_messages: int = 8,
        retrieval_top_k: int = 5
    ):
        """
        Inicializa o chatbot com configurações avançadas

        Args:
            openai_api_key: Chave API da OpenAI
            persist_directory: Diretório para guardar a base de dados ChromaDB
            embedding_model: Modelo de embeddings (default: text-embedding-3-large)
            llm_model: Modelo LLM (default: gpt-4o)
            temperature: Temperatura para geração (default: 0.7)
            max_context_messages: Máximo de mensagens no contexto (default: 8)
            retrieval_top_k: Número de FAQs a recuperar (default: 5)
        """
        self.client = OpenAI(api_key=openai_api_key)
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.temperature = temperature
        self.max_context_messages = max_context_messages
        self.retrieval_top_k = retrieval_top_k

        # Configurar OpenAI embedding function para ChromaDB
        self.openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=openai_api_key,
            model_name=embedding_model
        )

        # Inicializar ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # Collection para as FAQs com embeddings OpenAI
        try:
            self.collection = self.chroma_client.get_collection(
                name="solverde_faqs_v2",
                embedding_function=self.openai_ef
            )
            print(f"✓ Collection existente carregada ({self.collection.count()} documentos)")
        except:
            self.collection = self.chroma_client.create_collection(
                name="solverde_faqs_v2",
                embedding_function=self.openai_ef,
                metadata={"description": "Solverde.pt FAQs v2 com OpenAI embeddings"}
            )
            print("✓ Nova collection criada com OpenAI embeddings")

        # Armazenar conversas ativas
        self.conversations: Dict[str, List[Dict]] = {}

        # Cache para keyword search (TF-IDF simples)
        self.document_cache: Optional[List[Dict]] = None

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
        Carrega lista de FAQs para o ChromaDB com estratégia de chunking melhorada
        """
        if not faqs:
            print("⚠ Nenhuma FAQ para carregar")
            return

        ids = []
        documents = []
        metadatas = []

        for faq in faqs:
            base_id = faq['id']

            # Chunk 1: Pergunta com resposta curta (para quick matching)
            short_answer = faq['answer'][:300] + "..." if len(faq['answer']) > 300 else faq['answer']
            ids.append(f"{base_id}_q")
            documents.append(f"Pergunta: {faq['question']}\n\nResposta: {short_answer}")
            metadatas.append({
                'question': faq['question'],
                'title': faq.get('title', ''),
                'category': faq.get('category', ''),
                'keywords': faq.get('keywords', ''),
                'source': faq.get('source', ''),
                'chunk_type': 'question_focused',
                'full_id': base_id
            })

            # Chunk 2: Resposta completa (para contexto full)
            ids.append(f"{base_id}_full")
            doc_full = f"Pergunta: {faq['question']}\n\nResposta Completa: {faq['answer']}"
            if faq.get('category'):
                doc_full = f"Categoria: {faq['category']}\n\n" + doc_full
            documents.append(doc_full)
            metadatas.append({
                'question': faq['question'],
                'title': faq.get('title', ''),
                'category': faq.get('category', ''),
                'keywords': faq.get('keywords', ''),
                'source': faq.get('source', ''),
                'chunk_type': 'full_context',
                'full_id': base_id
            })

        # Adicionar ao ChromaDB
        try:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            print(f"✓ {len(faqs)} FAQs carregadas ({len(ids)} chunks)")

            # Atualizar cache de documentos para keyword search
            self.document_cache = None  # Forçar reconstrução do cache

        except Exception as e:
            print(f"✗ Erro ao carregar FAQs: {e}")

    def _semantic_search(
        self,
        query: str,
        conversation_history: List[Dict],
        n_results: int = 10
    ) -> List[tuple]:
        """
        Busca semântica usando ChromaDB embeddings
        Retorna lista de (document, metadata, distance)
        """
        # Construir contexto da conversa
        search_query = self._build_search_context(query, conversation_history)

        # Procurar no ChromaDB
        results = self.collection.query(
            query_texts=[search_query],
            n_results=n_results
        )

        if not results['documents'] or not results['documents'][0]:
            return []

        # Combinar resultados
        semantic_results = []
        for doc, metadata, distance in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ):
            semantic_results.append((doc, metadata, distance))

        return semantic_results

    def _keyword_search(self, query: str, n_results: int = 10) -> List[tuple]:
        """
        Busca por palavras-chave usando TF-IDF simples
        Retorna lista de (document, metadata, score)
        """
        # Obter todos os documentos do ChromaDB (cached)
        if self.document_cache is None:
            all_docs = self.collection.get()
            self.document_cache = [
                (doc, meta) for doc, meta in zip(
                    all_docs['documents'],
                    all_docs['metadatas']
                )
            ]

        # Tokenizar query
        query_tokens = set(self._tokenize(query.lower()))

        # Calcular scores
        scored_docs = []
        for doc, metadata in self.document_cache:
            doc_tokens = self._tokenize(doc.lower())

            # Calcular overlap de palavras
            overlap = len(query_tokens & set(doc_tokens))

            # Bonus para keywords match
            if metadata.get('keywords'):
                kw_tokens = set(self._tokenize(metadata['keywords'].lower()))
                overlap += len(query_tokens & kw_tokens) * 2  # 2x weight

            # Bonus para question match
            if metadata.get('question'):
                q_tokens = set(self._tokenize(metadata['question'].lower()))
                overlap += len(query_tokens & q_tokens) * 1.5  # 1.5x weight

            if overlap > 0:
                # TF-IDF-like score
                tf = overlap / len(doc_tokens) if doc_tokens else 0
                score = tf * math.log(len(self.document_cache) / (overlap + 1))
                scored_docs.append((doc, metadata, score))

        # Ordenar por score
        scored_docs.sort(key=lambda x: x[2], reverse=True)

        return scored_docs[:n_results]

    def _tokenize(self, text: str) -> List[str]:
        """Tokenização simples para português"""
        # Remove pontuação e split por espaços
        tokens = re.findall(r'\b\w+\b', text)
        # Remove stopwords comuns em português
        stopwords = {'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'do', 'da', 'dos', 'das',
                     'em', 'no', 'na', 'nos', 'nas', 'por', 'para', 'com', 'e', 'ou'}
        return [t for t in tokens if t not in stopwords and len(t) > 2]

    def _reciprocal_rank_fusion(
        self,
        semantic_results: List[tuple],
        keyword_results: List[tuple],
        k: int = 60
    ) -> List[Dict]:
        """
        Combina resultados usando Reciprocal Rank Fusion (RRF)
        RRF score = sum(1 / (k + rank_i))
        """
        # Calcular scores RRF
        rrf_scores = {}

        # Processar resultados semânticos
        for rank, (doc, metadata, _) in enumerate(semantic_results, 1):
            doc_id = metadata.get('full_id', str(uuid.uuid4()))
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = {
                    'score': 0,
                    'doc': doc,
                    'metadata': metadata
                }
            rrf_scores[doc_id]['score'] += 1 / (k + rank)

        # Processar resultados de keywords
        for rank, (doc, metadata, _) in enumerate(keyword_results, 1):
            doc_id = metadata.get('full_id', str(uuid.uuid4()))
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = {
                    'score': 0,
                    'doc': doc,
                    'metadata': metadata
                }
            rrf_scores[doc_id]['score'] += 1 / (k + rank)

        # Ordenar por score final
        ranked_results = sorted(
            rrf_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )

        return ranked_results

    def _hybrid_search(
        self,
        query: str,
        conversation_history: List[Dict],
        n_results: int = 5
    ) -> str:
        """
        Busca híbrida combinando semantic + keyword search
        """
        # 1. Busca semântica
        semantic_results = self._semantic_search(query, conversation_history, n_results=10)

        # 2. Busca por keywords
        keyword_results = self._keyword_search(query, n_results=10)

        # 3. Combinar usando RRF
        combined_results = self._reciprocal_rank_fusion(semantic_results, keyword_results)

        # 4. Deduplicate e pegar top N
        seen_full_ids = set()
        unique_results = []
        for result in combined_results:
            full_id = result['metadata'].get('full_id')
            if full_id and full_id not in seen_full_ids:
                seen_full_ids.add(full_id)
                unique_results.append(result)
                if len(unique_results) >= n_results:
                    break

        # 5. Formatar contexto
        if not unique_results:
            return "Nenhuma FAQ relevante encontrada."

        faqs_context = "FAQs RELEVANTES:\n\n"
        for i, result in enumerate(unique_results, 1):
            doc = result['doc']
            metadata = result['metadata']

            faqs_context += f"FAQ {i}:\n"
            faqs_context += f"{doc}\n"

            if metadata.get('category'):
                faqs_context += f"Categoria: {metadata['category']}\n"
            if metadata.get('source'):
                faqs_context += f"Fonte: {metadata['source']}\n"

            faqs_context += "\n---\n\n"

        return faqs_context

    def _build_search_context(
        self,
        query: str,
        conversation_history: List[Dict]
    ) -> str:
        """
        Constrói contexto inteligente para retrieval
        """
        if not conversation_history:
            return query

        context_parts = []

        # Sempre incluir mensagens recentes
        recent_messages = conversation_history[-6:]  # últimas 3 trocas

        # Se conversa é longa, adicionar mensagens relevantes anteriores
        if len(conversation_history) > 6:
            earlier_messages = conversation_history[:-6]
            query_words = set(query.lower().split())

            scored_messages = []
            for msg in earlier_messages:
                if msg['role'] == 'user':
                    msg_words = set(msg['content'].lower().split())
                    overlap = len(query_words & msg_words)
                    if overlap > 0:
                        scored_messages.append((overlap, msg))

            # Top 2 mensagens relevantes
            scored_messages.sort(reverse=True, key=lambda x: x[0])
            relevant_earlier = [msg for _, msg in scored_messages[:2]]

            context_parts.extend([f"{msg['role']}: {msg['content']}" for msg in relevant_earlier])

        # Adicionar mensagens recentes
        context_parts.extend([f"{msg['role']}: {msg['content']}" for msg in recent_messages])

        # Query atual
        context_parts.append(f"user: {query}")

        return "\n".join(context_parts)

    def _build_enhanced_system_prompt(self, faqs_context: str) -> str:
        """
        Constrói system prompt melhorado com few-shot examples
        """
        few_shot_examples = """
EXEMPLOS DE CONVERSAS BEM SUCEDIDAS:

Exemplo 1 - Resposta Direta:
User: Quanto tempo demora o levantamento?
Assistant: Graças aos Levantamentos Flash, podes levantar os teus ganhos de forma imediata na Solverde.pt!

Os prazos variam por método:
- Levantamentos a partir de 20€: imediatos
- Transferência bancária: 72 horas (até 5 dias úteis)
- Paypal, Neteller, Skrill: quase imediato (excepcionalmente até 48h)
- Cartão VISA: 2 a 4 dias úteis

Já fizeste o pedido? Qual método estás a usar?

Exemplo 2 - Pedir Clarificação:
User: Não recebi o meu dinheiro
Assistant: Compreendo a tua preocupação. Para te poder ajudar melhor, preciso de alguns detalhes:
- Trata-se de um levantamento ou depósito?
- Há quantos dias fizeste o pedido?
- Que método de pagamento utilizaste?

Com esta informação consigo dar-te uma resposta mais precisa.

Exemplo 3 - Seguimento com Contexto:
User: Como uso free spins?
Assistant: Para usar as tuas free spins:
1. Aceita a oferta quando aparecer no ecrã
2. Vai à homepage do casino e procura "Joga Free Spins"
3. Escolhe jogos dessa grelha

Podes consultar quantas tens em "Os Meus Bónus" > "Histórico e Código Promocional Casino".

User: E onde fica essa área?
Assistant: É simples! Clica no ícone da tua conta no canto superior direito. Isso abre "Os Meus Bónus". Depois clica em "Histórico e Código Promocional Casino" e verás todas as tuas free spins.
"""

        base_instructions = f"""És um assistente virtual especializado do Solverde.pt. Ajudas utilizadores com questões sobre a plataforma de forma clara, natural e útil.

REGRAS FUNDAMENTAIS:

1. **CONHECIMENTO LIMITADO**: Responde APENAS com informação das FAQs fornecidas. Se não está nas FAQs, diz claramente e sugere contactar suporte@solverde.pt.

2. **CONVERSAÇÃO NATURAL**:
   - Tom amigável e profissional em português de Portugal
   - Não dês toda a informação de uma vez - conversa naturalmente
   - Faz perguntas de clarificação quando necessário
   - Mostra empatia

3. **PEDIR CLARIFICAÇÃO ESTRATÉGICA**:
   Quando a pergunta é vaga, pergunta naturalmente:
   - "Qual é o teu banco?" (para prazos específicos)
   - "Que método de pagamento usaste?"
   - "Há quantos dias fizeste o pedido?"

4. **SER ESPECÍFICO**: As FAQs têm informação detalhada (prazos por banco, horários, etc.). Usa essa especificidade.

5. **CONTEXTO DA CONVERSA**: Lembra-te do que foi dito. Não perguntes informação que o utilizador já te deu.

6. **QUANDO NÃO SABES**:
   "Não encontrei informação específica sobre isso. Para te ajudar melhor:
   - Contacta suporte@solverde.pt
   - Usa o chat ao vivo no site
   - Liga para a linha de apoio"

7. **NUNCA INVENTES**: Não assumes informação que não está nas FAQs. É melhor admitir que não sabes.

8. **ESTRUTURA DE RESPOSTAS**:
   - Respostas simples: 1-2 parágrafos diretos
   - Processos: listas numeradas
   - Múltiplas opções: bullet points
   - Sempre pergunta se precisa de mais esclarecimentos

{few_shot_examples}

---

CONTEXTO DAS FAQs RELEVANTES:

{faqs_context}

---

Responde ao utilizador de forma útil, lembrando-te de todo o contexto da conversa."""

        return base_instructions

    def chat(self, session_id: str, user_message: str) -> str:
        """
        Processa mensagem do utilizador e retorna resposta (não-streaming)

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

        # 1. Busca híbrida de FAQs relevantes
        faqs_context = self._hybrid_search(
            user_message,
            conversation,
            n_results=self.retrieval_top_k
        )

        # 2. Construir system prompt melhorado
        system_prompt = self._build_enhanced_system_prompt(faqs_context)

        # 3. Adicionar mensagem do user ao histórico
        conversation.append({
            "role": "user",
            "content": user_message
        })

        # 4. Preparar mensagens para GPT
        messages = [
            {"role": "system", "content": system_prompt}
        ] + conversation[-self.max_context_messages:]  # Limitar contexto

        # 5. Chamar GPT
        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                temperature=self.temperature
            )

            assistant_message = response.choices[0].message.content

        except Exception as e:
            assistant_message = f"Desculpa, ocorreu um erro ao processar a tua mensagem. Por favor, tenta novamente. (Erro: {str(e)})"

        # 6. Adicionar resposta ao histórico
        conversation.append({
            "role": "assistant",
            "content": assistant_message
        })

        # 7. Limitar tamanho do histórico
        if len(conversation) > 20:
            conversation = conversation[-20:]
            self.conversations[session_id] = conversation

        return assistant_message

    async def chat_stream(self, session_id: str, user_message: str) -> AsyncIterator[Dict]:
        """
        Processa mensagem e faz stream da resposta token por token

        Args:
            session_id: ID único da sessão
            user_message: Mensagem do utilizador

        Yields:
            Dict com {"type": "token", "content": str} ou {"type": "done"}
        """
        # Criar ou recuperar conversa
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        conversation = self.conversations[session_id]

        # 1. Busca híbrida (não async, operação rápida)
        faqs_context = self._hybrid_search(
            user_message,
            conversation,
            n_results=self.retrieval_top_k
        )

        # 2. Construir system prompt
        system_prompt = self._build_enhanced_system_prompt(faqs_context)

        # 3. Adicionar mensagem do user
        conversation.append({
            "role": "user",
            "content": user_message
        })

        # 4. Preparar mensagens
        messages = [
            {"role": "system", "content": system_prompt}
        ] + conversation[-self.max_context_messages:]

        # 5. Stream from OpenAI
        full_response = ""

        try:
            stream = self.client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                temperature=self.temperature,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_response += token
                    yield {"type": "token", "content": token}

            # Signal completion
            yield {"type": "done"}

        except Exception as e:
            yield {"type": "error", "content": str(e)}
            full_response = f"Erro: {str(e)}"

        # 6. Guardar resposta completa no histórico
        conversation.append({
            "role": "assistant",
            "content": full_response
        })

        # 7. Limitar histórico
        if len(conversation) > 20:
            self.conversations[session_id] = conversation[-20:]

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
