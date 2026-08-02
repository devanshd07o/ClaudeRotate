import os
import sys
import json
import time
import subprocess
import winreg
import tkinter as tk
from tkinter import messagebox, ttk

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # internal/
ROOT_DIR = os.path.dirname(BASE_DIR)                  # root/
CONFIG_FILE = os.path.join(BASE_DIR, "accounts_config.json")
EXT_CONFIG = os.path.join(ROOT_DIR, "extension", "config.json")
CHROME_USER_DATA = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")

# --- Registry Lookup for Chrome path ---
def get_chrome_path():
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(root, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:
                return winreg.QueryValue(key, None)
        except OSError:
            pass
    return r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# --- Chrome Preferences Scan ---
def get_profile_name(profile_dir):
    pref_path = os.path.join(CHROME_USER_DATA, profile_dir, "Preferences")
    if os.path.exists(pref_path):
        try:
            with open(pref_path, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("profile", {}).get("name") or profile_dir
        except Exception:
            pass
    return profile_dir

def scan_profiles():
    if not os.path.exists(CHROME_USER_DATA):
        return []
    directories = [
        name for name in os.listdir(CHROME_USER_DATA)
        if os.path.isdir(os.path.join(CHROME_USER_DATA, name)) and
        (name == "Default" or name.startswith("Profile "))
    ]
    directories.sort(key=lambda name: (name != "Default", int(name.split()[-1]) if name != "Default" and name.split()[-1].isdigit() else 9999))
    
    valid_profiles = []
    for name in directories:
        if os.path.isfile(os.path.join(CHROME_USER_DATA, name, "Preferences")):
            valid_profiles.append({"dir": name, "name": get_profile_name(name)})
    return valid_profiles

def is_chrome_running():
    result = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq chrome.exe", "/NH"],
        capture_output=True, text=True
    )
    return "chrome.exe" in result.stdout

def enable_dev_mode_in_profile(profile_name):
    prefs_path = os.path.join(CHROME_USER_DATA, profile_name, "Preferences")
    if not os.path.isfile(prefs_path):
        return False, "Preferences file not found"
    try:
        with open(prefs_path, encoding="utf-8") as f:
            prefs = json.load(f)
    except Exception as e:
        return False, f"Read error: {e}"

    already_on = prefs.get("extensions", {}).get("ui", {}).get("developer_mode", False)
    if already_on:
        return True, "Already enabled"

    prefs.setdefault("extensions", {}).setdefault("ui", {})["developer_mode"] = True
    tmp = prefs_path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(prefs, f, separators=(",", ":"))
        os.replace(tmp, prefs_path)
        return True, "Enabled"
    except Exception as e:
        return False, f"Write error: {e}"

# --- GUI Application ---
class SetupApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Claude Switcher Setup Wizard")
        self.geometry("640x760")
        self.configure(bg="#0d0f18")
        self.resizable(False, False)
        
        # Load existing configs
        self.existing_keys = {}
        self.existing_provider = "groq"
        self.existing_profiles = {}
        self.load_existing_config()
        
        # Scanned profiles
        self.profiles = scan_profiles()
        self.profile_vars = {}
        
        # Icon & Theme setup
        self.find_and_set_window_icon()
        self.setup_styles()
        self.create_widgets()
        
    def find_and_set_window_icon(self):
        icon_path = os.path.join(BASE_DIR, "app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # General Styles
        self.style.configure(".", background="#0d0f18", foreground="#f8fafc", fieldbackground="#16192b")
        self.style.configure("TLabel", background="#0d0f18", foreground="#f8fafc", font=("Outfit", 10))
        
        # Combobox Custom Styles
        self.style.configure("TCombobox", fieldbackground="#1c1f35", background="#16192b", foreground="#f8fafc", arrowcolor="#a855f7", borderwidth=0, relief="flat")
        self.style.map("TCombobox", fieldbackground=[("readonly", "#1c1f35")], foreground=[("readonly", "#f8fafc")])
        
        # Flat scrollbar styling
        self.style.configure("Vertical.TScrollbar", 
                             background="#1c1f35", 
                             troughcolor="#0d0f18", 
                             bordercolor="#0d0f18", 
                             arrowcolor="#a855f7",
                             lightcolor="#1c1f35", 
                             darkcolor="#1c1f35")

    def load_existing_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                    self.existing_keys = data.get("api_keys", {}) or {}
                    # Old structure fallback
                    if not self.existing_keys and "groq_api_keys" in data:
                        self.existing_keys = {"groq": data["groq_api_keys"] or []}
                    self.existing_provider = data.get("default_provider", "groq") or "groq"
                    
                    accounts_list = data.get("accounts", []) or []
                    for acc in accounts_list:
                        if acc and "chrome_profile" in acc:
                            self.existing_profiles[acc["chrome_profile"]] = {
                                "name": acc.get("display_name"),
                                "active": acc.get("active", True)
                            }
            except Exception:
                pass

    def create_widgets(self):
        # Top Header Banner
        banner_frame = tk.Frame(self, bg="#16192b", height=75)
        banner_frame.pack(fill="x", side="top")
        banner_frame.pack_propagate(False)
        
        header = tk.Label(
            banner_frame, 
            text="🎭 CLAUDE SWITCHER SETUP SUITE", 
            fg="#a855f7", 
            bg="#16192b",
            font=("Outfit", 14, "bold")
        )
        header.pack(pady=22, anchor="center")

        # Custom Tab Bar Frame
        self.tab_bar = tk.Frame(self, bg="#0d0f18", height=42)
        self.tab_bar.pack(fill="x", side="top", pady=(20, 0), padx=25)
        self.tab_bar.pack_propagate(False)

        # Tab button references
        self.pages = {}
        self.tab_buttons = {}

        # Content frame container
        self.page_container = tk.Frame(self, bg="#0d0f18")
        self.page_container.pack(fill="both", expand=True, padx=25, pady=(10, 10))

        # Create pages (pages are children of page_container)
        self.pages["profiles"] = tk.Frame(self.page_container, bg="#0d0f18")
        self.pages["keys"] = tk.Frame(self.page_container, bg="#0d0f18")
        self.pages["actions"] = tk.Frame(self.page_container, bg="#0d0f18")

        # Configure Tab Bar Buttons
        tabs = [
            ("profiles", "👥 Chrome Profiles"),
            ("keys", "🔑 API Providers"),
            ("actions", "⚙️ Actions & Setup")
        ]
        
        for name, label in tabs:
            btn = tk.Button(
                self.tab_bar, 
                text=label,
                font=("Outfit", 10, "bold"),
                bg="#16192b", 
                fg="#94a3b8",
                activebackground="#7c3aed",
                activeforeground="#ffffff",
                bd=0,
                padx=20,
                cursor="hand2",
                command=lambda n=name: self.show_page(n)
            )
            btn.pack(side="left", padx=(0, 4), fill="y")
            self.tab_buttons[name] = btn

            # Hover bindings for tab buttons
            def make_tab_hover(b=btn, n=name):
                b.bind("<Enter>", lambda e: b.config(bg="#252945") if self.current_page != n else None)
                b.bind("<Leave>", lambda e: b.config(bg="#16192b") if self.current_page != n else None)
            make_tab_hover()

        # --- TAB 1: PROFILES ---
        tab_profiles = self.pages["profiles"]

        lbl_profiles = tk.Label(
            tab_profiles, 
            text="Check the profiles you want to rotate inside Claude Switcher:",
            font=("Outfit", 11, "bold"),
            bg="#0d0f18",
            fg="#f8fafc"
        )
        lbl_profiles.pack(anchor="w", padx=5, pady=(15, 10))

        # Scrollable container for checkboxes
        list_container = tk.Frame(tab_profiles, bg="#16192b", bd=1, relief="flat", highlightbackground="#2a2e4d", highlightthickness=1)
        list_container.pack(fill="both", expand=True, padx=5, pady=(0, 15))

        canvas_p = tk.Canvas(list_container, bg="#16192b", highlightthickness=0)
        scrollbar_p = ttk.Scrollbar(list_container, orient="vertical", command=canvas_p.yview, style="Vertical.TScrollbar")
        scroll_frame_p = tk.Frame(canvas_p, bg="#16192b")

        scroll_frame_p.bind("<Configure>", lambda e: canvas_p.configure(scrollregion=canvas_p.bbox("all")))
        canvas_p.create_window((0, 0), window=scroll_frame_p, anchor="nw")
        canvas_p.configure(yscrollcommand=scrollbar_p.set)

        canvas_p.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar_p.pack(side="right", fill="y")

        # Scanned profile boxes
        for p in self.profiles:
            is_active = True
            if self.existing_profiles:
                if p["dir"] in self.existing_profiles:
                    is_active = self.existing_profiles[p["dir"]]["active"]
                else:
                    is_active = False

            var = tk.BooleanVar(self)
            var.set(is_active)
            self.profile_vars[p["dir"]] = var

            chk = tk.Checkbutton(
                scroll_frame_p,
                text=f"  {p['name']} ({p['dir']})",
                variable=var,
                bg="#16192b",
                fg="#f8fafc",
                selectcolor="#1c1f35",
                activebackground="#16192b",
                activeforeground="#f8fafc",
                font=("Outfit", 10),
                padx=15,
                pady=10,
                bd=0,
                relief="flat",
                highlightthickness=0,
                anchor="w"
            )
            chk.pack(anchor="w", fill="x")

        # --- TAB 2: API KEYS ---
        tab_keys = self.pages["keys"]

        # Select Provider frame
        prov_select_frame = tk.Frame(tab_keys, bg="#0d0f18")
        prov_select_frame.pack(fill="x", padx=5, pady=(15, 10))
        
        lbl_prov = tk.Label(prov_select_frame, text="Default AI Provider:", font=("Outfit", 11, "bold"), bg="#0d0f18", fg="#f8fafc")
        lbl_prov.pack(side="left", padx=(0, 10))
        
        self.provider_combo = ttk.Combobox(
            prov_select_frame, 
            values=["groq", "cerebras", "gemini", "mistral", "openrouter"],
            state="readonly",
            font=("Outfit", 10),
            width=15
        )
        self.provider_combo.pack(side="left", padx=10)
        self.provider_combo.set(self.existing_provider)

        # Scrollable keys container
        keys_outer_container = tk.Frame(tab_keys, bg="#16192b", bd=1, relief="flat", highlightbackground="#2a2e4d", highlightthickness=1)
        keys_outer_container.pack(fill="both", expand=True, padx=5, pady=(5, 15))

        canvas_k = tk.Canvas(keys_outer_container, bg="#16192b", highlightthickness=0)
        scrollbar_k = ttk.Scrollbar(keys_outer_container, orient="vertical", command=canvas_k.yview, style="Vertical.TScrollbar")
        scroll_frame_k = tk.Frame(canvas_k, bg="#16192b")

        scroll_frame_k.bind("<Configure>", lambda e: canvas_k.configure(scrollregion=canvas_k.bbox("all")))
        canvas_k.create_window((0, 0), window=scroll_frame_k, anchor="nw")
        canvas_k.configure(yscrollcommand=scrollbar_k.set)

        canvas_k.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar_k.pack(side="right", fill="y")

        self.key_entries = {}
        self.key_row_frames = {}
        self.key_rows_frame = {}
        
        providers = [
            ("groq", "Groq Cloud API"),
            ("cerebras", "Cerebras Inference API"),
            ("gemini", "Google Gemini developer API"),
            ("mistral", "Mistral AI platform developer API"),
            ("openrouter", "OpenRouter standard endpoint API")
        ]
        
        for prov_id, prov_desc in providers:
            # Subtle card frame (no retro border)
            p_frame = tk.Frame(scroll_frame_k, bg="#16192b", bd=1, relief="flat", highlightbackground="#2a2e4d", highlightthickness=1)
            p_frame.pack(fill="x", expand=True, padx=10, pady=10)

            # Header inside the card
            lbl_title = tk.Label(
                p_frame,
                text=prov_desc,
                font=("Outfit", 11, "bold"),
                bg="#16192b",
                fg="#a855f7",
                anchor="w"
            )
            lbl_title.pack(fill="x", padx=15, pady=(15, 10))

            # Container for input rows
            rows_frame = tk.Frame(p_frame, bg="#16192b")
            rows_frame.pack(fill="x", expand=True)
            self.key_rows_frame[prov_id] = rows_frame
            
            # Action buttons frame (Add/Remove)
            actions_frame = tk.Frame(p_frame, bg="#16192b")
            actions_frame.pack(fill="x", pady=(10, 15), padx=15)
            
            self.key_entries[prov_id] = []
            self.key_row_frames[prov_id] = []
            
            # Add dynamic buttons with flat layout styles
            btn_add = tk.Button(
                actions_frame, text="+ Add Key", 
                command=lambda p=prov_id: self.add_key_row(p),
                bg="#20243c", fg="#a855f7", activebackground="#252945", activeforeground="#f8fafc",
                font=("Outfit", 9, "bold"), bd=0, padx=12, pady=5, cursor="hand2", relief="flat"
            )
            btn_add.pack(side="left", padx=2)
            
            btn_rem = tk.Button(
                actions_frame, text="- Remove", 
                command=lambda p=prov_id: self.remove_key_row(p),
                bg="#20243c", fg="#ef4444", activebackground="#252945", activeforeground="#f8fafc",
                font=("Outfit", 9, "bold"), bd=0, padx=12, pady=5, cursor="hand2", relief="flat"
            )
            btn_rem.pack(side="left", padx=2)

            # Add hover logic to action buttons
            def make_hover(btn, color_enter, color_leave):
                btn.bind("<Enter>", lambda e: btn.config(bg=color_enter))
                btn.bind("<Leave>", lambda e: btn.config(bg=color_leave))
            make_hover(btn_add, "#2a2e4d", "#20243c")
            make_hover(btn_rem, "#2a2e4d", "#20243c")

            # Populate with existing keys or a default row
            existing_prov_keys = self.existing_keys.get(prov_id, [])
            if existing_prov_keys:
                for k in existing_prov_keys:
                    self.add_key_row(prov_id, k)
            else:
                self.add_key_row(prov_id)  # Start with 1 empty row by default

        # --- TAB 3: SYSTEM SETUP ---
        tab_system = self.pages["actions"]

        # Instruction info block
        info_block = tk.Frame(
            tab_system,
            bg="#16192b",
            bd=1,
            relief="flat",
            highlightbackground="#2a2e4d",
            highlightthickness=1
        )
        info_block.pack(fill="both", expand=True, padx=5, pady=15)

        lbl_summary_title = tk.Label(
            info_block,
            text="Configuration Operations Summary",
            font=("Outfit", 11, "bold"),
            bg="#16192b",
            fg="#a855f7"
        )
        lbl_summary_title.pack(fill="x", padx=20, pady=(20, 10), anchor="w")

        operation_text = (
            "Claude Account Switcher setup will execute the following items:\n\n"
            "✓ Close open Chrome processes to safely apply configurations.\n\n"
            "✓ Modify Developer Mode settings inside all target profiles.\n\n"
            "✓ Generate 'accounts_config.json' inside the internal/ folder.\n\n"
            "✓ Copy keys and providers parameters to the Chrome extension.\n\n"
            "✓ Build Desktop & Local shortcuts pointing to silent.vbs wrappers.\n\n"
            "✓ Register 'ClaudeExtractor.lnk' inside the Startup directory.\n\n"
            "✓ Silently launch the handover server in the background."
        )
        lbl_info = tk.Label(
            info_block, 
            text=operation_text, 
            justify="left", 
            bg="#16192b", 
            fg="#f8fafc", 
            font=("Outfit", 10),
            wraplength=520
        )
        lbl_info.pack(anchor="nw", padx=20, pady=(0, 20))

        # Large Premium action button
        self.setup_btn = tk.Button(
            tab_system, 
            text="🚀 Configure System (One-Click Setup)", 
            font=("Outfit", 12, "bold"),
            bg="#10b981", 
            fg="#ffffff",
            activebackground="#059669",
            activeforeground="#ffffff",
            bd=0,
            padx=20,
            pady=12,
            cursor="hand2",
            command=self.run_setup_process,
            relief="flat"
        )
        self.setup_btn.pack(pady=(10, 5), padx=5, fill="x")

        # Configure button hover
        self.setup_btn.bind("<Enter>", lambda e: self.setup_btn.config(bg="#059669") if self.setup_btn.cget("text") == "🚀 Configure System (One-Click Setup)" else None)
        self.setup_btn.bind("<Leave>", lambda e: self.setup_btn.config(bg="#10b981") if self.setup_btn.cget("text") == "🚀 Configure System (One-Click Setup)" else None)

        # Status Label below the button
        self.status_lbl = tk.Label(
            tab_system, 
            text="", 
            foreground="#10b981", 
            font=("Outfit", 10, "bold"), 
            background="#0d0f18",
            anchor="center",
            justify="center"
        )
        self.status_lbl.pack(pady=10)

        # Footer Spacer Frame
        footer_frame = tk.Frame(self, bg="#0d0f18", height=15)
        footer_frame.pack(fill="x", side="bottom")

        # Show first page
        self.current_page = None
        self.show_page("profiles")

    def show_page(self, name):
        if self.current_page == name:
            return
            
        # Hide current page
        for p_name in self.pages:
            self.pages[p_name].pack_forget()
            self.tab_buttons[p_name].config(bg="#16192b", fg="#94a3b8")
            
        # Show new page
        self.current_page = name
        self.pages[name].pack(fill="both", expand=True)
        self.tab_buttons[name].config(bg="#7c3aed", fg="#ffffff")

    def add_key_row(self, prov_id, initial_value=""):
        rows_frame = self.key_rows_frame[prov_id]
        idx = len(self.key_entries[prov_id])
        
        row = tk.Frame(rows_frame, bg="#16192b")
        row.pack(fill="x", pady=4, padx=15)
        
        # Label showing Key number
        lbl = tk.Label(row, text=f"Key {idx+1}:", bg="#16192b", fg="#94a3b8", font=("Consolas", 10), width=8, anchor="w")
        lbl.pack(side="left")
        
        # Sleek custom input entry container
        ent_container = tk.Frame(row, bg="#20243c", bd=1, relief="flat", highlightbackground="#2d325a", highlightthickness=1)
        ent_container.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        ent = tk.Entry(
            ent_container, 
            font=("Consolas", 10), 
            show="*", 
            bg="#20243c", 
            fg="#f8fafc", 
            insertbackground="#f8fafc",
            bd=0, 
            relief="flat",
            highlightthickness=0
        )
        ent.pack(fill="both", expand=True, padx=10, pady=6)
        
        if initial_value:
            ent.insert(0, initial_value)
            
        # Create eye toggle button for this specific entry
        btn_eye = tk.Button(
            row, text="👁", 
            command=lambda e=ent: self.toggle_single_key_visibility(e),
            bg="#20243c", fg="#94a3b8", activebackground="#2a2e4d", activeforeground="#f8fafc",
            font=("Outfit", 9), bd=0, padx=10, pady=3, cursor="hand2", relief="flat"
        )
        btn_eye.pack(side="right")
        
        # Eye button hover effect
        btn_eye.bind("<Enter>", lambda e: btn_eye.config(bg="#2a2e4d"))
        btn_eye.bind("<Leave>", lambda e: btn_eye.config(bg="#20243c"))
            
        # Store the entry widget and its row frame container
        self.key_entries[prov_id].append(ent)
        self.key_row_frames[prov_id].append(row)

    def remove_key_row(self, prov_id):
        if len(self.key_entries[prov_id]) > 1:
            ans = messagebox.askyesno(
                "Confirm Key Removal",
                f"Are you sure you want to remove the last key for {prov_id.upper()}?"
            )
            if ans:
                ent = self.key_entries[prov_id].pop()
                row = self.key_row_frames[prov_id].pop()
                row.destroy()

    def toggle_single_key_visibility(self, entry_widget):
        current_show = entry_widget.cget("show")
        if current_show == "*":
            entry_widget.configure(show="")
        else:
            entry_widget.configure(show="*")

    def run_setup_process(self):
        # 1. Close Chrome warning
        if is_chrome_running():
            ans = messagebox.askyesno(
                "Chrome is running!",
                "All Google Chrome windows must be closed to apply Developer Mode preferences.\n\n"
                "Would you like to continue anyway?"
            )
            if not ans:
                return

        # 2. Check at least one profile selected
        selected_profiles = []
        for p in self.profiles:
            if self.profile_vars[p["dir"]].get():
                selected_profiles.append(p)
                
        if not selected_profiles:
            messagebox.showerror("Error", "Please select at least one Chrome profile!")
            return

        # 3. Retrieve Keys for all providers dynamically
        api_keys = {}
        for prov_id in ["groq", "cerebras", "gemini", "mistral", "openrouter"]:
            provider_keys = []
            for ent in self.key_entries[prov_id]:
                k = ent.get().strip()
                if k:
                    provider_keys.append(k)
            api_keys[prov_id] = provider_keys

        default_provider = self.provider_combo.get()

        # 4. Enable Developer Mode
        failed_dev = []
        for p in selected_profiles:
            ok, _ = enable_dev_mode_in_profile(p["dir"])
            if not ok:
                failed_dev.append(p["name"])
                
        if failed_dev:
            messagebox.showwarning(
                "Developer Mode warning",
                f"Could not automatically set Developer Mode in these profiles: {', '.join(failed_dev)}.\n"
                "You might need to enable 'Developer mode' manually at chrome://extensions/ inside those profiles."
            )

        # 5. Write Accounts config
        chrome_exe = get_chrome_path()
        accounts = []
        for pos, p in enumerate(selected_profiles):
            d_name = p["name"]
            if p["dir"] in self.existing_profiles:
                d_name = self.existing_profiles[p["dir"]]["name"] or p["name"]
                
            accounts.append({
                "index": pos,
                "chrome_profile": p["dir"],
                "display_name": d_name,
                "active": True
            })
            
        config_data = {
            "chrome_user_data": CHROME_USER_DATA,
            "chrome_exe": chrome_exe,
            "api_keys": api_keys,
            "default_provider": default_provider,
            "accounts": accounts
        }
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)

        # 6. Write extension config
        with open(EXT_CONFIG, "w", encoding="utf-8") as f:
            json.dump({
                "api_keys": api_keys,
                "default_provider": default_provider
            }, f, indent=2)

        # 7. Create Shortcuts (Desktop & Local Folder)
        icon_arg = os.path.join(BASE_DIR, "app_icon.ico")
        if not os.path.exists(icon_arg):
            icon_arg = chrome_exe
        else:
            icon_arg = os.path.abspath(icon_arg)

        launcher_path = os.path.join(BASE_DIR, "silent_switcher.vbs")
        working_dir = BASE_DIR

        # Resolve exact Desktop path dynamically (handling standard vs OneDrive fallback)
        desktop_folder = os.path.join(os.path.expanduser("~"), "Desktop")
        onedrive_desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
        if os.path.exists(onedrive_desktop):
            desktop_folder = onedrive_desktop
            
        desktop_shortcut = os.path.join(desktop_folder, "Claude Switcher.lnk")
        desktop_shortcut_esc = desktop_shortcut.replace("\\", "\\\\")

        # PowerShell script to create Desktop shortcut
        desktop_ps = f"""
        $launcher = "{launcher_path}"
        $shortcutPath = "{desktop_shortcut_esc}"
        $WshShell = New-Object -ComObject WScript.Shell
        $shortcut = $WshShell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = "wscript.exe"
        $shortcut.Arguments = "`"$launcher`""
        $shortcut.WorkingDirectory = "{working_dir}"
        $shortcut.Description = "Claude Auto Account Switcher"
        $shortcut.IconLocation = "{icon_arg}, 0"
        $shortcut.Save()
        """
        
        # PowerShell script to create Local project folder shortcut (in ROOT_DIR)
        local_ps = f"""
        $launcher = "{launcher_path}"
        $shortcutPath = Join-Path "{ROOT_DIR}" "Claude Switcher.lnk"
        $WshShell = New-Object -ComObject WScript.Shell
        $shortcut = $WshShell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = "wscript.exe"
        $shortcut.Arguments = "`"$launcher`""
        $shortcut.WorkingDirectory = "{working_dir}"
        $shortcut.Description = "Claude Auto Account Switcher"
        $shortcut.IconLocation = "{icon_arg}, 0"
        $shortcut.Save()
        """
        
        # PowerShell script to create Startup shortcut
        vbs_extractor_path = os.path.join(BASE_DIR, "silent_server.vbs")
        startup_ps = f"""
        $vbsPath = "{vbs_extractor_path}"
        $startupFolder = [Environment]::GetFolderPath("Startup")
        $shortcutPath = Join-Path $startupFolder "ClaudeExtractor.lnk"
        $WshShell = New-Object -ComObject WScript.Shell
        $shortcut = $WshShell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = "wscript.exe"
        $shortcut.Arguments = "`"$vbsPath`""
        $shortcut.WorkingDirectory = "{working_dir}"
        $shortcut.Description = "Claude Context Extractor Server (runs at startup)"
        $shortcut.WindowStyle = 7
        $shortcut.Save()
        """

        try:
            subprocess.run(["powershell", "-Command", desktop_ps], check=True)
            subprocess.run(["powershell", "-Command", local_ps], check=True)
            subprocess.run(["powershell", "-Command", startup_ps], check=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create shortcuts: {e}")
            return

        # 8. Start Extractor Server
        try:
            vbs_extractor = os.path.join(BASE_DIR, "silent_server.vbs")
            subprocess.Popen(["wscript.exe", vbs_extractor])
        except Exception:
            pass

        messagebox.showinfo(
            "Success!",
            "Claude Switcher suite successfully configured!\n\n"
            "✓ Desktop shortcut created!\n"
            "✓ Local folder shortcut created!\n"
            "✓ Windows Startup entry created!\n"
            "✓ Background server launched on port 5757!"
        )
        
        # Display completion state on GUI
        self.status_lbl.configure(
            text="✓ Claude Switcher configured successfully!\n"
                 "• Desktop & Local shortcuts created\n"
                 "• Extractor server running in background on port 5757",
            foreground="#10b981"
        )
        self.setup_btn.configure(
            text="✓ Done / Finish & Close Wizard",
            bg="#7c3aed",
            command=self.destroy
        )
        # Done hover bindings
        self.setup_btn.bind("<Enter>", lambda e: self.setup_btn.config(bg="#6d28d9"))
        self.setup_btn.bind("<Leave>", lambda e: self.setup_btn.config(bg="#7c3aed"))

if __name__ == "__main__":
    app = SetupApp()
    app.mainloop()
