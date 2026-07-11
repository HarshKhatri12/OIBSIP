# 🌤 Live Weather App

A full-featured graphical weather app built with **Python + Tkinter**.  
Fetches real-time live weather data from [wttr.in](https://wttr.in) — **no API key or signup required**.

---

## Features

| # | Feature | Details |
|---|---------|---------|
| 1 | **Live GPS Location** | Auto-detects your city on startup via IP geolocation (ipapi.co) |
| 2 | **Full-Screen Window** | Opens maximised; toggle true fullscreen with `F11`, exit with `Escape` |
| 3 | **Search History** | Every search saved to `weather_history.json`; click any entry to re-fetch |
| 4 | **Weather Graph** | 4-panel chart (Temperature, Feels Like, Humidity, Wind) embedded in the app |
| 5 | **3-Day Forecast** | Daily high/low with emoji weather icons |
| 6 | **Hourly Strip** | 8 time slots for today (every 3 hours) |
| 7 | **°C / °F Toggle** | Switches all values and graph instantly without re-fetching |
| 8 | **Scrollable UI** | Mouse-wheel scroll through all content |
| 9 | **Error Handling** | Handles bad location, no internet, timeout, and unknown city gracefully |

---

## Project Structure

```
Weather app/
├── weather_app.py        ← Main application
├── requirements.txt      ← Python dependencies
├── weather_history.json  ← Auto-created when you first search
└── README.md             ← This file
```

---

## Requirements

- Python **3.8+**
- Tkinter (bundled with Python on Windows — no extra install needed)
- `requests` library
- `matplotlib` library

---

## Installation & Setup

### Step 1 — Clone or download the project

Place `weather_app.py` and `requirements.txt` in the same folder.

### Step 2 — Install dependencies

Open a terminal in the project folder and run:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install requests matplotlib
```

### Step 3 — Run the app

```bash
python weather_app.py
```

That's it. No API key, no config, no signup.

---

## How to Use

| Action | How |
|--------|-----|
| Auto-detect location | Happens automatically on startup |
| Search a city | Type in the search box → press `Enter` or click **Search** |
| Use your location | Click the **📍 My Location** button |
| Switch units | Click **°C** or **°F** radio buttons in the toolbar |
| Fullscreen | Press `F11` or click the **⛶ Fullscreen** button |
| Exit fullscreen | Press `Escape` |
| Scroll content | Use mouse wheel or the scrollbar |
| Re-search from history | Click any entry in the right **📋 History** panel |
| Clear history | Click **🗑 Clear** in the history panel |

### Search examples that work
```
Mumbai
New York
London, UK
10001          (ZIP code)
Tokyo
Paris, France
DXB            (airport code)
Eiffel Tower   (landmark)
```

---

## Graph — What's Shown

The graph section at the bottom shows **4 subplots** for today's hourly data:

```
┌──────────────────┬──────────────────┐
│  Temperature     │  Feels Like      │
│  (°C or °F)      │  (°C or °F)      │
├──────────────────┼──────────────────┤
│  Humidity (%)    │  Wind Speed      │
│                  │  (km/h or mph)   │
└──────────────────┴──────────────────┘
```

Each chart shows annotated data points, a shaded area fill, and dark-themed styling.

---

## Bugs Fixed (v2.1)

| Bug | Fix Applied |
|-----|------------|
| `fill_between` crash on string x-axis | Changed to numeric indices; labels set separately |
| `tight_layout=True` in `Figure()` constructor (deprecated) | Moved to `fig.tight_layout()` method call |
| History listbox index mismatch (multi-line entries) | Changed to single-line entries; added bounds check |
| `plt.Figure` usage (wrong class) | Replaced with `matplotlib.figure.Figure` |
| `__file__` not defined in some run contexts | Added `os.getcwd()` fallback for `HISTORY_FILE` path |
| Old matplotlib figures accumulating in memory | `plt.close(fig)` called before building new graph |

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Search current input |
| `F11` | Toggle fullscreen |
| `Escape` | Exit fullscreen |
| Mouse wheel | Scroll content |

---

## Troubleshooting

**"Location detection failed"**  
→ Your network may block ipapi.co. Just type a city manually — it works fine.

**"City not found" error**  
→ Try adding the country: `Springfield, USA`. For ZIPs, add country code: `10001,us`.

**Graph not showing**  
→ Make sure matplotlib is installed: `pip install matplotlib`

**Pylance shows import errors for matplotlib in VS Code**  
→ Run `pip install matplotlib` in the **same terminal VS Code uses**, then reload the window (`Ctrl+Shift+P` → Reload Window).

**App opens but looks tiny**  
→ The app starts maximised (`zoomed`). If it doesn't, press `F11` for fullscreen.

---

## Dependencies

```
requests==2.32.3
matplotlib==3.9.2
```

*Tkinter is bundled with Python — no separate install needed on Windows.*
