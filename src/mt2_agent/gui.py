"""
Tkinter control panel for the Metin2 Agent.

Main thread: tkinter.  Bot loop: daemon thread.
GUI mutates ScheduledTask.enabled / .interval / .params directly.
"""

import tkinter as tk
import logging

logger = logging.getLogger(__name__)

# ── palette — warm dark ────────────────────────────────────────────────────
BG          = "#2b2d31"
BG_SEC      = "#313338"
BG_CARD     = "#383a40"
BG_HOVER    = "#3f4147"
FG          = "#e0e1e5"
FG_DIM      = "#8b8d93"
FG_MUTED    = "#5c5e66"
BORDER      = "#44464d"
GREEN       = "#57d28f"
GREEN_DIM   = "#2d6b4a"
RED         = "#ed5565"
AMBER       = "#f0b232"
TOGGLE_OFF  = "#5c5e66"
INPUT_BG    = "#2b2d31"
INPUT_BD    = "#4e5058"
INPUT_FOCUS = "#5a8dee"
HEADER_BG   = "#1e1f22"
ACCENT      = "#5a8dee"

FONT        = "Segoe UI"
FONT_MONO   = "Consolas"
FONT_SM     = 9
FONT_XS     = 8

# ── feature definitions ───────────────────────────────────────────────────
# No default values for "on" or "interval" — those come from args/agent at
# runtime via set_agent().  Only static UI metadata lives here.

FEATURES = [
    {"id": "login",           "icon": "⏎", "label": "Auto-Login",      "desc": "Re-login on disconnect",    "no_interval": True, "expandable": "login"},
    {"id": "respawn",         "icon": "↻", "label": "Auto-Respawn",    "desc": "Respawn on death",          "no_interval": True, "expandable": "respawn"},
    {"id": "auto-cast",       "icon": "✦", "label": "Auto-Cast",       "desc": "Cycle hotkey spells",       "no_interval": True, "expandable": "auto-cast"},
    {"id": "auto-pickup",     "icon": "◇", "label": "Auto-Pickup",     "desc": "Pick up dropped items",     "tooltip": "Frequency of pressing the pick up key"},
    {"id": "auto-cape",       "icon": "⛨", "label": "Bravery Cape",    "desc": "Activate bravery cape",     "tooltip": "Frequency of pressing the bravery cape key"},
    {"id": "stuck-detection", "icon": "⊘", "label": "Stuck Detection", "desc": "Detect & unstick",          "expandable": "stuck",   "show_threshold": True, "tooltip": "How long in same place before detecting as stuck"},
    {"id": "auto-target",     "icon": "◎", "label": "Auto-Target",     "desc": "YOLO detection targeting",  "expandable": "target",  "tooltip": "How often to click on targets"},
    {"id": "captcha",         "icon": "⬡", "label": "Captcha Solver",  "desc": "Auto-solve captcha",        "no_interval": True, "expandable": "captcha"},
    {"id": "biolog",          "icon": "⬢", "label": "Biolog",          "desc": "Biolog hand-in",            "tooltip": "How often to try to submit biolog items"},
    {"id": "attack",          "icon": "⚔", "label": "Attack Hold",     "desc": "Hold spacebar",             "no_interval": True},
    {"id": "screenshots",     "icon": "📷", "label": "Screenshots",     "desc": "Periodic screenshots",      "expandable": "screenshots", "tooltip": "How often to take screenshots"},
]

STUCK_PARAMS = [
    {"key": "stuck_interval",         "label": "Check interval", "unit": "sec",  "min": 1,    "max": 60,   "type": float},
    {"key": "unstuck_threshold",      "label": "Threshold",      "unit": "sec",  "min": 5,    "max": 300,  "type": int,   "task_param": True},
    {"key": "unstuck_clicks",         "label": "Clicks",         "unit": "",     "min": 1,    "max": 100,  "type": int,   "task_param": True},
    {"key": "unstuck_interval",       "label": "Click delay",    "unit": "sec",  "min": 0.01, "max": 2.0,  "type": float, "task_param": True},
    {"key": "unstuck_center_radius",  "label": "Radius",         "unit": "%",    "min": 0.1,  "max": 1.0,  "type": float, "task_param": True},
]

