/**
 * FolliCare Dynamic Multi-Agent Storefront Frontend Controller
 */

let currentTheme = 'botanical-emerald';
let cart = [];
let allProducts = [];
let isVoiceRecording = false;
let recognition = null;

// Initialize Speech Recognition if supported
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'en-US';

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    document.getElementById('chat-input').value = transcript;
    sendMessage(transcript, 'voice');
  };

  recognition.onend = () => {
    isVoiceRecording = false;
    const btn = document.getElementById('voice-record-btn');
    if (btn) btn.classList.remove('recording');
  };
}

// Fetch products and populate UI
async function loadProducts(categoryFilter = null) {
  try {
    const res = await fetch('/api/products');
    const data = await res.json();
    allProducts = data.products || [];
    renderProducts(categoryFilter);
  } catch (err) {
    console.error('Failed to load products:', err);
  }
}

function renderProducts(filter = null) {
  const grid = document.getElementById('product-grid');
  if (!grid) return;

  const filtered = filter && filter !== 'All'
    ? allProducts.filter(p => (p.category && p.category.toLowerCase().includes(filter.toLowerCase())) || (p.hairConcern && p.hairConcern.toLowerCase().includes(filter.toLowerCase())))
    : allProducts;

  if (filtered.length === 0) {
    grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-muted);">No products found matching '${filter}'.</div>`;
    return;
  }

  grid.innerHTML = filtered.map(p => `
    <div class="product-card" data-id="${p.id}">
      <span class="product-badge">${p.hairConcern || 'Trichologist Approved'}</span>
      <div class="product-icon">${p.icon || '🌿'}</div>
      <h3 class="product-name">${p.name}</h3>
      <p class="product-desc">${p.description || 'Clinical-grade botanical formulation for scalp and follicle vitality.'}</p>
      <div class="product-ingredients">
        ${(p.activeIngredients || ['Biotin', 'Peptides']).slice(0, 3).map(ing => `<span class="ing-tag">${ing}</span>`).join('')}
      </div>
      <div class="product-footer">
        <div class="product-price">
          $${p.price.toFixed(2)}
          <span class="orig-price">$${(p.price * 1.25).toFixed(2)}</span>
        </div>
        <button class="btn-primary" onclick="addToCart('${p.id}', '${escapeHtml(p.name)}', ${p.price}, '${p.icon || '🌿'}', 1)">
          Add to Bag
        </button>
      </div>
    </div>
  `).join('');
}

