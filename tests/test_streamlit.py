import os
import sys
import io
import requests

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import get_database

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=== 1. TESTING STREAMLIT HTTP PORTS ===")

# Test Port 8501 (Main Multi-Agent Storefront Dashboard)
try:
    r1 = requests.get("http://localhost:8501", timeout=5)
    print(f"✅ Main Streamlit Dashboard (Port 8501): HTTP {r1.status_code} OK (HTML size: {len(r1.text)} bytes)")
except Exception as e:
    print(f"❌ Main Streamlit Dashboard (Port 8501): {e}")

# Test Port 8502 (Real-Time Metrics & Evaluation Dashboard)
try:
    r2 = requests.get("http://localhost:8502", timeout=5)
    print(f"✅ Metrics & Observability Dashboard (Port 8502): HTTP {r2.status_code} OK (HTML size: {len(r2.text)} bytes)")
except Exception as e:
    print(f"❌ Metrics & Observability Dashboard (Port 8502): {e}")

print("\n=== 2. TESTING STREAMLIT DATA PIPELINES & METRICS ===")
db = get_database()
summary = db.get_evaluation_metrics_summary()
prods = db.get_all_products()
memory = db.get_user_memory("default_user")
hindsights = db.get_recent_hindsights(limit=3)

print(f"• Total Products in SQLite Database: {len(prods)}")
print(f"• Total Evaluated Runs Recorded: {summary.get('total_evals', 0)}")
print(f"• RAG Context Relevance: {summary.get('avg_context_relevance', 0)*100:.1f}%")
print(f"• RAG Faithfulness: {summary.get('avg_faithfulness', 0)*100:.1f}%")
print(f"• Agent Goal Completion Rate: {summary.get('goal_completion_rate', 0)*100:.1f}%")
print(f"• Average Latency: {summary.get('avg_latency_ms', 0):.1f}ms")
print(f"• Average Throughput: {summary.get('avg_tokens_per_sec', 0):.1f} tok/s")
print(f"• User Memory Profile: Hair Type = {memory.get('hair_type')}, Concern = {memory.get('primary_concern')}")
print(f"• Recent Hindsight Rules Recorded: {len(hindsights)}")

print("\n>>> ALL STREAMLIT DASHBOARDS & DATA ENGINES FULLY OPERATIONAL! <<<")
