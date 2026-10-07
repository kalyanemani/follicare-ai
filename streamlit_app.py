import os
import json
import time
import streamlit as st
import pandas as pd

# Set page config
st.set_page_config(
    page_title="FolliCare Multi-Agent AI & RAG Platform",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-family: 'Playfair Display', serif;
        font-size: 2.3rem;
        font-weight: 700;
        color: #10b981;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1rem;
        color: #6ee7b7;
        margin-bottom: 20px;
    }
    .stat-badge {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .product-card-st {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# Lazy import backend agents & stores
@st.cache_resource
def load_multi_agent_system():
    from agents.orchestrator import MultiAgentSupervisor
    from rag.vector_store import get_vector_store
    from agents.product_agent import ProductManagementAgent
    from mcp_server import FolliCareMCPServer
    
    return {
        "supervisor": MultiAgentSupervisor(),
        "vector_store": get_vector_store(),
        "product_agent": ProductManagementAgent(),
        "mcp_server": FolliCareMCPServer()
    }

system = load_multi_agent_system()
supervisor = system["supervisor"]
vector_store = system["vector_store"]
product_agent = system["product_agent"]
mcp_server = system["mcp_server"]

# Base Data Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRODUCTS_FILE = os.path.join(BASE_DIR, "data", "products.json")

def load_products():
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Initialize Session State
if "cart" not in st.session_state:
    st.session_state.cart = []
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hello! I am your **FolliCare AI Trichologist & Store Supervisor**. Ask me about hair formulas, clinical studies, or tell me to add products directly to your cart or store catalog!"}
    ]

# Sidebar
with st.sidebar:
    st.markdown("### 🌿 FolliCare Navigation")
    tab_selection = st.radio(
        "Choose Mode:",
        ["🤖 Multi-Agent AI Copilot", "🛍️ Product Catalog Explorer", "✨ Hair Diagnostic Regimen", "➕ Add Formula (AI Ingestion)", "🔌 MCP Server & RAG Inspector"]
    )
    
    st.markdown("---")
    # Live Shopping Cart Widget in Sidebar
    cart_total = sum(item["product"]["price"] * item["quantity"] for item in st.session_state.cart)
    cart_qty = sum(item["quantity"] for item in st.session_state.cart)
    st.markdown(f"### 🛍️ Shopping Bag ({cart_qty} items)")
    if st.session_state.cart:
        for idx, item in enumerate(st.session_state.cart):
            p = item["product"]
            c_col1, c_col2 = st.columns([3, 1])
            with c_col1:
                st.markdown(f"**{p.get('icon', '🌿')} {p['name']}**")
                st.caption(f"${p['price']:.2f} × {item['quantity']}")
            with c_col2:
                if st.button("❌", key=f"del_cart_{idx}_{p['id']}"):
                    st.session_state.cart.pop(idx)
                    st.rerun()
        st.markdown(f"**Subtotal: `${cart_total:.2f}`**")
        if st.button("🛒 Proceed to Checkout", use_container_width=True):
            st.success(f"🎉 Order placed successfully for ${cart_total:.2f}!")
            st.session_state.cart = []
            st.rerun()
    else:
        st.caption("Your botanical bag is empty. Ask the agent to add any product!")

    st.markdown("---")
    st.markdown("#### ⚙️ System Metrics")
    st.write(f"**Architecture:** Hierarchical Multi-Agent Graph")
    st.write(f"**Indexed RAG Chunks:** `{len(vector_store.documents)}`")
    st.write(f"**Active Agents:** Supervisor, Ingestion, RAG, UI, Voice")
    st.write(f"**MCP Protocol:** JSON-RPC 2.0 (Active)")

# Tab 1: Multi-Agent AI Copilot
if tab_selection == "🤖 Multi-Agent AI Copilot":
    st.markdown('<p class="main-header">🌿 FolliCare Dual-Mode Multi-Agent Copilot</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Switch between Customer Shopping/Trichology Mode and UI Developer & Customizer Mode.</p>', unsafe_allow_html=True)
    
    # Dual Operating Mode Radio
    op_mode_choice = st.radio(
        "Select Operating Mode:",
        ["🛍️ Customer Conversational AI Mode", "🛠️ UI Developer & Customizer Mode"],
        horizontal=True,
        index=0 if st.session_state.get("op_mode", "customer") == "customer" else 1
    )
    current_mode = "customer" if "Customer" in op_mode_choice else "developer"
    st.session_state["op_mode"] = current_mode

    # Quick prompt buttons based on active mode
    if current_mode == "customer":
        st.write("**💡 Suggested Customer Prompts:**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("🛍️ Add 2 Rosemary Serums to Cart"):
                st.session_state["preset_query"] = "Two items of Rosemary serum to my cart."
        with col2:
            if st.button("🔬 Rosemary vs Minoxidil"):
                st.session_state["preset_query"] = "What does clinical science say about Rosemary Leaf Oil compared to Minoxidil?"
        with col3:
            if st.button("🎟️ Apply 25% Discount"):
                st.session_state["preset_query"] = "Apply discount coupon code GROWTH25 to my order"
        with col4:
            if st.button("📦 60-Day Guarantee Policy"):
                st.session_state["preset_query"] = "What is your return and 60-day satisfaction guarantee policy for opened bottles?"
    else:
        st.write("**🛠️ Suggested UI Developer Prompts:**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("✨ Inject Clinical Proof Module"):
                st.session_state["preset_query"] = "Inject a live clinical proof strip module under the hero section"
        with col2:
            if st.button("🌟 Verified Reviews Carousel"):
                st.session_state["preset_query"] = "Add customer reviews testimonial component to the store"
        with col3:
            if st.button("🎨 Frosted Glass & Glow CSS"):
                st.session_state["preset_query"] = "Apply custom CSS: glassmorphism blur and card neon glow"
        with col4:
            if st.button("📐 Reconfigure 4-Column Grid"):
                st.session_state["preset_query"] = "Modify layout to 4 responsive columns"

    # Display Chat Messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🌿" if msg["role"] == "assistant" else None):
            st.markdown(msg["content"])
            if "executed_actions" in msg and msg["executed_actions"]:
                for action_txt in msg["executed_actions"]:
                    st.success(f"⚡ **Action Executed:** {action_txt}")
            if "trace" in msg and msg["trace"]:
                with st.expander(f"🔍 Multi-Agent Observability Trace ({len(msg['trace'])} steps)"):
                    for step in msg["trace"]:
                        st.write(f"**{step['agent']}** — *{step['action']}* ({step.get('execution_time_ms', 0)}ms)")
                        st.caption(step['details'])
            if "citations" in msg and msg["citations"]:
                with st.expander("📚 Retrieved RAG Citations"):
                    for c in msg["citations"]:
                        st.write(f"• **{c['title']}** (`{c['category']}`) — Match: `{int(c['score']*100)}%`")

    # Chat Input Box
    query = st.chat_input("Ask hair trichology science or tell agent what to change / add to cart...")
    if "preset_query" in st.session_state and st.session_state["preset_query"]:
        query = st.session_state["preset_query"]
        st.session_state["preset_query"] = ""

    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant", avatar="🌿"):
            with st.spinner(f"🤖 Multi-Agent Graph executing in [{current_mode.upper()}] Mode..."):
                response = supervisor.process(query=query, input_type="text", mode=current_mode)
                st.markdown(response["reply"])

                # Execute UI Commands in Streamlit session state
                executed_actions = []
                if response.get("ui_commands"):
                    all_p = load_products()
                    for cmd in response["ui_commands"]:
                        action_type = cmd.get("action")
                        payload = cmd.get("payload", {})
                        if action_type == "ADD_TO_CART":
                            target_id = payload.get("productId")
                            target_p = next((p for p in all_p if p["id"] == target_id), None)
                            if target_p:
                                existing_item = next((item for item in st.session_state.cart if item["product"]["id"] == target_id), None)
                                if existing_item:
                                    existing_item["quantity"] += payload.get("quantity", 1)
                                else:
                                    st.session_state.cart.append({"product": target_p, "quantity": payload.get("quantity", 1)})
                                act_msg = f"Added {payload.get('quantity', 1)}x '{target_p['name']}' ({target_p.get('icon', '🌿')}) to Shopping Bag."
                                executed_actions.append(act_msg)
                                st.success(f"🛍️ **UI Action Executed:** {act_msg}")
                        elif action_type == "SET_CUSTOM_CSS":
                            act_msg = "Injected Custom CSS styling rules into DOM head."
                            executed_actions.append(act_msg)
                            st.info(f"🎨 **Developer Action Executed:** {act_msg}")
                        elif action_type == "INJECT_REACT_COMPONENT":
                            comp_name = payload.get("componentName", "Component")
                            act_msg = f"Injected Dynamic Component: '{comp_name}'."
                            executed_actions.append(act_msg)
                            st.success(f"✨ **Developer Action Executed:** {act_msg}")
                            if payload.get("html"):
                                st.markdown(payload["html"], unsafe_allow_html=True)
                        elif action_type == "MODIFY_LAYOUT":
                            act_msg = f"Reconfigured Catalog Layout to {payload.get('columns', 3)} columns."
                            executed_actions.append(act_msg)
                            st.info(f"📐 **Developer Action Executed:** {act_msg}")
                        elif action_type == "SET_THEME":
                            act_msg = f"Switched storefront visual aesthetic to '{payload.get('theme')}'."
                            executed_actions.append(act_msg)
                            st.info(f"✨ **UI Action Executed:** {act_msg}")
                        elif action_type == "FILTER_PRODUCTS":
                            act_msg = f"Filtered catalog view (Category: {payload.get('category', 'All')}, Concern: {payload.get('hairConcern', 'All')})."
                            executed_actions.append(act_msg)
                            st.info(f"🔍 **UI Action Executed:** {act_msg}")

                # Expandable Agent Execution Trace
                if response.get("trace_steps"):
                    with st.expander(f"🔍 Multi-Agent Observability Trace ({response.get('total_time_ms')}ms)"):
                        for step in response["trace_steps"]:
                            st.write(f"**{step['agent']}** — *{step['action']}* ({step.get('execution_time_ms', 0)}ms)")
                            st.caption(step["details"])

                # Expandable Citations
                if response.get("citations"):
                    with st.expander("📚 Retrieved RAG Citations"):
                        for c in response["citations"]:
                            st.write(f"• **{c['title']}** (`{c['category']}`) — Match: `{int(c['score']*100)}%`")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response["reply"],
                    "executed_actions": executed_actions,
                    "trace": response.get("trace_steps"),
                    "citations": response.get("citations")
                })
                st.rerun()

# Tab 2: Product Catalog Explorer
elif tab_selection == "🛍️ Product Catalog Explorer":
    st.markdown('<p class="main-header">🛍️ FolliCare Botanical Hair Cosmetics Catalog</p>', unsafe_allow_html=True)
    products = load_products()
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        concern_filter = st.selectbox(
            "Filter by Hair Concern:",
            ["All", "Hair Fall & Thinning", "Damaged & Dry Hair", "Dandruff & Oily Scalp", "Curly, Coily & Wavy (3A-4C)", "Frizz & Heat Protection", "Color Care & Blonde Tone"]
        )
    with col_f2:
        category_filter = st.selectbox(
            "Filter by Category:",
            ["All", "Scalp Care", "Shampoo & Wash", "Treatments & Masks", "Styling & Finish"]
        )
    with col_f3:
        max_price = st.slider("Max Price (USD):", 10.0, 60.0, 55.0, 1.0)

    filtered = products
    if concern_filter != "All":
        filtered = [p for p in filtered if p.get("hairConcern") == concern_filter]
    if category_filter != "All":
        filtered = [p for p in filtered if p.get("category") == category_filter]
    filtered = [p for p in filtered if float(p.get("price", 0)) <= max_price]

    st.write(f"Showing **{len(filtered)}** formula(s):")
    
    # 2-column card layout
    grid_col1, grid_col2 = st.columns(2)
    for idx, p in enumerate(filtered):
        target_col = grid_col1 if idx % 2 == 0 else grid_col2
        with target_col:
            with st.container():
                st.markdown(f"""
                <div class="product-card-st">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:1.4rem;">{p.get('icon', '🌿')}</span>
                        <span class="stat-badge">{p.get('tag', 'Clinical')}</span>
                    </div>
                    <h4 style="margin: 8px 0 4px 0;">{p.get('name')}</h4>
                    <p style="color:#10b981; font-weight:700; margin:0 0 8px 0;">${p.get('price'):.2f} <span style="font-size:0.75rem; color:#6ee7b7; font-weight:400;">({p.get('category')} | {p.get('hairConcern')})</span></p>
                    <p style="font-size:0.85rem; color:#d1fae5; line-height:1.4;">{p.get('description')}</p>
                    <p style="font-size:0.78rem; color:#34d399;"><b>Actives:</b> {", ".join(p.get('activeIngredients', []))}</p>
                    <p style="font-size:0.78rem; color:#fbbf24;">★ {p.get('rating', 4.9)} ({p.get('reviewsCount', 100)}+ reviews)</p>
                </div>
                """, unsafe_allow_html=True)

# Tab 3: Hair Diagnostic Regimen
elif tab_selection == "✨ Hair Diagnostic Regimen":
    st.markdown('<p class="main-header">✨ Personalized Hair Diagnostic Regimen Builder</p>', unsafe_allow_html=True)
    st.markdown("Select your primary condition to generate a custom 3-step trichology protocol:")
    
    concern_choice = st.selectbox(
        "Select Hair Condition:",
        ["Hair Fall & Thinning", "Damaged & Dry Hair", "Dandruff & Oily Scalp", "Curly, Coily & Wavy (3A-4C)", "Frizz & Heat Protection"]
    )
    
    if st.button("Generate 3-Step Botanical Protocol", type="primary"):
        with st.spinner("Formulating protocol..."):
            mcp_res = mcp_server.handle_call_tool("recommend_hair_routine", {"hairConcern": concern_choice})
            data = json.loads(mcp_res["content"][0]["text"])
            
            st.success(f"Generated Protocol for: {concern_choice}")
            st.write("---")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("#### 1️⃣ Step 1: Cleanse")
                st.write(data["step1_cleanse"])
            with col2:
                st.markdown("#### 2️⃣ Step 2: Treat")
                st.write(data["step2_treat"])
            with col3:
                st.markdown("#### 3️⃣ Step 3: Protect")
                st.write(data["step3_protect"])
                
            st.markdown("#### 🌿 Synergistic Recommended Bundle:")
            for p in data["recommended_products"]:
                st.write(f"• **{p['name']}** (${p['price']}) — *{p['category']}*")

# Tab 4: Add Formula (AI Ingestion)
elif tab_selection == "➕ Add Formula (AI Ingestion)":
    st.markdown('<p class="main-header">➕ Add Formula via Agent Ingestion</p>', unsafe_allow_html=True)
    st.markdown("Enter natural text or structured fields to add a formula. It will chunk, embed into local RAG, and update the catalog in real-time.")
    
    with st.form("add_product_form"):
        prod_name = st.text_input("Formula Name:", "Rosemary & Caffeine Follicle Density Oil")
        col_a, col_b = st.columns(2)
        with col_a:
            prod_cat = st.selectbox("Category:", ["Scalp Care", "Shampoo & Wash", "Treatments & Masks", "Styling & Finish"])
            prod_price = st.number_input("Price (USD):", min_value=5.0, max_value=200.0, value=29.99, step=1.0)
        with col_b:
            prod_concern = st.selectbox("Hair Concern:", ["Hair Fall & Thinning", "Damaged & Dry Hair", "Dandruff & Oily Scalp", "Curly, Coily & Wavy (3A-4C)", "Frizz & Heat Protection"])
            prod_actives = st.text_input("Active Ingredients (comma-separated):", "Organic Rosemary Oil 3%, Caffeine, Copper Peptides")
            
        prod_desc = st.text_area("Formula Description:", "Trichologist-formulated daily root density treatment.")
        submitted = st.form_submit_button("Ingest & Vector Embed Formula", type="primary")
        
        if submitted:
            actives_list = [a.strip() for a in prod_actives.split(",") if a.strip()]
            new_prod = {
                "id": f"prod_st_{int(time.time()) % 10000}",
                "name": prod_name,
                "category": prod_cat,
                "hairConcern": prod_concern,
                "price": float(prod_price),
                "originalPrice": round(float(prod_price) * 1.25, 2),
                "rating": 5.0,
                "reviewsCount": 1,
                "tag": "New Ingested Formula",
                "badgeColor": "badge-emerald",
                "description": prod_desc,
                "icon": "🌿",
                "inStock": True,
                "activeIngredients": actives_list,
                "benefits": ["Formulated via Streamlit Agent Ingestion", "Clean botanical actives", "Sulfate-free"],
                "clinicalResult": "Formulated according to clean trichological standards.",
                "usageInstructions": "Apply to scalp or hair strands daily.",
                "specs": ["Clean Beauty", "Dermatologist Tested", "Sulfate-Free"]
            }
            res = product_agent.ingest_product(new_prod)
            st.success(f"✅ Ingested and indexed '{prod_name}' (${prod_price}) into catalog & RAG vector store!")
            st.balloons()

# Tab 5: MCP Server & RAG Inspector
elif tab_selection == "🔌 MCP Server & RAG Inspector":
    st.markdown('<p class="main-header">🔌 Model Context Protocol (MCP) & RAG Inspector</p>', unsafe_allow_html=True)
    st.markdown("Directly test MCP tools, inspect knowledge chunks, and run semantic queries.")
    
    st.markdown("### 🛠️ Available MCP Tools")
    tools = mcp_server.get_tools_definition()
    for t in tools:
        st.write(f"• **`{t['name']}`**: {t['description']}")
        
    st.markdown("### 🔍 Live Semantic RAG Search")
    test_query = st.text_input("Test Query:", "What is the 60-day satisfaction guarantee policy?")
    if test_query:
        docs = vector_store.search(query=test_query, top_k=3)
        st.write(f"Retrieved **{len(docs)}** semantic chunk(s):")
        for d in docs:
            st.info(f"**{d.get('title')}** (Score: `{d.get('relevance_score')}` | Category: `{d.get('category')}`)\n\n{d.get('content')}")
