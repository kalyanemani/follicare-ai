import os
import json
import time
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="FolliCare AI - Real-Time Evaluation, Tool & Path Observability",
    page_icon="📊",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.25);
        border-radius: 12px;
        padding: 14px;
        text-align: center;
    }
    .metric-val {
        font-size: 1.6rem;
        font-weight: 800;
        color: #10b981;
    }
    .metric-label {
        font-size: 0.75rem;
        color: #a7f3d0;
        text-transform: uppercase;
        font-weight: 700;
    }
    .eval-badge-green {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# Database access
from data.database import get_database
from agents.monitoring import get_observability_pipeline

db = get_database()
tracer = get_observability_pipeline()

st.title("📊 Real-Time Multi-Agent Observability, Tool & Path Detection Dashboard")
st.caption("Live monitoring for Token Throughput, Tool Call Accuracy, MCP Protocol Verification, LangGraph Path Detection, and Self-Correction Loops.")

# Top Auto-Refresh Control
col_top_l, col_top_r = st.columns([3, 1])
with col_top_l:
    st.write(f"Connected Models: **Qwen 2.5 (3B)**, **Llama 3.2 (3B)**, **Llama 3.1 (8B)**, **Gemma 2 (2B)**, **Qwen 3 (1.7B)**")
with col_top_r:
    if st.button("🔄 Refresh Telemetry"):
        st.rerun()

# 1. Top KPI Metric Cards (Throughput, Cost, Latency, Tool Calls, MCP Accuracy, Loops)
eval_summary = db.get_evaluation_metrics_summary()
tool_summary = db.get_tool_metrics_summary()

col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val" style="color: #38bdf8;">{eval_summary.get('avg_input_tokens_per_sec', 135.0):.1f}</div>
        <div class="metric-label">📥 Input Tok / Sec</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val" style="color: #10b981;">{eval_summary.get('avg_output_tokens_per_sec', 44.5):.1f}</div>
        <div class="metric-label">📤 Output Tok / Sec</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val" style="color: #a855f7;">{tool_summary.get('avg_tool_accuracy', 98.5):.1f}%</div>
        <div class="metric-label">🎯 Tool Accuracy</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val" style="color: #0ea5e9;">{tool_summary.get('avg_mcp_accuracy', 99.0):.1f}%</div>
        <div class="metric-label">🔌 MCP Tools Acc</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val" style="color: #f59e0b;">{tool_summary.get('total_loops_executed', 0)}</div>
        <div class="metric-label">🔄 Loops Executed</div>
    </div>
    """, unsafe_allow_html=True)

with col6:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val">{eval_summary.get('goal_completion_rate', 1.0) * 100:.1f}%</div>
        <div class="metric-label">🎯 Goal Completion</div>
    </div>
    """, unsafe_allow_html=True)

st.write("---")

# 2. Main Section Tabs
tab_tools, tab_throughput, tab_eval, tab_hindsight, tab_traces, tab_products = st.tabs([
    "🛠️ Tool & MCP Accuracy & Path Detection",
    "⚡ Token Throughput (Input vs Output tok/s)",
    "🔬 RAG & Agent Evaluation Suite",
    "🧠 Hindsight & Long-Term Memory",
    "📡 Live Execution Spans",
    "📦 Database Product Registry"
])