LOGIN_PARAMS = [
    {"key": "login_interval", "label": "Check interval", "unit": "sec", "min": 1, "max": 60, "type": float},
]

RESPAWN_PARAMS = [
    {"key": "respawn_interval", "label": "Check interval", "unit": "sec", "min": 1, "max": 60, "type": float},
]

AUTOCAST_PARAMS = [
    {"key": "spells_interval", "label": "Check interval", "unit": "sec", "min": 0.5, "max": 30, "type": float},
]

CAPTCHA_PARAMS = [
    {"key": "captcha_interval", "label": "Check interval", "unit": "sec", "min": 1, "max": 60, "type": float},
]

TARGET_PARAMS = [
    {"key": "target_boss",    "label": "Boss priority",    "min": 0, "max": 10, "type": int, "task_param": True},
    {"key": "target_boulder", "label": "Boulder priority", "min": 0, "max": 10, "type": int, "task_param": True},
    {"key": "target_enemy",   "label": "Enemy priority",   "min": 0, "max": 10, "type": int, "task_param": True},
    {"key": "target_random",  "label": "Random priority",  "min": 0, "max": 10, "type": int, "task_param": True},
]

SCREENSHOT_PARAMS = [
    {"key": "screenshots_events", "label": "Event screenshots", "desc": "Capture on login, respawn, stuck, captcha"},
]

PATH_PARAMS = [
    {"key": "obj_model_path",                "label": "YOLO model"},
    {"key": "asset_icon_dir",                "label": "Icons dir"},
    {"key": "screenshot_path",               "label": "Screenshots"},
    {"key": "captcha_trigger_template_path",  "label": "Captcha template"},
    {"key": "debug_folder",                   "label": "Debug folder"},
    {"key": "debug_folder_screenshots",       "label": "Debug screenshots"},
]

# How often (ms) the GUI polls the agent for status changes.
_STATUS_POLL_MS = 500


# ═══════════════════════════════════════════════════════════════════════════
# Widgets
# ═══════════════════════════════════════════════════════════════════════════

class Toggle(tk.Canvas):
    W, H, PAD, R = 36, 20, 2, 8

    def __init__(self, master, on=False, command=None, **kw):
        bg = kw.pop("bg", BG_CARD)
        super().__init__(master, width=self.W, height=self.H,
                         highlightthickness=0, bd=0, bg=bg, **kw)
        self._on = on
        self._cmd = command
        self._track = self._rounded_rect(self.PAD, self.PAD,
                                          self.W - self.PAD, self.H - self.PAD,
                                          r=9, fill=GREEN if on else TOGGLE_OFF, outline="")
        kx = self._kx()
        cy = self.H // 2
        self._knob = self.create_oval(kx - self.R, cy - self.R, kx + self.R, cy + self.R,
                                       fill="#ffffff", outline="")
        self.bind("<Button-1>", self._click)
        self.config(cursor="hand2")

    def _kx(self):
        return (self.W - self.PAD - self.R - 1) if self._on else (self.PAD + self.R + 1)

    def _rounded_rect(self, x1, y1, x2, y2, r=8, **kw):
        pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2,
               x2-r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]
        return self.create_polygon(pts, smooth=True, **kw)

    def _click(self, _e=None):
        self._on = not self._on
        self._draw()
        if self._cmd:
            self._cmd(self._on)

    def _draw(self):
        self.itemconfig(self._track, fill=GREEN if self._on else TOGGLE_OFF)
        kx = self._kx()
        cy = self.H // 2
        self.coords(self._knob, kx-self.R, cy-self.R, kx+self.R, cy+self.R)

    def set(self, v):
        self._on = v
        self._draw()

    def get(self):
        return self._on


