import json
import time
from typing import Dict, Any, List, Optional
from data.database import get_database

class HindsightMemoryEngine:
    """
    Long-Term Memory & Hindsight Reflection Engine:
    Maintains persistent user profiles (hair type, scalp condition, allergies, preferences)
    and executes hindsight evaluation loops across multi-turn agent interactions.
    """
    def __init__(self):
        self.db = get_database()

    def get_user_context(self, session_id: str = "default_user") -> Dict[str, Any]:
        """Fetches long-term memory profile and recent hindsight reflections."""
        memory = self.db.get_user_memory(session_id)
        hindsights = self.db.get_recent_hindsights(session_id=session_id, limit=3)

        hindsight_rules = [h.get("learned_rule") for h in hindsights if h.get("learned_rule")]

        return {
            "session_id": session_id,
            "hair_type": memory.get("hair_type", "Unknown"),
            "scalp_condition": memory.get("scalp_condition", "Unknown"),
            "primary_concern": memory.get("primary_concern", "General Wellness"),
            "allergic_ingredients": memory.get("allergic_ingredients", "None"),
            "hindsight_rules": hindsight_rules,
            "past_purchases": memory.get("past_purchases", [])
        }

    def update_from_conversation(self, session_id: str, user_query: str):
        """Extracts and updates user profile attributes from conversational speech/text."""
        q_lower = user_query.lower()
        memory_update = {}

        # Hair Type detection
        if any(w in q_lower for w in ["curly", "coils", "3a", "3b", "3c", "4a", "4b", "4c"]):
            memory_update["hair_type"] = "Curly / Coily (3A-4C)"
        elif "wavy" in q_lower or "2a" in q_lower or "2b" in q_lower or "2c" in q_lower:
            memory_update["hair_type"] = "Wavy (2A-2C)"
        elif "straight" in q_lower or "fine hair" in q_lower:
            memory_update["hair_type"] = "Straight / Fine"

        # Scalp Condition & Primary Concern
        if any(w in q_lower for w in ["dandruff", "flakes", "itchy", "flaking"]):
            memory_update["scalp_condition"] = "Dandruff / Flaking Scalp"
            memory_update["primary_concern"] = "Dandruff & Scalp Health"
        elif any(w in q_lower for w in ["thinning", "hair loss", "shedding", "hair fall"]):
            memory_update["primary_concern"] = "Hair Fall & Thinning"
        elif any(w in q_lower for w in ["bleach", "damaged", "breakage", "split ends"]):
            memory_update["primary_concern"] = "Damaged & Dry Hair"
        elif any(w in q_lower for w in ["frizz", "heat", "blow dry"]):
            memory_update["primary_concern"] = "Frizz & Heat Protection"

        # Allergy detection
        if "allergic to" in q_lower or "cannot use" in q_lower:
            words = user_query.split("allergic to")[-1].split(".")[0].strip()
            memory_update["allergic_ingredients"] = words

        if memory_update:
            self.db.save_user_memory(session_id, memory_update)

    def reflect_and_record_hindsight(
        self,
        session_id: str,
        user_query: str,
        agent_intent: str,
        tool_calls: List[Dict[str, Any]],
        reply_message: str
    ):
        """
        Hindsight Reflection Loop:
        Reflects on tool execution outcomes and generates actionable guidance for future turns.
        """
        q_lower = user_query.lower()
        outcome = "SUCCESS"
        reflection = "Agent successfully processed user instruction and dispatched corresponding tools."
        learned_rule = ""

        if "cart" in q_lower and any(c.get("action") == "ADD_TO_CART" for c in tool_calls):
            learned_rule = "User actively buys recommended trichology treatments directly into cart."
        elif "theme" in q_lower and any(c.get("action") == "SET_THEME" for c in tool_calls):
            theme_cmd = next((c for c in tool_calls if c.get("action") == "SET_THEME"), None)
            if theme_cmd:
                learned_rule = f"User preference for storefront theme: '{theme_cmd.get('payload', {}).get('theme')}'."
        elif "thinning" in q_lower:
            learned_rule = "User prioritizing follicle density and rosemary/peptide actives."
        elif "curly" in q_lower or "cgm" in q_lower:
            learned_rule = "User follows Curly Girl Method (CGM); recommend zero-silicone styling custards."

        self.db.record_hindsight(
            session_id=session_id,
            query=user_query,
            intent=agent_intent,
            tool_calls=tool_calls,
            outcome=outcome,
            reflection=reflection,
            learned_rule=learned_rule
        )

# Singleton
_memory_engine = None

def get_hindsight_memory_engine() -> HindsightMemoryEngine:
    global _memory_engine
    if _memory_engine is None:
        _memory_engine = HindsightMemoryEngine()
    return _memory_engine
