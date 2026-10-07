import os
import json
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from agents.orchestrator import MultiAgentSupervisor
from agents.product_agent import ProductManagementAgent
from agents.monitoring import get_observability_pipeline
from rag.vector_store import get_vector_store
from mcp_server import FolliCareMCPServer

app = FastAPI(
    title="FolliCare Botanical Hair Cosmetics - Multi-Agent AI, Tracing & RAG Platform",
    description="Multi-Agent architecture with local Ollama models (Qwen, Llama, Gemma), OpenTelemetry-style tracing, local RAG, voice/text input, and real-time UI automation.",
    version="2.1.0"
)

# CORS configuration (allows React apps on localhost:3000 / localhost:5173 to connect seamlessly)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Multi-Agent Supervisor, Product Agent, Vector Store, Monitoring & MCP Server
supervisor = MultiAgentSupervisor()
product_agent = ProductManagementAgent()
vector_store = get_vector_store()
mcp_server = FolliCareMCPServer()
tracer = get_observability_pipeline()

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATA_DIR = os.path.join(BASE_DIR, "data")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")

# Request Models
class ChatRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    message: str
    input_type: Optional[str] = "text" # "text" or "voice"
    mode: Optional[str] = "customer" # "customer" or "developer"
    model_name: Optional[str] = "qwen2.5:3b"
    session_id: Optional[str] = "default_user"

class ProductCreateRequest(BaseModel):
    name: str
    price: float
    category: Optional[str] = "Scalp Care"
    hairConcern: Optional[str] = "Hair Fall & Thinning"
    activeIngredients: Optional[List[str]] = None
    description: Optional[str] = None
    icon: Optional[str] = "🌿"
    benefits: Optional[List[str]] = None

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "FolliCare Botanical Hair Cosmetics Multi-Agent Engine",
        "version": "2.1.0",
        "cloud_independent": True,
        "indexed_chunks": len(vector_store.documents),
        "agents": ["Supervisor", "Product Ingestion", "RAG Trichology", "UI Automation", "Voice Synthesis"],
        "monitoring_pipeline": "Active",
        "mcp_enabled": True
    }

@app.get("/api/models")
def get_available_models():
    models = supervisor.llm_client.fetch_available_models()
    return {
        "status": "success",
        "default_model": supervisor.llm_client.default_model,
        "available_models": models
    }

@app.get("/api/products")
def get_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    hairConcern: Optional[str] = Query(None, description="Filter by hair concern"),
    q: Optional[str] = Query(None, description="Keyword search query")
):
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            products = json.load(f)

        if category and category != "All":
            products = [p for p in products if p.get("category") == category]
        if hairConcern and hairConcern != "All":
            products = [p for p in products if p.get("hairConcern") == hairConcern]
        if q:
            q_lower = q.lower()
            products = [
                p for p in products if (
                    q_lower in p.get("name", "").lower() or
                    q_lower in p.get("description", "").lower() or
                    any(q_lower in str(act).lower() for act in p.get("activeIngredients", []))
                )
            ]

        return {"status": "success", "total": len(products), "products": products}
    return {"status": "error", "message": "Products file not found"}

@app.post("/api/products")
def create_product(req: ProductCreateRequest):
    if not req.name or req.price <= 0:
        raise HTTPException(status_code=400, detail="Product name and valid price are required.")

    product_dict = {
        "id": f"prod_custom_{len(vector_store.documents) + 1}",
        "name": req.name,
        "category": req.category,
        "hairConcern": req.hairConcern,
        "price": req.price,
        "originalPrice": round(req.price * 1.25, 2),
        "rating": 5.0,
        "reviewsCount": 1,
        "tag": "New Ingested Formula",
        "badgeColor": "badge-emerald",
        "description": req.description or f"Clinically formulated {req.category} for {req.hairConcern}.",
        "icon": req.icon or "🌿",
        "inStock": True,
        "activeIngredients": req.activeIngredients or ["Botanical Extracts", "Biotin", "Vitamin E"],
        "benefits": req.benefits or ["Strengthens hair follicles", "Restores shine and softness", "Cruelty-free & clean"],
        "clinicalResult": "Formulated following clean trichological standards.",
        "usageInstructions": "Apply to clean scalp or hair strands. Massage gently and style.",
        "specs": ["Clean Beauty", "Dermatologist Tested", "Sulfate-Free", "AI Ingested"]
    }

    result = product_agent.ingest_product(product_dict)
    return JSONResponse(content={"status": "success", "action": "ADD_PRODUCT", "product": product_dict})

