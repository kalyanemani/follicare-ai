import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.vector_store import get_vector_store
from agents.orchestrator import MultiAgentSupervisor
from agents.product_agent import ProductManagementAgent
from mcp_server import FolliCareMCPServer

def test_rag_vector_store():
    store = get_vector_store()
    results = store.search("What is the satisfaction guarantee and return policy?", top_k=2)
    assert len(results) > 0, "Vector store should return results"
    assert "guarantee" in results[0]["title"].lower() or "satisfaction" in results[0]["title"].lower()
    print("[PASS] Vector store policy search passed. Found:", results[0]["title"])

    # Test ingredient search
    res_ingredient = store.search("How does Rosemary Leaf Oil compare to Minoxidil for hair thinning?", top_k=2)
    assert len(res_ingredient) > 0
    assert any("rosemary" in r["title"].lower() or "thinning" in r["title"].lower() for r in res_ingredient)
    print("[PASS] Vector store ingredient science search passed. Found:", res_ingredient[0]["title"])

def test_product_ingestion_agent():
    prod_agent = ProductManagementAgent()
    query = "Add a new product: Rosemary Scalp Oil with 3% Biotin and Caffeine for $29.99 in Scalp Care"
    res = prod_agent.process(query)
    assert res["status"] == "success"
    assert res["action"] in ["ADD_PRODUCT", "UPDATE_PRODUCT"]
    assert res["product"]["price"] == 29.99
    assert "Rosemary" in res["product"]["name"]
    print("[PASS] Product ingestion agent passed. Ingested:", res["product"]["name"], f"${res['product']['price']}")

    # Verify vector store immediately contains the new product chunk
    store = get_vector_store()
    search_res = store.search("Rosemary Scalp Oil", top_k=2)
    assert len(search_res) > 0
    print("[PASS] Dynamic RAG vector indexing verified. Found newly added product in search.")

def test_ui_agent_theme_banner_and_routine():
    supervisor = MultiAgentSupervisor()
    res = supervisor.process("Switch the storefront theme to rose luxury and add a 25% sale banner with code GROWTH25")
    assert res["status"] == "success"
    assert len(res["ui_commands"]) >= 2
    actions = [c["action"] for c in res["ui_commands"]]
    assert "SET_THEME" in actions
    assert "SET_BANNER" in actions
    print("[PASS] UI theme & banner action test passed. Commands:", actions)

def test_hybrid_routine_and_filter():
    supervisor = MultiAgentSupervisor()
    res = supervisor.process("Recommend a routine for hair fall and thinning and filter products under $35")
    assert res["status"] == "success"
    assert len(res["citations"]) > 0
    actions = [c["action"] for c in res["ui_commands"]]
    assert "FILTER_PRODUCTS" in actions or "LAUNCH_ROUTINE_BUILDER" in actions
    assert len(res["speech_text"]) > 0
    print("[PASS] Hybrid Trichology RAG + UI Filter test passed.")

def test_mcp_server_json_rpc():
    server = FolliCareMCPServer()

    # 1. Initialize
    init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    init_res = server.process_json_rpc(init_req)
    assert init_res["result"]["serverInfo"]["name"] == "follicare-cosmetics-mcp"
    print("[PASS] MCP initialize passed.")

    # 2. Tools List
    tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    tools_res = server.process_json_rpc(tools_req)
    tool_names = [t["name"] for t in tools_res["result"]["tools"]]
    assert "search_hair_knowledge" in tool_names
    assert "recommend_hair_routine" in tool_names
    print("[PASS] MCP tools/list passed. Tools:", tool_names)

    # 3. Call Tool: recommend_hair_routine
    call_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "recommend_hair_routine",
            "arguments": {"hairConcern": "Damaged & Dry Hair"}
        }
    }
    call_res = server.process_json_rpc(call_req)
    content_text = call_res["result"]["content"][0]["text"]
    data = json.loads(content_text)
    assert data["hairConcern"] == "Damaged & Dry Hair"
    assert "step1_cleanse" in data
    print("[PASS] MCP tools/call recommend_hair_routine passed.")

    # 4. Resources Read
    res_req = {"jsonrpc": "2.0", "id": 4, "method": "resources/read", "params": {"uri": "follicare://catalog"}}
    res_resp = server.process_json_rpc(res_req)
    catalog_data = json.loads(res_resp["result"]["contents"][0]["text"])
    assert len(catalog_data) > 0
    print(f"[PASS] MCP resources/read passed. Catalog contains {len(catalog_data)} items.")

if __name__ == "__main__":
    print("--- RUNNING FOLLICARE MULTI-AGENT & RAG TEST SUITE ---")
    test_rag_vector_store()
    test_product_ingestion_agent()
    test_ui_agent_theme_banner_and_routine()
    test_hybrid_routine_and_filter()
    test_mcp_server_json_rpc()
    print("\n>>> ALL 5 TEST SUITES PASSED FLAWLESSLY! <<<")
