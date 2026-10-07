import time
from typing import Dict, Any, List, Optional

from agents.rag_agent import RAGAgent
from agents.ui_agent import UIAutomationAgent
from agents.response_agent import ResponseSynthesisAgent
from agents.product_agent import ProductManagementAgent
from agents.llm_client import LocalOllamaClient
from agents.monitoring import get_observability_pipeline
from agents.memory import get_hindsight_memory_engine
from agents.evaluator import get_evaluation_pipeline

class MultiAgentSupervisor:
    """
    Supervisor / Orchestrator Agent for FolliCare Hair Cosmetics:
    Coordinates the multi-agent graph with local Ollama LLMs (qwen2.5:3b, llama3.2, llama3.1, etc.),
    manages long-term user memory & hindsight loops, executes sub-agents, and logs evaluation metrics.
    """
    def __init__(self, default_model: str = "qwen2.5:3b"):
        self.rag_agent = RAGAgent()
        self.ui_agent = UIAutomationAgent()
        self.response_agent = ResponseSynthesisAgent()
        self.product_agent = ProductManagementAgent()
        self.llm_client = LocalOllamaClient(default_model=default_model)
        self.tracer = get_observability_pipeline()
        self.memory_engine = get_hindsight_memory_engine()
        self.eval_pipeline = get_evaluation_pipeline()

    def classify_intent(self, query: str, model_name: Optional[str] = None) -> str:
        q = query.lower()

        # Check for product ingestion or icon update
        if self.product_agent.is_product_ingestion_request(query) or "add product" in q or "add formula" in q or "ingest formula" in q:
            return "PRODUCT_INGESTION"

        has_cart_triggers = any(w in q for w in [
            "cart", "bag", "basket", "buy", "purchase", "order this", "checkout", "to my cart", "in my cart", "to cart"
        ])

        has_routine_triggers = any(w in q for w in [
            "routine", "regimen", "protocol", "how to treat", "step by step",
            "hair loss treatment", "dandruff routine", "curl routine", "find my routine"
        ])

        has_ui_triggers = has_cart_triggers or any(w in q for w in [
            "theme", "dark", "light", "emerald", "botanical", "rose", "lavender", "amber",
            "banner", "announcement", "flash sale", "hero", "title",
            "filter", "under $", "less than", "sort", "coupon", "code", "reset", "clear"
        ])

        has_kb_triggers = any(w in q for w in [
            "return", "refund", "policy", "ship", "delivery", "safety", "patch test",
            "ingredients", "rosemary", "biotin", "redensyl", "keratin", "peptide",
            "what is", "how much", "tell me about", "details", "information", "clinical", "science"
        ])

        if has_cart_triggers and not has_kb_triggers:
            return "UI_MUTATION"
        elif has_routine_triggers:
            return "ROUTINE_CONSULT"
        elif has_ui_triggers and has_kb_triggers:
            return "HYBRID"
        elif has_ui_triggers:
            return "UI_MUTATION"
        elif has_kb_triggers:
            return "KNOWLEDGE_QUERY"
        else:
            return "HYBRID"

    def process(
        self,
        query: str,
        input_type: str = "text",
        mode: str = "customer",
        model_name: Optional[str] = None,
        session_id: str = "default_user"
    ) -> Dict[str, Any]:
        from agents.langgraph_workflow import get_langgraph_engine
        engine = get_langgraph_engine()
        return engine.run(
            query=query,
            input_type=input_type,
            mode=mode,
            model_name=model_name or self.llm_client.default_model,
            session_id=session_id
        )

        # Span 1: Intent Classification & Routing
        span_sup = trace.start_span(agent_name="Supervisor Orchestrator", action="Intent Analysis & Graph Routing")
        intent = self.classify_intent(query, model_name=chosen_model)
        trace.intent = intent
        span_sup.set_attribute("intent", intent)
        span_sup.set_attribute("input_type", input_type)
        span_sup.set_attribute("mode", mode)
        span_sup.set_attribute("model", chosen_model)
        span_sup.set_attribute("session_id", session_id)
        span_sup.finish()

        hindsight_note = f" (Hindsight Memory Applied: {', '.join(user_mem['hindsight_rules'])})" if user_mem.get("hindsight_rules") else ""

        trace_steps.append({
            "step": 1,
            "span_id": span_sup.span_id,
            "agent": "🎯 Supervisor Orchestrator",
            "action": "Intent Classification & Graph Routing",
            "details": f"Classified input stream ({input_type}) in [{mode.upper()} MODE] as [{intent}] using model '{chosen_model}'.{hindsight_note}",
            "execution_time_ms": span_sup.duration_ms,
            "status": "completed"
        })

        product_result = None
        ui_result = {"commands": [], "actions_taken": [], "has_mutations": False}
        rag_result = {"top_docs": [], "citations": [], "context_text": ""}

        # Span 2: Product Ingestion OR RAG + UI
        if intent == "PRODUCT_INGESTION":
            span_prod = trace.start_span(agent_name="Product Ingestion Agent", action="Database Extraction & Vector Indexing", parent_span_id=span_sup.span_id)
            product_result = self.product_agent.process(query)
            span_prod.set_attribute("product_name", product_result["product"]["name"])
            span_prod.set_attribute("price", product_result["product"]["price"])
            span_prod.set_attribute("icon", product_result["product"].get("icon", "🌿"))
            span_prod.finish()

            ui_result = {
                "commands": [product_result["ui_command"]],
                "actions_taken": [f"Dynamically inserted new product '{product_result['product']['name']}' ({product_result['product'].get('icon', '🌿')}) into catalog."],
                "has_mutations": True,
                "execution_time_ms": span_prod.duration_ms
            }

            trace_steps.append({
                "step": 2,
                "span_id": span_prod.span_id,
                "agent": "📦 Product Ingestion Agent",
                "action": "SQLite Database & Vector Ingestion",
                "details": product_result.get("details", ""),
                "product": product_result.get("product"),
                "execution_time_ms": span_prod.duration_ms,
                "status": "completed"
            })

            rag_result = self.rag_agent.retrieve(query=product_result["product"]["name"], top_k=2)

        else:
            # RAG Knowledge Retrieval
            if intent in ["KNOWLEDGE_QUERY", "ROUTINE_CONSULT", "HYBRID"]:
                span_rag = trace.start_span(agent_name="RAG Trichology Agent", action="Semantic Vector Search", parent_span_id=span_sup.span_id)
                # Query ChromaDB with Cross-Encoder reranking
                rag_result = self.rag_agent.retrieve(query=query, top_k=3)
                span_rag.set_attribute("chunks_retrieved", len(rag_result.get("top_docs", [])))
                span_rag.finish()

                doc_titles = [d.get("title", "") for d in rag_result.get("top_docs", [])]
                trace_steps.append({
                    "step": 2,
                    "span_id": span_rag.span_id,
                    "agent": "📚 RAG Trichology Agent",
                    "action": "ChromaDB & Cross-Encoder Semantic Retrieval",
                    "details": f"Queried ChromaDB with Cross-Encoder reranking. Retrieved {len(doc_titles)} chunk(s): {', '.join(doc_titles) if doc_titles else 'None'}.",
                    "citations": rag_result.get("citations", []),
                    "execution_time_ms": span_rag.duration_ms,
                    "status": "completed"
                })

            # UI Automation Action Execution
            if intent in ["UI_MUTATION", "ROUTINE_CONSULT", "HYBRID", "KNOWLEDGE_QUERY"]:
                span_ui = trace.start_span(agent_name="UI Automation Agent", action="Declarative Action Compilation", parent_span_id=span_sup.span_id)
                ui_result = self.ui_agent.plan_and_execute(
                    query=query,
                    context=rag_result.get("context_text", "")
                )
                span_ui.set_attribute("commands_count", len(ui_result.get("commands", [])))
                span_ui.finish()

                cmd_actions = [c.get("action", "") for c in ui_result.get("commands", [])]
                if cmd_actions:
                    trace_steps.append({
                        "step": len(trace_steps) + 1,
                        "span_id": span_ui.span_id,
                        "agent": "⚡ UI Automation Agent",
                        "action": "Declarative DOM Action Compilation",
                        "details": f"Compiled {len(cmd_actions)} DOM mutation command(s): {', '.join(cmd_actions)}.",
                        "commands": ui_result.get("commands", []),
                        "execution_time_ms": span_ui.duration_ms,
                        "status": "completed"
                    })

        # Span 3: Dialogue Synthesis & Audio Generation
        span_voice = trace.start_span(agent_name="Voice & Response Agent", action="Dialogue Synthesis & Speech Stream", parent_span_id=span_sup.span_id)

        llm_telemetry = None
        if intent in ["KNOWLEDGE_QUERY", "ROUTINE_CONSULT"] and rag_result.get("context_text"):
            if mode == "developer":
                system_prompt = "You are FolliCare Senior UI & React Systems Architect. Explain UI modules, CSS variables, declarative commands, and dynamic DOM mutations concisely."
                prompt = f"UI Developer Query: {query}\n\nRelevant Architecture & React Context:\n{rag_result.get('context_text')}\n\nProvide a technical and concise response explaining the architecture or mutation."
            else:
                system_prompt = "You are FolliCare Lead Clinical Trichologist & Beauty Advisor. Be concise, warm, empathetic, and cite active botanicals and protocols."
                memory_context = f"User Profile: Hair Type: {user_mem['hair_type']}, Concern: {user_mem['primary_concern']}."
                prompt = f"{memory_context}\n\nCustomer Query: {query}\n\nRelevant Trichology Context:\n{rag_result.get('context_text')}\n\nProvide an empathetic, scientifically accurate response under 3 sentences."

            llm_res = self.llm_client.generate(prompt=prompt, system=system_prompt, model=chosen_model)
            if llm_res.get("status") == "success" and llm_res.get("text"):
                llm_telemetry = llm_res

        resp_result = self.response_agent.synthesize(
            query=query,
            intent=intent,
            rag_result=rag_result,
            ui_result=ui_result,
            product_result=product_result
        )

        if llm_telemetry and llm_telemetry.get("text"):
            resp_result["message"] = f"{llm_telemetry['text']}\n\n*(Generated with local model: `{chosen_model}`)*"
            resp_result["speech_text"] = llm_telemetry["text"].replace("**", "").replace("`", "")

        span_voice.set_attribute("speech_chars", len(resp_result.get("speech_text", "")))
        span_voice.finish()

        trace_steps.append({
            "step": len(trace_steps) + 1,
            "span_id": span_voice.span_id,
            "agent": "🎙️ Voice & Response Agent",
            "action": "Dialogue Synthesis & Audio Stream Generation",
            "details": f"Synthesized dialogue confirmation with speech audio transcript (Model: {chosen_model}).",
            "execution_time_ms": span_voice.duration_ms,
            "llm_telemetry": llm_telemetry,
            "status": "completed"
        })

        trace.finish()
        self.tracer.record_trace(trace)

        # 4. Hindsight Reflection Loop
        self.memory_engine.reflect_and_record_hindsight(
            session_id=session_id,
            user_query=query,
            agent_intent=intent,
            tool_calls=ui_result.get("commands", []),
            reply_message=resp_result.get("message", "")
        )

        # 5. Unified RAG & Agent Evaluation
        eval_metrics = self.eval_pipeline.evaluate_and_log(
            trace_id=trace.trace_id,
            query=query,
            intent=intent,
            retrieved_docs=rag_result.get("top_docs", []),
            context_text=rag_result.get("context_text", ""),
            generated_answer=resp_result.get("message", ""),
            ui_commands=ui_result.get("commands", []),
            product_ingested=product_result.get("product") if product_result else None,
            latency_ms=trace.total_duration_ms,
            tokens_evaluated=llm_telemetry.get("eval_tokens", 45) if llm_telemetry else 35,
            prompt_tokens=llm_telemetry.get("prompt_tokens", len(query.split())) if llm_telemetry else len(query.split()),
            input_tokens_per_sec=llm_telemetry.get("input_tokens_per_sec", 135.0) if llm_telemetry else 135.0,
            output_tokens_per_sec=llm_telemetry.get("output_tokens_per_sec", 44.5) if llm_telemetry else 44.5,
            model_name=chosen_model
        )

        return {
            "status": "success",
            "agentic_framework": "LangGraph (StateGraph)",
            "trace_id": trace.trace_id,
            "session_id": session_id,
            "query": query,
            "input_type": input_type,
            "mode": mode,
            "intent": intent,
            "model_used": chosen_model,
            "total_time_ms": trace.total_duration_ms,
            "reply": resp_result.get("message"),
            "speech_text": resp_result.get("speech_text"),
            "ui_commands": ui_result.get("commands", []),
            "citations": rag_result.get("citations", []),
            "product_ingested": product_result.get("product") if product_result else None,
            "user_memory": user_mem,
            "evaluation_metrics": eval_metrics,
            "trace_steps": trace_steps,
            "trace_summary": trace.to_dict()
        }
