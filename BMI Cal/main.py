import os
import json
import math
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

# --- Constants & Colors ---
FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_SUBTITLE = ("Segoe UI", 9)
FONT_BODY = ("Segoe UI", 10)
FONT_HEADING = ("Segoe UI", 11, "bold")
FONT_LABEL = ("Segoe UI", 9, "bold")
FONT_VALUE = ("Segoe UI", 18, "bold")

COLOR_BG = "#090d16"          # Deep dark blue
COLOR_CARD = "#111827"        # Dark gray-blue card
COLOR_CARD_HOVER = "#172135"  # Slightly lighter card hover
COLOR_BORDER = "#1f2937"      # Dark border
COLOR_BORDER_LIGHT = "#374151"# Light border
COLOR_TEXT = "#f3f4f6"        # Light gray text
COLOR_TEXT_MUTED = "#9ca3af"  # Dark gray text
COLOR_ACCENT = "#8b5cf6"      # Purple accent
COLOR_ACCENT_HOVER = "#7c3aed"# Purple accent hover
COLOR_ACCENT_SOFT = "#2d1b4e" # Soft purple background

COLOR_UNDERWEIGHT = "#3b82f6" # Blue
COLOR_NORMAL = "#10b981"      # Green
COLOR_OVERWEIGHT = "#f59e0b"  # Orange
COLOR_OBESE = "#ef4444"       # Red

# Dark theme zone background colors for Nomogram
COLOR_ZONE_UNDER = "#172554"  # Very dark blue
COLOR_ZONE_NORMAL = "#022c22" # Very dark green
COLOR_ZONE_OVER = "#451a03"   # Very dark orange/brown
COLOR_ZONE_OBESE = "#450a0a"  # Very dark red