class NumInput(tk.Frame):
    """Compact numeric entry with optional unit label."""

    def __init__(self, master, value, min_v, max_v, dtype=float, unit="", width=5,
                 on_change=None, **kw):
        bg = kw.pop("bg", BG_CARD)
        super().__init__(master, bg=bg)
        self._min, self._max, self._dtype = min_v, max_v, dtype
        self._cb = on_change
        self._var = tk.StringVar(value=self._fmt(value))

        self._entry = tk.Entry(self, textvariable=self._var, width=width, justify="right",
                               font=(FONT_MONO, FONT_SM), bg=INPUT_BG, fg=FG,
                               relief="flat", bd=0, highlightthickness=1,
                               highlightcolor=INPUT_FOCUS, highlightbackground=INPUT_BD,
                               insertbackground=FG)
        self._entry.pack(side="left", ipady=1)
        self._entry.bind("<FocusOut>", self._validate)
        self._entry.bind("<Return>", self._validate)

        if unit:
            tk.Label(self, text=unit, font=(FONT, FONT_XS), bg=bg, fg=FG_DIM
                     ).pack(side="left", padx=(2, 0))

    def _fmt(self, v):
        if self._dtype is int:
            return str(int(v))
        return f"{v:.2f}" if v != int(v) else f"{v:.1f}"

    def _validate(self, _e=None):
        try:
            v = self._dtype(self._var.get().strip())
        except (ValueError, TypeError):
            v = self._min
        v = max(self._min, min(self._max, v))
        self._var.set(self._fmt(v))
        if self._cb:
            self._cb(v)

    def get(self):
        try:
            return self._dtype(max(self._min, min(self._max, self._dtype(self._var.get().strip()))))
        except (ValueError, TypeError):
            return self._min

    def set(self, v):
        self._var.set(self._fmt(v))


class TextInput(tk.Frame):
    """Single-line text entry for path params."""

    def __init__(self, master, value="", on_change=None, **kw):
        bg = kw.pop("bg", BG_CARD)
        super().__init__(master, bg=bg)
        self._cb = on_change
        self._var = tk.StringVar(value=value)

        self._entry = tk.Entry(self, textvariable=self._var, width=30, font=(FONT_MONO, FONT_XS),
                               bg=INPUT_BG, fg=FG, relief="flat", bd=0,
                               highlightthickness=1, highlightcolor=INPUT_FOCUS,
                               highlightbackground=INPUT_BD, insertbackground=FG)
        self._entry.pack(fill="x", ipady=1)
        self._entry.bind("<FocusOut>", self._commit)
        self._entry.bind("<Return>", self._commit)

    def _commit(self, _e=None):
        if self._cb:
            self._cb(self._var.get().strip())

    def get(self):
        return self._var.get().strip()

    def set(self, v):
        self._var.set(str(v))


# ═══════════════════════════════════════════════════════════════════════════
# Tooltip
# ═══════════════════════════════════════════════════════════════════════════

class Tooltip:
    """Hover tooltip for any widget."""

    def __init__(self, widget, text):
        self._widget = widget
        self._text = text
        self._tw = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _e=None):
        x = self._widget.winfo_rootx() + self._widget.winfo_width() // 2
        y = self._widget.winfo_rooty() - 4
        self._tw = tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-topmost", True)
        lbl = tk.Label(tw, text=self._text, font=(FONT, FONT_XS),
                       bg="#1e1f22", fg=FG_DIM, relief="solid", bd=1,
                       padx=6, pady=3)
        lbl.pack()
        tw.update_idletasks()
        tw_w = tw.winfo_width()
        tw.wm_geometry(f"+{x - tw_w // 2}+{y - tw.winfo_height()}")

    def _hide(self, _e=None):
        if self._tw:
            self._tw.destroy()
            self._tw = None


# ═══════════════════════════════════════════════════════════════════════════
# Feature row
# ═══════════════════════════════════════════════════════════════════════════

