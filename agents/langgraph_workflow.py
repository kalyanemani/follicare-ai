import time
import re
from typing import TypedDict, Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END

from agents.rag_agent import RAGAgent
from agents.ui_agent import UIAutomationAgent
from agents.product_agent import ProductManagementAgent
from agents.response_agent import ResponseSynthesisAgent
from agents.react_coder_agent import get_react_coder_agent
from agents.llm_client import LocalOllamaClient
from agents.memory import get_hindsight_memory_engine
from agents.evaluator import get_evaluation_pipeline
from agents.monitoring import get_observability_pipeline
from data.database import get_database

class FolliCareState(TypedDict, total=False):
    """
    Formal LangGraph State Schema for FolliCare Multi-Agent System.
    Includes execution path history, self-correction loop counts, and tool metrics.
    """
    query: str
    input_type: str
    mode: str
    model_name: str
    session_id: str
    trace_id: str
    intent: str
    user_memory: Dict[str, Any]
    product_result: Optional[Dict[str, Any]]
    rag_result: Dict[str, Any]
    ui_result: Dict[str, Any]
    developer_result: Optional[Dict[str, Any]]
    reply_message: str
    speech_text: str
    trace_steps: List[Dict[str, Any]]
    path_traversed: List[str]
    loop_count: int
    validation_status: str
    evaluation_metrics: Dict[str, Any]
    start_time: float
    total_time_ms: float

