from typing import Dict, Any, List, Optional
import time
from rag.chroma_vector_store import get_chroma_vector_store
from rag.reranker import get_reranker

class RAGAgent:
    """
    Enterprise Two-Stage RAG Knowledge Agent:
    Stage 1: ChromaDB Vector Retrieval with strict Multi-Field Metadata Filtering.
    Stage 2: Deep Cross-Encoder attention-based semantic reranker.
    Covers Trichology Science, Clinical Studies, Store Policies, Product Catalog,
    and React UI & Developer Schemas.
    """
    def __init__(self):
        self.chroma_store = get_chroma_vector_store()
        self.reranker = get_reranker()
        self.agent_name = "Two-Stage ChromaDB & Cross-Encoder RAG Agent"

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        candidate_k: int = 8,
        category_filter: Optional[str] = None,
        hair_concern_filter: Optional[str] = None,
        doc_type_filter: Optional[str] = None,
        max_price: Optional[float] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        
        # Stage 1: ChromaDB Vector Search with Metadata Filtering
        candidates = self.chroma_store.search_with_metadata_filter(
            query=query,
            top_k=max(candidate_k, top_k * 2),
            category=category_filter,
            hair_concern=hair_concern_filter,
            doc_type=doc_type_filter,
            max_price=max_price
        )

        # Stage 2: Cross-Encoder Semantic Reranking
        rerank_result = self.reranker.rerank(
            query=query,
            candidates=candidates,
            top_n=top_k
        )
        top_docs = rerank_result["top_docs"]

        context_snippets = []
        citations = []

        for doc in top_docs:
            category = doc.get('category', 'General')
            concern = f" | Concern: {doc.get('hairConcern')}" if doc.get('hairConcern') else ""
            doc_type = f" | Type: {doc.get('doc_type')}" if doc.get('doc_type') else ""
            context_snippets.append(f"[{doc.get('title')} ({category}{concern}{doc_type})]: {doc.get('content')}")
            citations.append({
                "id": doc.get("id"),
                "title": doc.get("title"),
                "category": category,
                "hairConcern": doc.get("hairConcern"),
                "doc_type": doc.get("doc_type"),
                "score": doc.get("score"),
                "cross_score": doc.get("cross_score"),
                "retrieval_source": doc.get("retrieval_source", "chromadb")
            })

        execution_time_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "agent": self.agent_name,
            "status": "success",
            "query": query,
            "top_docs": top_docs,
            "citations": citations,
            "context_text": "\n\n".join(context_snippets),
            "execution_time_ms": execution_time_ms,
            "rerank_time_ms": rerank_result.get("rerank_time_ms", 0.0),
            "total_candidates_evaluated": len(candidates),
            "summary": f"Retrieved {len(candidates)} candidates from ChromaDB, reranked top {len(top_docs)} via Cross-Encoder."
        }
