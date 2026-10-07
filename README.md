# FolliCare Botanical Hair Cosmetics - Multi-Agent AI & RAG Platform

> **A Clinical Trichology & Botanical Hair Wellness Storefront powered by a Hierarchical Multi-Agent Architecture, Local Semantic Vector RAG, Real-Time Voice/UI Automation, and a Model Context Protocol (MCP) Server.**

---

## 🌟 Key Capabilities & Features

1. **🌿 Hair Health & Cosmetics Storefront**
   - **Clinical Formulas:** Formulated for targeted hair concerns: *Hair Fall & Thinning*, *Damaged & Bleached Strands*, *Dandruff & Flake Control*, *Curls & Coils (3A-4C)*, *Frizz & Thermal Heat Shield*, and *Color & Tone Glaze*.
   - **Interactive Hair Diagnostic Regimen Builder:** Formulates custom 3-step trichology routines with 1-click bundle purchase.
   - **Curated Beauty Aesthetic Themes:** 5 switchable themes: `🌿 Botanical Emerald`, `🌸 Rose Luxury`, `💜 Lavender Clean`, `🌙 Amber Noir`, and `☀️ Light Minimal`.

2. **📦 Voice & Text Product Ingestion Engine**
   - Ingest new cosmetic formulas on the fly using natural voice or chat (e.g., *"Add a new product: Rosemary Scalp Oil with 3% Biotin for $28"*).
   - **Automatic Extraction:** Parses formula name, category, actives, price, and hair concern.
   - **Real-Time RAG Indexing:** Automatically chunks and vector-indexes new products into the local semantic vector store.
   - **Live DOM Rendering:** Immediately injects the newly created product card directly into the storefront grid with animated pulse highlighting.

3. **📚 Local Semantic Vector RAG (Zero Cloud Dependency)**
   - **Multi-Strategy Chunker (`rag/chunker.py`):** Recursive character chunking & semantic field splitting with configurable token overlap.
   - **Dense Embeddings & Vector Search (`rag/vector_store.py`):** Sublinear TF-IDF (unigram, bigram, trigram) vector matrix + Cosine similarity + BM25-style keyword boosting with zero external cloud API lock-in.
   - **Trichology Knowledge Base:** Deep ingredient science (Rosemary, Copper Peptides, Redensyl, Keratin), dermatological clinical trial results, safety patch-testing guidelines, and 60-day guarantee policies.

4. **⚡ Multi-Agent Graph Architecture (`agents/`)**
   - **🎯 Supervisor Orchestrator Agent (`agents/orchestrator.py`):** Intent classification, graph state routing, and sub-agent coordination.
   - **📦 Product Ingestion Agent (`agents/product_agent.py`):** Structured entity parsing, catalog persistence, and vector re-indexing.
   - **📚 RAG Trichology Agent (`agents/rag_agent.py`):** Semantic retrieval with citations and relevance scoring.
   - **⚡ UI Automation Agent (`agents/ui_agent.py`):** Compiles declarative DOM mutation actions (`SET_THEME`, `SET_BANNER`, `UPDATE_HERO`, `FILTER_PRODUCTS`, `ADD_PRODUCT`, `ADD_TO_CART`, `LAUNCH_ROUTINE_BUILDER`).
   - **🎙️ Voice & Response Agent (`agents/response_agent.py`):** Synthesizes dialogue and generates clean audio speech transcripts for Web Speech API TTS.

5. **🔌 Model Context Protocol (MCP) Server (`mcp_server.py`)**
   - Compliant with Anthropic's **Model Context Protocol (JSON-RPC 2.0)** standard over stdio and HTTP (`/api/mcp/rpc`).
   - **Tools:** `search_hair_knowledge`, `get_catalog_products`, `ingest_new_product`, `execute_ui_mutation`, `recommend_hair_routine`.
   - **Resources:** `follicare://catalog`, `follicare://knowledge-base`, `follicare://system-info`.
   - **Prompts:** `hair_consultation_diagnostic`, `product_ingestion_prompt`.

---

## 🚀 Quick Start & Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Multi-Agent Application
You can run either the **FastAPI Web Application** or the **Interactive Streamlit Dashboard**:

**Option A: Run FastAPI Web Storefront**
```bash
python app.py
```
Visit **`http://127.0.0.1:8000`** in your browser.

**Option B: Run Streamlit Interactive Dashboard**
```bash
streamlit run streamlit_app.py
```
Visit **`http://localhost:8501`** in your browser.

### 3. Run the Automated Test Suite
```bash
python tests/test_agents.py
```

### 4. Run via Docker
```bash
docker-compose up --build
```

---

## 🛠️ MCP (Model Context Protocol) Server Configuration

To connect this store's MCP server to **Claude Desktop**, **Cursor**, or **Antigravity IDE**, add this block to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "follicare-cosmetics": {
      "command": "python",
      "args": ["c:/Users/krishkal/Desktop/er/mcp_server.py"]
    }
  }
}
```

---

## 📁 Repository Structure

```
.
├── app.py                      # FastAPI server & HTTP API routes
├── mcp_server.py               # Model Context Protocol (MCP) JSON-RPC 2.0 Server
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container definition
├── docker-compose.yml          # Container orchestration
├── agents/
│   ├── orchestrator.py         # Multi-Agent Supervisor & Graph Router
│   ├── product_agent.py        # Voice/Text Product Ingestion Agent
│   ├── rag_agent.py            # RAG Trichology Knowledge Agent
│   ├── ui_agent.py             # Declarative UI Automation Agent
│   └── response_agent.py       # Voice Dialogue & Speech Synthesis Agent
├── rag/
│   ├── chunker.py              # Recursive Character & Semantic Field Chunker
│   ├── vector_store.py         # Local In-Memory Dense Vector Store & Indexer
│   └── knowledge_base.json     # Trichology Guides, Clinical Trials & Policies
├── data/
│   └── products.json           # Hair Health & Cosmetics Catalog Database
├── static/
│   ├── index.html              # Luxury Cosmetics Storefront UI
│   ├── css/
│   │   └── style.css           # Design Tokens, 5 Curated Themes & Responsive Layout
│   └── js/
│       ├── app.js              # Frontend Catalog, Routine Wizard & Cart Controller
│       ├── ui-automation.js    # Client-side Declarative DOM Mutation Engine
│       └── agents-client.js    # Web Speech API STT/TTS & Trace Observability
└── tests/
    └── test_agents.py          # Automated Test Suite for RAG, Ingestion, UI & MCP
```