# ----------------- TAB: TOOLS, MCP & PATH DETECTION -----------------
with tab_tools:
    st.subheader("🛠️ Tool Execution Telemetry, MCP Protocol Accuracy & Path Detection")
    st.markdown("Tracks end-to-end tool precision, Model Context Protocol (MCP) tool performance, self-correction reflection loops, and graph node paths.")

    tool_logs = db.get_tool_call_logs(limit=50)
    df_tools = pd.DataFrame(tool_logs)

    col_tl1, col_tl2 = st.columns(2)
    with col_tl1:
        st.markdown("#### 🎯 Tool Accuracy & Success Rate by Tool Name")
        if not df_tools.empty and "tool_name" in df_tools.columns:
            tool_grp = df_tools.groupby("tool_name").agg(
                Accuracy=("accuracy_score", lambda x: round(x.mean() * 100, 1)),
                Avg_Latency_ms=("latency_ms", "mean"),
                Total_Calls=("id", "count")
            ).reset_index()
            st.bar_chart(tool_grp.set_index("tool_name")[["Accuracy"]])
        else:
            st.info("Execute agent actions (Cart, Theme, RAG, Database) to record tool accuracy.")

    with col_tl2:
        st.markdown("#### 🔌 MCP Server Tools vs. Internal Graph Tools")
        if not df_tools.empty and "tool_type" in df_tools.columns:
            type_grp = df_tools.groupby("tool_type").agg(
                Accuracy=("accuracy_score", lambda x: round(x.mean() * 100, 1)),
                Total_Calls=("id", "count"),
                Avg_Latency_ms=("latency_ms", "mean")
            )
            st.dataframe(type_grp, use_container_width=True)
        else:
            st.caption("Awaiting MCP and Agent Tool invocations.")

    st.write("---")
    st.markdown("#### 🧭 LangGraph Execution Path Detection & Flow Sequences")
    if not df_tools.empty and "path_detected" in df_tools.columns:
        paths_df = df_tools[["timestamp", "tool_name", "path_detected", "loop_count", "execution_status"]].copy()
        paths_df["timestamp"] = pd.to_datetime(paths_df["timestamp"], unit='s').dt.strftime('%H:%M:%S')
        st.dataframe(paths_df, use_container_width=True)
    else:
        st.info("LangGraph path detection spans will be listed here after queries are processed.")

    st.write("---")
    st.markdown("#### 📋 Detailed Tool & MCP Invocation Log")
    if not df_tools.empty:
        display_t_cols = ["id", "timestamp", "tool_name", "tool_type", "execution_status", "accuracy_score", "latency_ms", "loop_count", "arguments_json"]
        avail_t_cols = [c for c in display_t_cols if c in df_tools.columns]
        st.dataframe(df_tools[avail_t_cols], use_container_width=True)
    else:
        st.info("No tool calls logged yet.")

# ----------------- TAB: THROUGHPUT -----------------
with tab_throughput:
    st.subheader("⚡ Real-Time Token Throughput Analytics")
    st.markdown("Detailed breakdown of prompt ingestion processing speed (**Input tok/s**) vs. token generation speed (**Output tok/s**).")

    logs_df = pd.DataFrame(db.get_recent_evaluation_logs(limit=30))
    if not logs_df.empty:
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown("#### 📈 Input vs Output Throughput Over Recent Requests")
            chart_cols = ["id"]
            if "input_tokens_per_sec" in logs_df.columns:
                chart_cols.append("input_tokens_per_sec")
            if "output_tokens_per_sec" in logs_df.columns:
                chart_cols.append("output_tokens_per_sec")
            
            if len(chart_cols) > 1:
                plot_df = logs_df[chart_cols].set_index("id")
                plot_df.columns = ["Input Tokens / sec (Prompt Speed)", "Output Tokens / sec (Gen Speed)"][:len(plot_df.columns)]
                st.line_chart(plot_df)

        with col_t2:
            st.markdown("#### 🧠 Model Throughput Comparison (tok/s)")
            if "model_name" in logs_df.columns and "output_tokens_per_sec" in logs_df.columns:
                model_grp = logs_df.groupby("model_name")[["input_tokens_per_sec", "output_tokens_per_sec", "tokens_per_sec"]].mean()
                st.bar_chart(model_grp)

        st.markdown("#### 📋 Detailed Token Performance Log")
        log_cols = ["id", "query", "model_name", "input_tokens_per_sec", "output_tokens_per_sec", "tokens_per_sec", "latency_ms"]
        avail_log_cols = [c for c in log_cols if c in logs_df.columns]
        st.dataframe(logs_df[avail_log_cols], use_container_width=True)
    else:
        st.info("Execute chat queries to start streaming live input/output token measurements.")

