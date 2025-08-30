from typing import TypedDict,Annotated,Sequence
import os
import yaml
import json
import os, re, hashlib
from pathlib import Path
from langchain_core.messages import SystemMessage,BaseMessage,ToolMessage,HumanMessage
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langgraph.graph import StateGraph,END
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain.schema import Document
from dotenv import load_dotenv
from md_helpers import load_markdown_documents
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.prompts import ChatPromptTemplate

# -------------------- config --------------------
load_dotenv()

CONTENT_DIR = Path("docs/ajuda")
PERSIST_DIR = Path("db/chroma_solverde") 
COLLECTION_NAME = "solverde_chatbot_v1"

LLM_MODEL = "gpt-4o"
EMB_MODEL = "text-embedding-3-small"

from langchain.prompts import ChatPromptTemplate

CONDENSE_PROMPT = ChatPromptTemplate.from_template(
    "Histórico:\n{history}\n\nPergunta atual: {question}\n\nReformula uma pergunta única e completa em pt-PT."
)


# -------------------- LLM --------------------
llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
embeddings = OpenAIEmbeddings(model=EMB_MODEL)



# -------------------- load documents --------------------
all_docs = load_markdown_documents(CONTENT_DIR)

# optional long document splitting
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,
    chunk_overlap=200,
    separators=["\n### ", "\n## ", "\n# ", "\n\n", "\n", " "]
)
long_docs = [d for d in all_docs if len(d.page_content) > 1500]
short_docs = [d for d in all_docs if len(d.page_content) <= 1500]
docs_split = splitter.split_documents(long_docs)
docs_for_index = short_docs + docs_split

print(f"Loaded {len(all_docs)} FAQs/pages. Indexing {len(docs_for_index)} documents.")

# -------------------- create or update Chroma --------------------
PERSIST_DIR.mkdir(parents=True, exist_ok=True)
vectorstore = Chroma(
    embedding_function=embeddings,
    persist_directory=str(PERSIST_DIR),
    collection_name=COLLECTION_NAME,
)

# deterministic id 
def make_doc_id(d: Document) -> str:
    # try to use first 150 chars of content
    base = d.page_content[:150]
    return hashlib.sha1(base.encode("utf-8")).hexdigest()

doc_ids = [make_doc_id(d) for d in docs_for_index]

# delete existing documents
try:
    vectorstore.delete(ids=doc_ids)
except Exception:
    pass

vectorstore.add_documents(documents=docs_for_index, ids=doc_ids)
print("Vector store ready.")

base_retriever = vectorstore.as_retriever(search_kwargs={"k": 8})
compressor = LLMChainExtractor.from_llm(llm)
retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=base_retriever
)

# -------------------- tool with citation --------------------
@tool
def retriever_tool(query: str) -> str:
    """
    Devolve até 5 evidências compactas no formato JSON string:
    [{"title":..., "source":..., "snippet":...}, ...]
    """

    docs = retriever.invoke(query)  # já comprimidos
    if not docs:
        return json.dumps([])
    items = []
    for d in docs[:5]:
        items.append({
            "title": d.metadata.get("title","Sem título"),
            "source": d.metadata.get("source_url") or d.metadata.get("file"),
            "snippet": d.page_content.strip()[:600]
        })
    return json.dumps(items, ensure_ascii=False)

tools = [retriever_tool]
llm = llm.bind_tools(tools)

# -------------------- Agent state--------------------
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

def should_continue(state: AgentState):
    result = state["messages"][-1]
    return hasattr(result, "tool_calls") and len(result.tool_calls) > 0

system_prompt = """
És um assistente para a Ajuda Solverde.pt.

REGRAS:
1) Antes de responder usa SEMPRE o retriever_tool com a pergunta do utilizador.
2) Se a resposta depender de um detalhe do utilizador (ex.: banco, método de pagamento, dispositivo, localização, tipo de bónus), faz UMA pergunta de follow-up objetiva para escolher a opção certa. Se houver poucas opções, lista-as numeradas + 'Outro'.
3) Só depois de obter a resposta do utilizador volta a usar o retriever_tool e dá a resposta final.
4) Responde de forma curta e natural em pt-PT (3 a 6 linhas). Não copies texto das fontes.
5) Termina com: "Para mais detalhes, consulta: <título> (<url>)" (1 ou 2 fontes no máx.).
6) Se não houver evidência suficiente, diz que não encontraste nas fontes e sugere a página de Ajuda/Contactos.
"""



tools_dict = {t.name: t for t in tools}


# -------------------- graph nodes --------------------
def call_llm(state: AgentState) -> AgentState:
    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
    msg = llm.invoke(messages)
    return {"messages": [msg]}

def take_action(state: AgentState) -> AgentState:
    tool_calls = state["messages"][-1].tool_calls
    results = []
    for t in tool_calls:
        if t["name"] == "retriever_tool":
            result = retriever_tool.invoke(t["args"].get("query",""))
        else:
            result = "[]"
        results.append(ToolMessage(tool_call_id=t["id"], name=t["name"], content=result))
    return {"messages": results}

graph = StateGraph(AgentState)
graph.add_node("llm", call_llm)
graph.add_node("retriever_agent", take_action)
graph.add_conditional_edges("llm", should_continue, {True: "retriever_agent", False: END})
graph.add_edge("retriever_agent", "llm")
graph.set_entry_point("llm")
rag_agent = graph.compile()


# -------------------- runner --------------------

def condense_question(history_msgs: Sequence[BaseMessage], question: str) -> str:
    # junta últimas 6 trocas no máximo
    hist = []
    for m in history_msgs[-12:]:
        role = "U" if isinstance(m, HumanMessage) else "A"
        hist.append(f"{role}: {m.content}")
    hist_text = "\n".join(hist)
    prompt = CONDENSE_PROMPT.format_messages(history=hist_text, question=question)
    return llm.invoke(prompt).content.strip()

def running_agent():
    print("\n=== RAG AJUDA SOLVERDE ===")
    history: list[BaseMessage] = []
    while True:
        user_input = input("\nPergunta: ").strip()
        if user_input.lower() in ["exit","quit","sair"]:
            break

        # reformula com contexto curto
        condensed = condense_question(history, user_input)

        messages = history + [HumanMessage(content=condensed)]
        result = rag_agent.invoke({"messages": messages})
        answer = result["messages"][-1].content
        print("\n=== RESPOSTA ===")
        print(answer)

        # mantém histórico curto
        history = (history + [HumanMessage(content=user_input), result["messages"][-1]])[-12:]


if __name__ == "__main__":
    running_agent()
    