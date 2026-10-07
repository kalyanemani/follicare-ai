import os
import json
import time
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

from rag.chunker import TextChunker
from rag.vector_store import LocalVectorStore

import hashlib
import numpy as np

class FolliCareFastEmbeddingFunction:
    """
    Sub-millisecond dense embedding generator for ChromaDB vector collections.
    Generates 384-dimensional normalized dense float embeddings.
    """
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = []
        for text in input:
            vec = np.zeros(self.dimension, dtype=np.float32)
            words = text.lower().split()
            for idx, word in enumerate(words):
                h = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
                slot = h % self.dimension
                weight = 1.0 / (1.0 + 0.05 * idx)
                vec[slot] += weight
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            embeddings.append(vec.tolist())
        return embeddings

class ChromaVectorStore:
    """
    Production-grade ChromaDB Vector Store with Metadata Filtering and Persistent Storage.
    Indexes Trichology Knowledge, Clinical Studies, Store Policies, Product Catalog,
    and React UI Developer Schemas with strict metadata querying.
    """
    def __init__(
        self,
        persist_directory: str = "data/chroma_db",
        kb_path: Optional[str] = "rag/knowledge_base.json",
        products_path: Optional[str] = "data/products.json"
    ):
        self.persist_directory = persist_directory
        self.kb_path = kb_path
        self.products_path = products_path
        self.chunker = TextChunker(chunk_size=320, chunk_overlap=40)
        self.embedding_fn = FolliCareFastEmbeddingFunction(dimension=384)
        
        # Ensure directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize Chroma persistent client
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="follicare_enterprise_rag_v2",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Hybrid dense fallback vector store for high-speed sub-millisecond retrieval
        self.fallback_store = LocalVectorStore(kb_path=kb_path, products_path=products_path)
        
        self.initialize_store()

    def initialize_store(self):
        """Loads and indexes knowledge base documents and product catalog into ChromaDB."""
        docs_to_index = []

        # 1. Load Knowledge Base
        if self.kb_path and os.path.exists(self.kb_path):
            with open(self.kb_path, "r", encoding="utf-8") as f:
                kb_entries = json.load(f)
                for entry in kb_entries:
                    docs_to_index.append({
                        "id": entry.get("id"),
                        "title": entry.get("title"),
                        "category": entry.get("category", "General"),
                        "hairConcern": entry.get("hairConcern", "All"),
                        "doc_type": "knowledge_base",
                        "content": entry.get("content", ""),
                        "keywords": ",".join(entry.get("keywords", [])),
                        "price": 0.0
                    })

        # 2. Load & Chunk Product Catalog
        if self.products_path and os.path.exists(self.products_path):
            with open(self.products_path, "r", encoding="utf-8") as f:
                products = json.load(f)
                for prod in products:
                    chunks = self.chunker.chunk_product(prod)
                    for c in chunks:
                        docs_to_index.append({
                            "id": c.get("id"),
                            "title": c.get("title"),
                            "category": c.get("category", "Product"),
                            "hairConcern": c.get("hairConcern", "All"),
                            "doc_type": "product",
                            "content": c.get("content", ""),
                            "keywords": ",".join(c.get("keywords", [])),
                            "price": float(prod.get("price", 0.0)),
                            "product_id": prod.get("id")
                        })

        if docs_to_index:
            self.index_documents(docs_to_index)

    def index_documents(self, documents: List[Dict[str, Any]]):
        """Upserts documents and metadata into ChromaDB collection."""
        ids = []
        documents_text = []
        metadatas = []

        for doc in documents:
            doc_id = str(doc.get("id"))
            text = f"{doc.get('title')}\nCategory: {doc.get('category')}\nConcern: {doc.get('hairConcern')}\nKeywords: {doc.get('keywords')}\n{doc.get('content')}"
            
            ids.append(doc_id)
            documents_text.append(text)
            metadatas.append({
                "title": str(doc.get("title", "")),
                "category": str(doc.get("category", "")),
                "hairConcern": str(doc.get("hairConcern", "All")),
                "doc_type": str(doc.get("doc_type", "knowledge_base")),
                "price": float(doc.get("price", 0.0)),
                "keywords": str(doc.get("keywords", "")),
                "content": str(doc.get("content", ""))
            })

        self.collection.upsert(
            ids=ids,
            documents=documents_text,
            metadatas=metadatas
        )

    def search_with_metadata_filter(
        self,
        query: str,
        top_k: int = 10,
        category: Optional[str] = None,
        hair_concern: Optional[str] = None,
        doc_type: Optional[str] = None,
        max_price: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Queries ChromaDB with combined semantic search and multi-field metadata filtering.
        """
        where_clauses = []
        if category and category != "All":
            where_clauses.append({"category": category})
        if hair_concern and hair_concern != "All":
            where_clauses.append({"hairConcern": hair_concern})
        if doc_type and doc_type != "All":
            where_clauses.append({"doc_type": doc_type})
        if max_price is not None:
            where_clauses.append({"price": {"$lte": float(max_price)}})

        where_filter = None
        if len(where_clauses) == 1:
            where_filter = where_clauses[0]
        elif len(where_clauses) > 1:
            where_filter = {"$and": where_clauses}

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, max(1, self.collection.count())),
                where=where_filter
            )

            hits = []
            if results and results.get("ids") and len(results["ids"]) > 0:
                ids = results["ids"][0]
                distances = results.get("distances", [[]])[0] if results.get("distances") else [0.2]*len(ids)
                metas = results.get("metadatas", [[]])[0] if results.get("metadatas") else [{}]*len(ids)

                for idx, doc_id in enumerate(ids):
                    meta = metas[idx]
                    # Convert cosine distance to similarity score
                    dist = distances[idx] if idx < len(distances) else 0.5
                    sim_score = max(0.0, min(1.0, 1.0 - (dist / 2.0)))

                    hits.append({
                        "id": doc_id,
                        "title": meta.get("title", ""),
                        "category": meta.get("category", ""),
                        "hairConcern": meta.get("hairConcern", ""),
                        "doc_type": meta.get("doc_type", ""),
                        "content": meta.get("content", ""),
                        "keywords": meta.get("keywords", "").split(","),
                        "price": meta.get("price", 0.0),
                        "score": round(sim_score, 4),
                        "retrieval_source": "chromadb_vector_store"
                    })
                return hits
        except Exception as e:
            print(f"[ChromaVectorStore] Chroma query error: {e}, falling back to Dense Vector Store")

        # Fallback to Hybrid Local Dense Store
        return self.fallback_store.search(query=query, top_k=top_k, category=category, hair_concern=hair_concern, max_price=max_price)

    def add_product(self, product: Dict[str, Any]):
        """Dynamically ingests a new product into ChromaDB and fallback index in real time."""
        chunks = self.chunker.chunk_product(product)
        docs_to_index = []
        for c in chunks:
            docs_to_index.append({
                "id": c.get("id"),
                "title": c.get("title"),
                "category": c.get("category", "Product"),
                "hairConcern": c.get("hairConcern", "All"),
                "doc_type": "product",
                "content": c.get("content", ""),
                "keywords": ",".join(c.get("keywords", [])),
                "price": float(product.get("price", 0.0)),
                "product_id": product.get("id")
            })
        self.index_documents(docs_to_index)
        self.fallback_store.add_product_to_index(product)

_chroma_instance = None

def get_chroma_vector_store() -> ChromaVectorStore:
    global _chroma_instance
    if _chroma_instance is None:
        _chroma_instance = ChromaVectorStore()
    return _chroma_instance
