import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import time

# ── Constants ─────────────────────────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]
WINDOW_SIZES  = ["1920,1080", "1366,768", "1440,900"]
BASE_DIR      = os.path.dirname(os.path.abspath(__file__)) # internal/
ROOT_DIR      = os.path.dirname(BASE_DIR)                  # root/
STATE_FILE    = os.path.join(BASE_DIR, "switcher_state.json")
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts_config.json")
LOG_FILE      = os.path.join(BASE_DIR, "switcher_log.txt")

# ── Logging ───────────────────────────────────────────────────────────────────
def log(msg):
    print(msg, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    except Exception:
        pass

# ── Windows Toast ─────────────────────────────────────────────────────────────
def toast(title, msg):
    try:
        ps = (
            'Add-Type -AssemblyName System.Windows.Forms;'
            '$n=New-Object System.Windows.Forms.NotifyIcon;'
            '$n.Icon=[System.Drawing.SystemIcons]::Information;'
            '$n.Visible=$true;'
            f'$n.ShowBalloonTip(4000,"{title}","{msg}",[System.Windows.Forms.ToolTipIcon]::Info);'
            'Start-Sleep 5;$n.Dispose()'
        )
        subprocess.Popen(["powershell", "-WindowStyle", "Hidden", "-Command", ps],
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000))
    except Exception: pass

# ── Config Loader ─────────────────────────────────────────────────────────────
def fail(msg):
    log(f"ERROR: {msg}")
    sys.exit(1)

def load_accounts():
    if not os.path.isfile(ACCOUNTS_FILE):
        fail(f"Missing {ACCOUNTS_FILE}")
    with open(ACCOUNTS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    accounts = [a for a in data.get("accounts", []) if a.get("active", True)]
    if not accounts:
        fail("No active accounts.")
    return accounts, data.get("chrome_exe", "chrome.exe"), data.get("chrome_user_data", "")

def get_current_index(total):
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return int(json.load(f).get("index", 0)) % total
    except Exception: return 0

def save_next_index(index):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"index": index}, f)

# ── Launch Chrome ─────────────────────────────────────────────────────────────
def launch_chrome(chrome_exe, account, chrome_user_data):
    ua  = random.choice(USER_AGENTS)
    wsz = random.choice(WINDOW_SIZES)
    ext_path = os.path.join(ROOT_DIR, "extension")
    
    cmd = [
        chrome_exe,
        f"--profile-directory={account['chrome_profile']}",
        "--new-window",
        f"--user-agent={ua}",
        f"--window-size={wsz}",
        f"--load-extension={ext_path}",
        "https://claude.ai/new"
    ]
    if chrome_user_data:
        cmd.append(f"--user-data-dir={chrome_user_data}")
        
    log(f"[LAUNCH] Opening {account['chrome_profile']} with extension loaded")
    subprocess.Popen(cmd)

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"=== Run @ {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    except Exception: pass

    accounts, chrome_exe, chrome_user_data = load_accounts()
    index      = get_current_index(len(accounts))
    account    = accounts[index]
    next_index = (index + 1) % len(accounts)

    # Launch next profile
    log(f"[SWITCH] Opening {index+1}/{len(accounts)}: {account.get('display_name') or account['chrome_profile']}")
    launch_chrome(chrome_exe, account, chrome_user_data)
    
    save_next_index(next_index)
    log("[DONE]")

if __name__ == "__main__":
    main()
