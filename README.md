# ⚡ ClaudeRotate — Multi-Profile Switcher & 1-Click Handover Engine

**ClaudeRotate** is a complete, dual-component suite built for power users and developers on Claude.ai:
1. 🖥️ **Desktop Multi-Profile Switcher**: A 1-click Windows desktop app (`setup.vbs`) to instantly manage multiple Chrome profiles, run a silent local handover server, and switch profiles seamlessly.
2. 🧩 **ClaudeRotate Chrome Extension**: A Manifest V3 extension (`extension/`) that extracts complete chat transcripts (unmounted turns, code probes, DOM selectors) and runs a **Dual-Stage Parallel AI Map-Reduce Pipeline** to generate instant handover prompts.

---

## 🚀 1-Click Desktop App Setup (`setup.vbs`)

Setting up the desktop profile switcher and local background server is 100% automated:

1. **Clone or Download the Repository**:
   ```bash
   git clone https://github.com/devanshd07o/ClaudeRotate.git
   cd ClaudeRotate
   ```

2. **Run 1-Click Setup**:
   - Double-click **`setup.vbs`** in the root folder.
   - It automatically installs required Python packages (`customtkinter`, `requests`), sets up desktop shortcuts, and launches the **Claude Switcher** GUI installer silently.

3. **Desktop Features**:
   - **Multi-Profile Manager**: Open and switch between dedicated Chrome profiles for different Claude accounts.
   - **Silent Background Handover Server**: Listens locally on `http://localhost:5757` for background handover processing.

---

## 🧩 Chrome Extension Installation (`extension/`)

1. **Load Unpacked Extension in Chrome**:
   - Open Google Chrome and navigate to `chrome://extensions`.
   - Enable **Developer mode** (toggle switch in top-right corner).
   - Click **Load unpacked** (top-left corner).
   - Select the `extension` subfolder inside the cloned repository directory.

2. **Configure API Keys**:
   - Click the **ClaudeRotate** icon in your Chrome toolbar or open `extension/options.html`.
   - Click ⚙️ Settings to enter your API keys (Groq, Gemini, Cerebras, Mistral, OpenRouter).
   - Alternatively, copy `extension/config.example.json` to `extension/config.json` locally and add your keys.

3. **Use on Claude.ai**:
   - Open any chat session on `https://claude.ai`.
   - Click the floating purple ⚡ **Copy Handover** button (or click **Copy Handover Context** in the toolbar popup).
   - Paste the generated Handover Prompt directly into your replacement AI session!

---

## ✨ Feature Summary

- **⚡ 1-Click Floating FAB Widget & Popup**: Instant prompt copy directly from `claude.ai`.
- **🔄 Dual-Stage Parallel Map-Reduce Pipeline**: Splits chat into Part 1 (Top Half / Early Setup) and Part 2 (Bottom Half / Ground Truth), summarizing across multiple API keys in parallel.
- **🎯 Actionable Facts & Selector Engine**: Scrapes exact CSS selectors (`div.tiptap`, `textarea[placeholder="Message DeepSeek"]`, `button[aria-label="Submit"]`), modified files, and confirmed probe statuses (`✅` / `❌`).
- **💻 Real-Time Console Interceptor**: Intercepts `console.log`, `console.warn`, and `console.error` (`window.__councilLogs`) to capture DevTools probe outputs into handover prompts.
- **🖥️ 1-Click Windows Setup (`setup.vbs`)**: Zero-config silent setup for desktop profile switcher and local background server.
- **🛡️ Zero Key Leak Security**: `.gitignore` protection prevents local API keys from being committed to GitHub.

---

## 📂 Repository Structure

```
ClaudeRotate/
├── setup.vbs                # 1-Click Windows Desktop Installer & GUI Launcher
├── README.md                # Documentation & setup guide
├── LICENSE                  # Copyright & Privacy Policy agreement
├── requirements.txt         # Python dependencies for desktop app
├── extension/               # Chrome Extension (MV3)
│   ├── manifest.json        # Extension manifest
│   ├── background.js       # Map-Reduce LLM service worker
│   ├── content.js          # Injected DOM extractor & console interceptor
│   ├── content.css         # Floating FAB widget & toast styles
│   ├── popup.html          # Toolbar popup UI
│   ├── popup.js            # Popup logic
│   ├── options.html        # Options page UI
│   ├── options.js          # Storage & key management
│   ├── config.example.json # Public config template
│   └── icon16.png          # Icons
└── internal/                # Desktop App Python Scripts
    ├── installer_gui.py     # CustomTkinter GUI setup manager
    ├── profile_switcher.py  # Profile switcher logic
    ├── handover_server.py   # Local background server
    └── open_profiles.py     # Chrome profile launcher
```

---

## 🔒 Privacy Policy & Ownership Protection

- **100% Local & Confidential**: ClaudeRotate runs locally on your machine. API calls communicate directly with official LLM providers (Groq/Gemini). NO user data, chat history, or API keys are collected or sent to remote telemetry servers.
- **Intellectual Property**: Copyright (c) 2026 Devansh ([@devanshd07o](https://github.com/devanshd07o)). All rights reserved. See [LICENSE](LICENSE) for terms.
