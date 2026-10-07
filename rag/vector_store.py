import json
import os
import time
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from rag.chunker import TextChunker

class LocalVectorStore:
    """
    Lightweight, high-performance in-memory semantic vector store for Hair Health Cosmetics.
    Uses TF-IDF sublinear n-gram embeddings (unigram, bigram, trigram) with cosine similarity
    and BM25-style keyword boosting.
    Supports real-time dynamic document ingestion and chunking without cloud dependencies.
    """
    def __init__(self, kb_path: Optional[str] = None, products_path: Optional[str] = None):
        self.chunker = TextChunker(chunk_size=300, chunk_overlap=40)
        self.documents: List[Dict[str, Any]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.doc_vectors: Optional[np.ndarray] = None
        self.kb_path = kb_path
        self.products_path = products_path

        self.initialize_store()

    def initialize_store(self):
        """Loads and chunks knowledge base entries and product catalog."""
        all_docs = []

        # 1. Load Knowledge Base
        if self.kb_path and os.path.exists(self.kb_path):
            with open(self.kb_path, "r", encoding="utf-8") as f:
                kb_entries = json.load(f)
                all_docs.extend(kb_entries)

        # 2. Load & Chunk Products
        if self.products_path and os.path.exists(self.products_path):
            with open(self.products_path, "r", encoding="utf-8") as f:
                products = json.load(f)
                for prod in products:
                    prod_chunks = self.chunker.chunk_product(prod)
                    all_docs.extend(prod_chunks)

        self.build_index(all_docs)

    def build_index(self, docs: List[Dict[str, Any]]):
        """Builds n-gram TF-IDF vector matrix for all chunked documents."""
        self.documents = docs
        if not docs:
            self.vectorizer = None
            self.doc_vectors = None
            return

        corpus = []
        for doc in docs:
            keywords_str = " ".join(doc.get("keywords", []))
            concern_str = doc.get("hairConcern", "")
            full_text = f"{doc.get('title', '')}. {concern_str}. {keywords_str}. {doc.get('content', '')}"
            corpus.append(full_text)

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            sublinear_tf=True,
            stop_words='english',
            min_df=1
        )
        self.doc_vectors = self.vectorizer.fit_transform(corpus).toarray()

    def add_product_to_index(self, product: Dict[str, Any]):
        """Dynamically chunks and adds a newly created product into the live vector index."""
        new_chunks = self.chunker.chunk_product(product)
        # Remove any existing chunks for this product
        prod_id = product.get("id")
        existing_docs = [d for d in self.documents if d.get("product_id") != prod_id and d.get("id") != prod_id]
        existing_docs.extend(new_chunks)
        self.build_index(existing_docs)

    def search(
        self,
        query: str,
        top_k: int = 3,
        category_filter: Optional[str] = None,
        hair_concern_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic retrieval against stored hair health documents & products.
        """
        if not self.documents or self.vectorizer is None or self.doc_vectors is None:
            return []

        query_vec = self.vectorizer.transform([query]).toarray()
        scores = cosine_similarity(query_vec, self.doc_vectors)[0]

        # Keyword & domain match boost
        query_words = set(query.lower().split())
        boosted_scores = scores.copy()

        for idx, doc in enumerate(self.documents):
            doc_keywords = set(k.lower() for k in doc.get("keywords", []))
            doc_title_words = set(doc.get("title", "").lower().split())
            intersection = query_words.intersection(doc_keywords | doc_title_words)
            if intersection:
                boosted_scores[idx] += 0.20 * len(intersection)

            if category_filter and doc.get("category") != category_filter:
                boosted_scores[idx] = -1.0

            if hair_concern_filter and doc.get("hairConcern") != hair_concern_filter:
                boosted_scores[idx] -= 0.15

        # Rank indices
        top_indices = np.argsort(boosted_scores)[::-1]

        results = []
        for idx in top_indices:
            score = float(boosted_scores[idx])
            if score <= 0.05 and len(results) > 0:
                continue
            doc = self.documents[idx].copy()
            doc["relevance_score"] = round(min(1.0, max(0.0, score)), 3)
            results.append(doc)
            if len(results) >= top_k:
                break

        return results

# Singleton instance
_store_instance = None

def get_vector_store() -> LocalVectorStore:
    global _store_instance
    if _store_instance is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        kb_path = os.path.join(base_dir, "rag", "knowledge_base.json")
        products_path = os.path.join(base_dir, "data", "products.json")
        _store_instance = LocalVectorStore(kb_path, products_path)
    return _store_instance

def reload_vector_store() -> LocalVectorStore:
    global _store_instance
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kb_path = os.path.join(base_dir, "rag", "knowledge_base.json")
    products_path = os.path.join(base_dir, "data", "products.json")
    _store_instance = LocalVectorStore(kb_path, products_path)
    return _store_instance
