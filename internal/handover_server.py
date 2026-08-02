"""
Claude Context Extractor Server
================================
Runs silently in background on http://localhost:5757
User triggers it via a Chrome Bookmarklet saved in their browser.

Flow:
  1. User is on Claude tab, limit hit (or wants to switch)
  2. User clicks the "Claude Snapshot" bookmark in Chrome
  3. Bookmarklet extracts DOM text and POSTs to this server
  4. Server calls Groq, summarizes, copies to Windows clipboard
  5. User switches account, Ctrl+V pastes the handover prompt
"""

import json
import os
import sys
import time
import threading
import ctypes
import winreg
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    import pyperclip
except ImportError:
    pyperclip = None

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts_config.json")
LOG_FILE      = os.path.join(BASE_DIR, "server_log.txt")
SUMMARY_FILE  = os.path.join(BASE_DIR, "last_summary.txt")

SERVER_HOST   = "127.0.0.1"
SERVER_PORT   = 5757

GROQ_MODELS   = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
CHUNK_SIZE    = 14000
GROQ_TIMEOUT  = 30


# ── Logging ───────────────────────────────────────────────────────────────────
def log(msg):
    ts = time.strftime("%H:%M:%S")
    line = f"{ts} {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ── Windows Notification ──────────────────────────────────────────────────────
def notify(title, message):
    """Show Windows balloon notification via PowerShell (no dependencies needed)."""
    try:
        ps_cmd = (
            f'Add-Type -AssemblyName System.Windows.Forms;'
            f'$n = New-Object System.Windows.Forms.NotifyIcon;'
            f'$n.Icon = [System.Drawing.SystemIcons]::Information;'
            f'$n.Visible = $true;'
            f'$n.ShowBalloonTip(4000, "{title}", "{message}", [System.Windows.Forms.ToolTipIcon]::Info);'
            f'Start-Sleep -Seconds 5;'
            f'$n.Dispose()'
        )
        import subprocess
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-Command", ps_cmd],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    except Exception:
        pass  # Notification is optional, never crash


