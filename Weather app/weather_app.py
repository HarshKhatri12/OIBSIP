"""
🌤 Python Weather App — Enhanced
Features:
  1. Live GPS location (auto-detect via IP)
  2. Full-screen scrollable window
  3. Search history (saved to weather_history.json)
  4. Combined graph — Temp, Feels Like, Humidity, Wind on one figure
Powered by wttr.in — no API key required.
"""

import tkinter as tk
from tkinter import messagebox, ttk
import requests
import threading
import json
import os
from datetime import datetime

import matplotlib
matplotlib.use("TkAgg")                          # must be set before pyplot
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure             # use Figure directly, not plt.Figure

# ── PATHS ─────────────────────────────────────────────────────────────────────
_BASE_DIR    = os.path.dirname(os.path.abspath(__file__)) \
               if "__file__" in dir() else os.getcwd()
HISTORY_FILE = os.path.join(_BASE_DIR, "weather_history.json")

# ── API ───────────────────────────────────────────────────────────────────────
WTTR_URL    = "https://wttr.in/{location}?format=j1"
GEO_IP_URL  = "https://ipapi.co/json/"

# ── THEME ─────────────────────────────────────────────────────────────────────
BG      = "#0d1b2a"
CARD    = "#1b2a3b"
ACCENT  = "#1e3a5f"
TEXT    = "#e8eaf0"
MUTED   = "#7a8ba0"
RED     = "#e63946"
GREEN   = "#52b788"
YELLOW  = "#ffd166"
BLUE    = "#118ab2"
FONT    = "Segoe UI"

# ── WEATHER CODE → EMOJI ──────────────────────────────────────────────────────
WC_ICONS = {
    113:"☀️", 116:"⛅", 119:"☁️", 122:"☁️", 143:"🌫️",
    176:"🌦️", 179:"🌨️", 182:"🌧️", 185:"🌧️", 200:"⛈️",
    227:"🌨️", 230:"❄️", 248:"🌫️", 260:"🌫️", 263:"🌦️",
    266:"🌧️", 281:"🌧️", 284:"🌧️", 293:"🌦️", 296:"🌧️",
    299:"🌧️", 302:"🌧️", 305:"🌧️", 308:"🌧️", 311:"🌧️",
    314:"🌧️", 317:"🌨️", 320:"🌨️", 323:"🌨️", 326:"🌨️",
    329:"❄️",  332:"❄️",  335:"❄️",  338:"❄️",  350:"🌧️",
    353:"🌦️", 356:"🌧️", 359:"🌧️", 362:"🌨️", 365:"🌨️",
    368:"🌨️", 371:"❄️",  374:"🌨️", 377:"🌨️", 386:"⛈️",
    389:"⛈️",  392:"⛈️",  395:"❄️",
}

def wc_icon(code: int) -> str:
    return WC_ICONS.get(code, "🌡️")

# ── HISTORY HELPERS ───────────────────────────────────────────────────────────
def load_history() -> list:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(entries: list):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


