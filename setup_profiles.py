"""
setup_profiles.py — Run this ONCE to map your Chrome profiles to Claude accounts.
It opens each profile, checks if Claude is logged in, and saves the mapping.

Usage: Double-click or run: python setup_profiles.py
"""

import os
import json
import subprocess
import time

# ─── AUTO-DETECT ──────────────────────────────────────────────────────────────
CHROME_USER_DATA = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data")

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe"),
]

PROFILE_DIRS = [
    "Default",
    "Profile 1",  "Profile 2",  "Profile 3",  "Profile 4",
    "Profile 5",  "Profile 6",  "Profile 7",  "Profile 8",
    "Profile 9",  "Profile 10", "Profile 11", "Profile 12",
    "Profile 13", "Profile 14", "Profile 15",
]
# ──────────────────────────────────────────────────────────────────────────────

def find_chrome():
    for path in CHROME_CANDIDATES:
        if os.path.exists(path):
            return path
    return None

def get_profile_name(profile_dir):
    prefs_path = os.path.join(CHROME_USER_DATA, profile_dir, "Preferences")
    if not os.path.exists(prefs_path):
        return None
    try:
        with open(prefs_path, "r", encoding="utf-8") as f:
            prefs = json.load(f)
        return prefs.get("profile", {}).get("name", profile_dir)
    except Exception:
        return profile_dir

def scan_profiles():
    found = []
    for p in PROFILE_DIRS:
        full_path = os.path.join(CHROME_USER_DATA, p)
        if os.path.isdir(full_path):
            name = get_profile_name(p)
            found.append({"dir": p, "name": name, "path": full_path})

    print(f"\n  Found {len(found)} Chrome profiles:\n")
    for i, p in enumerate(found):
        print(f"  [{i}] {p['name']} -> {p['dir']}")
    return found

def open_profile_for_check(chrome_exe, profile_dir):
    subprocess.Popen([
        chrome_exe,
        f"--profile-directory={profile_dir}",
        f"--user-data-dir={CHROME_USER_DATA}",
        "https://claude.ai/new"
    ])

def save_account_map(profiles, selected_indices, chrome_exe):
    accounts = []
    for i in selected_indices:
        p = profiles[i]
        accounts.append({
            "index": len(accounts),
            "chrome_profile": p["dir"],
            "display_name": p["name"],
            "active": True
        })

    config = {
        "chrome_user_data": CHROME_USER_DATA,
        "chrome_exe": chrome_exe,
        "accounts": accounts,
        "current_account_index": 0
    }

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "claude_accounts.json")
    with open(out, "w") as f:
        json.dump(config, f, indent=2)

    print(f"\n  Saved {len(accounts)} accounts to claude_accounts.json")
    print("  Now double-click Claude.bat to launch!\n")

if __name__ == "__main__":
    print("=" * 50)
    print("   ClaudeRotate - One Time Setup")
    print("   by Devansh Dubey (github.com/devanshd07o)")
    print("=" * 50)

    if not os.path.isdir(CHROME_USER_DATA):
        print(f"\n  ERROR: Chrome User Data not found at:\n  {CHROME_USER_DATA}")
        print("  Is Chrome installed?")
        input("Press Enter to exit...")
        exit(1)

    chrome_exe = find_chrome()
    if not chrome_exe:
        print("\n  ERROR: Chrome executable not found.")
        print("  Install Chrome from: https://www.google.com/chrome/")
        input("Press Enter to exit...")
        exit(1)

    print(f"\n  Chrome found: {chrome_exe}")
    print(f"  User Data  : {CHROME_USER_DATA}")

    profiles = scan_profiles()

    if not profiles:
        print("\n  ERROR: No Chrome profiles found.")
        input("Press Enter to exit...")
        exit(1)

    check = input("\nOpen each profile in Chrome to verify Claude login? (y/n): ").strip().lower()
    if check == "y":
        for p in profiles:
            print(f"  Opening {p['name']} ({p['dir']})...")
            open_profile_for_check(chrome_exe, p["dir"])
            time.sleep(2)
        input("\nDone checking? Press Enter to continue...")

    print("\nWhich profiles have Claude logged in?")
    print("Enter numbers separated by commas (e.g. 0,1,2,3):")
    raw = input("-> ").strip()

    try:
        indices = [int(x.strip()) for x in raw.split(",")]
        save_account_map(profiles, indices, chrome_exe)
    except Exception as e:
        print(f"\n  ERROR: {e}")
        print("  Re-run and enter valid numbers.")
        input("Press Enter to exit...")