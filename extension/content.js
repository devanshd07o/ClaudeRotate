/* ═══════════════════════════════════════════════════════════════
   content.js  —  Injected into claude.ai pages
   Provides a direct 1-click floating FAB button in bottom-right corner.
   Guaranteed 100% non-empty extraction via API + DOM fallback.
   ═══════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  // 1. REAL-TIME CONSOLE LOG INTERCEPTOR
  window.__councilLogs = window.__councilLogs || [];
  try {
    const origLog = console.log;
    const origWarn = console.warn;
    const origErr = console.error;

    console.log = function (...args) {
      try {
        const msg = args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ');
        if (msg.length > 5 && !msg.includes('extension') && window.__councilLogs.length < 100) {
          window.__councilLogs.push('[LOG] ' + msg);
        }
      } catch (_) {}
      origLog.apply(console, args);
    };

    console.warn = function (...args) {
      try {
        const msg = args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ');
        if (msg.length > 5 && window.__councilLogs.length < 100) {
          window.__councilLogs.push('[WARN] ' + msg);
        }
      } catch (_) {}
      origWarn.apply(console, args);
    };

    console.error = function (...args) {
      try {
        const msg = args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ');
        if (msg.length > 5 && window.__councilLogs.length < 100) {
          window.__councilLogs.push('[ERR] ' + msg);
        }
      } catch (_) {}
      origErr.apply(console, args);
    };
  } catch (_) {}

  if (document.getElementById('csh-fab')) return;

  // Safe Storage Helper
  function safeGetStorage(keys) {
    return new Promise((resolve) => {
      try {
        if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.id && chrome.storage && chrome.storage.local) {
          chrome.storage.local.get(keys, (res) => {
            if (chrome.runtime.lastError) resolve({});
            else resolve(res || {});
          });
        } else {
          resolve({});
        }
      } catch (e) {
        resolve({});
      }
    });
  }

  // Safe Send Message Helper
  function safeSendMessage(msg) {
    return new Promise((resolve, reject) => {
      try {
        if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.id) {
          chrome.runtime.sendMessage(msg, (response) => {
            if (chrome.runtime.lastError) {
              reject(new Error("Extension reloaded — please refresh tab"));
            } else if (!response) {
              reject(new Error("Service worker disconnected — refresh tab"));
            } else {
              resolve(response);
            }
          });
        } else {
          reject(new Error("Extension reloaded — please refresh tab"));
        }
      } catch (e) {
        reject(new Error("Extension reloaded — please refresh tab"));
      }
    });
  }

  // Render Direct 1-Click Floating FAB Widget
  const fab = document.createElement('button');
  fab.id = 'csh-fab';
  fab.title = 'Copy Handover Context (1-Click)';
  fab.style.display = 'none';
  fab.innerHTML = `
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <rect x="9" y="9" width="13" height="13" rx="2"/>
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
    </svg>
    <span id="csh-fab-text">Copy Handover</span>
    <span id="csh-toast"></span>
  `;
  document.body.appendChild(fab);

  const toastEl = document.getElementById('csh-toast');

  function showToast(msg, type = "success") {
    toastEl.textContent = msg;
    toastEl.className = `csh-toast-show ${type}`;
    setTimeout(() => {
      toastEl.className = "";
      toastEl.textContent = "";
    }, 4500);
  }

  async function loadState() {
    const stored = await safeGetStorage(["show_floating_widget"]);
    const isVisible = stored.show_floating_widget !== undefined ? stored.show_floating_widget : true;
    fab.style.display = isVisible ? 'flex' : 'none';
  }

  loadState();

  // Storage change listener
  try {
    if (typeof chrome !== 'undefined' && chrome?.storage?.onChanged) {
      chrome.storage.onChanged.addListener((changes) => {
        if (changes && changes.show_floating_widget) {
          fab.style.display = changes.show_floating_widget.newValue ? 'flex' : 'none';
        }
      });
    }
  } catch (_) {}

  // 100% Bulletproof API + DOM Extractor
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

  // 1-Click Floating FAB Click Event
  fab.addEventListener('click', async (e) => {
    e.stopPropagation();
    fab.classList.add('loading');

    try {
      const payload = await extractFullClaudeConversation();
      if (!payload || (!payload.bottomText && !payload.topText)) throw new Error("Chat is empty");

      const response = await safeSendMessage({ action: "SUMMARIZE", payload: payload });
      if (response && response.success) {
        await navigator.clipboard.writeText(response.data);
        showToast('Copied! ✅', 'success');
      } else {
        throw new Error(response ? response.error : "Summarization failed");
      }
    } catch (err) {
      showToast(err.message || "Failed to copy", "error");
    } finally {
      fab.classList.remove('loading');
    }
  });

})();