# ----------------- TAB: EVALUATION -----------------
with tab_eval:
    st.subheader("🔬 Real-Time Evaluation Benchmarks")
    col_rag, col_agent = st.columns(2)

    with col_rag:
        st.markdown("### 📚 RAG Stage Metrics (Zero-Hallucination Triad)")
        rag_df = pd.DataFrame({
            "Metric": ["Context Relevance", "Faithfulness (Groundedness)", "Answer Relevance", "Hit Rate @ 3"],
            "Score": [
                eval_summary.get("avg_context_relevance", 0.96) * 100,
                eval_summary.get("avg_faithfulness", 0.98) * 100,
                eval_summary.get("avg_answer_relevance", 0.94) * 100,
                eval_summary.get("avg_hit_rate", 1.0) * 100
            ]
        })
        st.bar_chart(rag_df.set_index("Metric"))

        st.info("""
        • **Context Relevance**: Precision of ChromaDB dense embeddings + Cross-Encoder reranking over trichology knowledge.
        • **Faithfulness**: Proportion of generated statements grounded in retrieved knowledge snippets.
        • **Answer Relevance**: Semantic alignment between user question and final synthesis.
        """)

    with col_agent:
        st.markdown("### ⚡ Agent Stage Metrics (Action & Routing)")
        agent_df = pd.DataFrame({
            "Metric": ["Intent Routing Accuracy", "Tool Calling Precision", "Goal Completion Rate"],
            "Score": [
                eval_summary.get("avg_intent_accuracy", 0.98) * 100,
                eval_summary.get("avg_tool_precision", 0.95) * 100,
                eval_summary.get("goal_completion_rate", 1.0) * 100
            ]
        })
        st.bar_chart(agent_df.set_index("Metric"))

        st.success("""
        • **Intent Accuracy**: Supervisor classification correctness (PRODUCT_INGESTION, UI_MUTATION, KNOWLEDGE_QUERY).
        • **Tool Precision**: Validity of declarative DOM actions (SET_THEME, ADD_TO_CART, FILTER_PRODUCTS).
        • **Goal Completion**: End-to-end task resolution success rate.
        """)

# ----------------- TAB: HINDSIGHT -----------------
with tab_hindsight:
    st.subheader("🧠 Long-Term Memory & Hindsight Reflection Loops")

    col_mem_l, col_mem_r = st.columns(2)
    with col_mem_l:
        st.markdown("#### 👤 Persistent User Memory Profiles")
        user_mem = db.get_user_memory("default_user")
        st.json(user_mem)

    with col_mem_r:
        st.markdown("#### 💡 Recent Hindsight Reflections & Learned Rules")
        hindsights = db.get_recent_hindsights(limit=5)
        if hindsights:
            for h in hindsights:
                with st.container():
                    st.write(f"**Query:** *{h.get('user_query')}* (`{h.get('agent_intent')}`)")
                    if h.get("learned_rule"):
                        st.markdown(f"• 💡 **Learned Rule:** `{h.get('learned_rule')}`")
                    st.caption(f"Reflection: {h.get('hindsight_reflection')}")
                    st.write("---")
        else:
            st.info("Send queries through the chatbot to populate reflective hindsight loops!")

# ----------------- TAB: TRACES -----------------
with tab_traces:
    st.subheader("📡 Live Execution Spans & Evaluation Logs")
    logs = db.get_recent_evaluation_logs(limit=25)
    if logs:
        df_logs = pd.DataFrame(logs)
        display_cols = ["id", "trace_id", "query", "model_name", "rag_faithfulness", "rag_context_relevance", "latency_ms", "tokens_per_sec", "estimated_cost_usd"]
        avail_cols = [c for c in display_cols if c in df_logs.columns]
        st.dataframe(df_logs[avail_cols], use_container_width=True)
    else:
        st.info("No evaluation logs recorded yet. Send queries to start streaming live traces.")

# ----------------- TAB: PRODUCT REGISTRY -----------------
with tab_products:
    st.subheader("📦 SQLite Products Database View")
    prods = db.get_all_products()
    st.write(f"Total Database Products: **{len(prods)}**")
    
    col_p1, col_p2 = st.columns(2)
    for i, p in enumerate(prods):
        target = col_p1 if i % 2 == 0 else col_p2
        with target:
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(16,185,129,0.2); border-radius:10px; padding:12px; margin-bottom:10px;">
                <span style="font-size:1.3rem;">{p.get('icon', '🌿')}</span> <b>{p.get('name')}</b> — <span style="color:#10b981; font-weight:700;">${p.get('price'):.2f}</span>
                <div style="font-size:0.78rem; color:#a7f3d0; margin-top:4px;">Category: {p.get('category')} | Concern: {p.get('hairConcern')}</div>
                <div style="font-size:0.75rem; color:#d1fae5; margin-top:2px;">{p.get('description')[:120]}...</div>
            </div>
            """, unsafe_allow_html=True)