# ── MAIN APP ──────────────────────────────────────────────────────────────────
class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🌤  Live Weather")
        # Start full-screen
        self.state("zoomed")          # maximised on Windows
        self.configure(bg=BG)
        self.bind("<F11>",  lambda _: self._toggle_fullscreen())
        self.bind("<Escape>", lambda _: self._exit_fullscreen())
        self._is_fullscreen = False

        self._unit          = tk.StringVar(value="C")
        self._last_data     = None
        self._last_location = ""
        self._history       = load_history()
        self._current_fig   = None               # tracks open matplotlib figure

        self._build_ui()
        # Auto-detect location on startup
        threading.Thread(target=self._auto_locate, daemon=True).start()

    # ── FULLSCREEN HELPERS ────────────────────────────────────────────────────
    def _toggle_fullscreen(self):
        self._is_fullscreen = not self._is_fullscreen
        self.attributes("-fullscreen", self._is_fullscreen)

    def _exit_fullscreen(self):
        self._is_fullscreen = False
        self.attributes("-fullscreen", False)

    # ── BUILD UI ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Top toolbar ───────────────────────────────────────────────────────
        toolbar = tk.Frame(self, bg=ACCENT, pady=10)
        toolbar.pack(fill="x")

        tk.Label(toolbar, text="🌤  Live Weather", font=(FONT, 18, "bold"),
                 bg=ACCENT, fg=TEXT).pack(side="left", padx=16)

        # Fullscreen button
        tk.Button(toolbar, text="⛶  Fullscreen", font=(FONT, 10),
                  bg=ACCENT, fg=TEXT, relief="flat", cursor="hand2",
                  activebackground=BG, activeforeground=TEXT,
                  command=self._toggle_fullscreen).pack(side="right", padx=8)

        # Unit toggle
        for lbl, val in [("°F", "F"), ("°C", "C")]:
            tk.Radiobutton(toolbar, text=lbl, variable=self._unit, value=val,
                           bg=ACCENT, fg=TEXT, selectcolor=BG,
                           activebackground=ACCENT, activeforeground=TEXT,
                           font=(FONT, 11, "bold"),
                           command=self._redraw).pack(side="right", padx=4)
        tk.Label(toolbar, text="Unit:", font=(FONT, 10),
                 bg=ACCENT, fg=MUTED).pack(side="right", padx=(8, 0))

        tk.Label(toolbar, text="wttr.in • No key required",
                 font=(FONT, 8), bg=ACCENT, fg=MUTED).pack(side="right", padx=16)

        # ── Search bar ────────────────────────────────────────────────────────
        sf = tk.Frame(self, bg=BG, pady=10)
        sf.pack(fill="x", padx=20)

        self._entry = tk.Entry(sf, font=(FONT, 14), bg=CARD, fg=TEXT,
                               insertbackground=TEXT, relief="flat", bd=8)
        self._entry.pack(side="left", fill="x", expand=True, ipady=8)
        self._entry.insert(0, "City, country or ZIP…")
        self._entry.config(fg=MUTED)
        self._entry.bind("<FocusIn>",  self._ph_clear)
        self._entry.bind("<FocusOut>", self._ph_restore)
        self._entry.bind("<Return>",   lambda _: self._search())

        tk.Button(sf, text="📍 My Location", font=(FONT, 11),
                  bg=GREEN, fg="white", relief="flat", padx=10, pady=6,
                  cursor="hand2", activebackground="#3d9a6a",
                  command=lambda: threading.Thread(
                      target=self._auto_locate, daemon=True).start()
                  ).pack(side="left", padx=(8, 4))

        tk.Button(sf, text="🔍 Search", font=(FONT, 11, "bold"),
                  bg=RED, fg="white", relief="flat", padx=14, pady=6,
                  cursor="hand2", activebackground="#c1121f",
                  command=self._search).pack(side="left", padx=(0, 0))

        # ── Main area: left content + right history panel ─────────────────────
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Scrollable left canvas ────────────────────────────────────────────
        self._canvas = tk.Canvas(main, bg=BG, highlightthickness=0)
        self._canvas.pack(side="left", fill="both", expand=True)

        vscroll = ttk.Scrollbar(main, orient="vertical",
                                command=self._canvas.yview)
        vscroll.pack(side="left", fill="y")
        self._canvas.configure(yscrollcommand=vscroll.set)

        self._scroll_frame = tk.Frame(self._canvas, bg=BG)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._scroll_frame, anchor="nw")

        self._scroll_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>",       self._on_canvas_configure)
        self._canvas.bind("<MouseWheel>",
                          lambda e: self._canvas.yview_scroll(
                              -1 * (e.delta // 120), "units"))

        # ── Right history sidebar ─────────────────────────────────────────────
        sidebar = tk.Frame(main, bg=CARD, width=200)
        sidebar.pack(side="right", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="📋 History", font=(FONT, 12, "bold"),
                 bg=CARD, fg=TEXT).pack(pady=(10, 4))
        tk.Button(sidebar, text="🗑 Clear", font=(FONT, 9),
                  bg=ACCENT, fg=TEXT, relief="flat", cursor="hand2",
                  command=self._clear_history).pack(pady=(0, 6))

        self._hist_list = tk.Listbox(sidebar, bg=BG, fg=TEXT,
                                     font=(FONT, 9), relief="flat",
                                     selectbackground=ACCENT,
                                     activestyle="none", bd=0,
                                     highlightthickness=0)
        self._hist_list.pack(fill="both", expand=True, padx=6, pady=4)
        self._hist_list.bind("<<ListboxSelect>>", self._on_history_click)
        self._refresh_history_list()

        # ── Build scrollable content ──────────────────────────────────────────
        self._build_content(self._scroll_frame)

        # ── Status bar ────────────────────────────────────────────────────────
        self._status = tk.StringVar(value="Auto-detecting your location…")
        tk.Label(self, textvariable=self._status,
                 font=(FONT, 9), bg=BG, fg=MUTED).pack(
                     side="bottom", pady=4)

    def _on_frame_configure(self, _):
        self._canvas.configure(
            scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    # ── SCROLLABLE CONTENT WIDGETS ────────────────────────────────────────────
    def _build_content(self, parent):
        pad = {"padx": 20, "pady": 6}

        # ── Current weather card ──────────────────────────────────────────────
        self._ccard = tk.Frame(parent, bg=CARD, padx=24, pady=18)
        self._ccard.pack(fill="x", **pad)

        top = tk.Frame(self._ccard, bg=CARD)
        top.pack()
        self._icon_lbl = tk.Label(top, text="", font=(FONT, 72),
                                  bg=CARD, fg=TEXT)
        self._icon_lbl.pack(side="left", padx=(0, 20))

        info = tk.Frame(top, bg=CARD)
        info.pack(side="left")
        self._temp_lbl = tk.Label(info, text="--", font=(FONT, 64, "bold"),
                                  bg=CARD, fg=TEXT)
        self._temp_lbl.pack(anchor="w")
        self._desc_lbl = tk.Label(info, text="--", font=(FONT, 16),
                                  bg=CARD, fg=MUTED)
        self._desc_lbl.pack(anchor="w")
        self._loc_lbl  = tk.Label(info, text="", font=(FONT, 13),
                                  bg=CARD, fg=MUTED)
        self._loc_lbl.pack(anchor="w")
        self._time_lbl = tk.Label(info, text="", font=(FONT, 10),
                                  bg=CARD, fg=MUTED)
        self._time_lbl.pack(anchor="w")

        # ── Detail tiles ─────────────────────────────────────────────────────
        r1 = tk.Frame(parent, bg=BG)
        r1.pack(fill="x", **pad)
        self._humidity   = self._tile(r1, "💧", "Humidity")
        self._wind       = self._tile(r1, "💨", "Wind")
        self._feels      = self._tile(r1, "🌡️", "Feels Like")
        self._uv         = self._tile(r1, "🔆", "UV Index")
        for t in (self._humidity, self._wind, self._feels, self._uv):
            t["frame"].pack(side="left", expand=True, fill="both", padx=4)

        r2 = tk.Frame(parent, bg=BG)
        r2.pack(fill="x", **pad)
        self._visibility = self._tile(r2, "👁️",  "Visibility")
        self._pressure   = self._tile(r2, "📊",  "Pressure")
        self._sunrise    = self._tile(r2, "🌅",  "Sunrise")
        self._sunset     = self._tile(r2, "🌇",  "Sunset")
        for t in (self._visibility, self._pressure, self._sunrise, self._sunset):
            t["frame"].pack(side="left", expand=True, fill="both", padx=4)

        # ── 3-day forecast ────────────────────────────────────────────────────
        tk.Label(parent, text="3-Day Forecast", font=(FONT, 13, "bold"),
                 bg=BG, fg=MUTED).pack(anchor="w", padx=24, pady=(10, 2))
        self._fcast_frame = tk.Frame(parent, bg=BG)
        self._fcast_frame.pack(fill="x", padx=20, pady=(0, 6))

        # ── Hourly strip ──────────────────────────────────────────────────────
        tk.Label(parent, text="Today — Hourly", font=(FONT, 13, "bold"),
                 bg=BG, fg=MUTED).pack(anchor="w", padx=24, pady=(6, 2))
        self._hourly_frame = tk.Frame(parent, bg=BG)
        self._hourly_frame.pack(fill="x", padx=20, pady=(0, 6))

        # ── Graph section ─────────────────────────────────────────────────────
        tk.Label(parent, text="📈 Weather Graph — Hourly Today",
                 font=(FONT, 13, "bold"),
                 bg=BG, fg=MUTED).pack(anchor="w", padx=24, pady=(10, 2))
        self._graph_frame = tk.Frame(parent, bg=CARD)
        self._graph_frame.pack(fill="x", padx=20, pady=(0, 20))

    # ── TILE HELPER ───────────────────────────────────────────────────────────
    def _tile(self, parent, icon, label):
        frame = tk.Frame(parent, bg=CARD, padx=6, pady=12)
        tk.Label(frame, text=icon,  font=(FONT, 22), bg=CARD, fg=TEXT).pack()
        var = tk.StringVar(value="--")
        tk.Label(frame, textvariable=var, font=(FONT, 13, "bold"),
                 bg=CARD, fg=TEXT).pack()
        tk.Label(frame, text=label, font=(FONT, 9),
                 bg=CARD, fg=MUTED).pack()
        return {"frame": frame, "var": var}

    # ── PLACEHOLDER ───────────────────────────────────────────────────────────
    def _ph_clear(self, _):
        if self._entry.get() == "City, country or ZIP…":
            self._entry.delete(0, "end")
            self._entry.config(fg=TEXT)

    def _ph_restore(self, _):
        if not self._entry.get().strip():
            self._entry.insert(0, "City, country or ZIP…")
            self._entry.config(fg=MUTED)

    # ── AUTO GPS LOCATION ─────────────────────────────────────────────────────
    def _auto_locate(self):
        self.after(0, lambda: self._status.set("📍 Detecting your location…"))
        try:
            r = requests.get(GEO_IP_URL, timeout=8,
                             headers={"User-Agent": "WeatherApp/2.0"})
            r.raise_for_status()
            geo = r.json()
            city    = geo.get("city", "")
            country = geo.get("country_name", "")
            loc     = f"{city}, {country}" if city else country
            if loc.strip(", "):
                self.after(0, lambda: self._entry.delete(0, "end"))
                self.after(0, lambda: self._entry.insert(0, loc))
                self.after(0, lambda: self._entry.config(fg=TEXT))
                self.after(0, lambda: self._status.set(
                    f"📍 Auto-detected: {loc}. Fetching weather…"))
                threading.Thread(target=self._fetch, args=(loc,),
                                 daemon=True).start()
            else:
                self.after(0, lambda: self._status.set(
                    "Could not detect location. Enter city manually."))
        except Exception:
            self.after(0, lambda: self._status.set(
                "Location detection failed. Enter city manually."))

    # ── SEARCH ────────────────────────────────────────────────────────────────
    def _search(self):
        loc = self._entry.get().strip()
        if not loc or loc == "City, country or ZIP…":
            messagebox.showwarning("Input", "Please enter a location.")
            return
        self._status.set(f"Fetching weather for {loc}…")
        threading.Thread(target=self._fetch, args=(loc,), daemon=True).start()

    # ── FETCH ─────────────────────────────────────────────────────────────────
    def _fetch(self, location: str):
        try:
            url  = WTTR_URL.format(location=requests.utils.quote(location))
            resp = requests.get(url, timeout=12,
                                headers={"User-Agent": "WeatherApp/2.0"})
            if resp.status_code == 404 or (
                    resp.status_code == 200 and "Unknown location" in resp.text):
                self.after(0, lambda: self._err(
                    f"'{location}' not found.\n"
                    "Try a different spelling or add country, e.g. 'Paris, France'."))
                return
            resp.raise_for_status()
            data = resp.json()
            self.after(0, lambda: self._render(data, location))
        except requests.exceptions.ConnectionError:
            self.after(0, lambda: self._err("No internet connection."))
        except requests.exceptions.Timeout:
            self.after(0, lambda: self._err("Request timed out. Try again."))
        except Exception as exc:
            self.after(0, lambda: self._err(f"Unexpected error:\n{exc}"))

    # ── RENDER ────────────────────────────────────────────────────────────────
    def _render(self, data: dict, location: str):
        self._last_data     = data
        self._last_location = location
        unit = self._unit.get()

        cur   = data["current_condition"][0]
        today = data["weather"][0]
        area  = data.get("nearest_area", [{}])[0]

        area_name    = area.get("areaName",  [{}])[0].get("value", "")
        country_name = area.get("country",   [{}])[0].get("value", "")
        region_name  = area.get("region",    [{}])[0].get("value", "")
        loc_str = ", ".join(filter(None,
                                   [area_name, region_name, country_name]))

        if unit == "C":
            temp, feels = cur["temp_C"], cur["FeelsLikeC"]
            max_t, min_t = today["maxtempC"], today["mintempC"]
            unit_sym = "°C"
        else:
            temp, feels = cur["temp_F"], cur["FeelsLikeF"]
            max_t, min_t = today["maxtempF"], today["mintempF"]
            unit_sym = "°F"

        desc  = cur["weatherDesc"][0]["value"]
        code  = int(cur["weatherCode"])
        icon  = wc_icon(code)
        astro = today.get("astronomy", [{}])[0]

        # ── Current card ──────────────────────────────────────────────────────
        self._icon_lbl.config(text=icon)
        self._temp_lbl.config(text=f"{temp}{unit_sym}")
        self._desc_lbl.config(text=desc)
        self._loc_lbl.config(
            text=f"📍 {loc_str}" if loc_str else f"📍 {location.title()}")
        self._time_lbl.config(
            text=f"High {max_t}{unit_sym}  •  Low {min_t}{unit_sym}  •  "
                 f"Updated {datetime.now().strftime('%H:%M:%S')}")

        wind_dir  = cur.get("winddir16Point", "")
        wind_str  = (f'{cur["windspeedKmph"]} km/h {wind_dir}' if unit == "C"
                     else f'{cur["windspeedMiles"]} mph {wind_dir}')

        self._humidity["var"].set(f'{cur["humidity"]}%')
        self._wind["var"].set(wind_str)
        self._feels["var"].set(f"{feels}{unit_sym}")
        self._uv["var"].set(cur.get("uvIndex", "--"))
        self._visibility["var"].set(f'{cur["visibility"]} km')
        self._pressure["var"].set(f'{cur["pressure"]} hPa')
        self._sunrise["var"].set(astro.get("sunrise", "--"))
        self._sunset["var"].set(astro.get("sunset",  "--"))

        # ── 3-day forecast ────────────────────────────────────────────────────
        for w in self._fcast_frame.winfo_children():
            w.destroy()
        for day_data in data["weather"][:3]:
            date   = datetime.strptime(
                day_data["date"], "%Y-%m-%d").strftime("%a %d %b")
            d_code = int(day_data["hourly"][4]["weatherCode"])
            d_icon = wc_icon(d_code)
            d_desc = day_data["hourly"][4]["weatherDesc"][0]["value"]
            hi = day_data["maxtempC"] if unit == "C" else day_data["maxtempF"]
            lo = day_data["mintempC"] if unit == "C" else day_data["mintempF"]
            tile = tk.Frame(self._fcast_frame, bg=CARD, padx=10, pady=12)
            tile.pack(side="left", expand=True, fill="both", padx=4)
            tk.Label(tile, text=date,  font=(FONT, 10, "bold"),
                     bg=CARD, fg=MUTED).pack()
            tk.Label(tile, text=d_icon, font=(FONT, 26),
                     bg=CARD, fg=TEXT).pack()
            tk.Label(tile, text=d_desc, font=(FONT, 9),
                     bg=CARD, fg=MUTED, wraplength=120).pack()
            tk.Label(tile, text=f"↑{hi}  ↓{lo}{unit_sym}",
                     font=(FONT, 11, "bold"), bg=CARD, fg=TEXT).pack(pady=(4,0))

        # ── Hourly strip ──────────────────────────────────────────────────────
        for w in self._hourly_frame.winfo_children():
            w.destroy()
        for h in today["hourly"]:
            htime  = f"{int(h['time'])//100:02d}:00"
            h_icon = wc_icon(int(h["weatherCode"]))
            h_temp = h["tempC"] if unit == "C" else h["tempF"]
            htile  = tk.Frame(self._hourly_frame, bg=CARD, padx=8, pady=10)
            htile.pack(side="left", expand=True, fill="both", padx=3)
            tk.Label(htile, text=htime,  font=(FONT, 9),
                     bg=CARD, fg=MUTED).pack()
            tk.Label(htile, text=h_icon, font=(FONT, 20),
                     bg=CARD, fg=TEXT).pack()
            tk.Label(htile, text=f"{h_temp}{unit_sym}",
                     font=(FONT, 10, "bold"), bg=CARD, fg=TEXT).pack()

        # ── Build graph ───────────────────────────────────────────────────────
        self._build_graph(today, unit, unit_sym)

        # ── Save to history ───────────────────────────────────────────────────
        self._record_history(loc_str or location.title(),
                             temp, unit_sym, desc, icon)

        self._status.set(
            f"Live data for {loc_str or location.title()}  •  "
            f"{datetime.now().strftime('%d %b %Y, %H:%M:%S')}  •  "
            "Press F11 for fullscreen")

    # ── GRAPH ─────────────────────────────────────────────────────────────────
    def _build_graph(self, today: dict, unit: str, unit_sym: str):
        # Destroy old widgets and close previous figure to free memory
        for w in self._graph_frame.winfo_children():
            w.destroy()
        if hasattr(self, "_current_fig") and self._current_fig is not None:
            plt.close(self._current_fig)
            self._current_fig = None

        hourly = today["hourly"]
        labels = [f"{int(h['time'])//100:02d}:00" for h in hourly]
        xs     = list(range(len(labels)))        # numeric x for fill_between

        temps    = [int(h["tempC"])        if unit == "C" else int(h["tempF"])
                    for h in hourly]
        feels    = [int(h["FeelsLikeC"])   if unit == "C" else int(h["FeelsLikeF"])
                    for h in hourly]
        humidity = [int(h["humidity"])     for h in hourly]
        wind     = [int(h["windspeedKmph"]) if unit == "C"
                    else int(h["windspeedMiles"]) for h in hourly]

        # Apply dark theme via rcParams
        plt.rcParams.update({
            "figure.facecolor": BG,
            "axes.facecolor":   CARD,
            "axes.edgecolor":   MUTED,
            "axes.labelcolor":  TEXT,
            "xtick.color":      MUTED,
            "ytick.color":      MUTED,
            "grid.color":       ACCENT,
            "grid.linestyle":   "--",
            "grid.alpha":       0.5,
            "text.color":       TEXT,
            "legend.facecolor": CARD,
            "legend.edgecolor": ACCENT,
        })

        fig = Figure(figsize=(10, 5.5), dpi=100)   # Figure, not plt.Figure
        self._current_fig = fig
        gs  = gridspec.GridSpec(2, 2, figure=fig, hspace=0.55, wspace=0.38)

        ax_temp = fig.add_subplot(gs[0, 0])
        ax_feel = fig.add_subplot(gs[0, 1])
        ax_hum  = fig.add_subplot(gs[1, 0])
        ax_wind = fig.add_subplot(gs[1, 1])

        def _plot(ax, y, title, color, ylabel):
            ax.plot(xs, y, color=color, linewidth=2.5,
                    marker="o", markersize=5, markerfacecolor="white")
            ax.fill_between(xs, y, alpha=0.15, color=color)  # numeric xs ✓
            ax.set_title(title, fontsize=10, fontweight="bold",
                         color=TEXT, pad=6)
            ax.set_ylabel(ylabel, fontsize=8)
            ax.set_xticks(xs)
            ax.set_xticklabels(labels, fontsize=7, rotation=30, ha="right")
            ax.grid(True)
            for xi, yi in zip(xs, y):
                ax.annotate(str(yi), (xi, yi),
                            textcoords="offset points", xytext=(0, 6),
                            ha="center", fontsize=7, color=color)

        _plot(ax_temp, temps,    f"Temperature ({unit_sym})",
              YELLOW, unit_sym)
        _plot(ax_feel, feels,    f"Feels Like ({unit_sym})",
              RED,    unit_sym)
        _plot(ax_hum,  humidity, "Humidity (%)",
              BLUE,   "%")
        _plot(ax_wind, wind,
              f"Wind ({'km/h' if unit == 'C' else 'mph'})",
              GREEN,  "km/h" if unit == "C" else "mph")

        fig.tight_layout()   # called on instance, not constructor arg ✓

        canvas = FigureCanvasTkAgg(fig, master=self._graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, pady=4)

    # ── HISTORY ───────────────────────────────────────────────────────────────
    def _record_history(self, loc: str, temp, unit_sym: str,
                        desc: str, icon: str):
        entry = {
            "location":  loc,
            "temp":      f"{temp}{unit_sym}",
            "desc":      desc,
            "icon":      icon,
            "timestamp": datetime.now().strftime("%d %b %Y %H:%M"),
        }
        # Remove duplicates (same location), keep latest
        self._history = [h for h in self._history
                         if h["location"].lower() != loc.lower()]
        self._history.insert(0, entry)
        self._history = self._history[:30]   # keep last 30
        save_history(self._history)
        self._refresh_history_list()

    def _refresh_history_list(self):
        self._hist_list.delete(0, "end")
        for h in self._history:
            # Single line per entry so listbox index == self._history index
            self._hist_list.insert(
                "end",
                f'{h["icon"]} {h["location"]}  {h["temp"]}  •  {h["timestamp"]}')

    def _on_history_click(self, _):
        sel = self._hist_list.curselection()
        if not sel:
            return
        idx   = sel[0]
        if idx >= len(self._history):
            return
        entry = self._history[idx]
        loc   = entry["location"]
        self._entry.delete(0, "end")
        self._entry.insert(0, loc)
        self._entry.config(fg=TEXT)
        self._status.set(f"Re-fetching {loc}…")
        threading.Thread(target=self._fetch, args=(loc,), daemon=True).start()

    def _clear_history(self):
        if messagebox.askyesno("Clear History",
                               "Delete all search history?"):
            self._history = []
            save_history(self._history)
            self._refresh_history_list()

    # ── REDRAW on unit change ─────────────────────────────────────────────────
    def _redraw(self):
        if self._last_data:
            self._render(self._last_data, self._last_location)

    # ── ERROR ─────────────────────────────────────────────────────────────────
    def _err(self, msg: str):
        self._status.set("Error — see popup.")
        messagebox.showerror("Weather Error", msg)


# ── ENTRY ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = WeatherApp()
    try:
        app.mainloop()
    finally:
        # Clean up matplotlib figure on exit to avoid Tk teardown errors
        if app._current_fig is not None:
            plt.close(app._current_fig)
