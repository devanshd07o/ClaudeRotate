// background.js — Direct 2-Stage Parallel Dual-API Pipeline (Fast 7s Timeout Engine)

const PROVIDER_MODELS = {
  groq:       ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
  cerebras:   ["llama-3.3-70b", "llama3.1-8b"],
  mistral:    ["mistral-large-latest", "mistral-small-latest"],
  gemini:     ["gemini-2.5-flash", "gemini-1.5-flash"],
  openrouter: ["meta-llama/llama-3.3-70b-instruct", "google/gemma-2-9b-it:free"]
};

const PROVIDER_URLS = {
  groq:       "https://api.groq.com/openai/v1/chat/completions",
  cerebras:   "https://api.cerebras.ai/v1/chat/completions",
  mistral:    "https://api.mistral.ai/v1/chat/completions",
  gemini:     "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
  openrouter: "https://openrouter.ai/api/v1/chat/completions"
};

const PROVIDER_FALLBACK_ORDER = ["groq", "cerebras", "mistral", "gemini", "openrouter"];

const TOP_HALF_PROMPT =
  "You are an Expert AI Handover Specialist analyzing PART 1 (THE TOP EARLY PORTION) of a chat transcript.\n" +
  "EXTRACT STRICT ACTIONABLE FACTS FROM THIS EARLY PORTION:\n" +
  "1. What files were being worked on\n" +
  "2. What was fixed (with exact selectors, function names, and code snippets if mentioned)\n" +
  "3. Confirmed facts, DOM class names, console outputs, or API responses\n\n" +
  "STRICT RULES:\n" +
  "- DO NOT generate questions or 'History Questions' or 'Early Discussion Turns' sections.\n" +
  "- DO NOT write 'not mentioned' or 'N/A' placeholders (SKIP completely if missing).\n" +
  "- Scan for CSS selectors (div., button[, class*=, #id), working flags (✅, FOUND, WORKING), and class names in quotes.\n" +
  "- ONLY actionable facts\n" +
  "- Quote exact code snippets, DOM selectors, and console outputs if present in text.";

const BOTTOM_HALF_PROMPT =
  "You are an Expert AI Handover Specialist analyzing PART 2 (THE BOTTOM LATEST PORTION) of a chat transcript.\n" +
  "EXTRACT STRICT ACTIONABLE GROUND TRUTH FROM THIS LATEST PORTION:\n" +
  "1. What files are currently being worked on\n" +
  "2. What was fixed (with exact selectors, function names, and code snippets)\n" +
  "3. What is STILL BROKEN or UNKNOWN (exact technical diagnostic root cause)\n" +
  "4. Confirmed technical facts & CSS selectors\n" +
  "5. The SINGLE next action needed\n\n" +
  "STRICT RULES:\n" +
  "- DO NOT generate questions.\n" +
  "- DO NOT write 'not mentioned' or 'N/A' placeholders (SKIP completely if missing).\n" +
  "- Scan for CSS selectors (div., button[, class*=, #id), working flags (✅, FOUND, WORKING), and class names in quotes.\n" +
  "- ONLY actionable facts\n" +
  "- Quote exact code snippets, DOM selectors, and console outputs if present in text.";

// Seeding config.json to chrome.storage.local on install/startup
async function seedConfig() {
  try {
    const stored = await chrome.storage.local.get(["config_seeded", "api_keys"]);
    const hasAnyKey = stored.api_keys && Object.values(stored.api_keys).some(arr => Array.isArray(arr) && arr.length > 0);
    
    if (!stored.config_seeded && !hasAnyKey) {
      const res = await fetch(chrome.runtime.getURL("config.json"));
      const cfg = await res.json();
      
      let apiKeys = cfg.api_keys || {};
      if ((!apiKeys.groq || apiKeys.groq.length === 0) && (cfg.groq_api_keys || cfg.groq_api_key)) {
        apiKeys.groq = cfg.groq_api_keys || (cfg.groq_api_key ? [cfg.groq_api_key] : []);
      }
      
      await chrome.storage.local.set({
        api_keys: apiKeys,
        default_provider: cfg.default_provider || "groq",
        config_seeded: true
      });
      console.log("Seeded config.json into chrome.storage.local");
    } else if (!stored.config_seeded && hasAnyKey) {
      await chrome.storage.local.set({ config_seeded: true });
    }
  } catch (e) {
    console.error("Failed to seed config:", e);
  }
}

chrome.runtime.onInstalled.addListener(seedConfig);
chrome.runtime.onStartup.addListener(seedConfig);
seedConfig();

async function getStoredConfig() {
  await seedConfig();
  const stored = await chrome.storage.local.get(["api_keys", "default_provider", "selected_model"]);
  return {
    apiKeys: stored.api_keys || {},
    provider: stored.default_provider || "groq",
    model: stored.selected_model || ""
  };
}

