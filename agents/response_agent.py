import time
from typing import Dict, Any, List

class ResponseSynthesisAgent:
    """
    Conversational Response & Voice Synthesis Agent for Hair Cosmetics:
    Synthesizes expert trichology and beauty advice, confirms executed UI mutations,
    and produces speech-ready transcripts for the Web Speech API voice engine.
    """
    def __init__(self):
        self.agent_name = "Voice & Response Agent"

    def synthesize(
        self,
        query: str,
        intent: str,
        rag_result: Dict[str, Any],
        ui_result: Dict[str, Any],
        product_result: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        start_time = time.time()

        actions = ui_result.get("actions_taken", []) if ui_result else []
        top_docs = rag_result.get("top_docs", []) if rag_result else []

        reply_parts = []
        speech_parts = []

        # 1. Product Ingestion Confirmation
        if product_result and product_result.get("status") == "success":
            prod = product_result.get("product", {})
            action_desc = f"🌿 Added '{prod.get('name')}' (${prod.get('price')}) to the live catalog and indexed it into the RAG vector store!"
            reply_parts.append(action_desc)
            speech_parts.append(f"I have added {prod.get('name')} to the store catalog and updated the search index.")

        # 2. UI Actions Confirmation
        if actions:
            action_bullet_list = " ".join([f"✨ {a}" for a in actions])
            reply_parts.append(action_bullet_list)
            speech_parts.append("I have updated the store interface: " + " and ".join(actions))

        # 3. Knowledge & Trichological Advice
        if intent in ["KNOWLEDGE_QUERY", "HYBRID"] or (not actions and not product_result and top_docs):
            if top_docs:
                best_doc = top_docs[0]
                reply_parts.append(f"\n\n**{best_doc['title']}**:\n{best_doc['content']}")
                speech_parts.append(f"Regarding {best_doc['title']}: {best_doc['content']}")

                if len(top_docs) > 1 and top_docs[1].get("category") in ["Product", "Hair_Concern_Guide"]:
                    second_doc = top_docs[1]
                    reply_parts.append(f"\n\n💡 *Also Recommended ({second_doc['title']})*: {second_doc['content'][:200]}...")
            else:
                reply_parts.append("I checked our FolliCare botanical hair knowledge base, but couldn't find exact matches. Feel free to ask about our scalp density serums, curl custards, bond repair masks, or 60-day satisfaction guarantee!")
                speech_parts.append("I couldn't find an exact match in our trichology records, but I can help you with hair routines, formulas, or store customization.")

        if not reply_parts:
            reply_parts.append("I'm ready! You can ask me to change the aesthetic theme (e.g. Botanical Emerald or Rose Luxury), filter products by hair concern, add a new cosmetic product via voice, or ask for a personalized hair care routine.")
            speech_parts.append("I'm ready to help you with hair formulas, store styling, or catalog updates.")

        full_message = "\n".join(reply_parts)

        # Clean speech string for Web Speech API TTS
        speech_text = " ".join(speech_parts)
        speech_text = speech_text.replace("**", "").replace("✨", "").replace("🌿", "").replace("🔥", "").replace("🚚", "").replace("💡", "").replace("•", "").replace("`", "").replace("*", "")

        execution_time_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "agent": self.agent_name,
            "status": "success",
            "message": full_message,
            "speech_text": speech_text,
            "execution_time_ms": execution_time_ms
        }