class FeatureRow(tk.Frame):
    def __init__(self, master, desc, on_toggle, on_interval, on_threshold=None):
        super().__init__(master, bg=BG_CARD, padx=10, pady=5)
        self.desc = desc
        self._on_toggle = on_toggle
        self._on_interval = on_interval
        self._on_threshold = on_threshold

        self.columnconfigure(2, weight=1)

        # toggle
        self.toggle = Toggle(self, on=False, command=self._toggled, bg=BG_CARD)
        self.toggle.grid(row=0, column=0, padx=(0, 6))

        # icon
        tk.Label(self, text=desc["icon"], font=(FONT, 11), bg=BG_CARD, fg=ACCENT,
                 width=2).grid(row=0, column=1, padx=(0, 4))

        # label + desc
        info = tk.Frame(self, bg=BG_CARD)
        info.grid(row=0, column=2, sticky="w")
        tk.Label(info, text=desc["label"], font=(FONT, FONT_SM, "bold"),
                 bg=BG_CARD, fg=FG).pack(side="left")
        tk.Label(info, text=f"  {desc['desc']}", font=(FONT, FONT_XS),
                 bg=BG_CARD, fg=FG_DIM).pack(side="left")

        # Right-hand side widget: either interval, threshold, or nothing
        self.interval_input = None
        self.threshold_input = None

        if desc.get("show_threshold"):
            # Stuck detection: show threshold (seconds) instead of interval
            self.threshold_input = NumInput(
                self, value=0, min_v=5, max_v=300,
                dtype=int, unit="s", width=5,
                on_change=self._threshold_changed, bg=BG_CARD,
            )
            self.threshold_input.grid(row=0, column=3, padx=(8, 0))
            if desc.get("tooltip"):
                Tooltip(self.threshold_input, desc["tooltip"])
        elif not desc.get("no_interval"):
            # Normal feature: show interval
            self.interval_input = NumInput(
                self, value=0, min_v=0, max_v=600,
                dtype=float, unit="s", width=5,
                on_change=self._interval_changed, bg=BG_CARD,
            )
            self.interval_input.grid(row=0, column=3, padx=(8, 0))
            if desc.get("tooltip"):
                Tooltip(self.interval_input, desc["tooltip"])

    def _toggled(self, v):
        self._on_toggle(self.desc["id"], v)

    def _interval_changed(self, v):
        self._on_interval(self.desc["id"], v)

    def _threshold_changed(self, v):
        if self._on_threshold:
            self._on_threshold(v)

    def set_enabled(self, v):
        self.toggle.set(v)

    def set_interval(self, v):
        if self.interval_input:
            self.interval_input.set(v)

    def set_threshold(self, v):
        if self.threshold_input:
            self.threshold_input.set(v)


# ═══════════════════════════════════════════════════════════════════════════
# Collapsible section
# ═══════════════════════════════════════════════════════════════════════════

class CollapsibleSection(tk.Frame):
    def __init__(self, master, title, **kw):
        super().__init__(master, bg=BG_SEC, **kw)
        self._open = False

        self._header = tk.Frame(self, bg=BG_SEC, cursor="hand2")
        self._header.pack(fill="x")

        self._arrow = tk.Label(self._header, text="▸", font=(FONT, FONT_XS),
                                bg=BG_SEC, fg=FG_DIM, width=2)
        self._arrow.pack(side="left", padx=(12, 0))

        tk.Label(self._header, text=title, font=(FONT, FONT_XS, "bold"),
                 bg=BG_SEC, fg=FG_DIM).pack(side="left")

        self._body = tk.Frame(self, bg=BG_SEC, padx=24, pady=4)
        # body starts hidden

        self._header.bind("<Button-1>", self._toggle)
        for child in self._header.winfo_children():
            child.bind("<Button-1>", self._toggle)

    def _toggle(self, _e=None):
        self._open = not self._open
        if self._open:
            self._arrow.config(text="▾")
            self._body.pack(fill="x")
        else:
            self._arrow.config(text="▸")
            self._body.pack_forget()

    @property
    def body(self):
        return self._body


# ═══════════════════════════════════════════════════════════════════════════
# Main panel
# ═══════════════════════════════════════════════════════════════════════════

