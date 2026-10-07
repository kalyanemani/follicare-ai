import re
from typing import List, Dict, Any, Optional

class TextChunker:
    """
    Multi-strategy text chunker for Hair Health & Cosmetics knowledge base and product documents.
    Supports recursive character chunking, token-aware splitting, and semantic field chunking.
    """

    def __init__(self, chunk_size: int = 250, chunk_overlap: int = 40):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def recursive_split(self, text: str, separators: Optional[List[str]] = None) -> List[str]:
        """
        Recursively splits text by prioritized delimiters: paragraphs, sentences, commas, words.
        """
        if separators is None:
            separators = ["\n\n", "\n", ". ", "; ", ", ", " "]

        text = text.strip()
        if not text:
            return []

        if len(text) <= self.chunk_size:
            return [text]

        # Find the highest priority separator that exists in text
        chosen_sep = ""
        for sep in separators:
            if sep in text:
                chosen_sep = sep
                break

        if not chosen_sep:
            # Fallback to arbitrary slice
            chunks = []
            start = 0
            while start < len(text):
                end = min(start + self.chunk_size, len(text))
                chunks.append(text[start:end].strip())
                start += self.chunk_size - self.chunk_overlap
            return [c for c in chunks if c]

        splits = text.split(chosen_sep)
        chunks = []
        current_chunk = ""

        for split in splits:
            piece = split.strip()
            if not piece:
                continue

            candidate = f"{current_chunk}{chosen_sep}{piece}" if current_chunk else piece

            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # Handle piece larger than chunk size recursively
                if len(piece) > self.chunk_size:
                    next_separators = separators[separators.index(chosen_sep) + 1:] if chosen_sep in separators else None
                    sub_chunks = self.recursive_split(piece, next_separators)
                    chunks.extend(sub_chunks[:-1])
                    current_chunk = sub_chunks[-1] if sub_chunks else ""
                else:
                    current_chunk = piece

        if current_chunk:
            chunks.append(current_chunk.strip())

        return [c for c in chunks if c]

    def chunk_product(self, product: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Semantic field chunker for hair cosmetic products.
        Splits product metadata into focused semantic chunks for fine-grained retrieval.
        """
        chunks = []
        prod_id = product.get("id", "prod_unknown")
        prod_name = product.get("name", "Product")
        category = product.get("category", "Hair Care")
        concern = product.get("hairConcern", "All Hair Types")
        price = product.get("price", 0.0)
        actives = ", ".join(product.get("activeIngredients", []))
        benefits = ", ".join(product.get("benefits", []))
        specs = ", ".join(product.get("specs", []))
        clinical = product.get("clinicalResult", "")
        usage = product.get("usageInstructions", "")

        # 1. Core overview chunk
        overview_text = (
            f"{prod_name} is a premium {category} formula designed for {concern}. "
            f"Price: ${price:.2f}. Key Actives: {actives}. Benefits: {benefits}. "
            f"{product.get('description', '')}"
        )
        chunks.append({
            "id": f"{prod_id}_overview",
            "product_id": prod_id,
            "title": f"{prod_name} - Overview & Actives",
            "category": "Product",
            "hairConcern": concern,
            "content": overview_text,
            "keywords": [prod_name.lower(), category.lower(), concern.lower()] + [a.lower() for a in product.get("activeIngredients", [])]
        })

        # 2. Clinical and usage chunk (if present)
        if clinical or usage or specs:
            clinical_text = (
                f"{prod_name} Clinical & Application Details: "
                f"Clinical Efficacy: {clinical}. "
                f"How to use: {usage}. "
                f"Key Specifications: {specs}."
            )
            chunks.append({
                "id": f"{prod_id}_usage",
                "product_id": prod_id,
                "title": f"{prod_name} - Clinical Study & Usage",
                "category": "Product_Clinical",
                "hairConcern": concern,
                "content": clinical_text,
                "keywords": [prod_name.lower(), "clinical", "usage", "how to apply", "routine"]
            })

        return chunks