# ── Load Groq Keys ────────────────────────────────────────────────────────────
# ── Load Config & API Keys ────────────────────────────────────────────────────
def load_config():
    try:
        if not os.path.exists(ACCOUNTS_FILE):
            return {}, "groq"
        with open(ACCOUNTS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        
        # New dictionary structure
        api_keys = data.get("api_keys", {})
        if not api_keys:
            # Fallback to old format
            groq_keys = data.get("groq_api_keys") or []
            if isinstance(groq_keys, str):
                groq_keys = [groq_keys]
            api_keys = {"groq": groq_keys}
            
        provider = data.get("default_provider", "groq")
        return api_keys, provider
    except Exception as e:
        log(f"[CONFIG] Could not load config: {e}")
    return {}, "groq"


# ── AI Provider Models & Fallback Hierarchy ──────────────────────────────────
PROVIDER_MODELS = {
    "groq": ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
    "cerebras": ["llama-3.3-70b", "llama3.1-70b", "llama3.1-8b"],
    "mistral": ["mistral-large-latest", "mistral-small-latest", "codestral-latest"],
    "gemini": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.5-flash"],
    "openrouter": ["meta-llama/llama-3.3-70b-instruct", "google/gemma-2-9b-it:free", "meta-llama/llama-3-8b-instruct:free"]
}


# ── Generic Chat completions Client (Urllib / No Dependencies) ───────────────
def call_chat_api(prompt, provider, keys, key_idx=0, failed_keys=None):
    if not keys:
        return None
    
    # Filter out known failed keys
    if failed_keys:
        active_keys = [k for k in keys if k not in failed_keys]
    else:
        active_keys = keys
        
    if not active_keys:
        return None

    # Handle rotation index safely
    actual_idx = key_idx % len(active_keys)
    ordered = active_keys[actual_idx:] + active_keys[:actual_idx]
    
    url = ""
    headers = {
        "Content-Type": "application/json"
    }
    
    if provider == "groq":
        url = "https://api.groq.com/openai/v1/chat/completions"
    elif provider == "cerebras":
        url = "https://api.cerebras.ai/v1/chat/completions"
    elif provider == "mistral":
        url = "https://api.mistral.ai/v1/chat/completions"
    elif provider == "gemini":
        url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    elif provider == "openrouter":
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers["HTTP-Referer"] = "http://localhost:5757"
        headers["X-Title"] = "Claude Switcher"
    else:
        log(f"[API] Unknown provider: {provider}")
        return None
        
    models = PROVIDER_MODELS.get(provider, [])
    if not models:
        log(f"[API] No models defined for provider: {provider}")
        return None
        
    import urllib.request
    import urllib.error
    
    # Try models in order (fallback hierarchy)
    for model in models:
        for key in ordered:
            # Check if key was added to failed_keys by another thread while looping
            if failed_keys and key in failed_keys:
                continue
                
            headers["Authorization"] = f"Bearer {key}"
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
            
            req = urllib.request.Request(
                url, 
                data=json.dumps(data).encode("utf-8"), 
                headers=headers,
                method="POST"
            )
            
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    txt = res_data["choices"][0]["message"]["content"].strip()
                    if txt:
                        log(f"[API] {provider} OK model={model} key=...{key[-4:]}")
                        return txt
            except urllib.error.HTTPError as he:
                if he.code in (401, 403):
                    log(f"[API] Auth error {he.code} with key ...{key[-4:]} on {provider}")
                    if failed_keys is not None:
                        failed_keys.add(key)
                    continue
                try:
                    body = he.read().decode("utf-8")
                except Exception:
                    body = ""
                log(f"[API] HTTP {he.code} on {provider} (model={model}): {body}")
            except Exception as e:
                log(f"[API] Error with key ...{key[-4:]} on {provider} (model={model}): {e}")
                
    return None


def summarize(text, api_keys, provider):
    """Summarize using parallel Map-Reduce dynamically scaled to K-1 parts for K keys (where K >= 3)."""
    keys = api_keys.get(provider, [])
    if not keys:
        log(f"[SUMMARIZE] No keys found for provider: {provider}")
        return None

    # Split chat log by block separator
    blocks = [b.strip() for b in text.split("\n\n---\n\n") if b.strip()]
    K = len(keys)
    
    # Thread-safe shared set for tracking invalid/rate-limited keys during this run
    shared_failed_keys = set()
    
    if K >= 3 and len(blocks) >= K:
        try:
            k_parts = K - 1
            log(f"[SUMMARIZE] Using parallel dynamic {k_parts}-part Map-Reduce with {K} keys.")
            
            chunk_size = len(blocks) // k_parts
            chunks = []
            for i in range(k_parts):
                if i == k_parts - 1:
                    chunks.append("\n\n---\n\n".join(blocks[i*chunk_size:]))
                else:
                    chunks.append("\n\n---\n\n".join(blocks[i*chunk_size : (i+1)*chunk_size]))
            
            recent_text = "\n\n---\n\n".join(blocks[-4:])

            prompts = []
            for i, chunk in enumerate(chunks):
                prompt = (
                    f"You are Key {i+1} in a parallel map-reduce summarization pipeline for a Claude developer session.\n"
                    f"Analyze Part {i+1} of {k_parts} of the chat history below and extract a HIGH-FIDELITY SUMMARY of the technical state. You MUST capture:\n"
                    "1. EXACT DECISIONS & ANSWERS: Capture the specific answers, preferences, and rules given by the user. Do not write generic summaries like 'user is about to respond'; write down the exact answers and decisions they already provided.\n"
                    "2. CORE ARCHITECTURE & CONFIGURATIONS: Detail any structural systems discussed (e.g., project components, system configurations, layout designs, operational modes, or database schemas).\n"
                    "3. SPECIFIC FILE EDITS: List files modified, created, or deleted, including exact functions, logic changes, and lines altered.\n"
                    "4. ERROR PATTERNS & EDGE CASES: Identify recurring bugs, repeat questions, and specific edge-cases that arose, along with how they were solved or why they are pending.\n\n"
                    "Provide a highly detailed, concise technical summary. No fluff, no generic statements.\n\n"
                    f"PART {i+1} CHAT LOG:\n{chunk}"
                )
                prompts.append(prompt)

            # Threaded parallel execution for all K-1 part summaries
            results = [None] * k_parts
            threads = []

            def runner(idx):
                results[idx] = call_chat_api(prompts[idx], provider, keys, idx, shared_failed_keys)

            for i in range(k_parts):
                t = threading.Thread(target=runner, args=(i,))
                threads.append(t)
                t.start()

            for t in threads:
                t.join(timeout=35)

            # Ensure all parts succeeded
            if all(r is not None for r in results):
                parts_summary = ""
                for i, r in enumerate(results):
                    parts_summary += f"--- PART {i+1} SUMMARY ---\n{r}\n\n"

                assembly_prompt = (
                    "You are the final Key (Synthesizer) in a parallel map-reduce pipeline for a Claude session handover.\n"
                    "Compile the final handover prompt that will be pasted directly into a new Claude chat.\n"
                    "The new Claude must understand exactly what has happened and immediately continue the work from where it stopped.\n\n"
                    "Combine the following details into a highly detailed, token-optimized, high-fidelity developer prompt:\n\n"
                    f"{parts_summary}"
                    f"--- RAW CONTEXT (LAST FEW CHAT TURNS) ---\n{recent_text}\n\n"
                    "Your output MUST be structured EXACTLY as follows (do not add any conversational intro/outro text, output only this ready-to-paste markdown content):\n\n"
                    "***\n"
                    "# 🎭 Claude Session Handover & State Resume\n\n"
                    "**Context**: We are pair programming on a project. My previous session hit a limit, and we are migrating directly to this new session. You must resume the task immediately without losing context.\n\n"
                    "## 📍 Current Session Summary & Milestones\n"
                    "[Detailed chronological summary of everything accomplished. Include specific decisions made, exact user preferences and rules established, key configurations chosen, and all milestones reached. Be technically precise — no vague generalities.]\n\n"
                    "## 📂 Codebase Changes & Files Modified\n"
                    "[For each file touched: state the filename, what was added/changed/deleted, which functions or logic blocks were modified, and why.]\n\n"
                    "## 🚨 Unresolved Issues & Next Action Steps\n"
                    "- **Current Objective**: [Exact goal being worked on when the session ended]\n"
                    "- **Pending Tasks**: [Remaining steps needed to complete the objective]\n"
                    "- **Open Bugs / Blockers**: [Any errors, failed attempts, or known issues that need attention]\n\n"
                    "## 🚀 Instructions for You (New Claude Session)\n"
                    "1. Read the summary above carefully — treat it as the ground truth for current project state.\n"
                    "2. Ask me to share any files you need to inspect before proceeding.\n"
                    "3. Do not guess or assume — list exactly what you need to continue.\n"
                    "4. Ask any clarifying questions before starting work.\n"
                    "***"
                )
                final = call_chat_api(assembly_prompt, provider, keys, K - 1, shared_failed_keys)
                if final:
                    return final
        except Exception as e:
            log(f"[SUMMARIZE] Map-Reduce error: {e}. Falling back to standard.")

    # Standard fallback direct summarization
    log("[SUMMARIZE] Falling back to standard direct summarization.")
    standard_prompt = (
        "You are a handover assistant for a Claude session handover.\n"
        "Analyze the chat history below and compile the final handover prompt that will be pasted directly into a new Claude chat.\n"
        "The new Claude must understand exactly what has happened and immediately continue the work from where it stopped.\n\n"
        f"CHAT LOG:\n{text[:14000]}\n\n"
        "Your output MUST be structured EXACTLY as follows (do not add any conversational intro/outro text, output only this ready-to-paste markdown content):\n\n"
        "***\n"
        "# 🎭 Claude Session Handover & State Resume\n\n"
        "**Context**: We are pair programming on a project. My previous session hit a limit, and we are migrating directly to this new session. You must resume the task immediately without losing context.\n\n"
        "## 📍 Current Session Summary & Milestones\n"
        "[Detailed chronological summary of everything accomplished. Include specific decisions made, exact user preferences and rules established, key configurations chosen, and all milestones reached. Be technically precise — no vague generalities.]\n\n"
        "## 📂 Codebase Changes & Files Modified\n"
        "[For each file touched: state the filename, what was added/changed/deleted, which functions or logic blocks were modified, and why.]\n\n"
        "## 🚨 Unresolved Issues & Next Action Steps\n"
        "- **Current Objective**: [Exact goal being worked on when the session ended]\n"
        "- **Pending Tasks**: [Remaining steps needed to complete the objective]\n"
        "- **Open Bugs / Blockers**: [Any errors, failed attempts, or known issues that need attention]\n\n"
        "## 🚀 Instructions for You (New Claude Session)\n"
        "1. Read the summary above carefully — treat it as the ground truth for current project state.\n"
        "2. Ask me to share any files you need to inspect before proceeding.\n"
        "3. Do not guess or assume — list exactly what you need to continue.\n"
        "4. Ask any clarifying questions before starting work.\n"
        "***"
    )
    return call_chat_api(standard_prompt, provider, keys, 0)


def copy_to_clipboard(text):
    """Copy text to clipboard. Falls back to file if pyperclip fails."""
    if pyperclip:
        try:
            pyperclip.copy(text)
            return True
        except Exception as e:
            log(f"[CLIPBOARD] pyperclip failed: {e}")

    # Windows ctypes fallback
    try:
        import ctypes
        ctypes.windll.user32.OpenClipboard(0)
        ctypes.windll.user32.EmptyClipboard()
        encoded = text.encode("utf-16-le") + b"\x00\x00"
        hMem = ctypes.windll.kernel32.GlobalAlloc(0x0042, len(encoded))
        pMem = ctypes.windll.kernel32.GlobalLock(hMem)
        ctypes.memmove(pMem, encoded, len(encoded))
        ctypes.windll.kernel32.GlobalUnlock(hMem)
        ctypes.windll.user32.SetClipboardData(13, hMem)  # 13 = CF_UNICODETEXT
        ctypes.windll.user32.CloseClipboard()
        return True
    except Exception as e:
        log(f"[CLIPBOARD] ctypes fallback failed: {e}")

    # Last resort: save to file
    try:
        with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
            f.write(text)
        log(f"[CLIPBOARD] Saved to {SUMMARY_FILE}")
    except Exception:
        pass
    return False


# ── HTTP Request Handler ──────────────────────────────────────────────────────
class ExtractHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # suppress default HTTP logs

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/ping":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self._cors_headers()
            self.end_headers()
            self.wfile.write(b"Claude Extractor Server is running!")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/switch":
            try:
                log("[SERVER] Manual switch requested.")
                threading.Thread(target=self._trigger_switch, daemon=True).start()
                self._respond(200, {"status": "success", "message": "Switching profiles..."})
            except Exception as e:
                log(f"[SERVER] Switch error: {e}")
                self._respond(500, {"status": "error", "message": str(e)})
            return

        if self.path != "/extract":
            self.send_response(404)
            self.end_headers()
            return

        try:
            length   = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length).decode("utf-8", errors="replace")
            data     = json.loads(raw_body)
            text     = data.get("text", "").strip()
            switch   = data.get("switch", False)

            if not text or len(text) < 50:
                self._respond(400, {"status": "error", "message": "No content received from Claude tab."})
                return

            log(f"[SERVER] Received {len(text):,} chars from bookmarklet (switch={switch}).")

            # Run summarization in background thread so response returns fast
            threading.Thread(target=self._process, args=(text, switch), daemon=True).start()

            self._respond(200, {"status": "processing", "message": "Summarizing... Ctrl+V ready in ~5 seconds!"})

        except Exception as e:
            log(f"[SERVER] Request error: {e}")
            self._respond(500, {"status": "error", "message": str(e)})

    def _respond(self, code, body_dict):
        body = json.dumps(body_dict).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _trigger_switch(self):
        try:
            sys.path.append(BASE_DIR)
            import profile_switcher
            profile_switcher.main()
        except Exception as e:
            log(f"[SWITCH] Error running profile_switcher.main(): {e}")

    def _process(self, text, switch=False):
        """Runs in background thread: summarize + copy to clipboard."""
        try:
            api_keys, provider = load_config()
            if not api_keys or not api_keys.get(provider):
                log(f"[PROCESS] No keys found for provider: {provider} in accounts_config.json!")
                notify("Claude Extractor", f"ERROR: No keys found for {provider}")
                return

            summary = summarize(text, api_keys, provider)
            if not summary:
                log(f"[PROCESS] Summarizer returned empty summary.")
                notify("Claude Extractor", "Summarization failed. Check server_log.txt")
                return

            ok = copy_to_clipboard(summary)
            if ok:
                log("[PROCESS] Summary copied to clipboard!")
                print("\a")  # beep
                notify("Claude Extractor ✅", "Context copied! Switching account...")
                if switch:
                    time.sleep(1) # small delay to let user see notification before switch
                    self._trigger_switch()
            else:
                notify("Claude Extractor", f"Check last_summary.txt — clipboard failed.")

        except Exception as e:
            log(f"[PROCESS] Unexpected error: {e}")
            notify("Claude Extractor", f"Error: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"=== Claude Extractor Server started @ {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    except Exception:
        pass

    if pyperclip is None:
        log("[WARN] pyperclip not installed. Run: pip install pyperclip (ctypes fallback active)")

    server = HTTPServer((SERVER_HOST, SERVER_PORT), ExtractHandler)
    log(f"[SERVER] Listening on http://{SERVER_HOST}:{SERVER_PORT}")
    log("[SERVER] Waiting for bookmarklet trigger...")
    log("[SERVER] To stop: close this window or press Ctrl+C")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("[SERVER] Stopped.")
        server.shutdown()


if __name__ == "__main__":
    main()
