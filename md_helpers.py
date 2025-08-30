import re
import yaml
from pathlib import Path
from typing import List
from langchain.schema import Document

# -------------------- helpers markdown --------------------
FM_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)

def parse_front_matter(text: str):
    m = FM_RE.match(text)
    if not m:
        return {}, text
    fm = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)
    return fm, body

def split_faq_blocks(body: str):
    """
    divide por headings nível 2: cada '## Título' vira um bloco
    devolve lista de tuplos (title, content)
    """
    parts = re.split(r"(?m)^##\s+", body)
    heads = re.findall(r"(?m)^##\s+(.+)$", body)
    blocks = []
    if heads:
        for h, content in zip(heads, parts[1:]):
            blocks.append((h.strip(), content.strip()))
    return blocks

def extract_meta_and_body(block_content: str):
    """
    do conteúdo do bloco remove linhas de meta:
    'Fonte: ...'  'ID: ...'  'Atualizado: ...' (opcional)
    retorna dict meta e o corpo limpo
    """
    lines = [l.rstrip() for l in block_content.splitlines()]
    source_url = None
    faq_id = None
    updated_at = None

    body_lines = []
    for l in lines:
        if l.startswith("Fonte:"):
            source_url = l.split(":", 1)[1].strip()
        elif l.startswith("ID:"):
            faq_id = l.split(":", 1)[1].strip()
        elif l.startswith("Atualizado:"):
            updated_at = l.split(":", 1)[1].strip()
        else:
            body_lines.append(l)
    body = "\n".join(body_lines).strip()
    return {"source_url": source_url, "id": faq_id, "updated_at": updated_at}, body

def load_markdown_documents(root: Path) -> List[Document]:
    """
    percorre todos os .md de root, cria Document por cada FAQ (##)
    """
    docs: List[Document] = []
    for md_path in root.rglob("*.md"):
        text = md_path.read_text(encoding="utf-8")
        fm, body = parse_front_matter(text)
        blocks = split_faq_blocks(body)
        if not blocks:
            # ficheiro sem ##, indexa como um único doc tipo "page"
            meta = {
                "title": fm.get("title") or md_path.stem.replace("-", " ").title(),
                "source_url": fm.get("source_url"),
                "id": fm.get("id"),
                "updated_at": fm.get("updated_at"),
                "section": fm.get("section"),
                "subcategory": fm.get("subcategory"),
                "lang": fm.get("lang", "pt-PT"),
                "doc_type": fm.get("doc_type", "page"),
                "file": str(md_path),
            }
            docs.append(Document(page_content=body.strip(), metadata=meta))
            continue

        # ficheiro com várias FAQs
        for idx, (title, content) in enumerate(blocks, start=1):
            meta_block, clean_body = extract_meta_and_body(content)
            doc_meta = {
                "title": title,
                "source_url": meta_block.get("source_url") or fm.get("source_url"),
                "id": meta_block.get("id"),
                "updated_at": meta_block.get("updated_at"),
                "section": fm.get("section"),
                "subcategory": fm.get("subcategory"),
                "lang": fm.get("lang", "pt-PT"),
                "doc_type": "faq",
                "file": str(md_path),
                "index_in_file": idx,
            }
            # garante prefixo Q e A se não existir
            body_text = clean_body.strip()
            if not body_text.lower().startswith("q:"):
                body_text = f"Q: {title}\n{body_text}"
            # mantém A: se existir, senão só o corpo
            docs.append(Document(page_content=body_text, metadata=doc_meta))
    return docs