# --- Helper Conversion Functions ---
def cm_to_ft_in(cm):
    inches = cm / 2.54
    ft = int(inches // 12)
    inc = int(round(inches % 12))
    return ft, 0 if inc == 12 else inc

def ft_in_to_cm(ft, inches):
    return (ft * 12 + inches) * 2.54

def kg_to_lb(kg):
    return kg * 2.20462

def lb_to_kg(lb):
    return lb / 2.20462

# --- Custom Scrollable Frame for Insights ---
class ScrollableFrame(tk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, bg=COLOR_CARD, bd=0, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLOR_CARD)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Mousewheel scroll support
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        # Only scroll if canvas is visible and active
        if self.canvas.winfo_exists():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

# --- Main Application Class ---
class FitScaleApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("FitScale™ - Premium BMI & Health Dashboard")
        self.geometry("1180x800")
        self.minsize(1050, 750)
        self.configure(bg=COLOR_BG)

        # Application State
        self.current_unit = "metric" # 'metric' or 'imperial'
        self.gender = tk.StringVar(value="male")
        self.height_cm = 175
        self.weight_kg = 70.0
        self.age = 28
        self.activity_factor = 1.375
        self.target_weight_kg = None # Store target weight in kg
        self.logs = []
        
        # Load logs from file
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bmi_history.json")
        self.load_history()

        # Styles Initialization
        self.setup_styles()

        # UI Layout Construction
        self.build_ui()
        
        # Populate with initial calculation
        self.recalculate()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure standard widgets styling
        style.configure(".", bg=COLOR_BG, foreground=COLOR_TEXT, fieldbackground=COLOR_CARD)
        
        # TFrame (Card)
        style.configure("Card.TFrame", background=COLOR_CARD, borderwidth=1, relief="flat")
        
        # Labels
        style.configure("TLabel", background=COLOR_CARD, foreground=COLOR_TEXT, font=FONT_BODY)
        style.configure("Muted.TLabel", background=COLOR_CARD, foreground=COLOR_TEXT_MUTED, font=FONT_SUBTITLE)
        style.configure("CardTitle.TLabel", background=COLOR_CARD, foreground=COLOR_TEXT, font=FONT_HEADING)
        
        # Entry
        style.configure("TEntry", background=COLOR_CARD, foreground=COLOR_TEXT, borderwidth=1, relief="flat", insertcolor=COLOR_TEXT)
        style.map("TEntry", fieldbackground=[("focus", COLOR_CARD_HOVER)], bordercolor=[("focus", COLOR_ACCENT)])

        # Combobox
        style.configure("TCombobox", background=COLOR_CARD, foreground=COLOR_TEXT, fieldbackground=COLOR_CARD, borderwidth=1, arrowcolor=COLOR_TEXT)
        style.map("TCombobox", fieldbackground=[("readonly", COLOR_CARD)], selectbackground=[("readonly", COLOR_ACCENT)])

        # Treeview (Table)
        style.configure("Treeview", background=COLOR_CARD, foreground=COLOR_TEXT, fieldbackground=COLOR_CARD, borderwidth=0, font=FONT_SUBTITLE, rowheight=26)
        style.configure("Treeview.Heading", background=COLOR_BG, foreground=COLOR_TEXT_MUTED, font=FONT_LABEL, relief="flat")
        style.map("Treeview", background=[("selected", COLOR_ACCENT)], foreground=[("selected", "#ffffff")])
        style.map("Treeview.Heading", background=[("active", COLOR_CARD_HOVER)], foreground=[("active", COLOR_TEXT)])

    def build_ui(self):
        # Outer grid layout
        self.grid_columnconfigure(0, weight=4) # Left Panel (inputs)
        self.grid_columnconfigure(1, weight=6) # Right Panel (outputs/logs)
        self.grid_rowconfigure(0, weight=1)

        # --- LEFT SIDE: INPUT CONTROLS ---
        left_panel = tk.Frame(self, bg=COLOR_BG, padx=15, pady=15)
        left_panel.grid(row=0, column=0, sticky="nsew")
        left_panel.grid_columnconfigure(0, weight=1)
        left_panel.grid_rowconfigure(1, weight=1)

        # Header Logo Frame
        logo_frame = tk.Frame(left_panel, bg=COLOR_BG)
        logo_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        lbl_logo = tk.Label(logo_frame, text="FitScale", font=("Outfit", 20, "bold"), bg=COLOR_BG, fg=COLOR_TEXT)
        lbl_logo.pack(side="left")
        lbl_dot = tk.Label(logo_frame, text=".", font=("Outfit", 20, "bold"), bg=COLOR_BG, fg=COLOR_ACCENT)
        lbl_dot.pack(side="left")
        lbl_sub = tk.Label(logo_frame, text=" | Desktop Health Assistant", font=FONT_SUBTITLE, bg=COLOR_BG, fg=COLOR_TEXT_MUTED)
        lbl_sub.pack(side="left", padx=5, pady=(8, 0))

        # Calculator Container Card
        calc_card = ttk.Frame(left_panel, style="Card.TFrame")
        calc_card.grid(row=1, column=0, sticky="nsew")
        calc_card.grid_columnconfigure(0, weight=1)
        calc_card.grid_rowconfigure(1, weight=1)

        # Tab selector for Units
        tabs_frame = tk.Frame(calc_card, bg=COLOR_CARD)
        tabs_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        
        self.btn_metric_tab = tk.Button(tabs_frame, text="Metric (cm/kg)", font=FONT_LABEL, bg=COLOR_ACCENT, fg="white", bd=0, activebackground=COLOR_ACCENT_HOVER, activeforeground="white", cursor="hand2", padx=15, pady=6, command=lambda: self.switch_units("metric"))
        self.btn_metric_tab.pack(side="left", fill="x", expand=True)

        self.btn_imperial_tab = tk.Button(tabs_frame, text="Imperial (in/lb)", font=FONT_LABEL, bg=COLOR_BG, fg=COLOR_TEXT_MUTED, bd=0, activebackground=COLOR_CARD_HOVER, activeforeground=COLOR_TEXT, cursor="hand2", padx=15, pady=6, command=lambda: self.switch_units("imperial"))
        self.btn_imperial_tab.pack(side="left", fill="x", expand=True)

        # Inputs Scrollable Inner Frame
        scroll_inputs = ScrollableFrame(calc_card)
        scroll_inputs.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        inputs_frame = scroll_inputs.scrollable_frame

        # Gender Selector
        lbl_gender = ttk.Label(inputs_frame, text="Gender", font=FONT_LABEL)
        lbl_gender.pack(anchor="w", pady=(5, 5))
        
        gender_sel_frame = tk.Frame(inputs_frame, bg=COLOR_CARD)
        gender_sel_frame.pack(fill="x", pady=(0, 10))
        
        self.rb_male = tk.Radiobutton(gender_sel_frame, text="Male", variable=self.gender, value="male", bg=COLOR_CARD, fg=COLOR_TEXT, selectcolor=COLOR_BG, font=FONT_BODY, activebackground=COLOR_CARD, activeforeground=COLOR_TEXT, bd=0, command=self.recalculate)
        self.rb_male.pack(side="left", expand=True, fill="x")
        
        self.rb_female = tk.Radiobutton(gender_sel_frame, text="Female", variable=self.gender, value="female", bg=COLOR_CARD, fg=COLOR_TEXT, selectcolor=COLOR_BG, font=FONT_BODY, activebackground=COLOR_CARD, activeforeground=COLOR_TEXT, bd=0, command=self.recalculate)
        self.rb_female.pack(side="left", expand=True, fill="x")

        # --- HEIGHT WIDGETS ---
        # Metric Height
        self.f_metric_height = tk.Frame(inputs_frame, bg=COLOR_CARD)
        self.f_metric_height.pack(fill="x", pady=5)
        
        h_label_row = tk.Frame(self_f_metric_height := self.f_metric_height, bg=COLOR_CARD)
        h_label_row.pack(fill="x")
        ttk.Label(h_label_row, text="Height", font=FONT_LABEL).pack(side="left")
        self.lbl_height_badge = ttk.Label(h_label_row, text="175 cm", font=FONT_LABEL, foreground=COLOR_ACCENT)
        self.lbl_height_badge.pack(side="right")
        
        h_slider_row = tk.Frame(self_f_metric_height, bg=COLOR_CARD)
        h_slider_row.pack(fill="x", pady=5)
        self.scale_height = tk.Scale(h_slider_row, from_=100, to=250, orient="horizontal", bg=COLOR_CARD, fg=COLOR_TEXT, troughcolor=COLOR_BG, highlightthickness=0, bd=0, activebackground=COLOR_ACCENT, command=self.on_height_scale)
        self.scale_height.set(self.height_cm)
        self.scale_height.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.entry_height_cm = ttk.Entry(h_slider_row, width=6, font=FONT_BODY, justify="center")
        self.entry_height_cm.insert(0, str(self.height_cm))
        self.entry_height_cm.pack(side="right")
        self.entry_height_cm.bind("<KeyRelease>", self.on_height_entry)

        # Imperial Height (Hidden initially)
        self.f_imperial_height = tk.Frame(inputs_frame, bg=COLOR_CARD)
        
        ttk.Label(self_f_imperial_height := self.f_imperial_height, text="Height", font=FONT_LABEL).pack(anchor="w", pady=(0, 5))
        h_imp_row = tk.Frame(self_f_imperial_height, bg=COLOR_CARD)
        h_imp_row.pack(fill="x")
        
        self.entry_height_ft = ttk.Entry(h_imp_row, width=8, font=FONT_BODY, justify="center")
        self.entry_height_ft.insert(0, "5")
        self.entry_height_ft.pack(side="left", padx=(0, 5))
        ttk.Label(h_imp_row, text="ft", font=FONT_LABEL, foreground=COLOR_TEXT_MUTED).pack(side="left", padx=(0, 15))
        
        self.entry_height_in = ttk.Entry(h_imp_row, width=8, font=FONT_BODY, justify="center")
        self.entry_height_in.insert(0, "9")
        self.entry_height_in.pack(side="left", padx=(0, 5))
        ttk.Label(h_imp_row, text="in", font=FONT_LABEL, foreground=COLOR_TEXT_MUTED).pack(side="left")
        
        self.entry_height_ft.bind("<KeyRelease>", self.on_imperial_height_entry)
        self.entry_height_in.bind("<KeyRelease>", self.on_imperial_height_entry)

        # --- WEIGHT WIDGETS ---
        # Metric Weight
        self.f_metric_weight = tk.Frame(inputs_frame, bg=COLOR_CARD)
        self.f_metric_weight.pack(fill="x", pady=10)
        
        w_label_row = tk.Frame(self_f_metric_weight := self.f_metric_weight, bg=COLOR_CARD)
        w_label_row.pack(fill="x")
        ttk.Label(w_label_row, text="Weight", font=FONT_LABEL).pack(side="left")
        self.lbl_weight_badge = ttk.Label(w_label_row, text="70.0 kg", font=FONT_LABEL, foreground=COLOR_ACCENT)
        self.lbl_weight_badge.pack(side="right")
        
        w_slider_row = tk.Frame(self_f_metric_weight, bg=COLOR_CARD)
        w_slider_row.pack(fill="x", pady=5)
        self.scale_weight = tk.Scale(w_slider_row, from_=20, to=250, resolution=0.5, orient="horizontal", bg=COLOR_CARD, fg=COLOR_TEXT, troughcolor=COLOR_BG, highlightthickness=0, bd=0, activebackground=COLOR_ACCENT, command=self.on_weight_scale)
        self.scale_weight.set(self.weight_kg)
        self.scale_weight.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.entry_weight_kg = ttk.Entry(w_slider_row, width=6, font=FONT_BODY, justify="center")
        self.entry_weight_kg.insert(0, str(self.weight_kg))
        self.entry_weight_kg.pack(side="right")
        self.entry_weight_kg.bind("<KeyRelease>", self.on_weight_entry)

        # Imperial Weight (Hidden initially)
        self.f_imperial_weight = tk.Frame(inputs_frame, bg=COLOR_CARD)
        
        w_imp_label_row = tk.Frame(self_f_imperial_weight := self.f_imperial_weight, bg=COLOR_CARD)
        w_imp_label_row.pack(fill="x")
        ttk.Label(w_imp_label_row, text="Weight", font=FONT_LABEL).pack(side="left")
        self.lbl_weight_lb_badge = ttk.Label(w_imp_label_row, text="154.3 lbs", font=FONT_LABEL, foreground=COLOR_ACCENT)
        self.lbl_weight_lb_badge.pack(side="right")
        
        w_imp_slider_row = tk.Frame(self_f_imperial_weight, bg=COLOR_CARD)
        w_imp_slider_row.pack(fill="x", pady=5)
        self.scale_weight_lb = tk.Scale(w_imp_slider_row, from_=40, to=550, resolution=1, orient="horizontal", bg=COLOR_CARD, fg=COLOR_TEXT, troughcolor=COLOR_BG, highlightthickness=0, bd=0, activebackground=COLOR_ACCENT, command=self.on_weight_lb_scale)
        self.scale_weight_lb.set(round(kg_to_lb(self.weight_kg)))
        self.scale_weight_lb.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.entry_weight_lb = ttk.Entry(w_imp_slider_row, width=6, font=FONT_BODY, justify="center")
        self.entry_weight_lb.insert(0, str(round(kg_to_lb(self.weight_kg), 1)))
        self.entry_weight_lb.pack(side="right")
        self.entry_weight_lb.bind("<KeyRelease>", self.on_weight_lb_entry)

        # Age & Activity Row
        age_act_frame = tk.Frame(inputs_frame, bg=COLOR_CARD)
        age_act_frame.pack(fill="x", pady=10)
        age_act_frame.grid_columnconfigure(0, weight=1)
        age_act_frame.grid_columnconfigure(1, weight=2)
        
        # Age
        age_frame = tk.Frame(age_act_frame, bg=COLOR_CARD)
        age_frame.grid(row=0, column=0, sticky="nw", padx=(0, 10))
        ttk.Label(age_frame, text="Age", font=FONT_LABEL).pack(anchor="w")
        self.entry_age = ttk.Entry(age_frame, font=FONT_BODY, justify="center", width=8)
        self.entry_age.insert(0, str(self.age))
        self.entry_age.pack(fill="x", pady=5)
        self.entry_age.bind("<KeyRelease>", self.on_age_change)

        # Activity
        act_frame = tk.Frame(age_act_frame, bg=COLOR_CARD)
        act_frame.grid(row=0, column=1, sticky="nsew")
        ttk.Label(act_frame, text="Activity Level", font=FONT_LABEL).pack(anchor="w")
        self.combo_activity = ttk.Combobox(act_frame, font=FONT_SUBTITLE, state="readonly")
        self.combo_activity["values"] = (
            "Sedentary (no exercise)", 
            "Lightly Active (1-3 days/wk)", 
            "Moderately Active (3-5 days/wk)", 
            "Very Active (6-7 days/wk)", 
            "Extra Active (hard job/training)"
        )
        self.combo_activity.current(1) # Default: Lightly Active
        self.combo_activity.pack(fill="x", pady=5)
        self.combo_activity.bind("<<ComboboxSelected>>", self.on_activity_change)

        # Target Weight
        lbl_target = ttk.Label(inputs_frame, text="Weight Goal (Optional)", font=FONT_LABEL)
        lbl_target.pack(anchor="w", pady=(10, 5))
        
        target_frame = tk.Frame(inputs_frame, bg=COLOR_CARD)
        target_frame.pack(fill="x")
        
        self.entry_target_weight = ttk.Entry(target_frame, font=FONT_BODY, justify="left", width=12)
        self.entry_target_weight.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.entry_target_weight.bind("<KeyRelease>", self.on_target_change)
        
        self.lbl_target_unit = ttk.Label(target_frame, text="kg", font=FONT_BODY)
        self.lbl_target_unit.pack(side="left", padx=5)

        self.btn_clear_target = tk.Button(target_frame, text="×", font=FONT_HEADING, bg=COLOR_BG, fg=COLOR_TEXT_MUTED, activebackground=COLOR_CARD_HOVER, activeforeground=COLOR_TEXT, bd=0, cursor="hand2", padx=10, command=self.clear_target_weight)
        self.btn_clear_target.pack(side="right")

        # Log Notes
        lbl_notes = ttk.Label(inputs_frame, text="Notes for Log Entry (Optional)", font=FONT_LABEL)
        lbl_notes.pack(anchor="w", pady=(15, 5))
        
        self.entry_notes = ttk.Entry(inputs_frame, font=FONT_BODY)
        self.entry_notes.pack(fill="x", pady=(0, 10))

        # Bottom Button Panel
        btn_panel = tk.Frame(calc_card, bg=COLOR_CARD, pady=15, padx=15)
        btn_panel.grid(row=2, column=0, sticky="ew")
        
        self.btn_calc = tk.Button(btn_panel, text="Calculate BMI", font=FONT_HEADING, bg=COLOR_ACCENT, fg="white", activebackground=COLOR_ACCENT_HOVER, activeforeground="white", bd=0, cursor="hand2", pady=8, command=self.recalculate)
        self.btn_calc.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_save = tk.Button(btn_panel, text="Save to Log", font=FONT_HEADING, bg=COLOR_BG, fg=COLOR_TEXT, activebackground=COLOR_CARD_HOVER, activeforeground="white", bd=0, cursor="hand2", pady=8, command=self.save_log_entry)
        self.btn_save.pack(side="right", fill="x", expand=True)

        # --- RIGHT SIDE: RESULTS, CHARTS, LOGS ---
        right_panel = tk.Frame(self, bg=COLOR_BG, padx=15, pady=15)
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(0, weight=3)  # Top Results section
        right_panel.grid_rowconfigure(1, weight=4)  # Middle Charts section
        right_panel.grid_rowconfigure(2, weight=3)  # Bottom logs and insights section

        # --- SECTION 1: HEALTH STATUS (TOP) ---
        top_results = ttk.Frame(right_panel, style="Card.TFrame")
        top_results.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        top_results.grid_columnconfigure(0, weight=4)  # Gauge Canvas
        top_results.grid_columnconfigure(1, weight=6)  # Stats mini grid
        top_results.grid_rowconfigure(0, weight=1)

        # Gauge Chart Drawing area
        self.canvas_gauge = tk.Canvas(top_results, bg=COLOR_CARD, highlightthickness=0, bd=0)
        self.canvas_gauge.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.canvas_gauge.bind("<Configure>", lambda e: self.draw_gauge())

        # Mini Cards grid container
        mini_grid_frame = tk.Frame(top_results, bg=COLOR_CARD)
        mini_grid_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 15), pady=15)
        mini_grid_frame.grid_columnconfigure(0, weight=1)
        mini_grid_frame.grid_columnconfigure(1, weight=1)
        mini_grid_frame.grid_rowconfigure(0, weight=1)
        mini_grid_frame.grid_rowconfigure(1, weight=1)

        # Card 1: Goal Target Weight Status
        card_target = tk.Frame(mini_grid_frame, bg=COLOR_BG, highlightbackground=COLOR_BORDER, highlightthickness=1)
        card_target.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        tk.Label(card_target, text="WEIGHT GOAL", font=FONT_LABEL, bg=COLOR_BG, fg=COLOR_TEXT_MUTED).pack(anchor="w", padx=8, pady=(8, 2))
        self.lbl_target_status = tk.Label(card_target, text="- -", font=FONT_HEADING, bg=COLOR_BG, fg=COLOR_TEXT)
        self.lbl_target_status.pack(anchor="w", padx=8)
        self.lbl_target_sub = tk.Label(card_target, text="Set a weight goal", font=FONT_SUBTITLE, bg=COLOR_BG, fg=COLOR_TEXT_MUTED)
        self.lbl_target_sub.pack(anchor="w", padx=8, pady=(2, 8))

        # Card 2: Ideal Range
        card_ideal = tk.Frame(mini_grid_frame, bg=COLOR_BG, highlightbackground=COLOR_BORDER, highlightthickness=1)
        card_ideal.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        tk.Label(card_ideal, text="IDEAL WEIGHT RANGE", font=FONT_LABEL, bg=COLOR_BG, fg=COLOR_NORMAL).pack(anchor="w", padx=8, pady=(8, 2))
        self.lbl_ideal_range = tk.Label(card_ideal, text="56.7 - 76.3 kg", font=FONT_HEADING, bg=COLOR_BG, fg=COLOR_TEXT)
        self.lbl_ideal_range.pack(anchor="w", padx=8)
        self.lbl_ideal_height = tk.Label(card_ideal, text="For Height: 175 cm", font=FONT_SUBTITLE, bg=COLOR_BG, fg=COLOR_TEXT_MUTED)
        self.lbl_ideal_height.pack(anchor="w", padx=8, pady=(2, 8))

        # Card 3: BMR
        card_bmr = tk.Frame(mini_grid_frame, bg=COLOR_BG, highlightbackground=COLOR_BORDER, highlightthickness=1)
        card_bmr.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        tk.Label(card_bmr, text="BMR (RESTING ENERGY)", font=FONT_LABEL, bg=COLOR_BG, fg=COLOR_OVERWEIGHT).pack(anchor="w", padx=8, pady=(8, 2))
        self.lbl_bmr_val = tk.Label(card_bmr, text="1,624 kcal", font=FONT_HEADING, bg=COLOR_BG, fg=COLOR_TEXT)
        self.lbl_bmr_val.pack(anchor="w", padx=8)
        tk.Label(card_bmr, text="Calories burned resting daily", font=FONT_SUBTITLE, bg=COLOR_BG, fg=COLOR_TEXT_MUTED).pack(anchor="w", padx=8, pady=(2, 8))

        # Card 4: TDEE
        card_tdee = tk.Frame(mini_grid_frame, bg=COLOR_BG, highlightbackground=COLOR_BORDER, highlightthickness=1)
        card_tdee.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        tk.Label(card_tdee, text="TDEE (MAINTENANCE)", font=FONT_LABEL, bg=COLOR_BG, fg=COLOR_OBESE).pack(anchor="w", padx=8, pady=(8, 2))
        self.lbl_tdee_val = tk.Label(card_tdee, text="2,233 kcal", font=FONT_HEADING, bg=COLOR_BG, fg=COLOR_TEXT)
        self.lbl_tdee_val.pack(anchor="w", padx=8)
        tk.Label(card_tdee, text="Calories to maintain weight", font=FONT_SUBTITLE, bg=COLOR_BG, fg=COLOR_TEXT_MUTED).pack(anchor="w", padx=8, pady=(2, 8))

        # --- SECTION 2: CHARTS TAB PANEL (MIDDLE) ---
        charts_card = ttk.Frame(right_panel, style="Card.TFrame")
        charts_card.grid(row=1, column=0, sticky="nsew", pady=10)
        charts_card.grid_columnconfigure(0, weight=1)
        charts_card.grid_rowconfigure(1, weight=1)

        # Tab Header for Charts
        chart_header = tk.Frame(charts_card, bg=COLOR_CARD)
        chart_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 5))
        tk.Label(chart_header, text="Interactive Charts", font=FONT_HEADING, bg=COLOR_CARD, fg=COLOR_TEXT).pack(side="left")
        
        self.chart_view_mode = "nomogram" # 'nomogram' or 'trend'
        self.btn_trend_chart_tab = tk.Button(chart_header, text="Weight History", font=FONT_LABEL, bg=COLOR_BG, fg=COLOR_TEXT_MUTED, bd=0, cursor="hand2", padx=10, pady=4, command=lambda: self.switch_chart_view("trend"))
        self.btn_trend_chart_tab.pack(side="right")
        
        self.btn_nomo_chart_tab = tk.Button(chart_header, text="BMI Zone Map", font=FONT_LABEL, bg=COLOR_ACCENT, fg="white", bd=0, cursor="hand2", padx=10, pady=4, command=lambda: self.switch_chart_view("nomogram"))
        self.btn_nomo_chart_tab.pack(side="right", padx=5)

        # Chart Drawings Canvas Widgets
        self.chart_container = tk.Frame(charts_card, bg=COLOR_CARD)
        self.chart_container.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 10))
        self.chart_container.grid_columnconfigure(0, weight=1)
        self.chart_container.grid_rowconfigure(0, weight=1)

        # Nomogram Canvas
        self.canvas_nomo = tk.Canvas(self.chart_container, bg=COLOR_CARD, highlightthickness=0, bd=0)
        self.canvas_nomo.grid(row=0, column=0, sticky="nsew")
        self.canvas_nomo.bind("<Configure>", lambda e: self.draw_nomogram())

        # Trend Canvas (Hidden initially)
        self.canvas_trend = tk.Canvas(self.chart_container, bg=COLOR_CARD, highlightthickness=0, bd=0)
        self.canvas_trend.bind("<Configure>", lambda e: self.draw_trend_chart())

        # --- SECTION 3: INSIGHTS & HISTORY LOG (BOTTOM) ---
        bottom_tabs_frame = tk.Frame(right_panel, bg=COLOR_BG)
        bottom_tabs_frame.grid(row=2, column=0, sticky="nsew")
        bottom_tabs_frame.grid_columnconfigure(0, weight=1)
        bottom_tabs_frame.grid_rowconfigure(0, weight=1)

        # Styled Frame combining Health insights and table log side by side
        bottom_split = tk.Frame(bottom_tabs_frame, bg=COLOR_BG)
        bottom_split.grid(row=0, column=0, sticky="nsew")
        bottom_split.grid_columnconfigure(0, weight=4) # Insights Box
        bottom_split.grid_columnconfigure(1, weight=6) # History list
        bottom_split.grid_rowconfigure(0, weight=1)

        # Card A: Insights
        insights_card = ttk.Frame(bottom_split, style="Card.TFrame")
        insights_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        insights_card.grid_columnconfigure(0, weight=1)
        insights_card.grid_rowconfigure(1, weight=1)

        tk.Label(insights_card, text="Health Insights Plan", font=FONT_HEADING, bg=COLOR_CARD, fg=COLOR_TEXT).grid(row=0, column=0, sticky="w", padx=15, pady=(12, 5))
        
        # Scrollable area inside Insights card
        self.scroll_insights = ScrollableFrame(insights_card)
        self.scroll_insights.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 10))
        self.insights_body = self.scroll_insights.scrollable_frame

        # Card B: History List
        history_card = ttk.Frame(bottom_split, style="Card.TFrame")
        history_card.grid(row=0, column=1, sticky="nsew")
        history_card.grid_columnconfigure(0, weight=1)
        history_card.grid_rowconfigure(1, weight=1)

        history_head_frame = tk.Frame(history_card, bg=COLOR_CARD)
        history_head_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 5))
        tk.Label(history_head_frame, text="Log History", font=FONT_HEADING, bg=COLOR_CARD, fg=COLOR_TEXT).pack(side="left")
        
        # Clear logs button
        self.btn_clear_history = tk.Button(history_head_frame, text="Clear Logs", font=FONT_SUBTITLE, bg="#450a0a", fg=COLOR_OBESE, activebackground=COLOR_OBESE, activeforeground="white", bd=0, cursor="hand2", padx=8, pady=2, command=self.clear_all_history)
        self.btn_clear_history.pack(side="right")

        # Treeview (Table) setup
        table_frame = tk.Frame(history_card, bg=COLOR_CARD)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 12))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = ("date", "height", "weight", "bmi", "category", "notes")
        self.table = ttk.Treeview(table_frame, columns=columns, show="headings", style="Treeview")
        self.table.grid(row=0, column=0, sticky="nsew")
        
        # Set column widths and alignments
        self.table.heading("date", text="Date")
        self.table.column("date", width=95, anchor="center")
        
        self.table.heading("height", text="Height")
        self.table.column("height", width=65, anchor="center")
        
        self.table.heading("weight", text="Weight")
        self.table.column("weight", width=70, anchor="center")
        
        self.table.heading("bmi", text="BMI")
        self.table.column("bmi", width=50, anchor="center")
        
        self.table.heading("category", text="Category")
        self.table.column("category", width=80, anchor="center")
        
        self.table.heading("notes", text="Notes")
        self.table.column("notes", width=120, anchor="w")

        # Table scrollbar
        table_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        table_scroll.grid(row=0, column=1, sticky="ns")
        self.table.configure(yscrollcommand=table_scroll.set)

    # --- UI Interactions & Callbacks ---
    def switch_units(self, unit):
        if self.current_unit == unit:
            return
        
        self.current_unit = unit
        
        if unit == "metric":
            self.btn_metric_tab.configure(bg=COLOR_ACCENT, fg="white")
            self.btn_imperial_tab.configure(bg=COLOR_BG, fg=COLOR_TEXT_MUTED)
            self.f_metric_height.pack(fill="x", pady=5)
            self.f_imperial_height.pack_forget()
            self.f_metric_weight.pack(fill="x", pady=10)
            self.f_imperial_weight.pack_forget()
            self.lbl_target_unit.configure(text="kg")
            if self.target_weight_kg:
                self.entry_target_weight.delete(0, tk.END)
                self.entry_target_weight.insert(0, f"{self.target_weight_kg:.1f}")
        else:
            self.btn_metric_tab.configure(bg=COLOR_BG, fg=COLOR_TEXT_MUTED)
            self.btn_imperial_tab.configure(bg=COLOR_ACCENT, fg="white")
            self.f_metric_height.pack_forget()
            self.f_imperial_height.pack(fill="x", pady=5)
            self.f_metric_weight.pack_forget()
            self.f_imperial_weight.pack(fill="x", pady=10)
            self.lbl_target_unit.configure(text="lbs")
            if self.target_weight_kg:
                self.entry_target_weight.delete(0, tk.END)
                self.entry_target_weight.insert(0, f"{kg_to_lb(self.target_weight_kg):.1f}")
                
            # Populate imperial height fields from current cm state
            ft, inch = cm_to_ft_in(self.height_cm)
            self.entry_height_ft.delete(0, tk.END)
            self.entry_height_ft.insert(0, str(ft))
            self.entry_height_in.delete(0, tk.END)
            self.entry_height_in.insert(0, str(inch))

        self.recalculate()

    def switch_chart_view(self, mode):
        if self.chart_view_mode == mode:
            return
        
        self.chart_view_mode = mode
        
        if mode == "nomogram":
            self.btn_nomo_chart_tab.configure(bg=COLOR_ACCENT, fg="white")
            self.btn_trend_chart_tab.configure(bg=COLOR_BG, fg=COLOR_TEXT_MUTED)
            self.canvas_trend.grid_forget()
            self.canvas_nomo.grid(row=0, column=0, sticky="nsew")
            self.draw_nomogram()
        else:
            self.btn_nomo_chart_tab.configure(bg=COLOR_BG, fg=COLOR_TEXT_MUTED)
            self.btn_trend_chart_tab.configure(bg=COLOR_ACCENT, fg="white")
            self.canvas_nomo.grid_forget()
            self.canvas_trend.grid(row=0, column=0, sticky="nsew")
            self.draw_trend_chart()

    # --- Sync Slider & Inputs Events ---
    def on_height_scale(self, val):
        self.height_cm = int(float(val))
        self.lbl_height_badge.configure(text=f"{self.height_cm} cm")
        # Update entry block
        self.entry_height_cm.delete(0, tk.END)
        self.entry_height_cm.insert(0, str(self.height_cm))
        self.recalculate()

    def on_height_entry(self, event):
        try:
            val = int(self.entry_height_cm.get())
            if 100 <= val <= 250:
                self.height_cm = val
                self.scale_height.set(val)
                self.lbl_height_badge.configure(text=f"{val} cm")
                self.recalculate()
        except ValueError:
            pass

    def on_imperial_height_entry(self, event):
        try:
            ft = int(self.entry_height_ft.get()) if self.entry_height_ft.get() else 0
            inches = int(self.entry_height_in.get()) if self.entry_height_in.get() else 0
            if 3 <= ft <= 8 and 0 <= inches <= 11:
                self.height_cm = ft_in_to_cm(ft, inches)
                self.scale_height.set(round(self.height_cm))
                self.recalculate()
        except ValueError:
            pass

    def on_weight_scale(self, val):
        self.weight_kg = float(val)
        self.lbl_weight_badge.configure(text=f"{self.weight_kg:.1f} kg")
        self.entry_weight_kg.delete(0, tk.END)
        self.entry_weight_kg.insert(0, f"{self.weight_kg:.1f}")
        
        # Sync imperial weight slider / entry
        lbs = kg_to_lb(self.weight_kg)
        self.scale_weight_lb.set(round(lbs))
        self.entry_weight_lb.delete(0, tk.END)
        self.entry_weight_lb.insert(0, f"{lbs:.1f}")
        self.lbl_weight_lb_badge.configure(text=f"{lbs:.1f} lbs")
        self.recalculate()

    def on_weight_entry(self, event):
        try:
            val = float(self.entry_weight_kg.get())
            if 20 <= val <= 250:
                self.weight_kg = val
                self.scale_weight.set(val)
                self.lbl_weight_badge.configure(text=f"{val:.1f} kg")
                
                # Sync imperial weight slider
                lbs = kg_to_lb(val)
                self.scale_weight_lb.set(round(lbs))
                self.entry_weight_lb.delete(0, tk.END)
                self.entry_weight_lb.insert(0, f"{lbs:.1f}")
                self.lbl_weight_lb_badge.configure(text=f"{lbs:.1f} lbs")
                self.recalculate()
        except ValueError:
            pass

    def on_weight_lb_scale(self, val):
        lbs = float(val)
        self.lbl_weight_lb_badge.configure(text=f"{lbs:.1f} lbs")
        self.entry_weight_lb.delete(0, tk.END)
        self.entry_weight_lb.insert(0, f"{lbs:.1f}")
        
        # Sync metric weight slider / entry
        self.weight_kg = lb_to_kg(lbs)
        self.scale_weight.set(self.weight_kg)
        self.entry_weight_kg.delete(0, tk.END)
        self.entry_weight_kg.insert(0, f"{self.weight_kg:.1f}")
        self.lbl_weight_badge.configure(text=f"{self.weight_kg:.1f} kg")
        self.recalculate()

    def on_weight_lb_entry(self, event):
        try:
            lbs = float(self.entry_weight_lb.get())
            if 40 <= lbs <= 550:
                self.scale_weight_lb.set(round(lbs))
                self.lbl_weight_lb_badge.configure(text=f"{lbs:.1f} lbs")
                
                self.weight_kg = lb_to_kg(lbs)
                self.scale_weight.set(self.weight_kg)
                self.entry_weight_kg.delete(0, tk.END)
                self.entry_weight_kg.insert(0, f"{self.weight_kg:.1f}")
                self.lbl_weight_badge.configure(text=f"{self.weight_kg:.1f} kg")
                self.recalculate()
        except ValueError:
            pass

    def on_age_change(self, event):
        try:
            val = int(self.entry_age.get())
            if 2 <= val <= 120:
                self.age = val
                self.recalculate()
        except ValueError:
            pass

    def on_activity_change(self, event):
        sel = self.combo_activity.current()
        factors = [1.2, 1.375, 1.55, 1.725, 1.9]
        self.activity_factor = factors[sel]
        self.recalculate()

    def on_target_change(self, event):
        try:
            raw = self.entry_target_weight.get()
            if not raw:
                self.target_weight_kg = None
                self.recalculate()
                return
            
            val = float(raw)
            if val > 0:
                if self.current_unit == "metric":
                    self.target_weight_kg = val
                else:
                    self.target_weight_kg = lb_to_kg(val)
                self.recalculate()
        except ValueError:
            pass

    def clear_target_weight(self):
        self.target_weight_kg = None
        self.entry_target_weight.delete(0, tk.END)
        self.recalculate()

    # --- Calculations & Updates ---
    def recalculate(self):
        # 1. Compute BMI
        h_m = self.height_cm / 100
        self.bmi = self.weight_kg / (h_m * h_m)
        
        # Determine category details
        if self.bmi < 18.5:
            self.category = "Underweight"
            self.category_color = COLOR_UNDERWEIGHT
        elif self.bmi < 25.0:
            self.category = "Normal"
            self.category_color = COLOR_NORMAL
        elif self.bmi < 30.0:
            self.category = "Overweight"
            self.category_color = COLOR_OVERWEIGHT
        else:
            self.category = "Obese"
            self.category_color = COLOR_OBESE

        # 2. Update Stats rows
        # Ideal Weight Limits (WHO standard 18.5 to 24.9)
        min_ideal_kg = 18.5 * (h_m * h_m)
        max_ideal_kg = 24.9 * (h_m * h_m)
        
        if self.current_unit == "metric":
            self.lbl_ideal_range.configure(text=f"{min_ideal_kg:.1f} - {max_ideal_kg:.1f} kg")
            self.lbl_ideal_height.configure(text=f"For Height: {self.height_cm} cm")
        else:
            self.lbl_ideal_range.configure(text=f"{kg_to_lb(min_ideal_kg):.1f} - {kg_to_lb(max_ideal_kg):.1f} lbs")
            ft, inch = cm_to_ft_in(self.height_cm)
            self.lbl_ideal_height.configure(text=f"For Height: {ft}'{inch}\"")

        # BMR & TDEE Calculations (Mifflin-St Jeor)
        if self.gender.get() == "male":
            self.bmr = 10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age + 5
        else:
            self.bmr = 10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age - 161
            
        self.tdee = self.bmr * self.activity_factor
        
        self.lbl_bmr_val.configure(text=f"{int(round(self.bmr)):,} kcal")
        self.lbl_tdee_val.configure(text=f"{int(round(self.tdee)):,} kcal")

        # Target Weight Goals delta
        if self.target_weight_kg:
            diff = self.weight_kg - self.target_weight_kg
            disp_unit = "kg" if self.current_unit == "metric" else "lbs"
            disp_target = self.target_weight_kg if self.current_unit == "metric" else kg_to_lb(self.target_weight_kg)
            disp_diff = abs(diff) if self.current_unit == "metric" else abs(kg_to_lb(diff))
            
            if diff > 0.1:
                self.lbl_target_status.configure(text=f"-{disp_diff:.1f} {disp_unit}", foreground=COLOR_OVERWEIGHT)
                self.lbl_target_sub.configure(text=f"To target ({disp_target:.1f} {disp_unit})")
            elif diff < -0.1:
                self.lbl_target_status.configure(text=f"+{disp_diff:.1f} {disp_unit}", foreground=COLOR_UNDERWEIGHT)
                self.lbl_target_sub.configure(text=f"To target ({disp_target:.1f} {disp_unit})")
            else:
                self.lbl_target_status.configure(text="Goal Met!", foreground=COLOR_NORMAL)
                self.lbl_target_sub.configure(text="Target reached!")
        else:
            self.lbl_target_status.configure(text="- -", foreground=COLOR_TEXT)
            self.lbl_target_sub.configure(text="Set a goal weight")

        # 3. Trigger Gauges, Graphs Redraw
        self.draw_gauge()
        self.draw_nomogram()
        self.draw_trend_chart()
        self.generate_insights(min_ideal_kg, max_ideal_kg)

    # --- Canvas Charts Drawing Logic ---

    def draw_gauge(self):
        canvas = self.canvas_gauge
        canvas.delete("all")
        
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 50 or h < 50:
            return  # Canvas is not fully resized yet

        # Central positioning
        cx = w / 2
        cy = h - 20
        r = min(cx - 20, cy - 20)

        # Drawing background semi-circular gauge track
        # Arc spans from 180 to 0 (top half circle)
        canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=0, extent=180, outline="#1f2937", style="arc", width=12)

        # Overlay category colored segments
        # Underweight (BMI 15 to 18.5) -> Map to angle range (180deg to 148.5deg)
        # Normal (BMI 18.5 to 25) -> Angle (148.5deg to 90deg)
        # Overweight (BMI 25 to 30) -> Angle (90deg to 45deg)
        # Obese (BMI 30 to 35) -> Angle (45deg to 0deg)
        canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=148.5, extent=31.5, outline=COLOR_UNDERWEIGHT, style="arc", width=12)
        canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=90.0, extent=58.5, outline=COLOR_NORMAL, style="arc", width=12)
        canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=45.0, extent=45.0, outline=COLOR_OVERWEIGHT, style="arc", width=12)
        canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=0.0, extent=45.0, outline=COLOR_OBESE, style="arc", width=12)

        # Map current BMI (range 15 to 35) to angle from 180 to 0 degrees
        percent = (self.bmi - 15) / 20
        percent = max(0.0, min(1.0, percent))
        angle_deg = 180 - (percent * 180)
        angle_rad = math.radians(angle_deg)

        # Draw needle indicator line
        nx = cx + (r - 10) * math.cos(angle_rad)
        ny = cy - (r - 10) * math.sin(angle_rad)
        canvas.create_line(cx, cy, nx, ny, fill=self.category_color, width=3, arrow="last", arrowshape=(10,12,4))
        
        # Center pivot dot
        canvas.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, fill=self.category_color, outline=COLOR_TEXT)

        # Value and category texts
        canvas.create_text(cx, cy - 35, text=f"{self.bmi:.1f}", font=("Segoe UI", 20, "bold"), fill=COLOR_TEXT)
        canvas.create_text(cx, cy - 15, text=self.category.upper(), font=("Segoe UI", 8, "bold"), fill=self.category_color)

    def draw_nomogram(self):
        canvas = self.canvas_nomo
        canvas.delete("all")
        
        cw = canvas.winfo_width()
        ch = canvas.winfo_height()
        if cw < 100 or ch < 100:
            return

        # Layout Margins
        ml, mr, mt, mb = 50, 20, 20, 40
        pw = cw - ml - mr
        ph = ch - mt - mb

        # Scales definitions (Metric CM vs KG)
        min_h, max_h = 130.0, 210.0
        min_w, max_w = 30.0, 130.0
        
        # Expand scales automatically if user is outside defaults
        if self.height_cm < min_h + 5:
            min_h = max(80.0, float(int(self.height_cm - 10)))
        if self.height_cm > max_h - 5:
            max_h = min(270.0, float(int(self.height_cm + 10)))
        if self.weight_kg < min_w + 5:
            min_w = max(10.0, float(int(self.weight_kg - 10)))
        if self.weight_kg > max_w - 5:
            max_w = min(350.0, float(int(self.weight_kg + 10)))

        def to_pixels(h_val, w_val):
            px = ml + ((h_val - min_h) / (max_h - min_h)) * pw
            py = mt + ((max_w - w_val) / (max_w - min_w)) * ph
            return px, py

        # --- Layer 1: Colored Zone Polygons ---
        # We trace boundary lines for BMI = 18.5, 25.0, 30.0.
        # Height lists in steps of 2cm
        h_steps = []
        val_h = min_h
        while val_h <= max_h + 0.1:
            h_steps.append(val_h)
            val_h += 2.0

        # Layer Obese Zone: Just color the entire chart background red
        canvas.create_rectangle(ml, mt, ml + pw, mt + ph, fill=COLOR_ZONE_OBESE, outline="")

        # Layer Overweight Zone: Below BMI 30
        poly_over = []
        poly_over.append(to_pixels(min_h, min_w))
        poly_over.append(to_pixels(max_h, min_w))
        for h in reversed(h_steps):
            limit_w = 30.0 * ((h / 100) ** 2)
            poly_over.append(to_pixels(h, min(max_w, max(min_w, limit_w))))
        canvas.create_polygon(poly_over, fill=COLOR_ZONE_OVER, outline="")

        # Layer Normal Zone: Below BMI 25
        poly_normal = []
        poly_normal.append(to_pixels(min_h, min_w))
        poly_normal.append(to_pixels(max_h, min_w))
        for h in reversed(h_steps):
            limit_w = 25.0 * ((h / 100) ** 2)
            poly_normal.append(to_pixels(h, min(max_w, max(min_w, limit_w))))
        canvas.create_polygon(poly_normal, fill=COLOR_ZONE_NORMAL, outline="")

        # Layer Underweight Zone: Below BMI 18.5
        poly_under = []
        poly_under.append(to_pixels(min_h, min_w))
        poly_under.append(to_pixels(max_h, min_w))
        for h in reversed(h_steps):
            limit_w = 18.5 * ((h / 100) ** 2)
            poly_under.append(to_pixels(h, min(max_w, max(min_w, limit_w))))
        canvas.create_polygon(poly_under, fill=COLOR_ZONE_UNDER, outline="")

        # --- Layer 2: Draw boundary curve lines ---
        for limit_bmi, color in [(18.5, COLOR_UNDERWEIGHT), (25.0, COLOR_NORMAL), (30.0, COLOR_OVERWEIGHT)]:
            line_pts = []
            for h in h_steps:
                w_val = limit_bmi * ((h / 100) ** 2)
                if min_w <= w_val <= max_w:
                    line_pts.append(to_pixels(h, w_val))
            if len(line_pts) > 1:
                # Unpack coordinates list for Tkinter line drawing
                flat_pts = [coord for pt in line_pts for coord in pt]
                canvas.create_line(flat_pts, fill=color, width=2, smooth=True)

        # --- Layer 3: Grid Lines & Labels ---
        # Grid X (Heights)
        grid_h = 130.0
        while grid_h <= max_h:
            gx, gy_start = to_pixels(grid_h, min_w)
            _, gy_end = to_pixels(grid_h, max_w)
            canvas.create_line(gx, gy_start, gx, gy_end, fill="#1f2937", dash=(2, 2))
            canvas.create_text(gx, mt + ph + 12, text=f"{int(grid_h)}", font=FONT_SUBTITLE, fill=COLOR_TEXT_MUTED)
            grid_h += 10.0

        # Grid Y (Weights)
        grid_w = 30.0
        while grid_w <= max_w:
            gx_start, gy = to_pixels(min_h, grid_w)
            gx_end, _ = to_pixels(max_h, grid_w)
            canvas.create_line(gx_start, gy, gx_end, gy, fill="#1f2937", dash=(2, 2))
            canvas.create_text(ml - 18, gy, text=f"{int(grid_w)}", font=FONT_SUBTITLE, fill=COLOR_TEXT_MUTED)
            grid_w += 10.0

        # Axis Titles
        canvas.create_text(ml + pw/2, mt + ph + 28, text="Height (cm)", font=FONT_LABEL, fill=COLOR_TEXT)
        canvas.create_text(ml - 38, mt + ph/2, text="Weight (kg)", font=FONT_LABEL, fill=COLOR_TEXT, angle=90)

        # Outer box border
        canvas.create_rectangle(ml, mt, ml + pw, mt + ph, outline=COLOR_BORDER)

        # --- Layer 4: Pulse User Marker ---
        user_x, user_y = to_pixels(self.height_cm, self.weight_kg)
        
        # Pulse circles
        canvas.create_oval(user_x - 12, user_y - 12, user_x + 12, user_y + 12, outline=COLOR_ACCENT, width=1.5)
        canvas.create_oval(user_x - 7, user_y - 7, user_x + 7, user_y + 7, fill=COLOR_ACCENT, outline="white", width=1.5)
        
        # Tooltip text
        category_short = self.category
        canvas.create_text(user_x, user_y - 20, text=f"BMI {self.bmi:.1f} ({category_short})", font=FONT_LABEL, fill="white", justify="center")

    def draw_trend_chart(self):
        canvas = self.canvas_trend
        canvas.delete("all")
        
        cw = canvas.winfo_width()
        ch = canvas.winfo_height()
        if cw < 100 or ch < 100:
            return

        # Layout Margins
        ml, mr, mt, mb = 60, 40, 20, 40
        pw = cw - ml - mr
        ph = ch - mt - mb

        canvas.create_rectangle(ml, mt, ml + pw, mt + ph, outline=COLOR_BORDER)

        # Handle empty logs
        if not self.logs:
            canvas.create_text(ml + pw/2, mt + ph/2, text="No historical weight records logged yet.\nSave logs in the left panel to build trend charts.", font=FONT_BODY, fill=COLOR_TEXT_MUTED, justify="center")
            return

        # Sort logs chronologically
        sorted_logs = sorted(self.logs, key=lambda x: x["date"])
        n_logs = len(sorted_logs)

        # Establish Y Scales (Weight in active unit)
        is_metric = self.current_unit == "metric"
        unit_lbl = "kg" if is_metric else "lbs"

        def get_log_weight(log_item):
            w = log_item["weightKg"]
            return w if is_metric else kg_to_lb(w)

        weights = [get_log_weight(log) for log in sorted_logs]
        min_y = min(weights) - 5
        max_y = max(weights) + 5
        
        # Include target line in scale range if set
        if self.target_weight_kg:
            target_val = self.target_weight_kg if is_metric else kg_to_lb(self.target_weight_kg)
            min_y = min(min_y, target_val - 2)
            max_y = max(max_y, target_val + 2)

        min_y = max(0.0, min_y)

        # Coordinates conversions
        def to_pixels(index, w_val):
            # X spaced evenly
            px = ml + (index / max(1, n_logs - 1)) * pw
            py = mt + ((max_y - w_val) / max(1.0, max_y - min_y)) * ph
            return px, py

        # Draw Grid Y Lines
        step_y = max(1.0, (max_y - min_y) / 5)
        curr_y = min_y
        while curr_y <= max_y:
            _, py = to_pixels(0, curr_y)
            canvas.create_line(ml, py, ml + pw, py, fill="#1f2937", dash=(2, 2))
            canvas.create_text(ml - 22, py, text=f"{curr_y:.0f}", font=FONT_SUBTITLE, fill=COLOR_TEXT_MUTED)
            curr_y += step_y

        # Draw Target line (if set)
        if self.target_weight_kg:
            target_val = self.target_weight_kg if is_metric else kg_to_lb(self.target_weight_kg)
            _, target_py = to_pixels(0, target_val)
            canvas.create_line(ml, target_py, ml + pw, target_py, fill=COLOR_OVERWEIGHT, width=2, dash=(6, 4))
            canvas.create_text(ml + pw - 45, target_py - 10, text=f"Target: {target_val:.1f} {unit_lbl}", font=FONT_SUBTITLE, fill=COLOR_OVERWEIGHT)

        # Plot log points
        pt_coords = []
        for idx, log in enumerate(sorted_logs):
            w_val = get_log_weight(log)
            px, py = to_pixels(idx, w_val)
            pt_coords.append((px, py))

            # Dot marker
            canvas.create_oval(px - 4, py - 4, px + 4, py + 4, fill=COLOR_ACCENT, outline="white")
            
            # Format date short label (MM/DD)
            try:
                dt = datetime.fromisoformat(log["date"])
                dt_str = dt.strftime("%b %d")
            except:
                dt_str = log["date"][:10]
            canvas.create_text(px, mt + ph + 12, text=dt_str, font=FONT_SUBTITLE, fill=COLOR_TEXT_MUTED)

            # Value annotation on hover or top
            canvas.create_text(px, py - 12, text=f"{w_val:.1f}", font=FONT_SUBTITLE, fill=COLOR_TEXT)

        # Connect log points with a continuous path
        if len(pt_coords) > 1:
            flat_pts = [coord for pt in pt_coords for coord in pt]
            canvas.create_line(flat_pts, fill=COLOR_ACCENT, width=3)

        # Axis Titles
        canvas.create_text(ml + pw/2, mt + ph + 28, text="Dates", font=FONT_LABEL, fill=COLOR_TEXT)
        canvas.create_text(ml - 42, mt + ph/2, text=f"Weight ({unit_lbl})", font=FONT_LABEL, fill=COLOR_TEXT, angle=90)

    # --- Recommendations Engine (Insights Box) ---

    def generate_insights(self, min_ideal_kg, max_ideal_kg):
        # Clear previous insight labels
        for child in self.insights_body.winfo_children():
            child.destroy()

        category = self.category
        unit_suffix = "kg" if self.current_unit == "metric" else "lbs"
        
        # Prepare recommendation content
        nutrition_bullets = []
        exercise_bullets = []

        if category == "Underweight":
            gap = min_ideal_kg - self.weight_kg
            disp_gap = gap if self.current_unit == "metric" else kg_to_lb(gap)
            alert_text = f"BMI is Underweight ({self.bmi:.1f}). Gaining {disp_gap:.1f} {unit_suffix} will reach normal range."
            alert_bg = COLOR_ZONE_UNDER
            alert_fg = COLOR_UNDERWEIGHT
            
            nutrition_bullets = [
                "Aim for a caloric surplus of 300 - 500 kcal above maintenance.",
                "Eat 1.6 - 2.0g protein per kg of bodyweight to build muscle.",
                "Eat energy-dense fats: Nuts, avocados, seeds, and peanut butter.",
                "Eat 5-6 meals a day to help meet calorie goals comfortably."
            ]
            exercise_bullets = [
                "Focus on compound lifts (squats, bench, deadlifts) 3-4 days/week.",
                "Limit high-intensity cardio to conserve energy for muscle growth.",
                "Sleep 8+ hours a night for cellular and muscle recovery."
            ]

        elif category == "Normal":
            alert_text = f"BMI is Healthy ({self.bmi:.1f}). Your body weight is optimal. Keep it up!"
            alert_bg = COLOR_ZONE_NORMAL
            alert_fg = COLOR_NORMAL
            
            nutrition_bullets = [
                "Consume calories matching your maintenance TDEE.",
                "Prioritize fresh vegetables, lean proteins, and complex fibers.",
                "Follow the 80/20 balance rule for treat meals.",
                "Drink 2.5 - 3.5 liters of clean water daily."
            ]
            exercise_bullets = [
                "Perform 150 minutes of moderate aerobic exercise weekly.",
                "Add muscle resistance training 2-3 times/week.",
                "Practice light flexibility stretching or yoga daily."
            ]

        else: # Overweight or Obese
            gap = self.weight_kg - max_ideal_kg
            disp_gap = gap if self.current_unit == "metric" else kg_to_lb(gap)
            alert_text = f"BMI is {category} ({self.bmi:.1f}). Reducing {disp_gap:.1f} {unit_suffix} will reach normal range."
            alert_bg = COLOR_ZONE_OBESE if category == "Obese" else COLOR_ZONE_OVER
            alert_fg = COLOR_OBESE if category == "Obese" else COLOR_OVERWEIGHT
            
            nutrition_bullets = [
                "Target a daily deficit of 500 kcal under your TDEE.",
                "Increase lean proteins to preserve muscle while losing fat.",
                "Eat high-volume, low-calorie greens like salads and broccoli.",
                "Avoid sugary sodas, commercial juices, and caloric beverages."
            ]
            exercise_bullets = [
                "Boost basic step counts to 8,000 - 10,000 steps daily.",
                "Incorporate full body resistance lifting 3 times a week.",
                "Add 2-3 cardio workouts (brisk walking, cycling, or HIIT) weekly."
            ]


        # Draw Recommendations to UI
        # A. Alert Banner
        banner = tk.Frame(self.insights_body, bg=alert_bg, bd=0, highlightbackground=alert_fg, highlightthickness=1)
        banner.pack(fill="x", padx=5, pady=5)
        tk.Label(banner, text=alert_text, font=FONT_LABEL, bg=alert_bg, fg=alert_fg, justify="left", wraplength=350).pack(padx=10, pady=8, anchor="w")

        # B. Nutrition Section
        tk.Label(self.insights_body, text="Nutrition Plan", font=FONT_LABEL, bg=COLOR_CARD, fg=COLOR_ACCENT).pack(anchor="w", padx=5, pady=(10, 2))
        for bullet in nutrition_bullets:
            f = tk.Frame(self.insights_body, bg=COLOR_CARD)
            f.pack(fill="x", anchor="w", padx=10, pady=1)
            tk.Label(f, text="•", font=FONT_BODY, bg=COLOR_CARD, fg=COLOR_ACCENT).pack(side="left", anchor="n")
            tk.Label(f, text=bullet, font=FONT_SUBTITLE, bg=COLOR_CARD, fg=COLOR_TEXT, justify="left", wraplength=330).pack(side="left", fill="x", expand=True, anchor="w")

        # C. Exercise Section
        tk.Label(self.insights_body, text="Exercise Plan", font=FONT_LABEL, bg=COLOR_CARD, fg=COLOR_ACCENT).pack(anchor="w", padx=5, pady=(10, 2))
        for bullet in exercise_bullets:
            f = tk.Frame(self.insights_body, bg=COLOR_CARD)
            f.pack(fill="x", anchor="w", padx=10, pady=1)
            tk.Label(f, text="•", font=FONT_BODY, bg=COLOR_CARD, fg=COLOR_ACCENT).pack(side="left", anchor="n")
            tk.Label(f, text=bullet, font=FONT_SUBTITLE, bg=COLOR_CARD, fg=COLOR_TEXT, justify="left", wraplength=330).pack(side="left", fill="x", expand=True, anchor="w")



    # --- Database Log History Operations ---

    def load_history(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r") as f:
                    self.logs = json.load(f)
            except Exception as e:
                print(f"Error loading logs: {e}")
                self.logs = []
        else:
            self.logs = []

    def save_history(self):
        try:
            with open(self.db_path, "w") as f:
                json.dump(self.logs, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Could not save database: {e}")

    def render_log_table(self):
        # Clear existing logs in table
        for item in self.table.get_children():
            self.table.delete(item)

        # Sort logs descending by date
        sorted_logs = sorted(self.logs, key=lambda x: x["date"], reverse=True)

        for log in sorted_logs:
            # Format Iso Date to human readable
            try:
                dt = datetime.fromisoformat(log["date"])
                dt_str = dt.strftime("%b %d, %y - %H:%M")
            except:
                dt_str = log["date"]

            h = log["heightCm"]
            w = log["weightKg"]

            # Units display dynamically converted
            is_metric = self.current_unit == "metric"
            h_disp = f"{round(h)} cm" if is_metric else f"{cm_to_ft_in(h)[0]}'{cm_to_ft_in(h)[1]}\""
            w_disp = f"{w:.1f} kg" if is_metric else f"{kg_to_lb(w):.1f} lbs"

            # Recompute BMI and Category
            h_m = h / 100
            bmi_val = w / (h_m * h_m)
            
            if bmi_val < 18.5:
                cat = "Underweight"
            elif bmi_val < 25.0:
                cat = "Normal"
            elif bmi_val < 30.0:
                cat = "Overweight"
            else:
                cat = "Obese"

            self.table.insert("", "end", values=(
                dt_str, 
                h_disp, 
                w_disp, 
                f"{bmi_val:.1f}", 
                cat, 
                log.get("notes", "")
            ))

    def save_log_entry(self):
        notes = self.entry_notes.get().strip()
        
        # Assemble log object
        new_log = {
            "date": datetime.now().isoformat(),
            "heightCm": self.height_cm,
            "weightKg": self.weight_kg,
            "age": self.age,
            "gender": self.gender.get(),
            "activity": self.activity_factor,
            "targetWeight": self.target_weight_kg,
            "notes": notes
        }

        self.logs.append(new_log)
        self.save_history()
        
        # Clear notes entry
        self.entry_notes.delete(0, tk.END)
        
        messagebox.showinfo("Success", "BMI reading saved to database log!")
        
        # Update dashboard elements
        self.recalculate()

    def clear_all_history(self):
        if not self.logs:
            return
        
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to delete ALL logged history? This cannot be undone."):
            self.logs = []
            self.save_history()
            self.recalculate()

# --- Program Entry Point ---
if __name__ == "__main__":
    app = FitScaleApp()
    app.mainloop()