class FolliCareLangGraphEngine:
    """
    Explicit LangGraph Hierarchical Multi-Agent Graph Engine for FolliCare:
    Implements a formal StateGraph with conditional routing, self-correction feedback loops,
    path detection, specialized agent nodes, ChromaDB RAG retrieval, Cross-Encoder reranking,
    React Coder Agent (Qwen 2.5 Coder 7B), DOM mutations, hindsight memory, and LLM-as-a-Judge evaluation.
    """
    def __init__(self, default_model: str = "qwen2.5:3b"):
        self.default_model = default_model
        self.rag_agent = RAGAgent()
        self.ui_agent = UIAutomationAgent()
        self.product_agent = ProductManagementAgent()
        self.response_agent = ResponseSynthesisAgent()
        self.react_coder_agent = get_react_coder_agent()
        self.llm_client = LocalOllamaClient(default_model=default_model)
        self.memory_engine = get_hindsight_memory_engine()
        self.eval_pipeline = get_evaluation_pipeline()
        self.tracer = get_observability_pipeline()
        self.db = get_database()

        # Build and compile the LangGraph workflow
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(FolliCareState)

        # 1. Define Nodes
        workflow.add_node("supervisor_intent_node", self.supervisor_intent_node)
        workflow.add_node("react_developer_node", self.react_developer_node)
        workflow.add_node("product_ingestion_node", self.product_ingestion_node)
        workflow.add_node("rag_trichology_node", self.rag_trichology_node)
        workflow.add_node("ui_automation_node", self.ui_automation_node)
        workflow.add_node("tool_validator_node", self.tool_validator_node)
        workflow.add_node("reflection_loop_node", self.reflection_loop_node)
        workflow.add_node("response_synthesis_node", self.response_synthesis_node)
        workflow.add_node("hindsight_memory_node", self.hindsight_memory_node)
        workflow.add_node("llm_judge_evaluator_node", self.llm_judge_evaluator_node)

        # 2. Add Edges & Conditional Routing
        workflow.add_edge(START, "supervisor_intent_node")

        workflow.add_conditional_edges(
            "supervisor_intent_node",
            self.route_intent,
            {
                "DEVELOPER_UI_CODE": "react_developer_node",
                "PRODUCT_INGESTION": "product_ingestion_node",
                "KNOWLEDGE_QUERY": "rag_trichology_node",
                "UI_MUTATION": "ui_automation_node",
                "HYBRID": "rag_trichology_node",
                "ROUTINE_CONSULT": "rag_trichology_node"
            }
        )

        workflow.add_edge("react_developer_node", "tool_validator_node")
        workflow.add_edge("product_ingestion_node", "tool_validator_node")
        workflow.add_edge("rag_trichology_node", "ui_automation_node")
        workflow.add_edge("ui_automation_node", "tool_validator_node")

        # Iterative Loop Conditional Edge
        workflow.add_conditional_edges(
            "tool_validator_node",
            self.route_validation,
            {
                "RETRY_LOOP": "reflection_loop_node",
                "PROCEED": "response_synthesis_node"
            }
        )

        # Route reflection loop back into RAG or UI node
        workflow.add_conditional_edges(
            "reflection_loop_node",
            self.route_reflection_target,
            {
                "RETRY_RAG": "rag_trichology_node",
                "RETRY_UI": "ui_automation_node"
            }
        )

        workflow.add_edge("response_synthesis_node", "hindsight_memory_node")
        workflow.add_edge("hindsight_memory_node", "llm_judge_evaluator_node")
        workflow.add_edge("llm_judge_evaluator_node", END)

        return workflow.compile()

    # ------------------ Node Functions ------------------

    def supervisor_intent_node(self, state: FolliCareState) -> FolliCareState:
        path = list(state.get("path_traversed", []))
        path.append("supervisor_intent_node")

        q = state["query"].lower()
        session_id = state.get("session_id", "default_user")
        mode = state.get("mode", "customer").lower()

        # Update and fetch user long-term profile
        self.memory_engine.update_from_conversation(session_id, state["query"])
        user_mem = self.memory_engine.get_user_context(session_id)

        # Classify intent (Developer Mode triggers React Coder Agent)
        is_price_mutation = any(w in q for w in ["change the price", "change price", "update price", "set price", "price through", "price to"]) or (("price" in q or "cost" in q) and ("$" in q or any(c.isdigit() for c in q)) and any(a in q for a in ["change", "update", "set", "make", "reduce", "increase", "through", "to"]))
        is_card_sizing = any(w in q for w in ["card size", "reduce the card", "reduce card", "shrink card", "enlarge card", "card width", "card scale", "card style", "resize card", "make card"])
        is_theme_change = bool(re.search(r'\b(theme|palette|aesthetic|dark mode|light mode)\b', q)) or bool(re.search(r'\b(switch|change|turn|set)\b.*?\b(to|from)?\s*(green|emerald|ruby|red|amber|lavender|purple|blue)\b', q))
        is_cart_mutation = any(w in q for w in ["add one more", "add 1 more", "add another", "add to cart", "add to bag", "buy this", "purchase this", "add to basket", "order this"])

        if mode == "developer" or any(w in q for w in ["react code", "jsx", "component", "developer mode", "update frontend", "modify code", "build component"]):
            intent = "DEVELOPER_UI_CODE"
        elif self.product_agent.is_product_ingestion_request(state["query"]) or "add product" in q or "add formula" in q:
            intent = "PRODUCT_INGESTION"
        elif is_price_mutation or is_card_sizing or is_theme_change or is_cart_mutation:
            intent = "UI_MUTATION"
        elif any(w in q for w in ["cart", "bag", "basket", "buy", "purchase", "order this", "checkout", "to my cart", "in my cart", "to cart"]):
            intent = "UI_MUTATION" if not any(w in q for w in ["what is", "why", "how much", "clinical", "science"]) else "HYBRID"
        elif any(w in q for w in ["routine", "regimen", "protocol", "how to treat", "step by step", "recommend a routine"]):
            intent = "ROUTINE_CONSULT"
        elif any(w in q for w in ["return", "refund", "policy", "what is", "how does", "ingredient", "ingredients", "science", "clinical", "side effect", "dht", "follicle", "trichology", "anagen"]):
            intent = "KNOWLEDGE_QUERY"
        else:
            intent = "HYBRID"


        trace_steps = list(state.get("trace_steps", []))
        trace_steps.append({
            "step": 1,
            "agent": "LangGraph: Supervisor Router Node",
            "action": "Intent Classification & Memory Lookup",
            "details": f"Classified intent as [{intent}] in [{state.get('mode', 'customer').upper()} MODE]."
        })

        return {
            **state,
            "intent": intent,
            "user_memory": user_mem,
            "trace_steps": trace_steps,
            "path_traversed": path,
            "loop_count": state.get("loop_count", 0)
        }

    def route_intent(self, state: FolliCareState) -> str:
        return state.get("intent", "HYBRID")

    def react_developer_node(self, state: FolliCareState) -> FolliCareState:
        path = list(state.get("path_traversed", []))
        path.append("react_developer_node (qwen2.5-coder:7b)")

        dev_res = self.react_coder_agent.process_developer_instruction(
            query=state["query"],
            session_id=state.get("session_id", "default_user"),
            trace_id=state.get("trace_id", "")
        )

        trace_steps = list(state.get("trace_steps", []))
        trace_steps.append({
            "step": 2,
            "agent": "LangGraph: React Coder Node (Qwen 2.5 Coder 7B)",
            "action": "React Code Generation & Live UI Reflection",
            "details": f"Generated code modifications for '{dev_res.get('plan', {}).get('target_file')}'. Live commands: {len(dev_res.get('ui_commands', []))}."
        })

        ui_res = {
            "commands": dev_res.get("ui_commands", []),
            "actions_taken": [dev_res.get("plan", {}).get("explanation", "React component updated")],
            "has_mutations": len(dev_res.get("ui_commands", [])) > 0
        }

        return {
            **state,
            "developer_result": dev_res,
            "ui_result": ui_res,
            "reply_message": dev_res.get("reply_message", ""),
            "speech_text": dev_res.get("speech_text", ""),
            "trace_steps": trace_steps,
            "path_traversed": path
        }

    def product_ingestion_node(self, state: FolliCareState) -> FolliCareState:
        path = list(state.get("path_traversed", []))
        path.append("product_ingestion_node")


        start_t = time.time()
        prod_res = self.product_agent.process(state["query"])
        ui_res = {
            "commands": [prod_res["ui_command"]],
            "actions_taken": [f"Inserted new product '{prod_res['product']['name']}' into catalog."],
            "has_mutations": True
        }
        rag_res = self.rag_agent.retrieve(query=prod_res["product"]["name"], top_k=2)

        latency_ms = round((time.time() - start_t) * 1000, 2)
        # Log tool execution to SQLite
        self.db.log_tool_call({
            "session_id": state.get("session_id", "default_user"),
            "trace_id": state.get("trace_id", ""),
            "tool_name": "product_ingestion_agent",
            "tool_type": "agent_internal",
            "arguments": {"query": state["query"]},
            "execution_status": "SUCCESS" if prod_res.get("status") == "success" else "FAILURE",
            "latency_ms": latency_ms,
            "accuracy_score": 1.0,
            "path_detected": " -> ".join(["START"] + path),
            "loop_count": state.get("loop_count", 0)
        })

        trace_steps = list(state.get("trace_steps", []))
        trace_steps.append({
            "step": 2,
            "agent": "LangGraph: Product Ingestion Node",
            "action": "Database & Vector Ingestion",
            "details": f"Ingested {prod_res['product']['name']} (${prod_res['product']['price']}) into SQLite and ChromaDB."
        })

        return {
            **state,
            "product_result": prod_res,
            "ui_result": ui_res,
            "rag_result": rag_res,
            "trace_steps": trace_steps,
            "path_traversed": path
        }

    def rag_trichology_node(self, state: FolliCareState) -> FolliCareState:
        path = list(state.get("path_traversed", []))
        path.append("rag_trichology_node")

        start_t = time.time()
        rag_res = self.rag_agent.retrieve(query=state["query"], top_k=3)
        doc_names = [d["title"] for d in rag_res.get("top_docs", [])]
        latency_ms = round((time.time() - start_t) * 1000, 2)

        # Log RAG tool call
        acc = 1.0 if len(doc_names) > 0 else 0.7
        self.db.log_tool_call({
            "session_id": state.get("session_id", "default_user"),
            "trace_id": state.get("trace_id", ""),
            "tool_name": "chromadb_rag_retrieval",
            "tool_type": "agent_internal",
            "arguments": {"query": state["query"], "top_k": 3},
            "execution_status": "SUCCESS",
            "latency_ms": latency_ms,
            "accuracy_score": acc,
            "path_detected": " -> ".join(["START"] + path),
            "loop_count": state.get("loop_count", 0)
        })

        trace_steps = list(state.get("trace_steps", []))
        trace_steps.append({
            "step": len(trace_steps) + 1,
            "agent": "LangGraph: ChromaDB RAG Node",
            "action": "Two-Stage Vector Search & Cross-Encoder",
            "details": f"Retrieved and reranked {len(doc_names)} chunks: {', '.join(doc_names)}."
        })

        return {
            **state,
            "rag_result": rag_res,
            "trace_steps": trace_steps,
            "path_traversed": path
        }

    def ui_automation_node(self, state: FolliCareState) -> FolliCareState:
        path = list(state.get("path_traversed", []))
        path.append("ui_automation_node")

        start_t = time.time()
        rag_context = state.get("rag_result", {}).get("context_text", "")
        ui_res = self.ui_agent.plan_and_execute(query=state["query"], context=rag_context)
        latency_ms = round((time.time() - start_t) * 1000, 2)

        cmd_names = [c["action"] for c in ui_res.get("commands", [])]
        acc = 1.0 if len(cmd_names) > 0 or state.get("intent") == "KNOWLEDGE_QUERY" else 0.8

        self.db.log_tool_call({
            "session_id": state.get("session_id", "default_user"),
            "trace_id": state.get("trace_id", ""),
            "tool_name": "ui_automation_agent",
            "tool_type": "agent_internal",
            "arguments": {"query": state["query"], "commands_count": len(cmd_names)},
            "execution_status": "SUCCESS",
            "latency_ms": latency_ms,
            "accuracy_score": acc,
            "path_detected": " -> ".join(["START"] + path),
            "loop_count": state.get("loop_count", 0)
        })

        trace_steps = list(state.get("trace_steps", []))
        if cmd_names:
            trace_steps.append({
                "step": len(trace_steps) + 1,
                "agent": "LangGraph: UI Automation Node",
                "action": "Declarative Action Compilation",
                "details": f"Generated {len(cmd_names)} action(s): {', '.join(cmd_names)}."
            })

        return {
            **state,
            "ui_result": ui_res,
            "trace_steps": trace_steps,
            "path_traversed": path
        }

    def tool_validator_node(self, state: FolliCareState) -> FolliCareState:
        """Validates tool call accuracy & determines whether a self-correction loop is required."""
        path = list(state.get("path_traversed", []))
        path.append("tool_validator_node")

        loop_count = state.get("loop_count", 0)
        intent = state.get("intent", "HYBRID")
        rag_docs = state.get("rag_result", {}).get("top_docs", [])
        ui_cmds = state.get("ui_result", {}).get("commands", [])

        needs_retry = False
        # If user intended a UI Mutation (e.g. cart or theme) but 0 commands were generated
        if intent == "UI_MUTATION" and len(ui_cmds) == 0 and loop_count < 1:
            needs_retry = True
        # If user asked a knowledge query but 0 RAG documents were retrieved
        elif intent in ["KNOWLEDGE_QUERY", "ROUTINE_CONSULT"] and len(rag_docs) == 0 and loop_count < 1:
            needs_retry = True

        status = "RETRY_LOOP" if needs_retry else "PROCEED"

        trace_steps = list(state.get("trace_steps", []))
        trace_steps.append({
            "step": len(trace_steps) + 1,
            "agent": "LangGraph: Tool Validator & Gatekeeper Node",
            "action": "Accuracy & Loop Feasibility Check",
            "details": f"Validation Status: [{status}] (Loop Iteration: {loop_count})."
        })

        return {
            **state,
            "validation_status": status,
            "trace_steps": trace_steps,
            "path_traversed": path
        }

    def route_validation(self, state: FolliCareState) -> str:
        return state.get("validation_status", "PROCEED")

    def reflection_loop_node(self, state: FolliCareState) -> FolliCareState:
        """Self-correction & reflection loop: reformulates queries and relaxes constraints."""
        path = list(state.get("path_traversed", []))
        path.append("reflection_loop_node")

        current_loops = state.get("loop_count", 0) + 1
        q = state["query"]

        # Reformulate query by removing noise words for fallback retry
        refined_query = re.sub(r'(can you please|could you|i would like to|please)\s+', '', q, flags=re.I).strip()

        trace_steps = list(state.get("trace_steps", []))
        trace_steps.append({
            "step": len(trace_steps) + 1,
            "agent": "LangGraph: Self-Correction Reflection Loop",
            "action": f"Iterative Loop #{current_loops}",
            "details": f"Refined query representation to: '{refined_query}' for optimal agent routing."
        })

        return {
            **state,
            "query": refined_query,
            "loop_count": current_loops,
            "trace_steps": trace_steps,
            "path_traversed": path
        }

    def route_reflection_target(self, state: FolliCareState) -> str:
        intent = state.get("intent", "HYBRID")
        if intent == "UI_MUTATION":
            return "RETRY_UI"
        return "RETRY_RAG"

    def response_synthesis_node(self, state: FolliCareState) -> FolliCareState:
        path = list(state.get("path_traversed", []))
        path.append("response_synthesis_node")

        query = state["query"]
        mode = state.get("mode", "customer")
        chosen_model = state.get("model_name", self.default_model)
        rag_result = state.get("rag_result", {})
        ui_result = state.get("ui_result", {})
        product_result = state.get("product_result")

        # LLM Synthesis
        llm_telemetry = None
        if rag_result.get("context_text"):
            if mode == "developer":
                sys_prompt = "You are FolliCare Senior UI & React Systems Architect. Explain UI modules, CSS variables, declarative commands, and dynamic DOM mutations concisely."
                user_prompt = f"UI Developer Query: {query}\n\nRelevant Architecture Context:\n{rag_result.get('context_text')}\n\nExplain the architecture or mutation."
            else:
                sys_prompt = "You are FolliCare Lead Clinical Trichologist & Beauty Advisor. Be concise, warm, empathetic, and cite active botanicals."
                user_prompt = f"Customer Query: {query}\n\nRelevant Trichology Context:\n{rag_result.get('context_text')}\n\nProvide an empathetic response under 3 sentences."

            llm_res = self.llm_client.generate(prompt=user_prompt, system=sys_prompt, model=chosen_model)
            if llm_res.get("status") == "success" and llm_res.get("text"):
                llm_telemetry = llm_res

        resp_res = self.response_agent.synthesize(
            query=query,
            intent=state["intent"],
            rag_result=rag_result,
            ui_result=ui_result,
            product_result=product_result
        )

        if state.get("developer_result") and state.get("reply_message"):
            final_reply = state.get("reply_message")
            speech_text = state.get("speech_text")
        elif llm_telemetry and llm_telemetry.get("text"):
            final_reply = f"{llm_telemetry['text']}\n\n*(Generated via LangGraph with local model: `{chosen_model}`)*"
            speech_text = llm_telemetry["text"].replace("**", "").replace("`", "")
        else:
            final_reply = resp_res.get("message", "")
            speech_text = resp_res.get("speech_text", "")


        trace_steps = list(state.get("trace_steps", []))
        trace_steps.append({
            "step": len(trace_steps) + 1,
            "agent": "LangGraph: Response Synthesis Node",
            "action": "Dialogue Generation & Speech Transcript",
            "details": f"Generated final dialogue response (Model: {chosen_model})."
        })

        return {
            **state,
            "reply_message": final_reply,
            "speech_text": speech_text,
            "trace_steps": trace_steps,
            "path_traversed": path
        }

    def hindsight_memory_node(self, state: FolliCareState) -> FolliCareState:
        path = list(state.get("path_traversed", []))
        path.append("hindsight_memory_node")

        session_id = state.get("session_id", "default_user")
        self.memory_engine.reflect_and_record_hindsight(
            session_id=session_id,
            user_query=state["query"],
            agent_intent=state.get("intent", "HYBRID"),
            tool_calls=state.get("ui_result", {}).get("commands", []),
            reply_message=state.get("reply_message", "")
        )
        return {
            **state,
            "path_traversed": path
        }

    def llm_judge_evaluator_node(self, state: FolliCareState) -> FolliCareState:
        path = list(state.get("path_traversed", []))
        path.append("llm_judge_evaluator_node")

        start_t = state.get("start_time", time.time())
        latency_ms = round((time.time() - start_t) * 1000, 2)

        eval_metrics = self.eval_pipeline.evaluate_and_log(
            trace_id=state.get("trace_id", "trace-langgraph"),
            query=state["query"],
            intent=state.get("intent", "HYBRID"),
            retrieved_docs=state.get("rag_result", {}).get("top_docs", []),
            context_text=state.get("rag_result", {}).get("context_text", ""),
            generated_answer=state.get("reply_message", ""),
            ui_commands=state.get("ui_result", {}).get("commands", []),
            product_ingested=state.get("product_result", {}).get("product") if state.get("product_result") else None,
            latency_ms=latency_ms,
            model_name=state.get("model_name", self.default_model)
        )

        return {
            **state,
            "evaluation_metrics": eval_metrics,
            "total_time_ms": latency_ms,
            "path_traversed": path
        }

    # ------------------ Public Entrypoint ------------------

    def run(
        self,
        query: str,
        input_type: str = "text",
        mode: str = "customer",
        model_name: Optional[str] = None,
        session_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Executes the LangGraph Multi-Agent Workflow with full path detection and iterative loops.
        """
        initial_state: FolliCareState = {
            "query": query,
            "input_type": input_type,
            "mode": mode,
            "model_name": model_name or self.default_model,
            "session_id": session_id,
            "trace_id": f"trace-{int(time.time()*1000)}",
            "start_time": time.time(),
            "trace_steps": [],
            "path_traversed": [],
            "loop_count": 0
        }

        final_state = self.graph.invoke(initial_state)
        detected_path = " -> ".join(["START"] + final_state.get("path_traversed", []) + ["END"])

        return {
            "status": "success",
            "framework": "LangGraph (StateGraph)",
            "trace_id": final_state.get("trace_id"),
            "session_id": final_state.get("session_id"),
            "query": final_state.get("query"),
            "input_type": final_state.get("input_type"),
            "mode": final_state.get("mode"),
            "intent": final_state.get("intent"),
            "model_used": final_state.get("model_name"),
            "total_time_ms": final_state.get("total_time_ms", 120.0),
            "reply": final_state.get("reply_message"),
            "reply_message": final_state.get("reply_message"),
            "speech_text": final_state.get("speech_text"),
            "ui_commands": final_state.get("ui_result", {}).get("commands", []),
            "developer_result": final_state.get("developer_result"),
            "citations": final_state.get("rag_result", {}).get("citations", []),
            "product_ingested": final_state.get("product_result", {}).get("product") if final_state.get("product_result") else None,
            "user_memory": final_state.get("user_memory"),
            "evaluation_metrics": final_state.get("evaluation_metrics"),
            "trace_steps": final_state.get("trace_steps"),
            "path_detected": detected_path,
            "loop_count": final_state.get("loop_count", 0)
        }


_langgraph_engine = None

def get_langgraph_engine() -> FolliCareLangGraphEngine:
    global _langgraph_engine
    if _langgraph_engine is None:
        _langgraph_engine = FolliCareLangGraphEngine()
    return _langgraph_engine
