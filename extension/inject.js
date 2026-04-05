(async () => {
  if (window.__cavemanDone) return;
  window.__cavemanDone = true;

  const PROMPT =
    "From now on, act as a token-optimized strict assistant.\n\n" +
    "Use 'Caveman' style communication: No filler words, no greetings, " +
    "no apologies, no lengthy explanations. Use short keywords.\n" +
    "For code/document edits: Never output the entire file. Output ONLY " +
    "the modified lines or exact blocks to replace.\n" +
    "Context Navigation: Implement a graph-based tree search method for " +
    "large files. First, map the provided context into a concise, " +
    "hierarchical bulleted tree structure. Stop and ask me which specific " +
    "node to expand. Use this to navigate directly to the exact location " +
    "without re-scanning or outputting the entire file.\n" +
    "Acknowledge with 'Optimized Mode Active'.";

  const sl = ms => new Promise(r => setTimeout(r, ms));

  const EDITOR_SELS = [
    'div[contenteditable="true"].ProseMirror',
    'div[contenteditable="true"][data-placeholder]',
    'fieldset div[contenteditable="true"]',
    'div[contenteditable="true"]',
  ];

  const SEND_SELS = [
    'button[aria-label="Send message"]',
    'button[aria-label="Send Message"]',
    'button[data-testid="send-button"]',
  ];

  // ── 1. Wait for editor (React takes time to hydrate) ──────────
  let box = null;
  for (let i = 0; i < 40 && !box; i++) {
    for (const s of EDITOR_SELS) {
      box = document.querySelector(s);
      if (box) break;
    }
    if (!box) await sl(500);
  }
  if (!box) return; // editor never appeared

  // ── 2. Only inject on empty editor (fresh page) ───────────────
  if ((box.textContent || "").trim().length > 0) return;

  box.focus();
  await sl(200);

  // ── 3a. Try ClipboardEvent paste (React-friendly) ─────────────
  let inserted = false;
  try {
    const dt = new DataTransfer();
    dt.setData("text/plain", PROMPT);
    box.dispatchEvent(
      new ClipboardEvent("paste", { clipboardData: dt, bubbles: true, cancelable: true })
    );
    await sl(600);
    if ((box.textContent || "").trim().length > 10) inserted = true;
  } catch (_) {}

  // ── 3b. Fallback: execCommand ─────────────────────────────────
  if (!inserted) {
    box.focus();
    document.execCommand("selectAll", false, null);
    await sl(30);
    document.execCommand("insertText", false, PROMPT);
    await sl(600);
    inserted = (box.textContent || "").trim().length > 10;
  }

  if (!inserted) return;

  // ── 4. Click Send ─────────────────────────────────────────────
  await sl(800);
  for (let t = 0; t < 20; t++) {
    for (const s of SEND_SELS) {
      const btn = document.querySelector(s);
      if (btn && !btn.disabled) {
        btn.click();
        return;
      }
    }
    await sl(300);
  }
})();