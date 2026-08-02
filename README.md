# ⚡ ClaudeRotate — 1-Click Claude.ai Session Handover & State Resume

**ClaudeRotate** is a high-precision, MV3 Chrome Extension designed for pair-programming developers using Claude.ai. When your session hits context or token limits, ClaudeRotate extracts the complete conversation transcript (including unmounted turns, open code artifacts, and console probe outputs), runs a **Dual-Stage Parallel AI Map-Reduce Pipeline**, and copies an actionable, zero-hallucination Handover Prompt directly to your clipboard.

---

## ✨ Features

- **⚡ 1-Click Floating FAB Widget & Popup**: Extract and copy handover prompts directly from the active `claude.ai` tab.
- **🔄 Dual-Stage Parallel Map-Reduce Pipeline**: Splits chat into Part 1 (Top Half / Early Setup) and Part 2 (Bottom Half / Ground Truth), running parallel LLM summarization across multiple keys for maximum speed.
- **🎯 Actionable Facts & DOM Selector Engine**: Scrapes exact CSS selectors (`div.tiptap`, `textarea[placeholder="Message DeepSeek"]`, `button[aria-label="Submit"]`), modified files, and confirmed probe statuses (`✅` / `❌`).
- **💻 Real-Time Console Interceptor**: Hooks into `console.log`, `console.warn`, and `console.error` (`window.__councilLogs`), capturing DevTools probe outputs automatically into the handover prompt.
- **🔑 Multi-Provider Key Rotation**: Out-of-the-box support for **Groq, Cerebras, Mistral, Gemini, and OpenRouter** with automatic 7-second timeouts and key rotation fallbacks.
- **🛡️ Zero API Leak Security**: Local configuration files (`config.json`) are automatically `.gitignore`-protected to prevent accidental credential leaks on GitHub.

---

## 🚀 How to Install in Chrome

1. **Clone or Download the Repository**:
   ```bash
   git clone https://github.com/devanshd07o/ClaudeRotate.git
   cd ClaudeRotate
   ```

2. **Load Unpacked Extension in Chrome**:
   - Open Google Chrome and navigate to `chrome://extensions`.
   - Enable **Developer mode** (toggle switch in the top-right corner).
   - Click **Load unpacked** in the top-left corner.
   - Select the `extension` subfolder inside the cloned repository directory.

3. **Configure API Keys**:
   - Click the **ClaudeRotate** icon in your Chrome extensions toolbar or open `extension/options.html`.
   - Click the ⚙️ Settings gear to enter your API key(s) (e.g. Groq, Gemini, etc.).
   - Alternatively, copy `extension/config.example.json` to `extension/config.json` locally and add your keys.

4. **Use on Claude.ai**:
   - Open any active chat session on `https://claude.ai`.
   - Click the purple floating ⚡ button in the bottom-right corner (or click **Copy Handover Context** in the toolbar popup).
   - Paste the generated Handover Prompt directly into your replacement AI assistant session!

---

## 🔒 Privacy Policy & Ownership Protection

- **100% Local & Confidential**: ClaudeRotate processes all AI handover context locally on your device and communicates directly with official LLM providers (Groq/Gemini). NO user data, chat transcripts, or API keys are ever collected or sent to any third-party server.
- **Intellectual Property**: Copyright (c) 2026 Devansh ([@devanshd07o](https://github.com/devanshd07o)). All rights reserved. Re-branding, re-publishing, or claiming ownership of this codebase without explicit written consent is strictly prohibited under the [LICENSE](LICENSE).

---

## 📂 Repository Structure

```
ClaudeRotate/
├── extension/
│   ├── manifest.json         # Manifest V3 extension configuration
│   ├── background.js        # Service worker handling Map-Reduce LLM pipeline
│   ├── content.js           # Injected DOM extractor & console interceptor
│   ├── content.css          # Floating FAB widget & toast badge styling
│   ├── popup.html           # Toolbar popup UI
│   ├── popup.js             # Popup logic & settings manager
│   ├── options.html         # Full-screen options page
│   ├── options.js           # API key storage manager
│   ├── config.example.json  # Public configuration template
│   └── icon16.png           # Extension icons
├── .gitignore               # Excludes config.json and local logs
├── LICENSE                  # Copyright & Privacy Policy agreement
└── README.md                # Documentation & usage guide
```

---

## 🛡️ License

Copyright © 2026 Devansh (devanshd07o). All Rights Reserved. See [LICENSE](LICENSE) for full details.