class ControlPanel(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Metin2 Agent")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self._agent = None
        self._args = None
        self._cards: dict[str, FeatureRow] = {}
        self._param_inputs: dict[str, NumInput | TextInput] = {}
        self._toggle_inputs: dict[str, Toggle] = {}

        self._build_header()
        self._build_features()
        self._build_paths_section()
        self._build_footer()

    # ── header ──────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = tk.Frame(self, bg=HEADER_BG, padx=14, pady=8)
        hdr.pack(fill="x")

        tk.Label(hdr, text="⚙", font=(FONT, 14), bg=HEADER_BG, fg=ACCENT
                 ).pack(side="left")
        tk.Label(hdr, text=" METIN2 AGENT", font=(FONT, 12, "bold"),
                 bg=HEADER_BG, fg=FG).pack(side="left")

        # status — updated by polling agent._agent_active
        self._status = tk.Label(hdr, text="● STARTING", font=(FONT, FONT_SM, "bold"),
                                bg=HEADER_BG, fg=FG_DIM)
        self._status.pack(side="right", padx=(8, 0))

        # debug toggle
        self._debug_var = tk.BooleanVar(value=False)
        self._debug_toggle = Toggle(hdr, on=False, command=self._on_debug, bg=HEADER_BG)
        self._debug_toggle.pack(side="right", padx=(0, 4))
        tk.Label(hdr, text="DEBUG", font=(FONT, FONT_XS, "bold"),
                 bg=HEADER_BG, fg=FG_DIM).pack(side="right", padx=(0, 4))

    # ── features ────────────────────────────────────────────────────────

    def _build_features(self):
        container = tk.Frame(self, bg=BG, padx=8, pady=4)
        container.pack(fill="both", expand=True)

        for i, desc in enumerate(FEATURES):
            if i > 0:
                tk.Frame(container, height=1, bg=BORDER).pack(fill="x", padx=4)

            row = FeatureRow(
                container, desc,
                on_toggle=self._handle_toggle,
                on_interval=self._handle_interval,
                on_threshold=self._handle_stuck_threshold if desc.get("show_threshold") else None,
            )
            row.pack(fill="x")
            self._cards[desc["id"]] = row

            # expandable sub-sections
            if desc.get("expandable") == "login":
                self._login_section = CollapsibleSection(container, "Auto-Login Settings")
                self._login_section.pack(fill="x")
                self._build_interval_params(self._login_section.body, LOGIN_PARAMS, "login")
                self._build_character_select_row(self._login_section.body)

            elif desc.get("expandable") == "respawn":
                self._respawn_section = CollapsibleSection(container, "Auto-Respawn Settings")
                self._respawn_section.pack(fill="x")
                self._build_interval_params(self._respawn_section.body, RESPAWN_PARAMS, "respawn")

            elif desc.get("expandable") == "auto-cast":
                self._autocast_section = CollapsibleSection(container, "Auto-Cast Settings")
                self._autocast_section.pack(fill="x")
                self._build_interval_params(self._autocast_section.body, AUTOCAST_PARAMS, "auto-cast")

            elif desc.get("expandable") == "stuck":
                self._stuck_section = CollapsibleSection(container, "Stuck Detection Settings")
                self._stuck_section.pack(fill="x")
                self._build_stuck_params(self._stuck_section.body)

            elif desc.get("expandable") == "target":
                self._target_section = CollapsibleSection(container, "Target Priority Settings")
                self._target_section.pack(fill="x")
                self._build_target_params(self._target_section.body)

            elif desc.get("expandable") == "captcha":
                self._captcha_section = CollapsibleSection(container, "Captcha Solver Settings")
                self._captcha_section.pack(fill="x")
                self._build_interval_params(self._captcha_section.body, CAPTCHA_PARAMS, "captcha")

            elif desc.get("expandable") == "screenshots":
                self._screenshots_section = CollapsibleSection(container, "Screenshot Settings")
                self._screenshots_section.pack(fill="x")
                self._build_screenshot_params(self._screenshots_section.body)

    def _build_stuck_params(self, parent):
        for p in STUCK_PARAMS:
            row = tk.Frame(parent, bg=BG_SEC)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=p["label"], font=(FONT, FONT_XS), bg=BG_SEC, fg=FG_DIM,
                     width=12, anchor="w").pack(side="left")

            if p["key"] == "stuck_interval":
                # This is the task interval — route changes through _handle_interval
                inp = NumInput(row, value=0, min_v=p["min"], max_v=p["max"],
                              dtype=p["type"], unit=p["unit"], width=6,
                              on_change=lambda v: self._handle_interval("stuck-detection", v),
                              bg=BG_SEC)
            elif p.get("task_param"):
                # Task param — route changes through _set_task_param
                inp = NumInput(row, value=0, min_v=p["min"], max_v=p["max"],
                              dtype=p["type"], unit=p["unit"], width=6,
                              on_change=lambda v, k=p["key"]: self._set_task_param("stuck-detection", k, v),
                              bg=BG_SEC)
            else:
                inp = NumInput(row, value=0, min_v=p["min"], max_v=p["max"],
                              dtype=p["type"], unit=p["unit"], width=6,
                              on_change=lambda v, k=p["key"]: self._set_arg(k, v), bg=BG_SEC)
            inp.pack(side="right")
            self._param_inputs[p["key"]] = inp

    def _build_interval_params(self, parent, params, feature_id):
        """Build a collapsible section that contains interval params for a feature.

        The interval key (e.g. 'login_interval') routes changes through
        _handle_interval so the ScheduledTask.interval is updated live.
        """
        for p in params:
            row = tk.Frame(parent, bg=BG_SEC)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=p["label"], font=(FONT, FONT_XS), bg=BG_SEC, fg=FG_DIM,
                     width=12, anchor="w").pack(side="left")
            inp = NumInput(row, value=0, min_v=p["min"], max_v=p["max"],
                          dtype=p["type"], unit=p["unit"], width=6,
                          on_change=lambda v, fid=feature_id: self._handle_interval(fid, v),
                          bg=BG_SEC)
            inp.pack(side="right")
            self._param_inputs[p["key"]] = inp

    def _build_character_select_row(self, parent):
        """Add a character-select toggle + interval inside the login collapsible section."""
        # separator
        tk.Frame(parent, height=1, bg=BORDER).pack(fill="x", pady=(4, 2))

        row = tk.Frame(parent, bg=BG_SEC)
        row.pack(fill="x", pady=1)

        tk.Label(row, text="Char select", font=(FONT, FONT_XS), bg=BG_SEC, fg=FG_DIM,
                 width=12, anchor="w").pack(side="left")

        self._char_select_toggle = Toggle(
            row, on=False,
            command=lambda v: self._handle_toggle("character-select", v),
            bg=BG_SEC,
        )
        self._char_select_toggle.pack(side="left", padx=(4, 8))

        inp = NumInput(row, value=0, min_v=1, max_v=60,
                      dtype=float, unit="sec", width=6,
                      on_change=lambda v: self._handle_interval("character-select", v),
                      bg=BG_SEC)
        inp.pack(side="right")
        self._param_inputs["character_select_interval"] = inp

    def _build_target_params(self, parent):
        for p in TARGET_PARAMS:
            row = tk.Frame(parent, bg=BG_SEC)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=p["label"], font=(FONT, FONT_XS), bg=BG_SEC, fg=FG_DIM,
                     width=16, anchor="w").pack(side="left")

            if p.get("task_param"):
                inp = NumInput(row, value=0, min_v=p["min"], max_v=p["max"],
                              dtype=p["type"], unit="", width=4,
                              on_change=lambda v, k=p["key"]: self._set_task_param("auto-target", k, v),
                              bg=BG_SEC)
            else:
                inp = NumInput(row, value=0, min_v=p["min"], max_v=p["max"],
                              dtype=p["type"], unit="", width=4,
                              on_change=lambda v, k=p["key"]: self._set_arg(k, v), bg=BG_SEC)
            inp.pack(side="right")
            self._param_inputs[p["key"]] = inp

    def _build_screenshot_params(self, parent):
        for p in SCREENSHOT_PARAMS:
            row = tk.Frame(parent, bg=BG_SEC)
            row.pack(fill="x", pady=1)

            tk.Label(row, text=p["label"], font=(FONT, FONT_XS), bg=BG_SEC, fg=FG_DIM,
                     width=16, anchor="w").pack(side="left")

            if "desc" in p:
                tk.Label(row, text=p["desc"], font=(FONT, FONT_XS), bg=BG_SEC, fg=FG_MUTED
                         ).pack(side="left", padx=(4, 0))

            toggle = Toggle(row, on=False,
                            command=lambda v, k=p["key"]: self._set_arg(k, v), bg=BG_SEC)
            toggle.pack(side="right")
            self._toggle_inputs[p["key"]] = toggle

    # ── paths section ───────────────────────────────────────────────────

    def _build_paths_section(self):
        sep = tk.Frame(self, height=1, bg=BORDER)
        sep.pack(fill="x", padx=12, pady=(4, 0))

        self._paths_section = CollapsibleSection(self, "Paths & Advanced")
        self._paths_section.pack(fill="x", padx=8)

        for p in PATH_PARAMS:
            row = tk.Frame(self._paths_section.body, bg=BG_SEC)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=p["label"], font=(FONT, FONT_XS), bg=BG_SEC, fg=FG_DIM,
                     width=16, anchor="w").pack(side="left")
            inp = TextInput(row, value="",
                           on_change=lambda v, k=p["key"]: self._set_arg(k, v), bg=BG_SEC)
            inp.pack(side="right", fill="x", expand=True)
            self._param_inputs[p["key"]] = inp

    # ── footer ──────────────────────────────────────────────────────────

    def _build_footer(self):
        tk.Frame(self, height=1, bg=BORDER).pack(fill="x", padx=12, pady=(4, 0))

        ftr = tk.Frame(self, bg=BG, padx=14, pady=6)
        ftr.pack(fill="x")

        self._pause_btn = tk.Button(
            ftr, text="⏸  PAUSE ALL", font=(FONT, FONT_SM, "bold"),
            bg=AMBER, fg="#1e1f22", relief="flat", cursor="hand2",
            bd=0, padx=12, pady=3, activebackground="#d99a1f",
            command=self._toggle_pause,
        )
        self._pause_btn.pack(side="right")

        tk.Label(ftr, text="changes apply immediately", font=(FONT, FONT_XS),
                 bg=BG, fg=FG_MUTED).pack(side="left")

    # ── agent binding ───────────────────────────────────────────────────

    def set_agent(self, agent):
        self._agent = agent
        self._args = agent.args

        # Map feature ids to their interval param keys (for features whose
        # interval was moved into a collapsible section).
        _FEATURE_INTERVAL_KEY = {
            "login":            "login_interval",
            "character-select": "character_select_interval",
            "respawn":          "respawn_interval",
            "auto-cast":        "spells_interval",
            "captcha":          "captcha_interval",
            "stuck-detection":  "stuck_interval",
        }

        # sync feature toggles & intervals from the live ScheduledTask objects
        for name, task in agent.all_tasks.items():
            card = self._cards.get(name)
            if card is None:
                continue
            card.set_enabled(task.enabled)
            if card.interval_input is not None:
                card.set_interval(task.interval)

            # sync interval into collapsible panel if applicable
            interval_key = _FEATURE_INTERVAL_KEY.get(name)
            if interval_key and interval_key in self._param_inputs:
                self._param_inputs[interval_key].set(task.interval)

        # stuck detection: sync threshold into the row widget
        stuck_card = self._cards.get("stuck-detection")
        stuck_task = agent.all_tasks.get("stuck-detection")
        if stuck_card and stuck_card.threshold_input and stuck_task:
            stuck_card.threshold_input.set(stuck_task.params.get("unstuck_threshold", 60))

        # character-select: sync toggle + interval into the login sub-section
        cs_task = agent.all_tasks.get("character-select")
        if cs_task and hasattr(self, "_char_select_toggle"):
            self._char_select_toggle.set(cs_task.enabled)
            inp = self._param_inputs.get("character_select_interval")
            if inp:
                inp.set(cs_task.interval)

        # sync task params into their GUI inputs
        for name, task in agent.all_tasks.items():
            for key, value in task.params.items():
                inp = self._param_inputs.get(key)
                if inp is not None:
                    inp.set(value)

        # sync args-based params (skip interval keys and task-param keys already handled)
        _handled_keys = set(_FEATURE_INTERVAL_KEY.values())
        for task in agent.all_tasks.values():
            _handled_keys.update(task.params.keys())

        for key, inp in self._param_inputs.items():
            if key in _handled_keys:
                continue
            val = getattr(self._args, key, None)
            if val is not None:
                inp.set(val)

        # sync toggle params (like screenshots_events)
        for key, toggle in self._toggle_inputs.items():
            val = getattr(self._args, key, None)
            if val is not None:
                toggle.set(bool(val))

        # sync debug
        self._debug_toggle.set(self._args.debug)

        # start polling agent status
        self._poll_agent_status()

    # ── status polling ──────────────────────────────────────────────────

    def _poll_agent_status(self):
        """Periodically read agent._agent_active and update the header."""
        if self._agent is not None:
            active = self._agent._agent_active
            if active:
                self._status.config(text="● RUNNING", fg=GREEN)
                self._pause_btn.config(text="⏸  PAUSE ALL", bg=AMBER, activebackground="#d99a1f")
            else:
                self._status.config(text="● PAUSED", fg=AMBER)
                self._pause_btn.config(text="▶  RESUME", bg=GREEN, activebackground="#3fb873")

        self.after(_STATUS_POLL_MS, self._poll_agent_status)

    # ── callbacks ───────────────────────────────────────────────────────

    def _handle_toggle(self, fid, enabled):
        logger.info("GUI: %s -> %s", fid, "ON" if enabled else "OFF")
        if self._agent is None:
            return
        task = self._agent.all_tasks.get(fid)
        if task:
            task.enabled = enabled

    def _handle_interval(self, fid, interval):
        logger.debug("GUI: %s interval -> %.1f", fid, interval)
        if self._agent is None:
            return
        task = self._agent.all_tasks.get(fid)
        if task:
            task.interval = interval

    def _handle_stuck_threshold(self, value):
        """Update the stuck-detection task's threshold param from the row widget."""
        self._set_task_param("stuck-detection", "unstuck_threshold", value)
        # Also keep the collapsible panel input in sync
        inp = self._param_inputs.get("unstuck_threshold")
        if inp:
            inp.set(value)

    def _set_task_param(self, task_id, key, value):
        """Update a task.params[key] value directly on the live ScheduledTask."""
        if self._agent is None:
            return
        task = self._agent.all_tasks.get(task_id)
        if task:
            task.params[key] = value
            logger.debug("GUI: %s.params[%s] = %s", task_id, key, value)

    def _set_arg(self, key, value):
        if self._args is not None:
            setattr(self._args, key, value)
            logger.debug("GUI: args.%s = %s", key, value)

    def _on_debug(self, val):
        if self._args is not None:
            self._args.debug = val
            if val:
                logging.getLogger("mt2_agent").setLevel(logging.DEBUG)
            else:
                logging.getLogger("mt2_agent").setLevel(logging.INFO)
            logger.info("GUI: debug = %s", val)

    def _toggle_pause(self):
        if self._agent is None:
            return

        if self._agent._agent_active:
            # Pause: disable all tasks
            for task in self._agent.all_tasks.values():
                task.enabled = False
            for card in self._cards.values():
                card.set_enabled(False)
            if hasattr(self, "_char_select_toggle"):
                self._char_select_toggle.set(False)
        else:
            # Resume: re-enable tasks that were on by default (read from args)
            _ARG_FLAG_FOR_FEATURE = {
                "login": "login",
                "character-select": "character_select",
                "respawn": "respawn",
                "auto-cast": "spells",
                "auto-pickup": "pickup",
                "auto-cape": "cape",
                "stuck-detection": "stuck",
                "auto-target": "target",
                "captcha": "captcha",
                "biolog": "biolog",
                "attack": "attack",
                "screenshots": "screenshots",
            }
            for name, task in self._agent.all_tasks.items():
                flag = _ARG_FLAG_FOR_FEATURE.get(name)
                should_enable = getattr(self._args, flag, False) if flag else False
                task.enabled = should_enable
                card = self._cards.get(name)
                if card:
                    card.set_enabled(should_enable)
            # sync character-select toggle (no card, lives in login section)
            cs_flag = _ARG_FLAG_FOR_FEATURE.get("character-select")
            cs_enable = getattr(self._args, cs_flag, False) if cs_flag else False
            if hasattr(self, "_char_select_toggle"):
                self._char_select_toggle.set(cs_enable)

        # The status label will update on the next poll cycle