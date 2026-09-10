import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import time

# ── Constants & Valid Cloudflare-Safe Windows User Agents ────────────────────
VALID_WINDOWS_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
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

# ── Windows Toast Notification ───────────────────────────────────────────────
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

# ── Dynamic Profile Scanner ────────────────────────────────────────────────────
def get_profile_display_name(user_data_dir, profile_dir):
    pref_path = os.path.join(user_data_dir, profile_dir, "Preferences")
    if os.path.isfile(pref_path):
        try:
            with open(pref_path, encoding="utf-8") as f:
                data = json.load(f)
                name = data.get("profile", {}).get("name")
                if name:
                    return name
        except Exception:
            pass
    return profile_dir

def scan_valid_chrome_profiles(user_data_dir):
    """Dynamically scan disk for only valid, non-empty Chrome profiles."""
    if not os.path.isdir(user_data_dir):
        return []
    
    entries = []
    try:
        for name in os.listdir(user_data_dir):
            if name == "Default" or name.startswith("Profile "):
                full_path = os.path.join(user_data_dir, name)
                pref_path = os.path.join(full_path, "Preferences")
                if os.path.isdir(full_path) and os.path.isfile(pref_path) and os.path.getsize(pref_path) > 50:
                    display_name = get_profile_display_name(user_data_dir, name)
                    entries.append({"dir": name, "display_name": display_name})
    except Exception as e:
        log(f"[WARN] Error scanning profiles directory: {e}")
        
    def sort_key(item):
        d = item["dir"]
        if d == "Default":
            return (0, 0)
        parts = d.split()
        if len(parts) > 1 and parts[-1].isdigit():
            return (1, int(parts[-1]))
        return (2, d)
        
    entries.sort(key=sort_key)
    return entries

# ── Config Loader & Dynamic Sync ───────────────────────────────────────────────
def fail(msg):
    log(f"ERROR: {msg}")
    sys.exit(1)

def load_accounts():
    config_data = {}
    if os.path.isfile(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception as e:
            log(f"[WARN] Could not parse config: {e}")

    chrome_user_data = config_data.get("chrome_user_data") or os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    chrome_exe = config_data.get("chrome_exe") or r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    rotate_ua = config_data.get("rotate_user_agent", True)

    live_profiles = scan_valid_chrome_profiles(chrome_user_data)
    if not live_profiles:
        fail(f"No valid Chrome profiles found in {chrome_user_data}")

    existing_map = {}
    for acc in config_data.get("accounts", []):
        if isinstance(acc, dict) and "chrome_profile" in acc:
            existing_map[acc["chrome_profile"]] = acc

    updated_accounts = []
    for idx, p in enumerate(live_profiles):
        p_dir = p["dir"]
        existing = existing_map.get(p_dir, {})
        
        account_entry = {
            "index": idx,
            "chrome_profile": p_dir,
            "display_name": existing.get("display_name") or p["display_name"],
            "active": existing.get("active", True)
        }
        updated_accounts.append(account_entry)

    config_data["chrome_user_data"] = chrome_user_data
    config_data["chrome_exe"] = chrome_exe
    config_data["accounts"] = updated_accounts

    try:
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)
    except Exception:
        pass

    active_accounts = [a for a in updated_accounts if a.get("active", True)]
    if not active_accounts:
        fail("No active accounts found.")

    return active_accounts, chrome_exe, chrome_user_data, rotate_ua

def get_current_index(total):
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return int(json.load(f).get("index", 0)) % total
    except Exception: return 0

def save_next_index(index):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"index": index}, f)

# ── Launch Chrome Smartly ─────────────────────────────────────────────────────
def launch_chrome(chrome_exe, account):
    ext_path = os.path.join(ROOT_DIR, "extension")
    
    cmd = [
        chrome_exe,
        f"--profile-directory={account['chrome_profile']}",
        "--new-window"
    ]

    if os.path.isdir(ext_path):
        cmd.append(f"--load-extension={ext_path}")

    cmd.append("https://claude.ai/new")

    log(f"[LAUNCH] Opening {account['chrome_profile']} ({account.get('display_name')}) with extension loaded")
    subprocess.Popen(cmd)

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"=== Run @ {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    except Exception: pass

    accounts, chrome_exe, chrome_user_data, rotate_ua = load_accounts()
    index      = get_current_index(len(accounts))
    account    = accounts[index]
    next_index = (index + 1) % len(accounts)

    display_name = account.get('display_name') or account['chrome_profile']
    log(f"[SWITCH] Opening {index+1}/{len(accounts)}: {display_name} [{account['chrome_profile']}]")
    
    toast("Claude Switcher", f"Switched to Account #{index+1}: {display_name}")
    launch_chrome(chrome_exe, account)
    
    save_next_index(next_index)
    log("[DONE]")

if __name__ == "__main__":
    main()
