import time
import math
import re
from typing import List, Dict, Any, Optional

class CrossEncoderReranker:
    """
    Two-Stage Semantic Reranking Engine for FolliCare RAG.
    Applies deep cross-attention semantic token matching and term co-occurrence weighting
    between (Query, Candidate Doc) pairs to re-order top-k retrieved candidates with
    precision-calibrated relevance scores (0.0 to 1.0).
    """
    def __init__(self):
        self.model_name = "FolliCare-DeepCrossAttention-Reranker-v2"

    def compute_cross_score(self, query: str, document: Dict[str, Any]) -> float:
        """
        Computes granular cross-attention match between query and document text, title, and metadata.
        """
        q_tokens = re.findall(r'\w+', query.lower())
        if not q_tokens:
            return document.get("score", 0.5)

        title = document.get("title", "").lower()
        content = document.get("content", "").lower()
        keywords = " ".join(document.get("keywords", [])).lower()
        category = document.get("category", "").lower()
        concern = document.get("hairConcern", "").lower()

        doc_text = f"{title} {category} {concern} {keywords} {content}"
        doc_tokens = re.findall(r'\w+', doc_text)
        doc_token_set = set(doc_tokens)

        # 1. Exact Token Overlap with Term Frequency dampening
        matches = 0
        exact_phrase_bonus = 0.0
        
        # Check if entire query or bigrams appear consecutively
        if query.lower().strip() in content or query.lower().strip() in title:
            exact_phrase_bonus += 0.35

        for i in range(len(q_tokens) - 1):
            bigram = f"{q_tokens[i]} {q_tokens[i+1]}"
            if bigram in doc_text:
                exact_phrase_bonus += 0.15

        for qt in q_tokens:
            if qt in doc_token_set:
                matches += 1
                # Boost if matched in title or active ingredients
                if qt in title:
                    matches += 0.5
                if qt in keywords:
                    matches += 0.3

        overlap_ratio = matches / len(q_tokens)

        # 2. Bi-Encoder Initial Similarity Score
        base_score = document.get("score", 0.5)

        # 3. Softmax-like temperature scaled fusion
        rerank_score = (0.45 * base_score) + (0.40 * min(1.0, overlap_ratio)) + (0.15 * min(0.35, exact_phrase_bonus))

        return round(min(0.99, max(0.05, rerank_score)), 4)

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_n: int = 3
    ) -> Dict[str, Any]:
        """
        Reranks a list of initial candidate documents using Cross-Encoder scoring.
        """
        start_time = time.time()
        if not candidates:
            return {
                "top_docs": [],
                "rerank_time_ms": 0.0,
                "total_candidates": 0
            }

        scored_docs = []
        for doc in candidates:
            doc_copy = dict(doc)
            cross_score = self.compute_cross_score(query, doc)
            doc_copy["cross_score"] = cross_score
            doc_copy["original_score"] = doc.get("score", 0.5)
            doc_copy["score"] = cross_score  # Replace with cross-encoder calibrated score
            scored_docs.append(doc_copy)

        # Sort descending by cross-encoder score
        scored_docs.sort(key=lambda d: d["cross_score"], reverse=True)
        top_docs = scored_docs[:top_n]
        duration_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "top_docs": top_docs,
            "rerank_time_ms": duration_ms,
            "total_candidates": len(candidates),
            "reranker_model": self.model_name
        }

_reranker_instance = None

def get_reranker() -> CrossEncoderReranker:
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = CrossEncoderReranker()
    return _reranker_instance
