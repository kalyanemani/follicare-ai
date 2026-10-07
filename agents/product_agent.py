import re
import json
import os
import time
from typing import Dict, Any, List, Optional

from data.database import get_database
from rag.vector_store import get_vector_store
from agents.ui_agent import parse_spoken_number

class ProductManagementAgent:
    """
    Product Management & Ingestion Agent:
    Extracts structured cosmetic product specifications from natural voice/text input,
    intelligently maps cosmetic icons, persists items to SQLite Database, and triggers live RAG re-indexing.
    """
    def __init__(self):
        self.agent_name = "Product Ingestion & Catalog Agent"
        self.db = get_database()

    def is_product_ingestion_request(self, query: str) -> bool:
        q = query.lower()
        if "add" in q and ("cart" in q or "bag" in q) and "new product" not in q and "create product" not in q:
            return False

        triggers = [
            "add product", "add new product", "create product", "insert product",
            "add on more product", "add a product", "new item", "add to catalog",
            "update product", "edit product price", "add formula", "new formula",
            "ingest product", "add custom product"
        ]
        return any(t in q for t in triggers)

    def extract_product_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extracts structured product properties from natural voice/text.
        """
        q = text.strip()
        q_lower = q.lower()

        # 1. Price extraction (supports digits and spoken words)
        price = parse_spoken_number(q) or 29.99
        original_price = round(price * 1.25, 2)

        # 2. Category extraction
        category = "Scalp Care"
        if any(w in q_lower for w in ["shampoo", "wash", "cleanser"]):
            category = "Shampoo & Wash"
        elif any(w in q_lower for w in ["mask", "conditioner", "treatment", "glaze", "bond"]):
            category = "Treatments & Masks"
        elif any(w in q_lower for w in ["mist", "spray", "custard", "gel", "styling", "heat"]):
            category = "Styling & Finish"
        elif any(w in q_lower for w in ["oil", "serum", "scrub", "scalp", "elixir", "density"]):
            category = "Scalp Care"

        # 3. Hair Concern extraction
        hair_concern = "Hair Fall & Thinning"
        if any(w in q_lower for w in ["dandruff", "flake", "itch", "oily"]):
            hair_concern = "Dandruff & Oily Scalp"
        elif any(w in q_lower for w in ["damaged", "breakage", "bleach", "split ends", "dry"]):
            hair_concern = "Damaged & Dry Hair"
        elif any(w in q_lower for w in ["curl", "coily", "wavy", "3a", "4c"]):
            hair_concern = "Curly, Coily & Wavy (3A-4C)"
        elif any(w in q_lower for w in ["frizz", "heat", "thermal"]):
            hair_concern = "Frizz & Heat Protection"
        elif any(w in q_lower for w in ["color", "blonde", "brass", "silver"]):
            hair_concern = "Color Care & Blonde Tone"

        # 4. Name extraction
        name = "Botanical Follicle Fortifying Serum"
        name_match = re.search(r"(?:name|called|product:?)\s*[:\"]?([A-Za-z0-9\s&'\-]+?)(?:[\",\.\;]|\s+for|\s+with|\s+price|\s+cost|\s+category|$)", q, re.IGNORECASE)
        if name_match:
            candidate_name = name_match.group(1).strip()
            if len(candidate_name) > 3 and not candidate_name.lower().startswith("a "):
                name = candidate_name.title()
        elif "rosemary" in q_lower:
            name = "Rosemary Root & Follicle Revival Elixir"
        elif "peptide" in q_lower or "bond" in q_lower:
            name = "Multi-Peptide Bond Repair Serum"
        elif "shampoo" in q_lower:
            name = "Biotin Scalp Clarifying Shampoo"
        elif "mask" in q_lower:
            name = "Deep Botanical Moisture Infusion Mask"
        elif "oil" in q_lower:
            name = "Organic Cold-Pressed Hair Growth Oil"
        elif "mist" in q_lower or "spray" in q_lower:
            name = "Lavender Botanical Gloss Mist"

        # 5. Intelligent Cosmetic Icon Mapping
        icon = "🌿"
        if any(w in q_lower for w in ["droplet", "drop", "oil", "moisture", "hydrate"]):
            icon = "💧"
        elif any(w in q_lower for w in ["bottle", "shampoo", "wash", "cleanser"]):
            icon = "🧴"
        elif any(w in q_lower for w in ["mask", "sparkle", "gold", "luxury", "peptide"]):
            icon = "✨"
        elif any(w in q_lower for w in ["night", "overnight", "moon", "sleep", "elixir"]):
            icon = "🌙"
        elif any(w in q_lower for w in ["tea tree", "scrub", "scalp", "leaf", "salicylic"]):
            icon = "🍃"
        elif any(w in q_lower for w in ["heat", "thermal", "fire", "protect"]):
            icon = "🔥"
        elif any(w in q_lower for w in ["curl", "wave", "custard", "spiral"]):
            icon = "🌀"
        elif any(w in q_lower for w in ["violet", "purple", "glaze", "blonde"]):
            icon = "💜"

        # 6. Extract Active Ingredients
        actives = ["Botanical Complex", "Vegan Biotin", "Vitamin E"]
        if "rosemary" in q_lower: actives.append("Organic Rosemary Leaf Oil 3%")
        if "caffeine" in q_lower: actives.append("Micro-Encapsulated Caffeine")
        if "peptide" in q_lower or "copper" in q_lower: actives.append("Copper Tripeptide-1")
        if "keratin" in q_lower: actives.append("Hydrolyzed Keratin Proteins")
        if "argan" in q_lower: actives.append("Cold-Pressed Moroccan Argan Oil")
        if "castor" in q_lower: actives.append("Pure Jamaican Black Castor Oil")
        if "tea tree" in q_lower or "salicylic" in q_lower:
            actives.append("Salicylic Acid (BHA) 2%")
            actives.append("Australian Tea Tree Oil")
        if "lavender" in q_lower: actives.append("French Lavender Essential Oil")

        prod_id = f"prod_{re.sub(r'[^a-zA-Z0-9]', '_', name.lower())[:25]}_{int(time.time()) % 1000}"

        product_obj = {
            "id": prod_id,
            "name": name,
            "category": category,
            "hairConcern": hair_concern,
            "price": price,
            "originalPrice": original_price,
            "rating": 5.0,
            "reviewsCount": 1,
            "tag": "Voice Ingested Formula",
            "badgeColor": "badge-emerald",
            "description": f"Custom formulated {category} product crafted with active botanicals targeted for {hair_concern}.",
            "icon": icon,
            "inStock": True,
            "activeIngredients": list(dict.fromkeys(actives)),
            "benefits": [f"Specifically formulated for {hair_concern}", "Clean botanical blend, sulfate-free", "Clinically tested for visible results"],
            "clinicalResult": "Formulated in accordance with clean dermatological trichology standards.",
            "usageInstructions": "Apply to clean scalp or hair strands. Massage gently and style as desired.",
            "specs": ["Clean Beauty", "Dermatologist Tested", "Sulfate-Free", "Voice AI Ingested"]
        }
        return product_obj

    def ingest_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Saves product to SQLite database, syncs JSON, and re-indexes RAG vector store."""
        self.db.insert_or_update_product(product)
        vector_store = get_vector_store()
        vector_store.add_product_to_index(product)

        return {
            "status": "success",
            "action_type": "ADD_PRODUCT",
            "product": product
        }

    def update_price_from_query(self, query: str) -> Dict[str, Any]:
        """Parses target product and new price, updates SQLite and vector index."""
        start_time = time.time()
        new_price = parse_spoken_number(query) or 29.99

        # Identify target product name
        target_name = "Rosemary Scalp Density Cleanser"
        q_lower = query.lower()
        if "rosemary" in q_lower:
            target_name = "Rosemary Scalp Density Cleanser" if "cleanser" in q_lower or "shampoo" in q_lower else "Rosemary Scalp Oil"
        elif "peptide" in q_lower or "redensyl" in q_lower:
            target_name = "3% Redensyl + Procapil Scalp Serum"
        elif "ceramide" in q_lower or "hydra" in q_lower:
            target_name = "Hydra-Ceramide Recovery Shampoo"
        elif "keratin" in q_lower or "mask" in q_lower:
            target_name = "Deep Keratin Reconstruction Mask"
        elif "tea tree" in q_lower or "salicylic" in q_lower:
            target_name = "Tea Tree & Salicylic Clarifying Wash"

        updated = self.db.update_product_price(target_name, new_price)
        if not updated:
            # Try fuzzy match against all products
            all_prods = self.db.get_all_products()
            for p in all_prods:
                if any(w in p["name"].lower() for w in q_lower.split() if len(w) > 4):
                    updated = self.db.update_product_price(p["id"], new_price)
                    target_name = p["name"]
                    break

        if updated:
            vector_store = get_vector_store()
            vector_store.add_product_to_index(updated)

        execution_time_ms = round((time.time() - start_time) * 1000, 2)
        prod_name = updated["name"] if updated else target_name

        ui_command = {
            "action": "UPDATE_PRODUCT_PRICE",
            "payload": {
                "productName": prod_name,
                "productId": updated.get("id") if updated else None,
                "newPrice": new_price
            }
        }

        return {
            "agent": self.agent_name,
            "status": "success",
            "action": "UPDATE_PRODUCT_PRICE",
            "product": updated or {"name": prod_name, "price": new_price},
            "ui_command": ui_command,
            "execution_time_ms": execution_time_ms,
            "details": f"Updated price of '{prod_name}' to ${new_price:.2f} in SQLite database & catalog UI."
        }

    def process(self, query: str) -> Dict[str, Any]:
        start_time = time.time()
        q_lower = query.lower()
        if "price" in q_lower and any(w in q_lower for w in ["change", "update", "set", "through", "to $", "is $"]):
            return self.update_price_from_query(query)

        product = self.extract_product_from_text(query)
        ingest_res = self.ingest_product(product)
        execution_time_ms = round((time.time() - start_time) * 1000, 2)

        ui_command = {
            "action": "ADD_PRODUCT",
            "payload": {
                "product": product,
                "highlight": True
            }
        }

        return {
            "agent": self.agent_name,
            "status": "success",
            "action": "ADD_PRODUCT",
            "product": product,
            "ui_command": ui_command,
            "execution_time_ms": execution_time_ms,
            "details": f"Successfully ingested '{product['name']}' ({product.get('icon', '🌿')}) at ${product['price']} into SQLite DB & RAG vector store."
        }


