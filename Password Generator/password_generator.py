import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import string
import secrets
import time

# --- High-DPI Awareness for Windows ---
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# --- Theme Colors ---
COLOR_BG = "#121824"          # Deep dark blue-gray
COLOR_CARD = "#1e293b"        # Slate card background
COLOR_TEXT_PRIMARY = "#f8fafc" # Off-white
COLOR_TEXT_MUTED = "#94a3b8"   # Cool gray
COLOR_ACCENT = "#6366f1"       # Indigo
COLOR_ACCENT_HOVER = "#4f46e5" # Darker Indigo
COLOR_BORDER = "#334155"       # Slate border
COLOR_STRENGTH_WEAK = "#ef4444"   # Rose red
COLOR_STRENGTH_FAIR = "#f59e0b"   # Amber orange
COLOR_STRENGTH_GOOD = "#10b981"   # Emerald green
COLOR_STRENGTH_EXCELLENT = "#06b6d4"# Cyan/Teal

class PasswordGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Secure Password Generator")
        self.root.geometry("820x600")
        self.root.configure(bg=COLOR_BG)
        self.root.minsize(780, 560)

        # Style configurations
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('.', background=COLOR_BG, foreground=COLOR_TEXT_PRIMARY)
        
        # Custom Checkbutton Styling
        self.style.configure('Custom.TCheckbutton', 
                             background=COLOR_CARD, 
                             foreground=COLOR_TEXT_PRIMARY,
                             focuscolor=COLOR_CARD)
        self.style.map('Custom.TCheckbutton',
                       background=[('active', COLOR_CARD)],
                       foreground=[('active', COLOR_TEXT_PRIMARY)])

        # State Variables
        self.password_len = tk.IntVar(value=16)
        self.use_upper = tk.BooleanVar(value=True)
        self.use_lower = tk.BooleanVar(value=True)
        self.use_digits = tk.BooleanVar(value=True)
        self.use_symbols = tk.BooleanVar(value=True)
        self.exclude_chars = tk.StringVar(value="")
        self.enforce_all = tk.BooleanVar(value=True)
        
        self.generated_password = tk.StringVar(value="")
        self.strength_text = tk.StringVar(value="Select options to generate password")
        self.strength_color = COLOR_TEXT_MUTED
        
        # Password History (stores dicts: {"password": str, "timestamp": str, "masked": bool})
        self.history = []

        # Setup GUI Components
        self.create_widgets()
        
        # Trigger initial password generation
        self.generate_password()

    def create_widgets(self):
        # --- Top Header ---
        header_frame = tk.Frame(self.root, bg=COLOR_BG, pady=15)
        header_frame.pack(fill=tk.X, padx=25)

        # Vector Icon (Shield and Lock)
        self.icon_canvas = tk.Canvas(header_frame, width=44, height=44, bg=COLOR_BG, bd=0, highlightthickness=0)
        self.icon_canvas.pack(side=tk.LEFT)
        self.draw_shield_icon()

        title_label = tk.Label(header_frame, text="Secure Password Generator", 
                               font=("Segoe UI", 18, "bold"), bg=COLOR_BG, fg=COLOR_TEXT_PRIMARY)
        title_label.pack(side=tk.LEFT, padx=10)
        
        subtitle_label = tk.Label(header_frame, text="Cryptographically secure generator with visual strength analysis", 
                                  font=("Segoe UI", 9), bg=COLOR_BG, fg=COLOR_TEXT_MUTED)
        subtitle_label.pack(side=tk.RIGHT, pady=8)

        # --- Main Layout Split ---
        main_container = tk.Frame(self.root, bg=COLOR_BG)
        main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 20))

        # Left Panel (Controls and Display)
        left_panel = tk.Frame(main_container, bg=COLOR_BG)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Right Panel (History Log)
        self.right_panel = tk.Frame(main_container, bg=COLOR_CARD, bd=1, highlightbackground=COLOR_BORDER, highlightthickness=1, width=280)
        self.right_panel.pack_propagate(False)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(15, 0))

        # --- Left Panel Content ---
        # 1. Output Card
        output_card = tk.Frame(left_panel, bg=COLOR_CARD, bd=1, highlightbackground=COLOR_BORDER, highlightthickness=1, pady=18, padx=20)
        output_card.pack(fill=tk.X, pady=(0, 15))

        # Password Display (Entry)
        self.pwd_entry = tk.Entry(output_card, textvariable=self.generated_password, 
                                  font=("Consolas", 18, "bold"), bg=COLOR_BG, fg=COLOR_TEXT_PRIMARY, 
                                  bd=0, highlightthickness=1, highlightbackground=COLOR_BORDER,
                                  insertbackground=COLOR_TEXT_PRIMARY, selectbackground=COLOR_ACCENT)
        self.pwd_entry.pack(fill=tk.X, ipady=8, pady=(0, 10))

        # Strength Bar Canvas
        self.strength_canvas = tk.Canvas(output_card, height=6, bg=COLOR_BG, bd=0, highlightthickness=0)
        self.strength_canvas.pack(fill=tk.X, pady=(0, 8))
        self.update_strength_bar(0) # start empty

        # Action Info Frame (Strength Label & Copy Notification)
        action_info_frame = tk.Frame(output_card, bg=COLOR_CARD)
        action_info_frame.pack(fill=tk.X, pady=(0, 10))

        self.lbl_strength = tk.Label(action_info_frame, textvariable=self.strength_text, 
                                     font=("Segoe UI", 9, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED)
        self.lbl_strength.pack(side=tk.LEFT)

        self.lbl_copied_feedback = tk.Label(action_info_frame, text="", 
                                            font=("Segoe UI", 9, "bold"), bg=COLOR_CARD, fg=COLOR_STRENGTH_GOOD)
        self.lbl_copied_feedback.pack(side=tk.RIGHT)

        # Actions buttons
        actions_btn_frame = tk.Frame(output_card, bg=COLOR_CARD)
        actions_btn_frame.pack(fill=tk.X)

        self.btn_generate = tk.Button(actions_btn_frame, text="Generate Password", 
                                      font=("Segoe UI", 10, "bold"), bg=COLOR_ACCENT, fg=COLOR_TEXT_PRIMARY,
                                      activebackground=COLOR_ACCENT_HOVER, activeforeground=COLOR_TEXT_PRIMARY,
                                      bd=0, cursor="hand2", command=self.generate_password, height=2)
        self.btn_generate.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.btn_copy = tk.Button(actions_btn_frame, text="Copy to Clipboard", 
                                  font=("Segoe UI", 10, "bold"), bg=COLOR_BG, fg=COLOR_TEXT_PRIMARY,
                                  activebackground=COLOR_BORDER, activeforeground=COLOR_TEXT_PRIMARY,
                                  bd=1, highlightbackground=COLOR_BORDER, highlightthickness=1, 
                                  cursor="hand2", command=self.copy_password, height=2)
        self.btn_copy.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

        # Add hover binds for flat buttons
        self.btn_generate.bind("<Enter>", lambda e: self.btn_generate.config(bg=COLOR_ACCENT_HOVER))
        self.btn_generate.bind("<Leave>", lambda e: self.btn_generate.config(bg=COLOR_ACCENT))
        self.btn_copy.bind("<Enter>", lambda e: self.btn_copy.config(bg=COLOR_BORDER))
        self.btn_copy.bind("<Leave>", lambda e: self.btn_copy.config(bg=COLOR_BG))

        # 2. Settings Card
        settings_card = tk.Frame(left_panel, bg=COLOR_CARD, bd=1, highlightbackground=COLOR_BORDER, highlightthickness=1, pady=18, padx=20)
        settings_card.pack(fill=tk.BOTH, expand=True)

        tk.Label(settings_card, text="Password Parameters", font=("Segoe UI", 11, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY).pack(anchor=tk.W, pady=(0, 15))

        # Length Slider & Entry
        len_frame = tk.Frame(settings_card, bg=COLOR_CARD)
        len_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(len_frame, text="Password Length:", font=("Segoe UI", 10), bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY).pack(side=tk.LEFT)
        
        self.lbl_len_val = tk.Label(len_frame, text="16", font=("Segoe UI", 10, "bold"), bg=COLOR_CARD, fg=COLOR_ACCENT)
        self.lbl_len_val.pack(side=tk.RIGHT, padx=(5, 0))

        # Sync value logic
        def on_slider_move(val):
            rounded = int(float(val))
            self.password_len.set(rounded)
            self.lbl_len_val.config(text=str(rounded))
            self.generate_password()

        self.slider_len = ttk.Scale(settings_card, from_=4, to=64, variable=self.password_len, command=on_slider_move)
        self.slider_len.pack(fill=tk.X, pady=(0, 20))

        # Character Checkboxes (Grid layout inside a frame)
        chk_frame = tk.Frame(settings_card, bg=COLOR_CARD)
        chk_frame.pack(fill=tk.X, pady=(0, 15))
        chk_frame.columnconfigure(0, weight=1)
        chk_frame.columnconfigure(1, weight=1)

        c1 = ttk.Checkbutton(chk_frame, text="Uppercase (A-Z)", variable=self.use_upper, style='Custom.TCheckbutton', command=self.generate_password)
        c1.grid(row=0, column=0, sticky=tk.W, pady=8)

        c2 = ttk.Checkbutton(chk_frame, text="Lowercase (a-z)", variable=self.use_lower, style='Custom.TCheckbutton', command=self.generate_password)
        c2.grid(row=0, column=1, sticky=tk.W, pady=8)

        c3 = ttk.Checkbutton(chk_frame, text="Numbers (0-9)", variable=self.use_digits, style='Custom.TCheckbutton', command=self.generate_password)
        c3.grid(row=1, column=0, sticky=tk.W, pady=8)

        c4 = ttk.Checkbutton(chk_frame, text="Symbols (!@#$)", variable=self.use_symbols, style='Custom.TCheckbutton', command=self.generate_password)
        c4.grid(row=1, column=1, sticky=tk.W, pady=8)

        # Enforce all categories rule
        c5 = ttk.Checkbutton(settings_card, text="Include at least one character from each selected set", 
                             variable=self.enforce_all, style='Custom.TCheckbutton', command=self.generate_password)
        c5.pack(anchor=tk.W, pady=(5, 15))

        # Exclusion Frame
        excl_frame = tk.Frame(settings_card, bg=COLOR_CARD)
        excl_frame.pack(fill=tk.X, pady=(5, 0))

        tk.Label(excl_frame, text="Exclude Characters:", font=("Segoe UI", 9), bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY).pack(side=tk.LEFT)
        
        # Track exclusions
        def on_excl_change(*args):
            self.generate_password()
        self.exclude_chars.trace_add("write", on_excl_change)

        self.excl_entry = tk.Entry(excl_frame, textvariable=self.exclude_chars, 
                                   font=("Consolas", 10), bg=COLOR_BG, fg=COLOR_TEXT_PRIMARY,
                                   bd=0, highlightthickness=1, highlightbackground=COLOR_BORDER,
                                   insertbackground=COLOR_TEXT_PRIMARY)
        self.excl_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0), ipady=3)

        # --- Right Panel (History Log) Content ---
        history_header = tk.Frame(self.right_panel, bg=COLOR_CARD, bd=0, pady=12, padx=15)
        history_header.pack(fill=tk.X)
        
        tk.Label(history_header, text="Password History", font=("Segoe UI", 11, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY).pack(side=tk.LEFT)
        
        self.btn_clear_hist = tk.Button(history_header, text="Clear", font=("Segoe UI", 8, "bold"), bg=COLOR_BG, fg=COLOR_TEXT_MUTED,
                                        activebackground=COLOR_BORDER, activeforeground=COLOR_TEXT_PRIMARY,
                                        bd=0, cursor="hand2", command=self.clear_history, padx=8, pady=2)
        self.btn_clear_hist.pack(side=tk.RIGHT)
        self.btn_clear_hist.bind("<Enter>", lambda e: self.btn_clear_hist.config(bg=COLOR_BORDER, fg=COLOR_TEXT_PRIMARY))
        self.btn_clear_hist.bind("<Leave>", lambda e: self.btn_clear_hist.config(bg=COLOR_BG, fg=COLOR_TEXT_MUTED))

        # Divider
        divider = tk.Frame(self.right_panel, bg=COLOR_BORDER, height=1)
        divider.pack(fill=tk.X)

        # Scrollable History List
        self.history_canvas = tk.Canvas(self.right_panel, bg=COLOR_CARD, bd=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.right_panel, orient="vertical", command=self.history_canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.history_canvas, bg=COLOR_CARD)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.history_canvas.configure(
                scrollregion=self.history_canvas.bbox("all")
            )
        )

        self.history_canvas_window = self.history_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configure canvas to stretch window horizontally
        self.history_canvas.bind('<Configure>', lambda e: self.history_canvas.itemconfigure(self.history_canvas_window, width=e.width))

        self.history_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.history_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.update_history_ui()

    def draw_shield_icon(self):
        # Draw a beautiful vector shield outline with padlock details inside
        canvas = self.icon_canvas
        canvas.delete("all")
        
        # Background dark rounded shield shape
        canvas.create_polygon(22, 4, 38, 10, 38, 26, 22, 40, 6, 26, 6, 10, fill=COLOR_CARD, outline=COLOR_ACCENT, width=2)
        
        # Inner padlock shape
        # loop / shackle
        canvas.create_arc(17, 16, 27, 26, start=0, extent=180, outline=COLOR_TEXT_PRIMARY, width=2, style=tk.ARC)
        # lock body
        canvas.create_rectangle(14, 23, 30, 31, fill=COLOR_ACCENT, outline=COLOR_ACCENT, width=0)
        # keyhole dot
        canvas.create_oval(21, 25, 23, 27, fill=COLOR_TEXT_PRIMARY)

    def update_strength_bar(self, percentage, color=COLOR_TEXT_MUTED):
        # Redraw the custom progress bar in the strength canvas
        canvas = self.strength_canvas
        canvas.delete("all")
        
        width = canvas.winfo_width()
        if width <= 1:
            width = 300 # Fallback width before canvas is mapped to screen
            
        # Draw background track
        canvas.create_rectangle(0, 0, width, 6, fill=COLOR_BG, outline="", width=0)
        
        # Draw filled bar
        fill_width = int(width * (percentage / 100))
        if fill_width > 0:
            canvas.create_rectangle(0, 0, fill_width, 6, fill=color, outline="", width=0)

    def calculate_entropy(self, pwd):
        if not pwd:
            return 0
            
        # Determine pool size
        pool = 0
        if any(c in string.ascii_lowercase for c in pwd):
            pool += 26
        if any(c in string.ascii_uppercase for c in pwd):
            pool += 26
        if any(c in string.digits for c in pwd):
            pool += 10
        symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if any(c in symbols for c in pwd):
            pool += len(symbols)
            
        import math
        return len(pwd) * math.log2(pool) if pool > 0 else 0

    def evaluate_strength(self, pwd):
        if not pwd:
            self.strength_text.set("Select options to generate password")
            self.strength_color = COLOR_TEXT_MUTED
            self.update_strength_bar(0, COLOR_TEXT_MUTED)
            return

        entropy = self.calculate_entropy(pwd)
        length = len(pwd)
        
        if entropy < 40 or length < 6:
            level = "WEAK (Not Secure)"
            pct = 25
            color = COLOR_STRENGTH_WEAK
            tip = " - Tips: Add more characters and numbers."
        elif entropy < 60 or length < 10:
            level = "FAIR (Medium Complexity)"
            pct = 50
            color = COLOR_STRENGTH_FAIR
            tip = " - Tips: Use a mix of uppercase and symbols."
        elif entropy < 85 or length < 14:
            level = "STRONG (High Security)"
            pct = 75
            color = COLOR_STRENGTH_GOOD
            tip = " - Recommended security level."
        else:
            level = "VERY STRONG (Military Grade)"
            pct = 100
            color = COLOR_STRENGTH_EXCELLENT
            tip = " - Excellent cryptographically secure password."

        self.strength_text.set(f"{level} ({int(entropy)} bits entropy){tip if pct < 75 else ''}")
        self.strength_color = color
        self.lbl_strength.config(fg=color)
        
        self.root.update_idletasks()
        self.update_strength_bar(pct, color)

    def generate_password(self):
        length = self.password_len.get()
        exclusions = self.exclude_chars.get()

        upper_pool = [c for c in string.ascii_uppercase if c not in exclusions]
        lower_pool = [c for c in string.ascii_lowercase if c not in exclusions]
        digit_pool = [c for c in string.digits if c not in exclusions]
        
        symbols_list = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        symbol_pool = [c for c in symbols_list if c not in exclusions]

        active_pools = []
        if self.use_upper.get() and upper_pool:
            active_pools.append(upper_pool)
        if self.use_lower.get() and lower_pool:
            active_pools.append(lower_pool)
        if self.use_digits.get() and digit_pool:
            active_pools.append(digit_pool)
        if self.use_symbols.get() and symbol_pool:
            active_pools.append(symbol_pool)

        if not active_pools:
            self.generated_password.set("")
            self.evaluate_strength("")
            return

        combined_pool = [char for pool in active_pools for char in pool]
        
        if not combined_pool:
            self.generated_password.set("")
            self.evaluate_strength("")
            return

        password_chars = []
        
        if self.enforce_all.get() and length >= len(active_pools):
            for pool in active_pools:
                password_chars.append(secrets.choice(pool))
            
            remaining = length - len(active_pools)
            for _ in range(remaining):
                password_chars.append(secrets.choice(combined_pool))
            
            secrets.SystemRandom().shuffle(password_chars)
        else:
            for _ in range(length):
                password_chars.append(secrets.choice(combined_pool))

        pwd = "".join(password_chars)
        self.generated_password.set(pwd)
        self.evaluate_strength(pwd)

    def copy_password(self):
        pwd = self.generated_password.get()
        if not pwd:
            return
            
        self.root.clipboard_clear()
        self.root.clipboard_append(pwd)
        self.root.update()

        self.lbl_copied_feedback.config(text="✓ Copied to clipboard!")
        self.root.after(2000, lambda: self.lbl_copied_feedback.config(text=""))
        
        self.add_to_history(pwd)

    def add_to_history(self, pwd):
        if self.history and self.history[0]["password"] == pwd:
            return

        timestamp = time.strftime("%H:%M:%S")
        self.history.insert(0, {"password": pwd, "timestamp": timestamp, "masked": True})
        
        if len(self.history) > 10:
            self.history.pop()
            
        self.update_history_ui()

    def clear_history(self):
        self.history.clear()
        self.update_history_ui()

    def toggle_history_mask(self, index):
        if 0 <= index < len(self.history):
            self.history[index]["masked"] = not self.history[index]["masked"]
            self.update_history_ui()

    def copy_history_item(self, index):
        if 0 <= index < len(self.history):
            pwd = self.history[index]["password"]
            self.root.clipboard_clear()
            self.root.clipboard_append(pwd)
            self.root.update()
            
            self.lbl_copied_feedback.config(text="✓ Copied item from history!")
            self.root.after(2000, lambda: self.lbl_copied_feedback.config(text=""))

    def update_history_ui(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not self.history:
            lbl_empty = tk.Label(self.scrollable_frame, text="No passwords generated yet.\nGenerate and copy to see log.", 
                                 font=("Segoe UI", 9, "italic"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED, pady=40)
            lbl_empty.pack(fill=tk.X, expand=True)
            return

        for idx, item in enumerate(self.history):
            item_frame = tk.Frame(self.scrollable_frame, bg=COLOR_CARD, pady=6, bd=0)
            item_frame.pack(fill=tk.X, pady=(0, 6))

            card_body = tk.Frame(item_frame, bg=COLOR_BG, bd=1, highlightbackground=COLOR_BORDER, highlightthickness=1, padx=8, pady=6)
            card_body.pack(fill=tk.X)

            info_frame = tk.Frame(card_body, bg=COLOR_BG)
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            lbl_time = tk.Label(info_frame, text=item["timestamp"], font=("Segoe UI", 7), bg=COLOR_BG, fg=COLOR_TEXT_MUTED)
            lbl_time.pack(anchor=tk.W)

            display_text = "•" * len(item["password"]) if item["masked"] else item["password"]
            if not item["masked"] and len(display_text) > 18:
                display_text = display_text[:16] + "..."

            lbl_pwd = tk.Label(info_frame, text=display_text, font=("Consolas", 10, "bold"), bg=COLOR_BG, fg=COLOR_TEXT_PRIMARY)
            lbl_pwd.pack(anchor=tk.W, pady=(2, 0))

            btn_frame = tk.Frame(card_body, bg=COLOR_BG)
            btn_frame.pack(side=tk.RIGHT)

            eye_text = "👁" if item["masked"] else "🔒"
            btn_mask = tk.Button(btn_frame, text=eye_text, font=("Segoe UI", 8), bg=COLOR_BG, fg=COLOR_TEXT_MUTED,
                                 activebackground=COLOR_BORDER, activeforeground=COLOR_TEXT_PRIMARY,
                                 bd=0, cursor="hand2", width=3, command=lambda i=idx: self.toggle_history_mask(i))
            btn_mask.pack(side=tk.LEFT, padx=2)

            btn_copy_item = tk.Button(btn_frame, text="📋", font=("Segoe UI", 8), bg=COLOR_BG, fg=COLOR_TEXT_MUTED,
                                      activebackground=COLOR_BORDER, activeforeground=COLOR_TEXT_PRIMARY,
                                      bd=0, cursor="hand2", width=3, command=lambda i=idx: self.copy_history_item(i))
            btn_copy_item.pack(side=tk.RIGHT, padx=2)
            
            btn_mask.bind("<Enter>", lambda e, b=btn_mask: b.config(bg=COLOR_BORDER, fg=COLOR_TEXT_PRIMARY))
            btn_mask.bind("<Leave>", lambda e, b=btn_mask: b.config(bg=COLOR_BG, fg=COLOR_TEXT_MUTED))
            btn_copy_item.bind("<Enter>", lambda e, b=btn_copy_item: b.config(bg=COLOR_BORDER, fg=COLOR_TEXT_PRIMARY))
            btn_copy_item.bind("<Leave>", lambda e, b=btn_copy_item: b.config(bg=COLOR_BG, fg=COLOR_TEXT_MUTED))

        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))

if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordGeneratorApp(root)
    root.mainloop()
