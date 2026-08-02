// ══════════════════════════════════════════════════════════════════
//  CONSTANTS
// ══════════════════════════════════════════════════════════════════
const PROVIDER_MODELS = {
  groq:       ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
  cerebras:   ["llama-3.3-70b", "llama3.1-70b", "llama3.1-8b"],
  mistral:    ["mistral-large-latest", "mistral-small-latest", "codestral-latest"],
  gemini:     ["gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
  openrouter: ["meta-llama/llama-3.3-70b-instruct", "google/gemma-2-9b-it:free", "meta-llama/llama-3-8b-instruct:free"]
};

const PROVIDER_URLS = {
  groq:       "https://api.groq.com/openai/v1/chat/completions",
  cerebras:   "https://api.cerebras.ai/v1/chat/completions",
  mistral:    "https://api.mistral.ai/v1/chat/completions",
  gemini:     "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
  openrouter: "https://openrouter.ai/api/v1/chat/completions"
};

const PROVIDER_PLACEHOLDER = {
  groq:       "gsk_...",
  cerebras:   "csk_...",
  mistral:    "API key...",
  gemini:     "AIza...",
  openrouter: "sk-or-..."
};

const PROVIDER_FALLBACK_ORDER = ["groq", "cerebras", "mistral", "gemini", "openrouter"];

// ══════════════════════════════════════════════════════════════════
//  ALL DOM-DEPENDENT CODE
// ══════════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', async () => {

  // ── DOM Refs ────────────────────────────────────────────────────
  const btnCopy               = document.getElementById('btn-copy');
  const btnText               = document.getElementById('btn-text');
  const spinner               = document.getElementById('spinner');
  const statusEl              = document.getElementById('status');
  const btnOpenSettings       = document.getElementById('btn-open-settings');
  const btnCloseSettings      = document.getElementById('btn-close-settings');
  const overlay               = document.getElementById('settings-overlay');
  const providerTabs          = document.getElementById('provider-tabs');
  const keysContainer         = document.getElementById('keys-container');
  const keysLabel             = document.getElementById('keys-label');
  const btnAddKey             = document.getElementById('btn-add-key');
  const modelSelect           = document.getElementById('model-select');
  const btnSave               = document.getElementById('btn-save');
  const saveNote              = document.getElementById('save-note');
  const toggleFloatingWidget  = document.getElementById('toggle-floating-widget');

  // ── State ────────────────────────────────────────────────────────
  let configData           = { apiKeys: {}, provider: 'groq', model: '' };
  let activeProvider       = 'groq';
  let showFloatingWidget   = true;

  // ── Overlay ──────────────────────────────────────────────────────
  btnOpenSettings.addEventListener('click', () => {
    document.documentElement.classList.add('settings-open');
    overlay.classList.add('open');
    renderSettings();
  });
  btnCloseSettings.addEventListener('click', () => {
    document.documentElement.classList.remove('settings-open');
    overlay.classList.remove('open');
  });

  // ── Status ───────────────────────────────────────────────────────
  function showStatus(msg, type = 'info') {
    statusEl.textContent = msg;
    statusEl.className   = type;
  }

  // ── Config ───────────────────────────────────────────────────────
  async function loadConfig() {
    let apiKeys = {};
    let provider = 'groq';
    let model    = '';

    const stored = await chrome.storage.local.get(['api_keys', 'default_provider', 'selected_model', 'show_floating_widget']);
    
    const hasStoredKeys = stored.api_keys && Object.values(stored.api_keys).some(a => Array.isArray(a) && a.length > 0);

    if (hasStoredKeys) {
      apiKeys  = stored.api_keys;
      provider = stored.default_provider || 'groq';
      model    = stored.selected_model   || '';
    } else {
      try {
        const res = await fetch(chrome.runtime.getURL('config.json'));
        const cfg = await res.json();
        apiKeys  = cfg.api_keys || {};
        provider = cfg.default_provider || 'groq';
        if ((!apiKeys.groq || apiKeys.groq.length === 0) && (cfg.groq_api_keys || cfg.groq_api_key)) {
          apiKeys.groq = cfg.groq_api_keys || (cfg.groq_api_key ? [cfg.groq_api_key] : []);
        }
        await chrome.storage.local.set({ api_keys: apiKeys, default_provider: provider });
      } catch (_) { /* no config.json */ }
    }

    showFloatingWidget = stored.show_floating_widget !== undefined ? stored.show_floating_widget : true;
    toggleFloatingWidget.checked = showFloatingWidget;

    for (const p of Object.keys(PROVIDER_MODELS)) {
      if (!apiKeys[p]) apiKeys[p] = [];
    }
    configData     = { apiKeys, provider, model };
    activeProvider = provider;
  }

  // ── Settings UI ──────────────────────────────────────────────────
  function renderSettings() {
    document.querySelectorAll('.tab').forEach(b => {
      b.classList.toggle('active', b.dataset.p === activeProvider);
    });
    keysLabel.textContent = capitalize(activeProvider) + ' API Keys';
    renderKeyRows();
    renderModels();
  }

  function renderKeyRows() {
    keysContainer.innerHTML = '';
    const keys = configData.apiKeys[activeProvider] || [];
    const list = keys.length ? keys : [''];
    list.forEach((v, i) => addKeyRow(v, i === 0 && list.length === 1));
  }

  function addKeyRow(value = '', noDelete = false) {
    const row = document.createElement('div');
    row.className = 'key-row';

    const inp = document.createElement('input');
    inp.type        = 'password';
    inp.className   = 'key-input';
    inp.placeholder = PROVIDER_PLACEHOLDER[activeProvider] || 'API key...';
    inp.value       = value;

    const eye = document.createElement('button');
    eye.className = 'row-btn';
    eye.title     = 'Show/Hide';
    eye.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
    eye.addEventListener('click', () => { inp.type = inp.type === 'password' ? 'text' : 'password'; });

    const del = document.createElement('button');
    del.className = 'row-btn del';
    del.title     = 'Remove';
    del.innerHTML = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`;
    if (noDelete) del.style.opacity = '0.3';
    del.addEventListener('click', () => { if (keysContainer.children.length > 1) row.remove(); });

    row.append(inp, eye, del);
    keysContainer.appendChild(row);
  }

  function renderModels() {
    const models = PROVIDER_MODELS[activeProvider] || [];
    modelSelect.innerHTML = '';
    models.forEach(m => {
      const opt       = document.createElement('option');
      opt.value       = m;
      opt.textContent = m;
      opt.selected    = m === configData.model;
      modelSelect.appendChild(opt);
    });
  }

  // Provider tab clicks inside settings
  providerTabs.addEventListener('click', e => {
    const btn = e.target.closest('.tab');
    if (!btn) return;

    // Save inputs before tab switch
    const inputs = keysContainer.querySelectorAll('.key-input');
    const keys = Array.from(inputs).map(i => i.value.trim()).filter(k => k.length > 5);
    configData.apiKeys[activeProvider] = keys;

    activeProvider = btn.dataset.p;
    renderSettings();
  });

  // Add key row
  btnAddKey.addEventListener('click', () => addKeyRow(''));

  // Save Settings
  btnSave.addEventListener('click', async () => {
    const inputs = keysContainer.querySelectorAll('.key-input');
    const keys   = Array.from(inputs).map(i => i.value.trim()).filter(k => k.length > 5);
    configData.apiKeys[activeProvider] = keys;
    configData.provider = activeProvider;
    configData.model    = modelSelect.value;
    showFloatingWidget  = toggleFloatingWidget.checked;

    await chrome.storage.local.set({
      api_keys:             configData.apiKeys,
      default_provider:     configData.provider,
      selected_model:       configData.model,
      show_floating_widget: showFloatingWidget
    });

    saveNote.textContent = '✅ Saved!';
    setTimeout(() => { saveNote.textContent = ''; }, 2000);
  });

  // ── Copy button ──────────────────────────────────────────────────
  btnCopy.addEventListener('click', performHandover);

  async function performHandover() {
    const hasAnyKey = Object.values(configData.apiKeys).some(a => Array.isArray(a) && a.length > 0);
    if (!hasAnyKey) {
      await loadConfig();
      const retryHasKey = Object.values(configData.apiKeys).some(a => Array.isArray(a) && a.length > 0);
      if (!retryHasKey) {
        showStatus('No API keys found — click ⚙️ to add', 'error');
        return;
      }
    }

    try {
      btnCopy.classList.add('loading');
      btnText.textContent   = 'Extracting...';
      spinner.style.display = 'block';
      showStatus('Extracting chat payload...', 'info');

      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab || !tab.url.includes('claude.ai')) throw new Error('Not on a Claude.ai tab!');

      const [{ result: payload }] = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: extractFullClaudeConversation
      });
      if (!payload || (!payload.bottomText && !payload.topText)) throw new Error('Chat is empty or short');

      btnText.textContent = 'Summarising...';
      showStatus('Summarising 2-stage parallel...', 'info');

      const response = await new Promise((resolve) => {
        chrome.runtime.sendMessage({ action: "SUMMARIZE", payload: payload }, resolve);
      });

      if (!response) {
        throw new Error("Extension background script not reachable.");
      }
      if (!response.success) {
        throw new Error(response.error || "Summarization failed");
      }

      await navigator.clipboard.writeText(response.data);
      showStatus('Handover copied! ✅', 'success');

    } catch (err) {
      showStatus(err.message, 'error');
    } finally {
      btnCopy.classList.remove('loading');
      spinner.style.display = 'none';
      btnText.textContent   = 'Copy Handover Context';
    }
  }

  // Sync floating widget switch if changed elsewhere
  chrome.storage.onChanged.addListener((changes) => {
    if (changes.show_floating_widget) {
      toggleFloatingWidget.checked = changes.show_floating_widget.newValue;
    }
  });

  // ── Init ──────────────────────────────────────────────────────────
  await loadConfig();

  // Check keys after load
  const hasAnyKey = Object.values(configData.apiKeys).some(arr => Array.isArray(arr) && arr.length > 0);
  if (!hasAnyKey) {
    showStatus('⚠️ No API key — click ⚙️ to add one', 'error');
    btnOpenSettings.style.boxShadow   = '0 0 0 3px rgba(239,68,68,.5)';
    btnOpenSettings.style.borderColor = 'rgba(239,68,68,.6)';
  } else {
    showStatus('Ready to extract context', 'info');
  }

}); // end DOMContentLoaded


// ══════════════════════════════════════════════════════════════════
//  PURE FUNCTIONS — 100% Bulletproof API + DOM Extractor
// ══════════════════════════════════════════════════════════════════

async function extractFullClaudeConversation() {
  var topText = "";
  var bottomText = "";

  // 1. Try Backend API Extraction
  try {
    var match = window.location.pathname.match(/\/chat\/([a-f0-9\-]+)/i);
    if (match && match[1]) {
      var chatId = match[1];
      var baseUrl = window.location.origin;
      var orgsRes = await fetch(baseUrl + '/api/organizations');
      if (orgsRes.ok) {
        var orgs = await orgsRes.json();
        if (orgs && orgs.length > 0) {
          var orgId = orgs[0].uuid;
          var chatRes = await fetch(baseUrl + '/api/organizations/' + orgId + '/chat_conversations/' + chatId + '?tree=true');
          if (chatRes.ok) {
            var chatData = await chatRes.json();
            var messages = chatData.chat_messages || [];
            if (messages.length > 0) {
              var formattedTurns = messages.map(function(m) {
                var role = m.sender === 'human' ? '👤 USER' : '🤖 ASSISTANT';
                var text = m.text || '';
                if (!text && m.content && Array.isArray(m.content)) {
                  text = m.content.map(function(c) { return c.text || ''; }).join('\n');
                }
                if (!text || text.trim().length < 2) return null;
                return '### ' + role + ':\n' + text.trim();
              }).filter(Boolean);

              if (formattedTurns.length > 0) {
                var halfIndex = Math.ceil(formattedTurns.length / 2);
                topText    = formattedTurns.slice(0, halfIndex).join('\n\n---\n\n');
                bottomText = formattedTurns.slice(halfIndex).join('\n\n---\n\n');
              }
            }
          }
        }
      }
    }
  } catch (e) {
    console.warn("API extraction fallback to DOM:", e);
  }

  // 2. DOM Fallback
  if (!topText || !bottomText) {
    var domPayload = extractDualPayloadDOM();
    if (!topText) topText = domPayload.topText;
    if (!bottomText) bottomText = domPayload.bottomText;
  }

  // 3. Absolute Fallback: Grab entire main body text if empty
  if (!topText && !bottomText) {
    var mainContainer = document.querySelector('main') || document.querySelector('article') || document.body;
    bottomText = (mainContainer.innerText || mainContainer.textContent || '').trim();
  }

  // Scrape Intercepted Console Logs & DOM Code Blocks/Probe Outputs
  var probeContent = "";
  try {
    var logs = window.__councilLogs || [];
    var probeEls = document.querySelectorAll(
      'pre, code, [class*="console"], [class*="terminal"], [class*="output"], [data-testid*="artifact"], [class*="artifact"]'
    );
    var probes = [];
    probeEls.forEach(function(p) {
      var t = (p.innerText || p.textContent || '').trim();
      if (t.length > 10 && !probes.includes(t)) {
        probes.push(t.substring(0, 4000));
      }
    });

    if (logs.length > 0 || probes.length > 0) {
      probeContent = "\n\n=== 💻 INTERCEPTED CONSOLE LOGS & CONFIRMED DOM PROBES ===\n" +
        (logs.length > 0 ? "--- CONSOLE LOGS ---\n" + logs.slice(-30).join('\n') + "\n\n" : "") +
        (probes.length > 0 ? "--- DOM PROBES & CODE BLOCKS ---\n" + probes.join('\n\n---\n\n') : "");
    }
  } catch (_) {}

  bottomText += probeContent;

  return { topText: topText, bottomText: bottomText };
}

function extractDualPayloadDOM() {
  try {
    var selectors = [
      '[data-message-author]',
      '[data-testid="user-message"]',
      '[data-testid="assistant-message"]',
      '.font-user-message',
      '.font-claude-message',
      '[class*="HumanTurn"]',
      '[class*="AssistantMessage"]',
      '[class*="user-message"]',
      '[class*="assistant-message"]',
      '[class*="group/turn"]',
      'div[class*="group"]',
      'div[class*="prose"]'
    ];

    var rawMatched = Array.from(document.querySelectorAll(selectors.join(',')));

    if (rawMatched.length === 0) {
      var mainEl = document.querySelector('main') || document.querySelector('article') || document.body;
      rawMatched = Array.from(mainEl.querySelectorAll('div, p'));
    }

    var turns = rawMatched.filter(function(el) {
      if (!el.innerText || el.innerText.trim().length === 0) return false;
      return !rawMatched.some(function(other) {
        return other !== el && other.contains(el);
      });
    });

    turns.sort(function(a, b) {
      if (a === b) return 0;
      return (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING) ? -1 : 1;
    });

    function formatTurn(el) {
      var text = (el.innerText || el.textContent || '').trim();
      if (!text || text.length < 5) return null;

      if (text.includes("🎭 Claude Session Handover") || 
          text.includes("Diagnostic Root Cause: The root cause is the CSP") || 
          text.includes("script-src violations in the background.js file") ||
          text.includes("ai-council")) {
        return null;
      }

      var author = (el.getAttribute('data-message-author') || '').toLowerCase();
      var tid  = (el.getAttribute('data-testid') || '').toLowerCase();
      var cls  = (el.className || '').toString().toLowerCase();
      var html = (el.outerHTML || '').toLowerCase();
      var pCls = (el.parentElement ? el.parentElement.className || '' : '').toString().toLowerCase();

      var isUser = author === 'user' || tid.includes('user') || cls.includes('user') || cls.includes('human') || 
                  pCls.includes('user') || pCls.includes('human') || html.includes('user-message');
      
      var role = isUser ? '👤 USER' : '🤖 ASSISTANT';
      return '### ' + role + ':\n' + text;
    }

    var half = Math.ceil(turns.length / 2);
    var topNodes    = turns.slice(0, half);
    var bottomNodes = turns.slice(half);

    var topText    = topNodes.map(formatTurn).filter(Boolean).join('\n\n---\n\n');
    var bottomText = bottomNodes.map(formatTurn).filter(Boolean).join('\n\n---\n\n');

    return { topText: topText, bottomText: bottomText };
  } catch (e) {
    var m = document.querySelector('main') || document.body;
    return { topText: '', bottomText: (m.innerText || '').trim() };
  }
}

function capitalize(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : s; }
