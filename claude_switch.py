import subprocess, json, os, sys

# ─── PATHS ───────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
STATE_FILE    = os.path.join(BASE_DIR, "switch_state.json")
ACCOUNTS_FILE = os.path.join(BASE_DIR, "claude_accounts.json")

# Auto-detect Chrome executable
CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe"),
]
# ─────────────────────────────────────────────────────────────────

def find_chrome():
    for path in CHROME_CANDIDATES:
        if os.path.exists(path):
            return path
    return None

def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        print("❌ claude_accounts.json not found! Run setup_profiles.py first.")
        input("Press Enter to exit...")
        sys.exit(1)
    with open(ACCOUNTS_FILE) as f:
        data = json.load(f)
    accounts = [a for a in data["accounts"] if a.get("active", True)]
    # JSON path takes priority only if real path; fallback to auto-detect
    _exe = data.get("chrome_exe", "")
    chrome_exe = _exe if (_exe and _exe != "AUTO_DETECTED" and os.path.exists(_exe)) else find_chrome()
    return accounts, chrome_exe

def get_current_index(total):
    try:
        with open(STATE_FILE) as f:
            idx = json.load(f).get("index", 0)
            return idx % total
    except:
        return 0

def save_next_index(i):
    with open(STATE_FILE, "w") as f:
        json.dump({"index": i}, f)

def main():
    accounts, chrome_exe = load_accounts()
    total = len(accounts)

    if not chrome_exe or not os.path.exists(chrome_exe):
        print("❌ Chrome not found. Install Chrome or set chrome_exe in claude_accounts.json")
        input("Press Enter to exit...")
        sys.exit(1)

    idx      = get_current_index(total)
    account  = accounts[idx]
    profile  = account["chrome_profile"]
    next_idx = (idx + 1) % total

    print(f"┌─────────────────────────────────────┐")
    print(f"│  ClaudeRotate — {total} Accounts          │")
    print(f"├─────────────────────────────────────┤")
    print(f"│  Opening Account {idx + 1:>2} / {total:<2}             │")
    print(f"│  Profile: {profile:<26}│")
    print(f"│  Next run → Account {next_idx + 1:<2}               │")
    print(f"└─────────────────────────────────────┘")

    subprocess.Popen([
        chrome_exe,
        f"--profile-directory={profile}",
        "--new-window",
        "https://claude.ai/new",
    ])

    save_next_index(next_idx)

if __name__ == "__main__":
    main()