@app.post("/api/chat")
def chat_pipeline(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    result = supervisor.process(
        query=req.message.strip(),
        input_type=req.input_type,
        mode=req.mode or "customer",
        model_name=req.model_name,
        session_id=req.session_id or "default_user"
    )
    return JSONResponse(content=result)

@app.get("/api/monitoring/metrics")
def get_monitoring_metrics():
    metrics = tracer.get_metrics()
    return JSONResponse(content={"status": "success", "metrics": metrics})

@app.get("/api/monitoring/traces")
def get_monitoring_traces(limit: int = 20):
    traces = tracer.get_recent_traces(limit=limit)
    return JSONResponse(content={"status": "success", "total": len(traces), "traces": traces})

@app.get("/api/kb/search")
def kb_search(
    q: str = Query(..., description="Query for store and trichology documents"),
    k: int = 3,
    category: Optional[str] = Query(None, description="Category filter"),
    hairConcern: Optional[str] = Query(None, description="Hair concern filter")
):
    results = vector_store.search(
        query=q,
        top_k=k,
        category_filter=category,
        hair_concern_filter=hairConcern
    )
    return {"status": "success", "query": q, "total_results": len(results), "results": results}

@app.post("/api/multimodal/analyze")
async def analyze_scalp_image(request: Request):
    """
    Multimodal Vision RAG Endpoint:
    Uses local qwen2.5vl:7b to analyze scalp and hair strand photos.
    """
    body = await request.json()
    image_base64 = body.get("image_base64")
    user_prompt = body.get("prompt", "Analyze this scalp/hair image. Identify the hair condition, texture, and recommend botanical treatments.")

    if not image_base64:
        raise HTTPException(status_code=400, detail="image_base64 string is required.")

    from rag.multimodal_rag import get_multimodal_vision_rag
    vision_rag = get_multimodal_vision_rag()
    res = vision_rag.analyze_hair_image(image_base64, user_prompt)

    # Retrieve products for detected concern
    matching_prods = vector_store.search(query=res.get("detected_concern", "Hair Fall & Thinning"), top_k=3)

    return JSONResponse(content={
        "status": "success",
        "vision_analysis": res,
        "recommended_products": matching_prods
    })

@app.get("/api/routine")
def get_hair_routine(concern: str = Query("Hair Fall & Thinning", description="Hair concern")):
    mcp_res = mcp_server.handle_call_tool("recommend_hair_routine", {"hairConcern": concern})
    data = json.loads(mcp_res["content"][0]["text"])
    return {"status": "success", "routine": data}

@app.post("/api/mcp/rpc")
async def mcp_json_rpc(request: Request):
    body = await request.json()
    response = mcp_server.process_json_rpc(body)
    return JSONResponse(content=response)

@app.post("/api/mcp/git-sync")
async def mcp_git_sync(request: Request):
    """
    Triggers the Git Sync MCP Tool to stage, commit, and push complete React code to Git.
    """
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    branch = body.get("branch", "react-ui-sync")
    msg = body.get("message")
    remote_url = body.get("remoteUrl")

    res = mcp_server.handle_call_tool("git_push_react_code", {
        "branch": branch,
        "commitMessage": msg,
        "remoteUrl": remote_url
    })
    data = json.loads(res["content"][0]["text"])
    return JSONResponse(content=data)

@app.get("/api/agents/info")
def get_agents_info():
    return {
        "architecture": "Hierarchical Multi-Agent Graph with Supervisor, Local Ollama Models, & Observability Tracing",
        "mcp_server": "follicare-cosmetics-mcp (v1.0.0)",
        "vector_engine": "Local Sublinear n-gram TF-IDF Dense Embeddings + Cosine Similarity",
        "total_documents_indexed": len(vector_store.documents),
        "supported_local_models": supervisor.llm_client.available_models,
        "agents": [
            {
                "name": "Supervisor Orchestrator Agent",
                "role": "Intent classification, graph routing, and OpenTelemetry span creation.",
                "capabilities": ["Intent analysis", "Graph routing", "Observability trace generation"]
            },
            {
                "name": "Product Ingestion & Catalog Agent",
                "role": "Extracts structured product specifications from voice/text, persists items, and triggers live vector RAG indexing.",
                "capabilities": ["Voice/Text Schema Parsing", "Disk Persistence", "Dynamic Vector Ingestion", "ADD_PRODUCT Event Dispatch"]
            },
            {
                "name": "RAG Trichology & Knowledge Agent",
                "role": "Semantic retrieval over hair cosmetics science, clinical trial data, and store policies.",
                "capabilities": ["Recursive Chunker", "Semantic Similarity", "Confidence Scoring", "Zero Cloud Dependency"]
            },
            {
                "name": "UI Automation & Action Agent",
                "role": "Translates intent to declarative JSON UI mutation commands.",
                "capabilities": ["SET_THEME", "SET_BANNER", "UPDATE_HERO", "FILTER_PRODUCTS", "APPLY_DISCOUNT", "ADD_TO_CART", "LAUNCH_ROUTINE_BUILDER"]
            },
            {
                "name": "Voice & Response Agent",
                "role": "Synthesizes customer-friendly trichology consultations with local Ollama models and TTS speech stream.",
                "capabilities": ["Local LLM Reasoning", "Empathetic dialogue", "Web Speech API TTS stream synthesis"]
            }
        ]
    }

# Mount static folder
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_home():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "FolliCare frontend index.html not yet initialized"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