async function queryAPIWithKey(systemPrompt, userText, apiKey, provider, preferredModel) {
  const models = PROVIDER_MODELS[provider] || [];
  const url    = PROVIDER_URLS[provider];
  const hdrs   = { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + apiKey };
  if (provider === 'openrouter') {
    hdrs['HTTP-Referer'] = 'http://localhost:5757';
    hdrs['X-Title']      = 'Claude Switcher';
  }

  const orderedModels = preferredModel && models.includes(preferredModel)
    ? [preferredModel, ...models.filter(m => m !== preferredModel)]
    : models;

  // FAST ATTEMPT: 7-second max timeout per call
  for (const model of orderedModels) {
    try {
      const ctrl  = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 7000);
      const res   = await fetch(url, {
        method:  'POST',
        headers: hdrs,
        signal:  ctrl.signal,
        body:    JSON.stringify({
          model,
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: userText.substring(0, 12000) }
          ],
          temperature: 0.1,
          frequency_penalty: 0.5,
          presence_penalty: 0.3
        })
      });
      clearTimeout(timer);
      if (res.ok) {
        const d = await res.json();
        const content = d && d.choices && d.choices[0] && d.choices[0].message && d.choices[0].message.content;
        if (content) return content.trim();
      }
    } catch (e) { console.warn(e.message); }
  }
  throw new Error('API key call failed');
}

async function runStageWithFallback(systemPrompt, text, apiKeys, provider, preferredModel, keyIndexOffset = 0) {
  const providers = [provider, ...PROVIDER_FALLBACK_ORDER.filter(p => p !== provider)];

  for (const p of providers) {
    const pKeys = apiKeys[p] || [];
    if (!pKeys.length) continue;

    const startIndex = keyIndexOffset % pKeys.length;
    const orderedKeys = [...pKeys.slice(startIndex), ...pKeys.slice(0, startIndex)];

    for (const key of orderedKeys) {
      try {
        const res = await queryAPIWithKey(systemPrompt, text, key, p, preferredModel);
        if (res) return res;
      } catch (_) {}
    }
  }
  throw new Error("All API providers/keys failed for stage");
}

async function handleSummarize(payload) {
  const config = await getStoredConfig();
  const apiKeys = config.apiKeys;
  const primaryProvider = config.provider;
  const preferredModel = config.model;

  let topText = "";
  let bottomText = "";

  if (typeof payload === 'object' && (payload.topText || payload.bottomText)) {
    topText    = payload.topText || '';
    bottomText = payload.bottomText || '';
  } else {
    const raw = typeof payload === 'string' ? payload : (payload.text || '');
    const half = Math.floor(raw.length / 2);
    topText    = raw.substring(0, half);
    bottomText = raw.substring(half);
  }

  topText = topText.replace(/### 🎭 Claude Session Handover[\s\S]*?(\n\n|$)/g, '');
  bottomText = bottomText.replace(/### 🎭 Claude Session Handover[\s\S]*?(\n\n|$)/g, '');

  if (!topText && !bottomText) {
    throw new Error("Chat text is empty or too short");
  }

  // FAST PARALLEL CALLS: Max 7s per call, 12k chars per payload
  const [topSummary, bottomSummary] = await Promise.all([
    runStageWithFallback(TOP_HALF_PROMPT, topText || bottomText, apiKeys, primaryProvider, preferredModel, 0),
    runStageWithFallback(BOTTOM_HALF_PROMPT, bottomText || topText, apiKeys, primaryProvider, preferredModel, 1)
  ]);

  const masterHandover =
    "***\n" +
    "# 🎭 Claude Session Handover & Actionable Ground Truth\n\n" +
    "**Context**: The previous session hit a limit. We are migrating directly to this new session. Resume immediately.\n\n" +
    "## 📍 PART 1: EARLY CONTEXT & INITIAL FIXES\n" +
    topSummary + "\n\n" +
    "## 🚨 PART 2: LATEST ACTIVE GROUND TRUTH & PENDING BUGS\n" +
    bottomSummary + "\n\n" +
    "## 🚀 Next Session Instructions\n\n" +
    "1. **Read** all confirmed facts, selectors, and ground truth above carefully.\n\n" +
    "2. **Tell the user** your understanding in this exact format:\n" +
    "   > \"Resuming AI Council session. Here's what I understand:\n" +
    "   > ✅ Working: [list]\n" +
    "   > ❌ Broken/Unknown: [list]\n" +
    "   > 🎯 Next objective: [single line]\"\n\n" +
    "3. **Ask for what you need** before proceeding:\n" +
    "   - If any files are needed to continue → ask:\n" +
    "     *\"Please upload [filename] so I can resume work on it.\"*\n" +
    "   - If any probe output is missing → ask:\n" +
    "     *\"Please run [probe name] on [platform] and paste the output here.\"*\n" +
    "   - If anything in the handover is unclear → ask:\n" +
    "     *\"Can you clarify [specific thing]?\"*\n\n" +
    "4. **Wait for user confirmation** — do NOT start writing code until user says\n" +
    "   \"yes proceed\" or \"haan chalo\" or uploads the required files.\n\n" +
    "5. Only after confirmation → proceed with the fix.\n" +
    "***";

  return masterHandover;
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "SUMMARIZE") {
    handleSummarize(request.payload || request.text)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }
});