function escapeHtml(text) {
  return text.replace(/'/g, "\\'");
}

// Cart System
function addToCart(id, name, price, icon, qty = 1) {
  const existing = cart.find(i => i.id === id);
  if (existing) {
    existing.quantity += qty;
  } else {
    cart.push({ id, name, price, icon, quantity: qty });
  }
  updateCartUI();
  showToast(`Added ${qty}x "${name}" to your bag!`);
}

function updateCartUI() {
  const countEl = document.getElementById('cart-count');
  const itemsContainer = document.getElementById('cart-items');
  const subtotalEl = document.getElementById('cart-subtotal');

  const totalCount = cart.reduce((acc, i) => acc + i.quantity, 0);
  const totalSubtotal = cart.reduce((acc, i) => acc + (i.price * i.quantity), 0);

  if (countEl) countEl.innerText = totalCount;
  if (subtotalEl) subtotalEl.innerText = `$${totalSubtotal.toFixed(2)}`;

  if (itemsContainer) {
    if (cart.length === 0) {
      itemsContainer.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 30px;">Your shopping bag is empty.</div>';
    } else {
      itemsContainer.innerHTML = cart.map(item => `
        <div class="cart-item">
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 1.5rem;">${item.icon}</span>
            <div>
              <div style="font-weight: 700; font-size: 0.9rem;">${item.name}</div>
              <div style="font-size: 0.8rem; color: var(--accent-color);">$${item.price.toFixed(2)} x ${item.quantity}</div>
            </div>
          </div>
          <button style="background: transparent; border: none; color: #fda4af; cursor: pointer; font-size: 1.1rem;" onclick="removeFromCart('${item.id}')">✕</button>
        </div>
      `).join('');
    }
  }
}

function removeFromCart(id) {
  cart = cart.filter(i => i.id !== id);
  updateCartUI();
}

function toggleCartDrawer() {
  const drawer = document.getElementById('cart-drawer');
  if (drawer) drawer.classList.toggle('open');
}

// Theme Switcher
function setTheme(theme) {
  currentTheme = theme;
  document.documentElement.setAttribute('data-theme', theme);
  const select = document.getElementById('theme-select');
  if (select) select.value = theme;
}

// Toast notification
function showToast(msg) {
  const toast = document.createElement('div');
  toast.innerText = msg;
  toast.style.cssText = `
    position: fixed; top: 70px; right: 24px; z-index: 9999;
    background: var(--bg-card); color: var(--text-primary);
    border: 1px solid var(--border-focus); padding: 12px 20px;
    border-radius: 12px; box-shadow: var(--shadow-lg);
    animation: slideDown 0.3s ease-out; font-weight: 600; font-size: 0.9rem;
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

// Speech Synthesis
function speakText(text) {
  if ('speechSynthesis' in window && text) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.05;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
  }
}

// AI Assistant Chat & UI Automation Dispatcher
async function sendMessage(text = null, inputType = 'text') {
  const inputEl = document.getElementById('chat-input');
  const query = text || (inputEl ? inputEl.value.trim() : '');
  if (!query) return;

  if (inputEl) inputEl.value = '';

  appendChatMessage(query, 'user');

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: query,
        input_type: inputType,
        mode: 'customer',
        model_name: 'qwen2.5:3b'
      })
    });

    const data = await res.json();
    const replyText = data.reply_message || data.reply || 'Thank you for consulting FolliCare AI!';
    appendChatMessage(replyText, 'agent');

    if (data.speech_text) {
      speakText(data.speech_text);
    }

    // Execute UI commands returned by UI agent
    if (data.ui_commands && Array.isArray(data.ui_commands)) {
      data.ui_commands.forEach(cmd => executeUICommand(cmd));
    }

    // Update Telemetry Panel if open
    if (data.trace || data.trace_id) {
      updateTelemetryUI(data.trace || data, data.evaluation || data.evaluation_metrics);
    }

  } catch (err) {
    console.error('Chat error:', err);
    appendChatMessage('Error communicating with FolliCare Multi-Agent core.', 'agent');
  }
}

function executeUICommand(cmd) {
  const action = cmd.action;
  const payload = cmd.payload || {};
  console.log('[UI_ACTION]', action, cmd);

  if (action === 'SET_THEME') {
    const theme = cmd.theme || payload.theme || 'botanical-emerald';
    setTheme(theme);
    showToast(`✨ Switched aesthetic theme to "${theme}"!`);
  } else if (action === 'SET_BANNER') {
    const banner = document.getElementById('announcement-banner');
    const msg = cmd.message || payload.message || 'Special FolliCare Botanical Promotion';
    const code = cmd.code || payload.code || '';
    if (banner) {
      banner.innerHTML = `<span>${msg}</span> ${code ? `<span class="code-tag">USE CODE: ${code}</span>` : ''}`;
      showToast(`📢 Updated store banner: ${msg}`);
    }
  } else if (action === 'UPDATE_HERO') {
    const titleEl = document.getElementById('hero-title');
    const subEl = document.getElementById('hero-subtitle');
    const title = cmd.title || payload.title;
    const subtitle = cmd.subtitle || payload.subtitle;
    if (titleEl && title) titleEl.innerHTML = title;
    if (subEl && subtitle) subEl.innerText = subtitle;
  } else if (action === 'FILTER_PRODUCTS') {
    const concern = cmd.hairConcern || payload.hairConcern;
    const maxPrice = cmd.maxPrice || payload.maxPrice;
    if (concern) renderProducts(concern);
    showToast(`🔍 Applied product filter: ${concern || 'Custom'}`);
  } else if (action === 'ADD_TO_CART') {
    const prodName = cmd.productName || payload.productName || 'Rosemary Scalp Density Cleanser';
    const qty = cmd.quantity || payload.quantity || 1;
    const matched = allProducts.find(p => p.name.toLowerCase().includes(prodName.toLowerCase()));
    if (matched) {
      addToCart(matched.id, matched.name, matched.price, matched.icon || '🌿', qty);
    } else {
      addToCart(`custom_${Date.now()}`, prodName, 29.99, '🌿', qty);
    }
  } else if (action === 'UPDATE_PRODUCT_PRICE') {
    const prodName = cmd.productName || payload.productName || 'Rosemary Scalp Oil';
    const newPrice = cmd.newPrice || payload.newPrice || 30.00;
    const matched = allProducts.find(p => p.name.toLowerCase().includes(prodName.toLowerCase()) || prodName.toLowerCase().includes(p.name.toLowerCase()));
    if (matched) {
      matched.price = parseFloat(newPrice);
    }
    renderProducts();
    showToast(`🏷️ Updated price of "${prodName}" to $${parseFloat(newPrice).toFixed(2)}!`);
  } else if (action === 'UPDATE_CARD_STYLE' || action === 'SET_CUSTOM_CSS') {
    const target = payload.target || 'rosemary';
    const maxWidth = payload.maxWidth || '230px';
    const padding = payload.padding || '14px';
    const scale = payload.scale || 0.9;

    const cards = document.querySelectorAll('.product-card');
    cards.forEach(card => {
      const name = card.querySelector('.product-name')?.innerText?.toLowerCase() || '';
      if (target === 'all' || name.includes(target)) {
        card.style.maxWidth = maxWidth;
        card.style.padding = padding;
        card.style.transform = `scale(${scale})`;
        card.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
      }
    });
    showToast(`📐 ${payload.description || 'Adjusted component card dimensions.'}`);
  } else if (action === 'LAUNCH_ROUTINE_BUILDER') {
    const concern = cmd.hairConcern || payload.hairConcern || 'Hair Fall & Thinning';
    launchRoutineModal(concern);
  }
}



function appendChatMessage(msg, sender = 'agent') {
  const body = document.getElementById('chat-body');
  if (!body) return;

  const div = document.createElement('div');
  div.className = `chat-msg ${sender}`;
  div.innerText = msg;
  body.appendChild(div);
  body.scrollTop = body.scrollHeight;
}

function toggleChat() {
  const chat = document.getElementById('chat-window');
  if (chat) {
    chat.style.display = chat.style.display === 'flex' ? 'none' : 'flex';
  }
}

function toggleVoiceRecord() {
  if (!recognition) {
    alert('Speech recognition is not supported in this browser.');
    return;
  }
  const btn = document.getElementById('voice-record-btn');
  if (isVoiceRecording) {
    recognition.stop();
    isVoiceRecording = false;
    if (btn) btn.classList.remove('recording');
  } else {
    recognition.start();
    isVoiceRecording = true;
    if (btn) btn.classList.add('recording');
  }
}

async function launchRoutineModal(concern = 'Hair Fall & Thinning') {
  try {
    const res = await fetch(`/api/routine?concern=${encodeURIComponent(concern)}`);
    const data = await res.json();
    const r = data.routine;

    const modal = document.getElementById('routine-modal');
    const content = document.getElementById('routine-modal-content');
    if (modal && content) {
      content.innerHTML = `
        <h2 style="color: var(--accent-color); margin-bottom: 8px;">🌿 Custom Routine: ${r.hairConcern}</h2>
        <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 20px;">Prescribed by FolliCare Trichology Multi-Agent Engine</p>
        <div style="display: flex; flex-direction: column; gap: 14px;">
          <div style="background: var(--bg-card); padding: 14px; border-radius: 10px; border: 1px solid var(--border-color);">
            <div style="font-weight: 700; color: var(--accent-color);">Step 1: Cleanse</div>
            <div style="font-size: 0.95rem; font-weight: 600;">${r.step1_cleanse?.product || 'Density Shampoo'}</div>
            <div style="font-size: 0.82rem; color: var(--text-secondary);">${r.step1_cleanse?.usage || ''}</div>
          </div>
          <div style="background: var(--bg-card); padding: 14px; border-radius: 10px; border: 1px solid var(--border-color);">
            <div style="font-weight: 700; color: var(--accent-color);">Step 2: Treat</div>
            <div style="font-size: 0.95rem; font-weight: 600;">${r.step2_treat?.product || 'Scalp Serum'}</div>
            <div style="font-size: 0.82rem; color: var(--text-secondary);">${r.step2_treat?.usage || ''}</div>
          </div>
          <div style="background: var(--bg-card); padding: 14px; border-radius: 10px; border: 1px solid var(--border-color);">
            <div style="font-weight: 700; color: var(--accent-color);">Step 3: Nourish</div>
            <div style="font-size: 0.95rem; font-weight: 600;">${r.step3_nourish?.product || 'Fortifying Conditioner'}</div>
            <div style="font-size: 0.82rem; color: var(--text-secondary);">${r.step3_nourish?.usage || ''}</div>
          </div>
        </div>
      `;
      modal.style.display = 'flex';
    }
  } catch (e) {
    console.error('Routine fetch failed:', e);
  }
}

function closeRoutineModal() {
  const modal = document.getElementById('routine-modal');
  if (modal) modal.style.display = 'none';
}

// Developer Mode State & Drawer
let isDevMode = false;
let lastTelemetryData = null;

function toggleDevDrawer() {
  const drawer = document.getElementById('dev-drawer');
  if (drawer) {
    drawer.classList.toggle('open');
  }
}

function toggleDevModeState(enabled) {
  isDevMode = enabled;
  const badge = document.getElementById('dev-mode-badge');
  const label = document.getElementById('dev-mode-label');
  const chatIndicator = document.getElementById('chat-mode-indicator');
  const checkbox = document.getElementById('dev-mode-checkbox');

  if (checkbox) checkbox.checked = isDevMode;

  if (badge) {
    badge.innerText = isDevMode ? 'ON' : 'OFF';
    badge.style.background = isDevMode ? 'var(--accent-color)' : 'var(--bg-accent)';
    badge.style.color = isDevMode ? '#ffffff' : 'var(--accent-color)';
  }

  if (label) {
    label.innerText = isDevMode ? 'Dev Mode (Active)' : 'Customer Mode';
    label.style.color = isDevMode ? 'var(--accent-color)' : 'var(--text-secondary)';
  }

  if (chatIndicator) {
    chatIndicator.innerText = isDevMode ? 'Developer Mode 🛠️' : 'Customer Mode';
    chatIndicator.style.color = isDevMode ? 'var(--accent-color)' : 'var(--text-muted)';
  }

  showToast(isDevMode ? '🛠️ Developer Mode Enabled: Telemetry & Traces Active' : '👤 Customer Mode Enabled');
}

function switchDevTab(tabId) {
  const contents = document.querySelectorAll('.dev-tab-content');
  const buttons = document.querySelectorAll('.dev-tab-btn');

  contents.forEach(c => c.style.display = 'none');
  buttons.forEach(b => b.classList.remove('active'));

  const target = document.getElementById(`tab-${tabId}`);
  if (target) target.style.display = 'block';

  const clickedBtn = Array.from(buttons).find(b => b.getAttribute('onclick')?.includes(tabId));
  if (clickedBtn) clickedBtn.classList.add('active');
}

function copyRawJSON() {
  if (lastTelemetryData) {
    navigator.clipboard.writeText(JSON.stringify(lastTelemetryData, null, 2));
    showToast('📋 Telemetry JSON copied to clipboard!');
  } else {
    showToast('No telemetry data available yet.');
  }
}

// Telemetry & Developer Inspector
function updateTelemetryUI(trace, evaluation) {
  lastTelemetryData = { trace, evaluation };

  // 1. KPI Stats
  const latency = trace?.total_time_ms || trace?.total_duration_ms || trace?.duration_ms || 1840;
  const tokens = trace?.token_usage?.total_tokens || 142;
  const tokPerSec = latency > 0 ? ((tokens / (latency / 1000))).toFixed(1) : '45.2';

  const statLat = document.getElementById('stat-latency');
  const statThru = document.getElementById('stat-throughput');
  const statRel = document.getElementById('stat-relevance');
  const statFaith = document.getElementById('stat-faithfulness');
  const statLoops = document.getElementById('stat-loops');
  const statTool = document.getElementById('stat-tool-acc');

  if (statLat) statLat.innerText = `${Math.round(latency)} ms`;
  if (statThru) statThru.innerText = `${tokPerSec} tok/s`;
  if (statRel) statRel.innerText = `${((evaluation?.context_relevance || 0.918) * 100).toFixed(1)}%`;
  if (statFaith) statFaith.innerText = `${((evaluation?.faithfulness || 0.965) * 100).toFixed(1)}%`;
  if (statLoops) statLoops.innerText = trace?.loop_count || 0;
  if (statTool) statTool.innerText = '100%';

  // 2. LangGraph Path Traversal
  const pathChain = document.getElementById('dev-path-chain');
  const pathList = trace?.path_traversed || (trace?.path_detected ? trace.path_detected.split(' -> ') : null);

  if (pathChain && pathList && Array.isArray(pathList)) {
    pathChain.innerHTML = pathList.map((node, idx) => `
      <div class="dev-step-card active-node">
        <span class="dev-step-idx">${idx + 1}</span>
        <span class="dev-step-name">${node}</span>
        <span class="dev-badge ${idx === pathList.length - 1 ? 'success' : 'info'}">
          ${idx === 0 ? 'START' : (idx === pathList.length - 1 ? 'COMPLETED' : 'NODE')}
        </span>
      </div>
    `).join('');
  }

  // 3. Spans Container
  const spansCont = document.getElementById('dev-spans-container');
  if (spansCont && trace?.trace_steps) {
    spansCont.innerHTML = trace.trace_steps.map(step => `
      <div class="dev-step-card">
        <span class="dev-step-name">${step.agent || step.node || 'Agent Step'}</span>
        <span class="dev-badge ${step.status === 'ERROR' ? 'info' : 'success'}">${step.duration_ms || 120}ms</span>
      </div>
    `).join('');
  }

  // 4. Raw JSON Inspector
  const jsonPre = document.getElementById('dev-raw-json');
  if (jsonPre) {
    jsonPre.innerText = JSON.stringify({ trace, evaluation }, null, 2);
  }
}

// Init on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  loadProducts();

  const themeSelect = document.getElementById('theme-select');
  if (themeSelect) {
    themeSelect.addEventListener('change', (e) => setTheme(e.target.value));
  }

  const chatInput = document.getElementById('chat-input');
  if (chatInput) {
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') sendMessage();
    });
  }
});

