"""RAG retrieval tool for banking policy queries in CrewAI.

Task 3-5 & Task 7 requirements:
- Queries the indexed ChromaDB knowledge base collections (sentence-based / fixed-overlap).
- Provides resilient local knowledge base fallback from Markdown documents.
- Dispatched via declared argument schema (query: str).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

CHROMA_DIR = Path(__file__).resolve().parent.parent / "chroma_db"
KB_DIR = Path(__file__).resolve().parent.parent / "knowledge_base"
SENTENCE_COLLECTION = "banking_sentence_chunks"
FIXED_COLLECTION = "banking_fixed_overlap_chunks"


class RAGQueryInput(BaseModel):
    """Input schema for RAG policy retrieval."""
    query: str = Field(
        ...,
        description="The banking policy, procedure, fee, or rate question to search in the knowledge base.",
    )


def _direct_kb_fallback_search(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """Simple term-matching fallback over markdown knowledge base files."""
    if not KB_DIR.exists():
        return []

    query_tokens = set(query.lower().split())
    scored_docs: list[dict[str, Any]] = []

    for file_path in KB_DIR.glob("*.md"):
        content = file_path.read_text(encoding="utf-8")
        title = file_path.stem.replace("_", " ").title()
        content_lower = content.lower()
        score = sum(1 for token in query_tokens if token in content_lower)
        if score > 0:
            scored_docs.append({
                "document_name": file_path.name,
                "title": title,
                "score": round(score / max(1, len(query_tokens)), 4),
                "text": content.strip()[:600],
            })

    scored_docs.sort(key=lambda x: x["score"], reverse=True)
    return scored_docs[:top_k]


def search_knowledge_base(query: str, collection_name: str = SENTENCE_COLLECTION, top_k: int = 3) -> list[dict[str, Any]]:
    """Retrieve top-k relevant chunks from ChromaDB or fallback to Markdown KB."""
    hits: list[dict[str, Any]] = []

    # Attempt ChromaDB retrieval if available
    if CHROMA_DIR.exists():
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(CHROMA_DIR))
            # Try sentence chunks first, then fixed overlap
            coll = None
            try:
                coll = client.get_collection(collection_name)
            except Exception:
                try:
                    coll = client.get_collection(FIXED_COLLECTION)
                except Exception:
                    pass

            if coll and coll.count() > 0:
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
                q_emb = model.encode(query, normalize_embeddings=True).tolist()
                results = coll.query(
                    query_embeddings=[q_emb],
                    n_results=min(top_k, coll.count()),
                    include=["documents", "metadatas", "distances"],
                )
                docs = results.get("documents", [[]])[0]
                metas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]

                for i, doc in enumerate(docs):
                    meta = metas[i] if i < len(metas) else {}
                    # Cosine similarity = 1 - cosine distance
                    sim = round(1.0 - float(distances[i]), 4) if distances else 0.8
                    hits.append({
                        "document_name": meta.get("document_name", "unknown.md"),
                        "chunk_id": meta.get("chunk_id", f"chunk_{i}"),
                        "similarity_score": sim,
                        "text": doc,
                    })
                return hits
        except Exception:
            # Fall through to direct file fallback
            pass

    # Direct KB markdown fallback
    fallback_hits = _direct_kb_fallback_search(query, top_k=top_k)
    return fallback_hits


class RAGTool(BaseTool):
    """CrewAI tool for retrieving banking policy information."""

    name: str = "rag_policy_retrieval_tool"
    description: str = (
        "Retrieve official Cred banking policy details, interest rates, fees, KYC rules, "
        "and dispute procedures. Always use this tool for any policy or general banking inquiry."
    )
    args_schema: Type[BaseModel] = RAGQueryInput

    def _run(self, query: str) -> str:
        results = search_knowledge_base(query)
        if not results:
            return json.dumps({
                "message": "No relevant policy documents found for the given query.",
                "query": query,
                "retrieved_chunks": [],
            })

        return json.dumps({
            "query": query,
            "retrieved_count": len(results),
            "results": results,
        }, indent=2)


# Module export instance
rag_tool = RAGTool()

