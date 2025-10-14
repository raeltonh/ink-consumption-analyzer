from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple, TYPE_CHECKING

import streamlit as st
from PIL import Image as PILImage

DEFAULT_APP_TITLE = "Presto MAX — ml/m² & ROI Analyzer"
DEFAULT_APP_SUBTITLE = "ml/m², pixels, costs and A×B comparisons"
ASSETS = Path(__file__).parent / "assets"


def _resolve_page_icon() -> str | "Image.Image":
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        candidate = ASSETS / f"page_icon{ext}"
        if candidate.exists():
            try:
                return PILImage.open(candidate)
            except Exception:
                continue
    fallback = ASSETS / "app-icon.png"
    if fallback.exists():
        try:
            return PILImage.open(fallback)
        except Exception:
            pass
    return "🖨️"


st.set_page_config(page_title=DEFAULT_APP_TITLE, page_icon=_resolve_page_icon(), layout="wide")

# Ensure Streamlit config dir exists early
os.environ.setdefault("HOME", "/tmp")
(Path(os.environ["HOME"]) / ".streamlit").mkdir(parents=True, exist_ok=True)
# ---------- Fast/Safe boot block ----------
SAFE_MODE = (_os.getenv("INK_SAFE", "1") != "0")
try:
    _toggle_val = st.session_state.get("SAFE_MODE_TOGGLE", SAFE_MODE)
    _toggle_val = st.sidebar.toggle("⚡ Fast/Safe mode (abrir leve)", value=_toggle_val, key="SAFE_MODE_TOGGLE")
    SAFE_MODE = bool(_toggle_val)
except Exception:
    pass

def safe_section(title, fn):
    try:
        with st.expander(title, expanded=True):
            fn()
    except Exception as e:
        st.error(f"⚠️ {title} falhou: {e}")
        if st.checkbox(f"Mostrar detalhes ({title})", key=f"tb_{title}"):
            st.exception(e)

def _mpl():
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    return plt, PdfPages
# ---------- End fast/safe block ----------

# Pillow safety
Image.MAX_IMAGE_PIXELS = None
ImageFile.LOAD_TRUNCATED_IMAGES = True
warnings.simplefilter("ignore", Image.DecompressionBombWarning)

# ======= THEME: LIGHT PROFESSIONAL (background), dark texts, soft contrast.
st.markdown("""
<style>
:root{
  --ink-bg: #f6f8fc; /* App background: very light gray */
  --ink-panel: #f3f4f6; /* Cards/panels: light gray */
  --ink-edge: #e6e9f1; /* Panel border: subtle light gray */
  --ink-text: #111827; /* Primary text: dark gray */
  --ink-muted: #6b7280; /* Secondary text (captions): medium gray */
  --ink-chip: #eef2f7; /* Chips / secondary buttons */
  --ink-accent: #2563eb; /* Accent (blue): primary buttons, etc. */
  --ink-white: #ffffff; /* White */
  --ink-shadow: 0 1px 2px rgba(16,24,40,.08), 0 4px 12px rgba(16,24,40,.06); /* Elegant shadow */
}

/* Global background and typography */
html, body, [data-testid="stAppViewContainer"], .block-container{
  background:var(--ink-bg) !important;
  color:var(--ink-text) !important;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  font-feature-settings:"cv02","cv03","cv04","cv11";
}

/* Texts */
h1,h2,h3,h4,h5,h6,
p, small, label, span, div,
.stMarkdown, [data-testid="stMarkdownContainer"] *{
  color:var(--ink-text) !important;
}

/* Captions/help */
[data-testid="stCaptionContainer"] *{ color:var(--ink-muted) !important; }

/* Cards/sections */
.section-card{
  background:var(--ink-panel);
  border:1px solid var(--ink-edge);
  border-radius:16px; padding:18px 20px;
  color:var(--ink-text);
  box-shadow: var(--ink-shadow);
}
/* Harmonize section headings/subtitles */
.section-title{ font-size: clamp(18px, 1.6vw, 22px); font-weight: 700; }

.section-subtitle{ font-size: 13px; color: var(--ink-muted); }

/* Info tables (alternative to st.metric) */

/* Align number/select/text/radio labels across grids */
.ink-fixed-grid [data-testid="stNumberInput"] > label,
.ink-fixed-grid [data-testid="stSelectbox"] > label,
.ink-fixed-grid [data-testid="stTextInput"] > label,
.ink-fixed-grid [data-testid="stRadio"] > label{
  min-height: 26px; display:block; white-space: nowrap;
}
.ink-fixed-grid [data-baseweb="select"]{ min-width: 120px; }
.ink-fixed-grid [data-testid="stRadio"]{ margin-bottom: 0 !important; min-height:96px; }
.ink-fixed-grid [data-testid="stRadio"] [role="radiogroup"]{ align-items: center; height: 100%; }

.info-card{
  background:var(--ink-panel);
  border:1px solid var(--ink-edge);
  border-radius:16px;
  padding:14px 16px;
  box-shadow:var(--ink-shadow);
}
.info-card .title{
  font-size: clamp(16px, 1.5vw, 20px);
  font-weight: 700;
  margin-bottom: 8px;
}
.info-card table{
  width:100%;
  border-collapse: collapse;
}
.info-card th, .info-card td{
  padding:10px 6px;
}
.info-card th{
  color: var(--ink-muted);
  font-weight: 600;
  text-align:left;
}
.info-card td:last-child{
  text-align:right;
}
.info-card tr.emph td:first-child{
  font-weight:700;
}

/* Metrics — sizes tuned for readability */
[data-testid="stMetric"]{
  background:var(--ink-panel);
  border:1px solid var(--ink-edge);
  border-radius:14px; padding:12px;
  box-shadow: var(--ink-shadow);
  min-height: 88px; /* room for value + label */
  min-width: 170px; /* prevent box narrower than the text */
}
/* prevent the inner wrapper from clipping long values */
[data-testid="stMetric"] > div{
  overflow: visible !important;
}
/* Metric labels: allow explicit line breaks and avoid clipping */
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] *{
  color:var(--ink-muted) !important;
  font-size: 12px !important;
  letter-spacing: .2px !important;
  /* allow explicit \n line-breaks in labels (e.g., "Variable\n/m²") */
  white-space: pre-wrap !important;
  /* don't break words like "m²" */
  word-break: normal !important;
  overflow-wrap: normal !important;
  hyphens: manual !important;
  /* avoid ellipsis/clipping */
  overflow: visible !important;
  text-overflow: clip !important;
}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] *{
  color:var(--ink-text) !important;
  /* a tad smaller so it fits narrow columns better */
  font-size: clamp(14px, 1.6vw, 24px) !important;
  line-height: 1.15 !important;
  font-variant-numeric: tabular-nums !important;
  /* keep the number in one line (e.g., "R$ 30.36") */
  white-space: nowrap !important;
  word-break: normal !important;
  overflow-wrap: normal !important;
  overflow: visible !important;
  text-overflow: clip !important;
  max-width: 100% !important;
  display: inline-block !important;         /* allow width to fit content */
  min-width: max-content !important;        /* never squeeze the number */
}

/* === Compact metrics (Compare A×B) === */
.cmp-compact [data-testid="stMetric"]{
  min-height: 84px;
  padding: 12px;
}
.cmp-compact [data-testid="stMetricLabel"],
.cmp-compact [data-testid="stMetricLabel"] *{
  font-size: 11px !important;
  letter-spacing: .15px !important;
  white-space: pre-wrap !important;   /* honor explicit line breaks */
  word-break: normal !important;
  overflow-wrap: normal !important;
  hyphens: manual !important;
}
.cmp-compact [data-testid="stMetricValue"],
.cmp-compact [data-testid="stMetricValue"] *{
  font-size: clamp(12px, 1.3vw, 18px) !important;
  line-height: 1.10 !important;
  white-space: nowrap !important;
  word-break: normal !important;
  overflow-wrap: normal !important;
}
/* headings um pouco menores só no Compare */
.cmp-compact .section-title{ font-size: clamp(16px, 1.3vw, 20px); }
.cmp-compact h4, .cmp-compact h5{ font-size: clamp(14px, 1.2vw, 18px); }
/* Stronger overrides so nothing gets clipped in Compare A×B */
.cmp-compact [data-testid="stMetric"] > div{
  overflow: visible !important;
}
.cmp-compact [data-testid="stMetric"]{
  min-width: 150px !important; /* gives the value room before wrapping */
}

/* Inputs */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] div[role="combobox"],
[data-testid="stDateInput"] input{
  color:var(--ink-text) !important;
  background:var(--ink-white) !important;
  border:1px solid var(--ink-edge) !important;
  border-radius:12px !important;
  box-shadow: none;
}
[data-testid="stNumberInput"] label,
[data-testid="stTextInput"] label,
[data-testid="stSelectbox"] label{ color:var(--ink-muted) !important; }

/* Foco */
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus,
[data-testid="stSelectbox"] div[role="combobox"]:focus-within,
[data-testid="stDateInput"] input:focus{
  border-color: var(--ink-accent) !important;
  box-shadow: 0 0 0 3px rgba(37,99,235,.25) !important;
  outline: none !important;
}

/* Radio/checkbox/switch labels */
div[role="radiogroup"] * , div[role="checkbox"] * , div[role="switch"] *{ color:var(--ink-text) !important; }

/* PRIMARY (novo e legado) */
.stButton button[data-testid="baseButton-primary"],
.stButton>button[kind="primary"]{
  background: var(--ink-accent) !important;
  color:#ffffff !important;
  border:1px solid var(--ink-accent) !important;
  border-radius:12px !important;
  padding:10px 14px !important;
  box-shadow: var(--ink-shadow);
  transition: transform .06s ease, box-shadow .2s ease, filter .2s ease;
}
.stButton button[data-testid="baseButton-primary"]:hover,
.stButton>button[kind="primary"]:hover{ transform: translateY(-1px); }
.stButton button[data-testid="baseButton-primary"]:active,
.stButton>button[kind="primary"]:active{ transform: translateY(0); }
.stButton button[data-testid="baseButton-primary"]:focus,
.stButton>button[kind="primary"]:focus{
  outline:none !important; box-shadow:0 0 0 3px rgba(37,99,235,.35) !important;
}

/* SECONDARY (novo e legado) */
.stButton button[data-testid="baseButton-secondary"],
.stButton>button[kind="secondary"]{
  background: var(--ink-chip) !important;
  color: var(--ink-text) !important;
  border: 1px solid var(--ink-edge) !important;
  border-radius: 12px !important;
  padding: 10px 14px !important;
  box-shadow: var(--ink-shadow);
}
.stButton button[data-testid="baseButton-secondary"]:hover,
.stButton>button[kind="secondary"]:hover{ filter: brightness(0.98); }

/* Chips/anchors para canais */
a.chan-btn, .chan-btn{
  background:var(--ink-chip);
  border:1px solid var(--ink-edge);
  color:var(--ink-text);
  border-radius:10px;
  padding:10px 14px;
  display:block;
  width:100%;
  text-align:center;
  text-decoration:none;
}
a.chan-btn:hover{ filter:brightness(0.98); }
a.chan-btn.sel{ box-shadow:0 0 0 2px var(--ink-accent) inset; }

/* Chips */
.channel-chip{ background:#f0f3f9; border-radius:10px; }

/* Separador */
hr{ border-color:#e8edf7 !important; }

/* Tabelas e código */
[data-testid="stTable"], table{ background: var(--ink-panel) !important; }
code, pre{ background: #f8fafc !important; color: #0f172a !important; }

/* --- Visibility boost for important toggles (callout) --- */
.ink-callout{
  background: linear-gradient(180deg, var(--ink-panel) 0%, #eef2ff 100%) !important;
  border: 1px solid var(--ink-accent) !important;
  border-radius: 14px !important;
  padding: 14px 16px !important;
  box-shadow: var(--ink-shadow) !important;
  margin: 6px 0 12px !important;
}
.ink-callout label, .ink-callout [data-testid="stWidgetLabel"], .ink-callout *{
  color: var(--ink-text) !important;
}
.ink-callout label{ font-weight: 600 !important; letter-spacing: .1px; }

/* --- Toggle visibility / track colors (stronger specificity) --- */
/* Slight scale bump inside callouts */
.ink-callout div[role="switch"], .ink-callout [data-testid="stSwitch"]{ transform: scale(1.06); }

/* OFF state — make the track light gray, not white */
.ink-callout [data-testid="stSwitch"][aria-checked="false"],
.ink-callout [data-testid="stSwitch"][aria-checked="false"] > div:first-child,
.ink-callout div[role="switch"][aria-checked="false"],
.ink-callout div[role="switch"][aria-checked="false"] > div:first-child,
[data-testid="stSwitch"][aria-checked="false"],
[data-testid="stSwitch"][aria-checked="false"] > div:first-child,
div[role="switch"][aria-checked="false"],
div[role="switch"][aria-checked="false"] > div:first-child{
  background: #e5e7eb !important;       /* track */
  background-color: #e5e7eb !important; /* for engines that split bg props */
  border: 1px solid #cbd5e1 !important;
  border-radius: 9999px !important;
}

/* ON state — blue track */
.ink-callout [data-testid="stSwitch"][aria-checked="true"],
.ink-callout [data-testid="stSwitch"][aria-checked="true"] > div:first-child,
.ink-callout div[role="switch"][aria-checked="true"],
.ink-callout div[role="switch"][aria-checked="true"] > div:first-child,
[data-testid="stSwitch"][aria-checked="true"],
[data-testid="stSwitch"][aria-checked="true"] > div:first-child,
div[role="switch"][aria-checked="true"],
div[role="switch"][aria-checked="true"] > div:first-child{
  background: var(--ink-accent) !important;
  background-color: var(--ink-accent) !important;
  border: 1px solid var(--ink-accent) !important;
  border-radius: 9999px !important;
}

/* Thumb/knob — keep it white in both states */
.ink-callout [data-testid="stSwitch"] div div,
[data-testid="stSwitch"] div div,
div[role="switch"] > div > div{
  background: #ffffff !important;
  box-shadow: 0 0 0 1px rgba(0,0,0,.05) !important;
}

/* File uploader — white background, dark text (professional look) */
[data-testid="stFileUploader"]{
  color: var(--ink-text) !important;
}
[data-testid="stFileUploader"] *{
  color: var(--ink-text) !important;
}
/* Dropzone panel */
[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"],
[data-testid="stFileUploader"] [data-testid="stFileDropzone"]{
  background: var(--ink-white) !important;
  border: 1.5px dashed var(--ink-edge) !important;
  border-radius: 14px !important;
  box-shadow: none !important;
  color: var(--ink-text) !important;
}
/* Hover/focus state */
[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"]:hover,
[data-testid="stFileUploader"] [data-testid="stFileDropzone"]:hover{
  border-color: var(--ink-accent) !important;
  box-shadow: 0 0 0 3px rgba(37,99,235,.15) inset !important;
  filter: none !important;
}
/* "Browse files" control inside the uploader */
[data-testid="stFileUploader"] button{
  background: var(--ink-chip) !important;
  color: var(--ink-text) !important;
  border: 1px solid var(--ink-edge) !important;
  border-radius: 12px !important;
  padding: 8px 12px !important;
}
/* Icons inside the uploader */
[data-testid="stFileUploader"] svg{
  fill: var(--ink-text) !important;
}

/* Channel color line (under each channel button) */
.chan-swatch{ margin-top:6px; }
.chan-swatch .bar{ height:6px; border-radius:999px; width:100%; }
.chan-swatch .label{ text-align:center; font-size:12px; color:var(--ink-muted); margin-top:4px; }

.ink-row-spacer{ height: 96px; }

</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* === Compare A×B — Fixed allocation row alignment (Jobs A & B) === */
.ink-fixed-grid [data-testid="stNumberInput"] label,
.ink-fixed-grid [data-testid="stNumberInput"] label * ,
.ink-fixed-grid [data-testid="stNumberInput"] [data-testid="stWidgetLabel"],
.ink-fixed-grid [data-testid="stNumberInput"] [data-testid="stWidgetLabel"] *,
.ink-fixed-grid [data-testid="stRadio"] > label,
.ink-fixed-grid [data-testid="stRadio"] > label *,
.ink-fixed-grid [data-testid="stRadio"] [data-testid="stWidgetLabel"],
.ink-fixed-grid [data-testid="stRadio"] [data-testid="stWidgetLabel"] *{
  white-space: nowrap !important;   /* force single-line labels */
  word-break: normal !important;
  overflow-wrap: normal !important;
  line-height: 1.15 !important;
  min-height: 26px !important;      /* uniform label height */
  display: block !important;
}
.ink-fixed-grid [data-testid="stNumberInput"]{
  margin-bottom: 0 !important;      /* remove extra bottom gap */
}
.ink-fixed-grid [data-testid="stRadio"]{ margin-bottom: 0 !important; }
.ink-fixed-grid [data-testid="stRadio"] [role="radiogroup"]{ display:flex; align-items:center; }
.ink-fixed-grid [data-testid="stTextInput"],
.ink-fixed-grid [data-testid="stSelectbox"],
.ink-fixed-grid [data-testid="stDateInput"],
.ink-fixed-grid [data-testid="stFileUploader"],
.ink-fixed-grid [data-testid="stTextArea"]{
  margin-bottom: 0 !important;
}
.ink-fixed-grid [data-testid="stNumberInput"] input{
  height: 40px !important;          /* consistent input height */
}
/* ensure selectbox labels behave like number inputs */
.ink-fixed-grid [data-testid="stSelectbox"] > label,
.ink-fixed-grid [data-testid="stSelectbox"] [data-testid="stWidgetLabel"],
.ink-fixed-grid [data-testid="stSelectbox"] [data-testid="stWidgetLabel"] *{
  white-space: nowrap !important;
  line-height: 1.15 !important;
  min-height: 22px !important;
  display: block !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# Constantes & defaults
# =========================
DEFAULTS = {
    "ink_color_per_l": 70.00,
    "ink_white_per_l": 85.00,
    "fof_per_l": 60.00,         # Fixation / Duo Soft per L
    "fabric_per_unit": 3.50,    # por m² (ou por m em modo linear)
    # fixed (monthly) & production
    "fix_labor_month": 0.0,
    "fix_leasing_month": 0.0,
    "fix_capex_month": 0.0,
    "fix_indust_month": 0.0,
    "prod_month_units": 30800.0,
    # moeda
    "local_symbol": "R$",
    "usd_to_local": 5.57,
}

# Modos de impressão (velocidade em m²/h; m/h ≈ m²/h ÷ largura)
PRINT_MODES: Dict[str, Dict[str, object]] = {
    "Fast Quality":         {"speed": 270, "res_color": "800×400"},
    "Fast Production":      {"speed": 475, "res_color": "800×400"},
    "Standard Quality":     {"speed": 180, "res_color": "600×800"},
    "Standard Production":  {"speed": 278, "res_color": "600×800"},
    "Saturation Quality":   {"speed": 115, "res_color": "1000×800"},
    "Saturation Production":{"speed": 210, "res_color": "1000×800"},
}
WHITE_RES = "1000×400"
MODE_GROUP = {
    "Fast Quality":"fast","Fast Production":"fast",
    "Standard Quality":"standard","Standard Production":"standard",
    "Saturation Quality":"saturation","Saturation Production":"saturation"
}
CHANNELS_WHITE = {"white","w"}
CHANNELS_FOF   = {"fof","f","fix","fixation","pretreat","pre_treat","duosoft","softener","fixacao","fixacaofof"}
CHANNEL_COLORS = {
    "Cyan":"#00B7EB","Magenta":"#FF00A8","Yellow":"#FFD300",
    "Black":"#222222","Red":"#E53935","Green":"#43A047",
    "FOF":"#7E57C2","White":"#F2F2F2","Preview":"#9E9E9E"
}

# Paleta clara/borda para botões de canais
LIGHT_CHANNEL_BG = {
    "Preview": "#eef2f7",
    "Cyan":    "#e6f7ff",
    "Magenta": "#ffe6f5",
    "Yellow":  "#fff9e0",
    "Black":   "#eceef3",
    "Red":     "#ffe9e6",
    "Green":   "#eaf7ea",
    "FOF":     "#efe7ff",
    "White":   "#ffffff",
}
BORDER_COLORS = {
    "Preview": "#9E9E9E",
    "Cyan":    "#00B7EB",
    "Magenta": "#FF00A8",
    "Yellow":  "#FFD300",
    "Black":   "#111827",
    "Red":     "#E53935",
    "Green":   "#43A047",
    "FOF":     "#7E57C2",
    "White":   "#d0d5dd",
}

# =========================
# Pequenos helpers de UI
# =========================
def section(title: str, subtitle: str|None=None):
    st.markdown(f"""
<div class="section-card">
  <h3 class="section-title">{title}</h3>
  {f"<small class='section-subtitle'>{subtitle}</small>" if subtitle else ""}
</div>
""", unsafe_allow_html=True)

def ensure_df(obj, cols=None):
    if isinstance(obj, pd.DataFrame): df = obj.copy()
    elif isinstance(obj, (list, tuple)): df = pd.DataFrame(list(obj))
    elif isinstance(obj, dict): df = pd.DataFrame([obj])
    else: df = pd.DataFrame()
    if cols:
        for c in cols:
            if c not in df.columns:
                is_num_hint = any(tok in str(c).lower() for tok in ("value","usd","price"))
                df[c] = 0.0 if is_num_hint else ""
        df = df[cols]
    return df

from decimal import Decimal, ROUND_HALF_UP

def price_round(v: float, step: float = 0.05) -> float:
    if step <= 0: step = 0.01
    q = Decimal(str(step))
    return float((Decimal(str(v)) / q).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * q)

def pretty_money(v, symbol="US$", fx=1.0) -> str:
    try: val = float(v)
    except Exception: val = 0.0
    val *= (fx or 1.0)
    return f"{symbol} {val:,.2f}"

def unit_label_short(unit_mode:str) -> str:
    return "m²" if unit_mode=="m2" else "m"

def per_unit(unit_mode:str) -> str:
    # newline before "/m²" so Streamlit's metric labels can wrap cleanly
    return f"\n/{unit_label_short(unit_mode)}"

def speed_label(unit_mode: str, speed_m2h: float, width_m: float) -> str:
    """Rotula a velocidade apenas em m²/h (sem modo linear)."""
    m2_per_h = float(speed_m2h or 0.0)
    return f"{m2_per_h:.0f} m²/h"

from contextlib import contextmanager

@contextmanager
def st_div(class_name: str):
    st.markdown(f'<div class="{class_name}">', unsafe_allow_html=True)
    try:
        yield
    finally:
        st.markdown('</div>', unsafe_allow_html=True)

def style_button_by_key(key: str, bg: str, fg: str = "#ffffff", border: str = "transparent"):
    css = f"""
    <style>
    div[id="{key}"] button {{
        background: {bg} !important;
        color: {fg} !important;
        border: 1px solid {border} !important;
        border-radius: 10px !important;
    }}
    div[id="{key}"] button:hover {{ filter: brightness(0.98); }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ---- Helper: inject CSS for channel buttons (by aria-label)
def style_channel_buttons_by_aria(display_to_label: Dict[str, str], selected_display: str | None = None):
    """Apply background/border color to channel buttons using aria-label (button text).
    display_to_label: map 'display text' -> 'canonical channel' (e.g., 'FOF (DuoSoft)' -> 'FOF').
    selected_display: display text of the currently selected button (to highlight).
    """
    rules = []
    for disp, lab in (display_to_label or {}).items():
        bg = LIGHT_CHANNEL_BG.get(lab, "var(--ink-chip)")
        border = BORDER_COLORS.get(lab, "var(--ink-edge)")
        rules.append(
            f'''
            div[data-testid="stButton"] > button[aria-label="{disp}"] {{
                background: {bg} !important;
                color: var(--ink-text) !important;
                border: 1px solid {border} !important;
                border-radius: 10px !important;
                padding: 10px 14px !important;
            }}
            div[data-testid="stButton"] > button[aria-label="{disp}"]:hover {{
                filter: brightness(0.98);
            }}
            '''
        )
    if selected_display:
        rules.append(
            f'''
            div[data-testid="stButton"] > button[aria-label="{selected_display}"] {{
                box-shadow: 0 0 0 2px var(--ink-accent) inset !important;
            }}
            '''
        )
    if rules:
        st.markdown("<style>" + "\n".join(rules) + "</style>", unsafe_allow_html=True)

# ---- Helper: render compact info tables (alternative to st.metric)
from typing import List, Tuple
def render_info_table(title: str, rows: List[Tuple[str, str, bool]]):
    """Render a small card with a 2-column table (Item / Value).
    rows: list of tuples (label, formatted_value, emphasized_bool)
    """
    parts = [
        f'<div class="info-card"><div class="title">{title}</div>',
        '<table><thead><tr><th>Item</th><th>Value</th></tr></thead><tbody>'
    ]
    for label, value, emph in (rows or []):
        cls = ' class="emph"' if emph else ''
        parts.append(f'<tr{cls}><td>{label}</td><td>{value}</td></tr>')
    parts.append('</tbody></table></div>')
    st.markdown("".join(parts), unsafe_allow_html=True)

# =========================
# Gráfico de Break-even (Plotly)
# =========================
def breakeven_figure(price_u: float, variable_u: float, fixed_month: float,
                     unit_lbl: str, sym: str, fx: float, title: str = "Break-even"):
    if price_u <= 0 or price_u <= variable_u or fixed_month <= 0:
        fig = go.Figure()
        fig.update_layout(template="plotly_white", height=360,
                          title=f"{title} — fill in price, variable cost and monthly fixed cost.",
                          margin=dict(l=10, r=10, t=50, b=10))
        return fig
    # Build full BE chart
    try:
        p = float(price_u or 0.0) * float(fx or 1.0)
        v = float(variable_u or 0.0) * float(fx or 1.0)
        f = float(fixed_month or 0.0) * float(fx or 1.0)
        be_units = (f / (p - v)) if (p > v) else 0.0
        q_max = max(10, int(math.ceil(be_units * 1.6)))
        q_max = min(q_max, 100000)
        x = np.linspace(0, q_max, 60)
        revenue = p * x
        total_cost = f + v * x
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x, y=revenue, mode="lines", name="Revenue"))
        fig.add_trace(go.Scatter(x=x, y=total_cost, mode="lines", name="Total cost"))
        if be_units > 0:
            fig.add_vline(x=be_units, line_dash="dash",
                          annotation_text=f"BE ≈ {be_units:,.0f} {unit_lbl}",
                          annotation_position="top right")
        fig.update_layout(template="plotly_white", height=360, title=title,
                          xaxis_title=f"Volume ({unit_lbl}/month)", yaxis_title=f"{sym}",
                          margin=dict(l=10, r=10, t=50, b=10), legend_title=None)
        return fig
    except Exception:
        fig = go.Figure()
        fig.update_layout(template="plotly_white", height=360,
                          title=f"{title} — unavailable (invalid inputs).",
                          margin=dict(l=10, r=10, t=50, b=10))
        return fig


def render_break_even_insights(price_u: float, variable_u: float, fixed_month: float,
                               unit_lbl: str, sym: str, fx: float, label: str | None = None):
    """Render short, practical BE insights below the chart.
    Assumes price/variable/fixed are in base currency and converts using fx for display.
    """
    try:
        p = float(price_u or 0.0)
        v = float(variable_u or 0.0)
        f = float(fixed_month or 0.0)
        if p <= 0 or p <= v or f <= 0:
            st.info("Enter price > variable cost and a positive monthly fixed cost to compute break-even.")
            return
        be_units = f / (p - v)
        be_units_up = math.ceil(be_units)
        rec_units = math.ceil(be_units * 1.10)
        cm_unit = (p - v) * (fx or 1.0)
        p_loc = p * (fx or 1.0)
        f_loc = f * (fx or 1.0)
        title = f"{label} — " if label else ""
        st.markdown(
            f"- {title}Break-even volume: ≈ <b>{be_units_up:,.0f} {unit_lbl}</b> (contribution <b>{sym} {cm_unit:,.2f}</b> per {unit_lbl}).",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"- At price <b>{sym} {p_loc:,.2f}</b>, printing <b>{be_units_up:,.0f} {unit_lbl}</b> covers monthly fixed <b>{sym} {f_loc:,.2f}</b>.",
            unsafe_allow_html=True,
        )
        net_at_rec = max(0.0, (p - v) * rec_units - f) * (fx or 1.0)
        st.markdown(
            f"- Recommendation: plan for <b>{rec_units:,.0f} {unit_lbl}</b> at ≥ <b>{sym} {p_loc:,.2f}</b> to include ~10% buffer (expected net after fixed ≈ <b>{sym} {net_at_rec:,.2f}</b>).",
            unsafe_allow_html=True,
        )
    except Exception:
        pass


# =========================
# Sales — Quick quote (manual consumption)
# =========================
def ui_sales_quick_quote():
    UNIT = get_unit()
    unit_lbl = unit_label_short(UNIT)
    section("Sales — Quick quote (manual)", "Optional ZIP. Or manually enter ink consumption per m² or per linear meter.")

    up = st.file_uploader("Optional Job (ZIP)", type="zip", key="sales_up_zip")
    if up is not None:
        st.session_state["sales_zip_bytes"] = up.getvalue()
    z = st.session_state.get("sales_zip_bytes")

    st.markdown("---")
    # Aligned grid for Sales inputs with 3-column first row
    with st_div("ink-fixed-grid"):
        # Row 1: [vazio] | [vazio] | Consumption unit
        s1a, s1b, s1c = st.columns(3)
        with s1a: st.markdown('<div class="ink-row-spacer"></div>', unsafe_allow_html=True)
        with s1b: st.markdown('<div class="ink-row-spacer"></div>', unsafe_allow_html=True)
        cons_unit = s1c.radio("Consumption unit", ["ml/m²", "ml/m"], index=0, horizontal=True, key="sales_cons_unit")

        # Row 2: Usable width (m) | Color
        s2a, s2b = st.columns(2)
        width_m = s2a.number_input("Usable width (m)", min_value=0.0, value=1.45, step=0.01, key="sales_width_m")
        c = s2b.number_input(f"Color ({cons_unit})", min_value=0.0, value=6.0, step=0.1, key="sales_c")

        # Row 3: Length (m) | White
        s3a, s3b = st.columns(2)
        length_m = s3a.number_input("Length (m)", min_value=0.0, value=1.00, step=0.01, key="sales_length_m")
        w = s3b.number_input(f"White ({cons_unit})", min_value=0.0, value=0.0, step=0.1, key="sales_w")

        # Row 4: Waste (%) | FOF
        s4a, s4b = st.columns(2)
        waste = s4a.number_input("Waste (%)", min_value=0.0, value=2.0, step=0.5, key="sales_waste")
        f = s4b.number_input(f"FOF ({cons_unit})", min_value=0.0, value=0.0, step=0.1, key="sales_f")

    # Build ml/m² map from manual inputs
    if cons_unit == "ml/m":
        w_safe = max(1e-9, float(width_m or 0.0))
        ml_map_m2 = {"Color": c / w_safe, "White": w / w_safe, "FOF": f / w_safe}
    else:
        ml_map_m2 = {"Color": c, "White": w, "FOF": f}

    st.markdown("---")
    section("Costs & currency", "Applies to this quote.")
    with st_div("ink-fixed-grid"):
        cc1, cc2, cc3, cc4 = st.columns(4)
        ink_c = cc1.number_input("Color ink ($/L)", min_value=0.0, value=float(st.session_state.get("sales_ink_c", DEFAULTS["ink_color_per_l"])), step=1.0, key="sales_ink_c")
        ink_w = cc2.number_input("White ink ($/L)", min_value=0.0, value=float(st.session_state.get("sales_ink_w", DEFAULTS["ink_white_per_l"])), step=1.0, key="sales_ink_w")
        ink_f = cc3.number_input("FOF / Pretreat ($/L)", min_value=0.0, value=float(st.session_state.get("sales_fof", DEFAULTS["fof_per_l"])), step=1.0, key="sales_fof")
        fabric = cc4.number_input(f"Substrate ({per_unit(UNIT)})", min_value=0.0, value=float(st.session_state.get("sales_fabric", DEFAULTS["fabric_per_unit"])), step=0.10, key="sales_fabric")

    cur1, cur2, cur3 = st.columns(3)
    SYM  = cur1.text_input("Local currency symbol", value=st.session_state.get("sales_local_sym", DEFAULTS["local_symbol"]))
    FX   = cur2.number_input("USD → Local (FX)", min_value=0.0, value=float(st.session_state.get("sales_fx", DEFAULTS["usd_to_local"])), step=0.01)
    OUTC = cur3.radio("Output currency", ["USD", "Local"], index=1, horizontal=True, key="sales_curr_out")

    st.markdown("---")
    section("Pricing", "Direct per unit or monthly helper.")
    fix_mode = st.radio("Fixed costs mode", ["Direct per unit", "Monthly helper"], index=0, horizontal=True, key="sales_fix_mode")
    if fix_mode.startswith("Direct"):
        with st_div("ink-fixed-grid"):
            mv1, mv2, mv3, mv4, mv5 = st.columns(5)
            fixed_unit = mv1.number_input(f"Fixed allocation (/"+unit_lbl+")", min_value=0.0, value=0.0, step=0.05, key="sales_fixed_unit")
            price_in   = mv2.number_input(f"Price {per_unit(UNIT)}", min_value=0.0, value=0.0, step=0.10, key="sales_price_in")
            margin     = mv3.number_input("Target margin (%)", min_value=0.0, value=20.0, step=0.5, key="sales_margin")
            taxes      = mv4.number_input("Taxes (%)", min_value=0.0, value=10.0, step=0.5, key="sales_taxes")
            terms      = mv5.number_input("Fees/Terms (%)", min_value=0.0, value=2.10, step=0.05, key="sales_terms")
            rnd        = float(st.selectbox("Round to", ["0.01","0.05","0.10"], index=1, key="sales_round"))
        fixed_per_unit_used = fixed_unit
        total_fix_m = 0.0
        st.caption(f"Fixed allocation in use: {fixed_per_unit_used:.2f} {per_unit(UNIT)}")
    else:
        st.caption("Monthly fixed costs — labor, leasing, depreciation, overheads and other items.")
        with st_div("ink-fixed-grid"):
            fx1, fx2, fx3, fx4 = st.columns(4)
            fl = fx1.number_input("Labor (monthly)", min_value=0.0, value=0.0, step=10.0, key="sales_fix_labor_m")
            le = fx2.number_input("Leasing/Rent (monthly)", min_value=0.0, value=0.0, step=10.0, key="sales_fix_leasing_m")
            dp = fx3.number_input("Depreciation (monthly)", min_value=0.0, value=0.0, step=10.0, key="sales_fix_depr_m")
            oh = fx4.number_input("Overheads (monthly)", min_value=0.0, value=0.0, step=10.0, key="sales_fix_over_m")
        st.caption("Other fixed (monthly)")
        _fix_input = ensure_df(st.session_state.get("sales_fix_others", [{"Name":"—","Value":0.0}]), ["Name","Value"])
        df_fix = st.data_editor(_fix_input, num_rows="dynamic", use_container_width=True, key="sales_fix_others_editor")
        sum_others = ensure_df(df_fix, ["Name","Value"]).get("Value", pd.Series(dtype=float)).fillna(0).sum()
        prod_m = monthly_production_inputs(UNIT, unit_lbl, state_prefix="sales_fix")
        total_fix_m = fl+le+dp+oh+sum_others
        fixed_per_unit_used = (total_fix_m/prod_m) if prod_m>0 else 0.0
        with st_div("ink-fixed-grid"):
            price_in   = st.number_input(f"Price {per_unit(UNIT)}", min_value=0.0, value=0.0, step=0.10, key="sales_price_in")
            margin     = st.number_input("Target margin (%)", min_value=0.0, value=20.0, step=0.5, key="sales_margin")
            taxes      = st.number_input("Taxes (%)", min_value=0.0, value=10.0, step=0.5, key="sales_taxes")
            terms      = st.number_input("Fees/Terms (%)", min_value=0.0, value=2.10, step=0.05, key="sales_terms")
            rnd        = float(st.selectbox("Round to", ["0.01","0.05","0.10"], index=1, key="sales_round"))
        st.caption(f"Monthly fixed total: {total_fix_m:.2f}; production: {prod_m:,.0f} {unit_lbl}/month ⇒ allocation: {fixed_per_unit_used:.4f} {per_unit(UNIT)}")

    clicked = st.button("Calculate quote", type="primary", key="sales_calc")

    # Compute and render only after click
    if clicked:
        # Simulate — use a safe default speed for quick quotes
        res = simulate(
            UNIT, float(width_m), float(length_m), float(waste),
            PRINT_MODES["Standard Quality"]["speed"],
            ml_map_m2,
            ink_c, ink_w, ink_f,
            fabric, 0.0, 0.0,
            fixed_per_unit_used,
            show_time_metrics=False,
        )

        qty = max(1e-9, float(res.get("qty_units", 0.0)))
        total_cost = float(res.get("total_cost", 0.0))
        total_per_unit = total_cost/qty
        suggested = price_round(total_per_unit*(1 + margin/100 + taxes/100), rnd)
        suggested = price_round(suggested*(1+terms/100), rnd)
        effective_price = price_in if price_in>0 else suggested
        rows_tot, rows_unit = build_cost_rows_from_sim(res, unit_lbl, SYM if OUTC=="Local" else "US$", FX if OUTC=="Local" else 1.0, price=effective_price)

        st.markdown("---")
        st.subheader("Quote result")
        left, right = st.columns(2)
        with left:
            render_info_table("Total ($)", rows_tot)
        with right:
            render_info_table(f"Per unit (/{unit_lbl})", rows_unit)
        render_help_glossary()

        # Break-even chart (optional)
        ink_total   = float(res.get("cost_ink", 0.0))
        fabric_cost = fabric_total(res)
        other_var   = float(res.get("cost_other", 0.0))
        variable_total = ink_total + fabric_cost + other_var
        variable_per_unit = variable_total / qty
        fixed_month_total = float(total_fix_m) if fix_mode.startswith("Monthly") else 0.0
        fig_be = breakeven_figure(
            price_u=effective_price,
            variable_u=variable_per_unit,
            fixed_month=fixed_month_total,
            unit_lbl=unit_lbl,
            sym=(SYM if OUTC=="Local" else "US$"),
            fx=(FX if OUTC=="Local" else 1.0),
            title="Break-even — Quick quote",
        )
        st.plotly_chart(fig_be, use_container_width=True, key="sales_be_chart", config=plotly_cfg())
        try:
            sym_out = (SYM if OUTC=="Local" else "US$")
            fx_out  = (FX if OUTC=="Local" else 1.0)
            render_break_even_insights(effective_price, variable_per_unit, fixed_month_total, unit_lbl, sym_out, fx_out, label="Quote")
        except Exception:
            pass

        # Optional cost charts (per unit)
        st.markdown("---")
        show_charts = st.checkbox("Show cost charts", value=True, key="sales_show_cost_charts")
        if show_charts:
            fxv = FX if OUTC=="Local" else 1.0
            # Per-unit contributions
            color_ml_u = float(ml_map_m2.get("Color", 0.0))
            white_ml_u = float(ml_map_m2.get("White", 0.0))
            fof_ml_u   = float(ml_map_m2.get("FOF",   0.0))
            color_u = (color_ml_u/1000.0) * float(ink_c or 0.0)
            white_u = (white_ml_u/1000.0) * float(ink_w or 0.0)
            fof_u   = (fof_ml_u  /1000.0) * float(ink_f or 0.0)
            fabric_u = float(fabric or 0.0)
            fixed_u  = float(fixed_per_unit_used or 0.0)

            # Chart 1 — Variable vs Fixed (per unit)
            fig_vf = go.Figure()
            fig_vf.add_trace(go.Bar(name="Variable", x=["Per unit"], y=[(color_u+white_u+fof_u+fabric_u)*fxv], marker_color="#3b82f6"))
            fig_vf.add_trace(go.Bar(name="Fixed", x=["Per unit"], y=[fixed_u*fxv], marker_color="#9ca3af"))
            fig_vf.update_layout(barmode="stack", template="plotly_white", height=320, margin=dict(l=10,r=10,t=30,b=10), yaxis_title=f"{SYM if OUTC=='Local' else 'US$'} / {unit_lbl}")

            # Chart 2 — Variable breakdown (per unit)
            fig_var = go.Figure()
            fig_var.add_trace(go.Bar(x=["Color ink","White ink","FOF / Pretreat","Fabric"], y=[color_u*fxv, white_u*fxv, fof_u*fxv, fabric_u*fxv], marker_color=["#2563eb","#6b7280","#7e57c2","#10b981"]))
            fig_var.update_layout(template="plotly_white", height=320, margin=dict(l=10,r=10,t=30,b=10), yaxis_title=f"{SYM if OUTC=='Local' else 'US$'} / {unit_lbl}")

            cc1, cc2 = st.columns(2)
            with cc1: st.subheader("Variable × Fixed (per unit)"); st.plotly_chart(fig_vf, use_container_width=True, key="sales_vf_chart", config=plotly_cfg())
            with cc2: st.subheader("Variable breakdown (per unit)"); st.plotly_chart(fig_var, use_container_width=True, key="sales_var_chart", config=plotly_cfg())

# === Fire Pixels (helpers) =========================================
def fire_pixels_map_from_xml_bytes(xml_bytes: bytes) -> dict:
    """Retorna {Channel: pixels} com nomes normalizados."""
    _, _, fire_pixels, _ = parse_xml(xml_bytes)
    out = {}
    for sep, px in (fire_pixels or {}).items():
        out[normalize_sep_name(sep)] = float(px or 0.0)
    return out

def fire_pixels_union_all_xmls(zbytes: bytes, cache_ns: str | None = None) -> dict:
    """Sum fire pixels across all XMLs in the ZIP (useful if the selected XML only has FOF/White)."""
    out = {}
    _, xmls, *_ = read_zip_listing(zbytes, cache_ns=cache_ns)
    for xp in xmls:
        mp = fire_pixels_map_from_xml_bytes(read_bytes_from_zip(zbytes, xp, cache_ns=cache_ns))
        for k, v in (mp or {}).items():
            if not k:
                continue
            out[k] = out.get(k, 0.0) + float(v or 0.0)
    return out

# =========================
# ZIP / imagem helpers
# =========================
def has_color_channels(ml_map: dict) -> bool:
    for k in (ml_map or {}):
        low = (k or "").strip().lower()
        if low not in CHANNELS_WHITE and low not in CHANNELS_FOF:
            return True
    return False

def ml_map_union_all_xmls(zbytes: bytes, cache_ns: str | None = None) -> dict:
    out = {}
    files, xmls, *_ = read_zip_listing(zbytes, cache_ns=cache_ns)
    for xp in xmls:
        mm = ml_per_m2_from_xml_bytes(read_bytes_from_zip(zbytes, xp, cache_ns=cache_ns))
        for k, v in (mm or {}).items():
            if not k:
                continue
            out[k] = out.get(k, 0.0) + float(v or 0.0)
    return out
def pick_first_with_colors(zbytes: bytes, cache_ns: str | None = None) -> dict:
    """Return ml/m² map from the first XML in the ZIP that contains any color channel (not just White/FOF)."""
    _, xmls, *_ = read_zip_listing(zbytes, cache_ns=cache_ns)
    for xp in xmls:
        try:
            mm = ml_per_m2_from_xml_bytes(read_bytes_from_zip(zbytes, xp, cache_ns=cache_ns))
        except Exception:
            mm = {}
        if has_color_channels(mm):
            return mm
    return {}

def is_probably_tiff(raw: bytes) -> bool:
    sigs = [b"II*\x00", b"MM\x00*", b"II+\x00\x08\x00\x00\x00", b"MM\x00+\x00\x00\x00\x08"]
    return any(raw.startswith(s) for s in sigs)

def strip_appledouble(path: str) -> str:
    base = path.split("/")[-1]
    if base.startswith("._"):
        return path.rsplit("/",1)[0] + "/" + base[2:] if "/" in path else base[2:]
    return path

def _zip_digest(zbytes: bytes) -> str:
    return hashlib.sha1(zbytes).hexdigest()

@st.cache_data(max_entries=128, ttl=3600, show_spinner=False)
def _cached_zip_listing(zip_key: str, zbytes: bytes):
    with zipfile.ZipFile(io.BytesIO(zbytes)) as z:
        files = [n for n in z.namelist() if not n.endswith("/")]
    xmls = [n for n in files if n.lower().endswith(".xml")]
    jpgs = [n for n in files if n.lower().endswith((".jpg",".jpeg")) and not n.split("/")[-1].startswith("._")]
    tifs = [n for n in files if n.lower().endswith((".tif",".tiff")) and not n.split("/")[-1].startswith("._")]
    ad = any(n.split("/")[-1].startswith("._") for n in files)
    return files, xmls, jpgs, tifs, ad

def read_zip_listing(zfile_bytes: bytes, cache_ns: str | None = None):
    key = f"{cache_ns or 'zip'}_{_zip_digest(zfile_bytes)}"
    return _cached_zip_listing(key, zfile_bytes)

@st.cache_data(max_entries=512, ttl=3600, show_spinner=False)
def _cached_zip_entry(zip_key: str, inner_path: str, zbytes: bytes) -> bytes:
    with zipfile.ZipFile(io.BytesIO(zbytes)) as z:
        return z.read(inner_path)

def read_bytes_from_zip(zfile_bytes: bytes, inner_path: str, cache_ns: str | None = None) -> bytes:
    key = f"{cache_ns or 'zip'}_{_zip_digest(zfile_bytes)}"
    return _cached_zip_entry(key, inner_path, zfile_bytes)

def _get_preview_raw(zfile_bytes: bytes, inner_path: str, cache_ns: str | None = None) -> bytes:
    raw = read_bytes_from_zip(zfile_bytes, inner_path, cache_ns)
    if not is_probably_tiff(raw):
        alt = strip_appledouble(inner_path)
        if alt != inner_path:
            try:
                raw_alt = read_bytes_from_zip(zfile_bytes, alt, cache_ns)
                if is_probably_tiff(raw_alt):
                    raw = raw_alt
            except KeyError:
                pass
    return raw

@st.cache_data(max_entries=256, ttl=3600, show_spinner=False)
def make_preview_thumb(raw_img: bytes, target_w: int, target_h: int, *, fill: bool, trim: bool, max_side: int) -> bytes:
    """Return a JPEG thumbnail (bytes) ready for st.image rendering."""
    im = Image.open(io.BytesIO(raw_img))
    if getattr(im, "n_frames", 1) > 1:
        try:
            im.seek(0)
        except Exception:
            pass
    try:
        bigger = max(im.size)
        factor = max(1, int(bigger / (max_side * 2)))
        if factor > 1 and hasattr(im, "reduce"):
            im = im.reduce(factor)
    except Exception:
        pass
    if im.mode == "P":
        im = im.convert("RGB")
    elif im.mode == "1":
        im = im.convert("L")
    if trim:
        im = trim_margins(im)
    if fill:
        im = coverbox(im, target_w, target_h)
    else:
        im = letterbox(im, target_w, target_h)
    buf = io.BytesIO()
    save_kwargs = {"format": "JPEG", "quality": 85, "optimize": True}
    if im.mode == "RGBA":
        im = im.convert("RGB")
    im.save(buf, **save_kwargs)
    return buf.getvalue()

@fragment_decorator if fragment_decorator else (lambda fn: fn)
def preview_fragment(fragment_key: str, zip_bytes: bytes | None, inner_path: str | None, *, width: int, height: int, fill_flag: bool, trim_flag: bool, max_side: int, caption: str):
    if not zip_bytes or not inner_path:
        st.info("Preview unavailable for this selection.")
        return
    try:
        with st.spinner("Carregando preview…"):
            raw = _get_preview_raw(zip_bytes, inner_path, cache_ns=fragment_key)
            thumb_bytes = make_preview_thumb(
                raw,
                width,
                height,
                fill=fill_flag,
                trim=trim_flag,
                max_side=max_side,
            )
        st.image(thumb_bytes, caption=caption, width=width)
    except Exception as exc:
        st.error(f"Preview failed: {exc}")

def letterbox(im: PILImageType, target_w: int, target_h: int, bg=(245,247,251)) -> PILImageType:
    if im.mode not in ("RGB","RGBA","L"):
        im = im.convert("RGB")
    im_copy = im.copy()
    im_copy.thumbnail((target_w, target_h), Image.LANCZOS)
    canvas = Image.new("RGB", (target_w, target_h), bg)
    x = (target_w - im_copy.width)//2; y = (target_h - im_copy.height)//2
    canvas.paste(im_copy, (x,y))
    return canvas

def load_preview_light(zfile_bytes: bytes, inner_path: str, max_side: int = 640, cache_ns: str | None = None) -> PILImageType:
    raw = _get_preview_raw(zfile_bytes, inner_path, cache_ns)
    im = Image.open(io.BytesIO(raw))
    if getattr(im, "n_frames", 1) > 1:
        try: im.seek(0)
        except Exception: pass
    try:
        bigger = max(im.size)
        factor = max(1, int(bigger / (max_side*2)))
        if factor > 1 and hasattr(im, "reduce"):
            im = im.reduce(factor)
    except Exception:
        pass
    if im.mode == "P": im = im.convert("RGB")
    elif im.mode == "1": im = im.convert("L")
    im.thumbnail((max_side, max_side), Image.LANCZOS)
    return im

def coverbox(im: PILImageType, target_w: int, target_h: int) -> PILImageType:
    """Resize to completely fill the target box (center-crop if needed)."""
    if im.mode not in ("RGB","RGBA","L"):
        im = im.convert("RGB")
    iw, ih = im.size
    if iw == 0 or ih == 0:
        return letterbox(im, target_w, target_h)
    scale = max(target_w/iw, target_h/ih)
    new_w, new_h = max(1, int(iw*scale)), max(1, int(ih*scale))
    im_resized = im.resize((new_w, new_h), Image.LANCZOS)
    x0 = max(0, (new_w - target_w)//2)
    y0 = max(0, (new_h - target_h)//2)
    x1 = x0 + target_w
    y1 = y0 + target_h
    return im_resized.crop((x0, y0, x1, y1))

# Small inline hint icon for headings (native browser tooltip)
def render_title_with_hint(title_text: str, hint: str):
    safe_title = title_text.replace("<", "&lt;").replace(">", "&gt;")
    safe_hint = hint.replace("\"", "&quot;")
    st.markdown(
        f"**{safe_title}** <span style='cursor:help;color:#64748b' title=\"{safe_hint}\">ⓘ</span>",
        unsafe_allow_html=True,
    )

# Default Plotly config (hide logo, enable PNG export)
def plotly_cfg():
    try:
        return {
            "displaylogo": False,
            "toImageButtonOptions": {"format": "png", "scale": 2},
        }
    except Exception:
        return {}

# Session tools: reset heavy keys and clear caches
def _reset_heavy_session_state():
    try:
        keys = list(st.session_state.keys())
        patterns = ["_zip_bytes", "_panels", "_legend", "batch_"]
        for k in keys:
            if any(p in k for p in patterns):
                try:
                    del st.session_state[k]
                except Exception:
                    pass
    except Exception:
        pass

def render_tools_sidebar():
    try:
        with st.sidebar:
            st.markdown("### Tools")
            if st.button("Reset session", key="__btn_reset_session"):
                _reset_heavy_session_state()
                st.success("Session reset.")
            if st.button("Clear caches", key="__btn_clear_caches"):
                try:
                    st.cache_data.clear()
                except Exception:
                    pass
                st.success("Caches cleared.")
    except Exception:
        pass

def trim_margins(im: PILImageType, threshold: int = 245, margin_px: int = 2) -> PILImageType:
    """Auto-trim near-white borders. threshold 0-255: larger → more aggressive.
    Only removes uniform light margins; returns original if no content bbox is found."""
    try:
        arr = np.asarray(im.convert("L"))
        mask = arr < threshold  # True where there is content (darker than threshold)
        if not mask.any():
            return im
        rows = np.where(mask.any(axis=1))[0]
        cols = np.where(mask.any(axis=0))[0]
        r0, r1 = int(max(0, rows.min() - margin_px)), int(min(arr.shape[0], rows.max() + 1 + margin_px))
        c0, c1 = int(max(0, cols.min() - margin_px)), int(min(arr.shape[1], cols.max() + 1 + margin_px))
        if r1 <= r0 or c1 <= c0:
            return im
        return im.crop((c0, r0, c1, r1))
    except Exception:
        return im

def get_channel_from_filename(name: str):
    base_raw   = re.sub(r"\.[^.]+$", "", name or "")
    base_ascii = _deaccent(base_raw).lower()
    base_norm  = re.sub(r"[^a-z0-9]+", "_", base_ascii)
    tokens     = set(filter(None, base_norm.split("_")))
    glued      = base_norm.replace("_", "")

    # CMYK + extras (tokens)
    if tokens & {"c","cyan","ciano"}: return "Cyan"
    if tokens & {"m","magenta"}:      return "Magenta"
    if tokens & {"y","yellow","amarelo","amarela"}: return "Yellow"
    if tokens & {"k","black","preto"}: return "Black"
    if tokens & {"r","red","vermelho","vermelha"}:  return "Red"
    if tokens & {"g","green","verde"}:              return "Green"

    # White
    if tokens & {"w","white","branco","whiteink","white_ink","brancoink","branco_ink"}:
        return "White"

    # FOF / pré-trat.
    if tokens & {"fof","fix","fixation","pretreat","pre_treat","pretreatment",
                 "duosoft","softener","fixacao","pretratamento","pretratar","fixacaofof"}:
        return "FOF"

    # Sufixo único (_c/_m/_y/_k/_r/_g/_w/_f)
    suf = re.search(r"[_\-]([cmykrgwf])$", base_norm)
    if suf:
        return {"c":"Cyan","m":"Magenta","y":"Yellow","k":"Black",
                "r":"Red","g":"Green","w":"White","f":"FOF"}[suf.group(1)]

    # "f" sozinho só vira FOF se não houver outra letra de canal
    if ("f" in tokens) and not (tokens & {"c","m","y","k","r","g","w"}):
        return "FOF"
    # combinação NS + F (ex.: P7589_NS_F)
    if ("ns" in tokens) and ("f" in tokens):
        return "FOF"

    # Fallback por substring
    if "cyan" in base_ascii or "ciano" in base_ascii:   return "Cyan"
    if "magenta" in base_ascii:                          return "Magenta"
    if "yellow" in base_ascii or "amarel" in base_ascii: return "Yellow"
    if "black" in base_ascii or "preto"  in base_ascii:  return "Black"
    if "red"   in base_ascii or "vermelh" in base_ascii: return "Red"
    if "green" in base_ascii or "verde"   in base_ascii: return "Green"
    if "white" in base_ascii or "branco"  in base_ascii: return "White"
    if any(w in base_ascii for w in ["fof","fixation","pretreat","duosoft","softener","fixacao","pretrat"]):
        return "FOF"

    return None

def normalize_sep_name(name: str) -> str:
    n = (name or "").strip().lower().replace(" ", "").replace("_", "")
    # Canais de cor — aceita letra única e nomes
    if n in ("c","cyan","ciano"): return "Cyan"
    if n in ("m","magenta"): return "Magenta"
    if n in ("y","yellow","amarelo","amarela"): return "Yellow"
    if n in ("k","black","preto"): return "Black"
    if n in ("r","red","vermelho","vermelha"): return "Red"
    if n in ("g","green","verde"): return "Green"
    # White
    if n in ("w","white","branco","whiteink","brancoink"): return "White"
    # FOF / Fixation / DuoSoft (inclui 'f')
    if n in ("f","fof","fix","fixation","pretreat","pretreatment","pre_treat","duosoft","softener","fixacao","fixacaofof"):
        return "FOF"
    return (name or "").strip()

# =========================
# Parsing do XML e conversões
# =========================
@st.cache_data(show_spinner=False)
def parse_xml(xml_bytes: bytes):
    root = ET.fromstring(xml_bytes)
    def f(x):
        try: return float(x)
        except Exception: return 0.0
    width  = f(root.findtext("Width","0"))     # cm
    height = f(root.findtext("Height","0"))    # cm
    area_m2 = (width/100.0)*(height/100.0)

    ml_node = root.find("NumberOfMlPerSeparation")
    if ml_node is None:
        ml_node = root.find("NumberOfMlPerSeperation")
    ml_per_sep = {}
    if ml_node is not None:
        for child in ml_node:
            try: ml_per_sep[child.tag] = float(child.text or "0")
            except Exception: ml_per_sep[child.tag] = 0.0

    px_node = root.find("NumberOfFirePixelsPerSeparation")
    fire_pixels = {}
    if px_node is not None:
        for child in px_node:
            try: fire_pixels[child.tag] = int(float(child.text or "0"))
            except Exception: fire_pixels[child.tag] = 0

    meta = {
        "printer": root.findtext("Printer","N/A"),
        "job_name": root.findtext("JobName","N/A"),
        "resolution": root.findtext("Resolution","N/A"),
        "print_speed": root.findtext("PrintSpeed","N/A"),
        "output_profile": root.findtext("OutputProfile","N/A"),
        "width_cm": width, "height_cm": height, "area_m2": area_m2
    }
    return area_m2, ml_per_sep, fire_pixels, meta

def get_xml_dims_m(xml_bytes: bytes) -> Tuple[float,float,float]:
    area_m2, _, _, meta = parse_xml(xml_bytes)
    w_m = (meta.get("width_cm") or 0)/100.0
    h_m = (meta.get("height_cm") or 0)/100.0
    if w_m>0 and h_m>0:
        return w_m, h_m, area_m2
    if area_m2>0:
        side = math.sqrt(area_m2)
        return side, side, area_m2
    return 1.0, 1.0, 1.0

def ml_per_m2_from_xml_bytes(xml_bytes: bytes) -> dict:
    area, ml_sep, _, _ = parse_xml(xml_bytes)
    out = {}
    if area > 0:
        for sep, ml_total in ml_sep.items():
            out[normalize_sep_name(sep)] = ml_total/area
    return out

# =========================
# Utilidades de modo
# =========================
def has_white_in_xml(xml_bytes: bytes) -> bool:
    ml = ml_per_m2_from_xml_bytes(xml_bytes)
    return (ml.get("White", 0.0) or 0.0) > 0.0

def infer_mode_from_xml(xml_bytes: bytes):
    _, _, _, meta = parse_xml(xml_bytes)
    res = str(meta.get("resolution") or "").lower().replace(" ", "").replace("x","×")
    spd = str(meta.get("print_speed") or "").lower()
    if   "800×400" in res: group = "Fast"
    elif "600×800" in res: group = "Standard"
    elif "1000×800" in res: group = "Saturation"
    else: return None
    qp = "Production" if "prod" in spd else "Quality"
    return f"{group} {qp}"

def mode_option_label(mode_key: str, has_white: bool, unit_key: str, width_m: float) -> str:
    return f"{mode_key} — {PRINT_MODES[mode_key]['res_color']} (color){' • '+WHITE_RES+' (white)' if has_white else ''} • {speed_label(unit_key, PRINT_MODES[mode_key]['speed'], width_m)}"

def apply_mode_factors(ml_map: dict, group: str, factors: dict) -> dict:
    g = factors.get(group, {"color":1.0,"white":1.0,"fof":1.0})
    out = {}
    for k, v in (ml_map or {}).items():
        low = (k or "").lower()
        if low in CHANNELS_WHITE: m = g["white"]
        elif low in CHANNELS_FOF: m = g["fof"]
        else: m = g["color"]
        out[k] = float(v) * float(m)
    return out

# --- Per-mode scalers (state + UI + application) --------------------------
def ensure_mode_multiplier_state():
    ss = st.session_state
    # Fast
    ss.setdefault("single_mul_fc", 100.0)  # Fast — Color %
    ss.setdefault("single_mul_fw", 100.0)  # Fast — White % (fixed 100% in logic)
    ss.setdefault("single_mul_ff", 100.0)  # Fast — DuoSoft/FOF %
    # Standard
    ss.setdefault("single_mul_sc", 110.0)  # initial suggestion
    ss.setdefault("single_mul_sw", 100.0)
    ss.setdefault("single_mul_sf", 105.0)
    # Saturation
    ss.setdefault("single_mul_tc", 125.0)
    ss.setdefault("single_mul_tw", 100.0)
    ss.setdefault("single_mul_tf", 110.0)

def get_mode_factors_from_state() -> dict:
    """Retorna fatores normalizados (1.00 = 100%)."""
    ensure_mode_multiplier_state()
    return {
        "fast": {
            "color": (st.session_state["single_mul_fc"] or 100.0)/100.0,
            # Fast — White is fixed at 100% (option removed from UI)
            "white": 1.00,
            "fof":   (st.session_state["single_mul_ff"] or 100.0)/100.0,
        },
        "standard": {
            "color": (st.session_state["single_mul_sc"] or 100.0)/100.0,
            "white": (st.session_state["single_mul_sw"] or 100.0)/100.0,
            "fof":   (st.session_state["single_mul_sf"] or 100.0)/100.0,
        },
        "saturation": {
            "color": (st.session_state["single_mul_tc"] or 100.0)/100.0,
            "white": (st.session_state["single_mul_tw"] or 100.0)/100.0,
            "fof":   (st.session_state["single_mul_tf"] or 100.0)/100.0,
        },
    }

def render_mode_multiplier_controls(use_expander: bool = True, expanded: bool = False, show_presets: bool = True, key_prefix: str | None = None, sync_to_shared: bool = False):
    """Compact UI to edit per-mode scalers.

    use_expander: when True, render inside an expander (current default).
    expanded: controls the initial expander state.
    show_presets: show preset shortcuts (handy in the global panel); can be hidden inline.
    """
    ensure_mode_multiplier_state()
    header = "Per-mode scalers (%) — Color / White / DuoSoft"
    container = st.expander(header, expanded=expanded) if use_expander else st.container()
    with container:
        if not use_expander:
            st.markdown(f"**{header}**")
            st.caption("Adjust how **resolution/mode** affects consumption (ml/m²). Applies to A and B.")
        else:
            st.caption("Adjust how **resolution/mode** affects consumption (ml/m²).")
        # Extra note per request: Fast — White is fixed at 100%
        st.caption("Note: in the Fast group, White is fixed at 100% (no scaler).")

        # Helper to resolve widget keys and seed values if using prefix
        def _k(name: str) -> str:
            return f"{key_prefix}_{name}" if key_prefix else name
        # Seed prefixed widgets with shared values on first render
        shared_keys = [
            ("single_mul_fc", "Fast — Color %"),
            ("single_mul_ff", "Fast — DuoSoft %"),
            ("single_mul_sc", "Standard — Color %"),
            ("single_mul_sw", "Standard — White %"),
            ("single_mul_sf", "Standard — DuoSoft %"),
            ("single_mul_tc", "Saturation — Color %"),
            ("single_mul_tw", "Saturation — White %"),
            ("single_mul_tf", "Saturation — DuoSoft %"),
        ]
        if key_prefix:
            for sk, _ in shared_keys:
                pk = _k(sk)
                if pk not in st.session_state:
                    st.session_state[pk] = float(st.session_state.get(sk, 100.0))

        f1,f3 = st.columns(2)
        f1.number_input("Fast — Color %",     min_value=0.0, step=1.0, key=_k("single_mul_fc"), help="Fast: Color scaler (White fixed at 100%).")
        # Fast — White removed by request; kept internally at 100%
        f3.number_input("Fast — DuoSoft %",   min_value=0.0, step=1.0, key=_k("single_mul_ff"), help="Fast: DuoSoft/FOF scaler.")
        s1,s2,s3 = st.columns(3)
        s1.number_input("Standard — Color %", min_value=0.0, step=1.0, key=_k("single_mul_sc"))
        s2.number_input("Standard — White %", min_value=0.0, step=1.0, key=_k("single_mul_sw"))
        s3.number_input("Standard — DuoSoft %",min_value=0.0, step=1.0, key=_k("single_mul_sf"))
        t1,t2,t3 = st.columns(3)
        t1.number_input("Saturation — Color %",min_value=0.0, step=1.0, key=_k("single_mul_tc"))
        t2.number_input("Saturation — White %",min_value=0.0, step=1.0, key=_k("single_mul_tw"))
        t3.number_input("Saturation — DuoSoft %",min_value=0.0, step=1.0, key=_k("single_mul_tf"))

        # Note: syncing back to shared keys is handled by callers (e.g., on Apply buttons)

        if show_presets:
            # Presets rápidos — aplicam nos widgets correntes (prefixed ou shared)
            preset = st.selectbox(
                "Presets",
                ["—", "Conservador (+10C/+0W/+5FOF)", "Agressivo (+25C/+10W/+10FOF)"],
                key=f"{key_prefix or 'global'}_mul_preset"
            )
            def _apply_preset(conservador: bool):
                vals = dict(
                    single_mul_sc=110.0 if conservador else 120.0,
                    single_mul_sw=100.0 if conservador else 110.0,
                    single_mul_sf=105.0 if conservador else 110.0,
                    single_mul_tc=120.0 if conservador else 135.0,
                    single_mul_tw=100.0 if conservador else 110.0,
                    single_mul_tf=108.0 if conservador else 112.0,
                )
                for sk, val in vals.items():
                    st.session_state[_k(sk)] = val
                # Syncing to shared keys is deferred to caller (Apply buttons)
            if preset == "Conservador (+10C/+0W/+5FOF)":
                _apply_preset(True)
            elif preset == "Agressivo (+25C/+10W/+10FOF)":
                _apply_preset(False)


def sync_mode_scalers_from_prefix(prefix: str):
    """Copy values from prefixed widgets (e.g., 'cmpA_*') to the shared keys
    used in calculations (single_mul_*)."""
    def _k(name: str) -> str:
        return f"{prefix}_{name}"
    mapping = [
        "single_mul_fc","single_mul_ff",
        "single_mul_sc","single_mul_sw","single_mul_sf",
        "single_mul_tc","single_mul_tw","single_mul_tf",
    ]
    for sk in mapping:
        pk = _k(sk)
        if pk in st.session_state:
            try:
                st.session_state[sk] = float(st.session_state.get(pk, st.session_state.get(sk, 100.0)))
            except Exception:
                st.session_state[sk] = st.session_state.get(pk, st.session_state.get(sk, 100.0))

def apply_consumption_source(
    xml_bytes: bytes,
    source: str,
    mode_sel: str | None,
    factors: dict,
    man_color: float = 0.0,
    man_white: float = 0.0,
    man_fof: float   = 0.0,
) -> dict:
    """
    Build the ml/m² map from the chosen source:
    - "XML (exact)": XML consumption as-is
    - "XML + mode multiplier (%)": XML consumption scaled by group (fast/standard/saturation)
    - "Manual": user-provided Color/White/FOF values
    """
    src = (source or "").lower()
    if src.startswith("manual"):
        return {"Color": float(man_color or 0), "White": float(man_white or 0), "FOF": float(man_fof or 0)}

    # Base: XML
    base = ml_per_m2_from_xml_bytes(xml_bytes)
    if "mode" in src:  # "XML + mode multiplier (%)"
        group = MODE_GROUP.get(mode_sel or "", None)
        if group:
            base = apply_mode_factors(base, group, factors)
    return base

# =========================
# Core: Simulador de custo/tempo
# =========================
def simulate(unit_mode:str, width_m:float, length_m:float, waste_pct:float, speed_m2h:float, ml_map_m2:dict,
             ink_color_per_l_usd:float, ink_white_per_l_usd:float, fof_per_l_usd:float,
             fabric_per_unit_usd:float, others_var_per_unit_usd:float, post_h:float,
             fixed_per_unit_usd:float, show_time_metrics: bool = True):
    """Accepts ml/m² map (not linear meter); converts when unit_mode == 'm'."""
    area_base_m2 = max(0.0, (width_m or 0.0) * (length_m or 0.0))
    length_base_m = max(0.0, (length_m or 0.0))
    area_w = area_base_m2 * (1 + (waste_pct or 0)/100.0)
    length_w = length_base_m * (1 + (waste_pct or 0)/100.0)
    qty_units = area_w if unit_mode=="m2" else length_w

    color_ml = white_ml = fof_ml = 0.0
    for k, v in (ml_map_m2 or {}).items():
        v_unit = float(v) if unit_mode=="m2" else float(v) * float(width_m or 0.0)
        low = (k or "").strip().lower()
        if low in CHANNELS_WHITE: white_ml += v_unit
        elif low in CHANNELS_FOF: fof_ml += v_unit
        else: color_ml += v_unit

    ink_cost_per_unit = (color_ml/1000.0)*(ink_color_per_l_usd or 0) + (white_ml/1000.0)*(ink_white_per_l_usd or 0)
    ink_cost_per_unit += (fof_ml/1000.0)*(fof_per_l_usd or 0)

    cost_ink    = ink_cost_per_unit * qty_units
    cost_fabric = (fabric_per_unit_usd or 0) * qty_units
    cost_other  = (others_var_per_unit_usd or 0) * qty_units
    cost_fixed  = (fixed_per_unit_usd or 0) * qty_units

    time_print_h = (area_w / speed_m2h) if speed_m2h>0 else 0.0
    time_total_h = time_print_h + (post_h or 0.0)
    if show_time_metrics:
        t1, t2 = st.columns(2)
        t1.metric("Print time (h)", f"{time_print_h:.2f}")
        t2.metric("Total time (h)",        f"{time_total_h:.2f}")


    total_cost = cost_ink + cost_fabric + cost_other + cost_fixed
    total_ml_per_unit = float(sum(ml_map_m2.values())) if unit_mode=="m2" else float(sum(ml_map_m2.values()))*float(width_m or 0.0)
    ink_ml_total = total_ml_per_unit * qty_units

    return dict(
        qty_units=qty_units, unit_label=unit_label_short(unit_mode),
        area_waste_m2=area_w,
        total_ml_per_unit=total_ml_per_unit, ink_ml_total=ink_ml_total,
        time_print_h=time_print_h, time_total_h=time_total_h,
        cost_ink=cost_ink, cost_media=cost_fabric, cost_other=cost_other,
        cost_fixed=cost_fixed, total_cost=total_cost
    )

# ===== Fixed allocation resolver para Compare =====
def resolve_fixed_per_unit_for_compare(
    fix_mode: str,
    fixed_per_unit_A: float,
    fixed_per_unit_B: float,
    fix_month_total: float,
    prod_month_units: float,
) -> Tuple[float, float]:
    """
    Decide fixed allocation per unit for A×B:
    - 'Direct per unit': use values provided for A and B.
    - 'Monthly helper': per-unit = monthly_fixed_total / monthly_production (same for A & B).
    """
    if (fix_mode or "").strip().lower().startswith("direto") or (fix_mode or "").strip().lower().startswith("direct"):
        return float(fixed_per_unit_A or 0.0), float(fixed_per_unit_B or 0.0)
    per_unit = (float(fix_month_total or 0.0) / float(prod_month_units or 0.0)) if (prod_month_units or 0.0) > 0 else 0.0
    return float(per_unit), float(per_unit)

# --- Helper: monthly production input for A×B fixed allocation
def monthly_production_inputs(unit_key: str, unit_lbl: str, state_prefix: str) -> float:
    """
    Reusable UI for monthly production:
    - 'Enter directly' → digita o total
    - 'Calculate with helper' → preenche os 6 campos
    Returns monthly production and saves into st.session_state[f"{state_prefix}_prod_month_units"].
    """
    fxm1, fxm2 = st.columns([1, 1])
    prod_mode = fxm1.radio(
        "How do you want to provide monthly production?",
        ["Enter directly", "Calculate with helper"],
        index=0,
        horizontal=True,
        help="Enter the total directly or use the calculator.",
        key=f"{state_prefix}_prod_mode",
    )

    if prod_mode.startswith("Enter"):
        prod_month_units = fxm2.number_input(
            f"Monthly production ({unit_lbl}/month)",
            min_value=0.0,
            value=float(st.session_state.get(f"{state_prefix}_prod_month_units", DEFAULTS.get("prod_month_units", 30000.0))),
            step=100.0,
            help=f"Total produced per month in {unit_lbl}.",
            key=f"{state_prefix}_prod_units",
        )
    else:
        with st_div("ink-prod-grid"):
            ca = st.columns(6)
            shifts = ca[0].number_input("Shifts/day", min_value=0, value=1, step=1, help="Shifts per day.", key=f"{state_prefix}_prod_shifts")
            days = ca[1].number_input("Days/month", min_value=0, value=22, step=1, help="Days in the month.", key=f"{state_prefix}_prod_days")
            hours = ca[2].number_input("Hours/shift", min_value=0.0, value=7.0, step=0.5, help="Hours per shift.", key=f"{state_prefix}_prod_hours")
            speed_m2h = ca[3].number_input("Avg speed (m²/h)", min_value=0.0, value=200.0, step=5.0, help="Average speed.", key=f"{state_prefix}_prod_speed")
            width_use = ca[4].number_input("Usable width (m)", min_value=0.01, value=1.50, step=0.01, help="Used to convert m/h if unit = meter.", key=f"{state_prefix}_prod_width")
            util_pct = ca[5].number_input("Utilization factor (%)", min_value=0.0, value=85.0, step=1.0, help="Average efficiency.", key=f"{state_prefix}_prod_util")
            util = (util_pct / 100.0)
            if unit_key == "m2":
                prod_month_units = shifts * days * hours * speed_m2h * util
            else:
                m_per_h = speed_m2h / max(1e-9, width_use)
                prod_month_units = shifts * days * hours * m_per_h * util

    st.session_state[f"{state_prefix}_prod_month_units"] = float(prod_month_units or 0.0)
    return float(prod_month_units or 0.0)

def fabric_total(res: dict) -> float:
    """Return media/fabric cost from simulate() result, robust to alias key."""
    return float(res.get("cost_fabric", res.get("cost_media", 0.0)))

# ---- Build table rows from simulate() result (used in Compare A×B)
def build_cost_rows_from_sim(res, unit_lbl, sym, fx, price=None):
    """
    Returns (rows_tot, rows_unit) to be consumed by render_info_table().
    - rows_tot: Ink/Substrate/Other/Variable/Fixed/Total (in totals $)
    - rows_unit: Variable/Fixed/Cost/[Price] (per unit)
    """
    qty = max(1e-9, float(res.get("qty_units", 0.0)))
    ink_total   = float(res.get("cost_ink", 0.0))
    fabric_cost = fabric_total(res)
    other_var   = float(res.get("cost_other", 0.0))
    fixed_cost  = float(res.get("cost_fixed", 0.0))
    total_cost  = float(res.get("total_cost", 0.0))

    variable_total = ink_total + fabric_cost + other_var
    variable_per_unit = variable_total / qty
    fixed_per_unit_card = fixed_cost / qty
    cost_unit_calc = total_cost / qty

    rows_tot = [
        ("Ink",            pretty_money(ink_total, sym, fx), False),
        ("Substrate",      pretty_money(fabric_cost, sym, fx), False),
        ("Other expenses", pretty_money(other_var, sym, fx), False),
        ("Variable",       pretty_money(variable_total, sym, fx), True),
        ("Fixed",          pretty_money(fixed_cost, sym, fx), True),
        ("Total",          pretty_money(total_cost, sym, fx), True),
    ]
    rows_unit = [
        ("Variable", pretty_money(variable_per_unit, sym, fx), False),
        ("Fixed",    pretty_money(fixed_per_unit_card, sym, fx), False),
        ("Cost",     pretty_money(cost_unit_calc, sym, fx), True),
    ]
    if price is not None:
        rows_unit.append(("Price", pretty_money(price, sym, fx), True))
    return rows_tot, rows_unit
# === Compare Option B: shared runner (reads inputs from state, writes panels)
def run_compare_job(prefix: str, label: str, uploaded_zip_bytes: bytes, sym: str, fx: float):
    """
    Executa a simulação para A ou B, lendo st.session_state pelos keys com prefixo
    (ex.: 'cmpA_*' ou 'cmpB_*'). Salva os painéis formatados em st.session_state[f"{prefix}_panels"].
    """
    UNIT = get_unit()
    unit_lbl = unit_label_short(UNIT)

    # Keys (prefixados)
    k_xml     = f"{prefix}_xml_sel"
    k_mode    = f"{prefix}_mode_sel"
    k_width   = f"{prefix}_width_m"
    k_length  = f"{prefix}_length_m"
    k_waste   = f"{prefix}_waste"
    k_cons    = f"{prefix}_cons_source"
    k_man_c   = f"{prefix}_man_c"
    k_man_w   = f"{prefix}_man_w"
    k_man_f   = f"{prefix}_man_f"
    k_fixed   = f"{prefix}_fixed_unit"
    k_price   = f"{prefix}_price"
    k_margin  = f"{prefix}_margin"
    k_tax     = f"{prefix}_tax"
    k_terms   = f"{prefix}_terms"
    k_round   = f"{prefix}_round"

    # Compartilhados do Compare
    ink_c = float(st.session_state.get("cmp_ink_c",  DEFAULTS["ink_color_per_l"]))
    ink_w = float(st.session_state.get("cmp_ink_w",  DEFAULTS["ink_white_per_l"]))
    fof   = float(st.session_state.get("cmp_fof",    DEFAULTS["fof_per_l"]))
    media = float(st.session_state.get("cmp_fabric", DEFAULTS["fabric_per_unit"]))

    # Outros variáveis (por job) + mão de obra variável/h
    other_vars_df = ensure_df(st.session_state.get(f"{prefix}_other_vars", [{"Name":"—","Value":0.0}]), ["Name","Value"])

    # XML do ZIP
    xml_inner_path = st.session_state.get(k_xml)
    if not xml_inner_path:
        _, xmls, *_ = read_zip_listing(uploaded_zip_bytes, cache_ns=prefix)
        xml_inner_path = xmls[0] if xmls else None
    if not xml_inner_path:
        st.session_state[f"{prefix}_panels"] = {"error": "No XML in ZIP."}
        return
    xml_bytes = read_bytes_from_zip(uploaded_zip_bytes, xml_inner_path, cache_ns=prefix)

    # Fatores (usa os sliders compartilhados)
    factors = get_mode_factors_from_state()

    # Base de consumo (com possível multiplicador de modo)
    mlmap_use = apply_consumption_source(
        xml_bytes,
        st.session_state.get(k_cons, "XML (exact)"),
        st.session_state.get(k_mode),
        factors,
        st.session_state.get(k_man_c, 0.0),
        st.session_state.get(k_man_w, 0.0),
        st.session_state.get(k_man_f, 0.0),
    )

    # Fallback: se a fonte é XML e o mapa tem só White/FOF, tenta primeiro XML com cores
    if str(st.session_state.get(k_cons, "XML (exact)")).lower().startswith("xml") and not has_color_channels(mlmap_use):
        fb = pick_first_with_colors(uploaded_zip_bytes, cache_ns=prefix)
        if fb:
            if "mode" in str(st.session_state.get(k_cons, "")).lower():
                group_key = MODE_GROUP.get(st.session_state.get(k_mode), "")
                mlmap_use = apply_mode_factors(fb, group_key, factors)
            else:
                mlmap_use = fb

    width_m  = float(st.session_state.get(k_width,  1.0))
    length_m = float(st.session_state.get(k_length, 1.0))
    waste    = float(st.session_state.get(k_waste,  0.0))
    # Resolve speed from a robust mode key
    _mode_key = st.session_state.get(k_mode)
    if _mode_key not in PRINT_MODES:
        _mode_key = infer_mode_from_xml(xml_bytes) if infer_mode_from_xml(xml_bytes) in PRINT_MODES else (list(PRINT_MODES.keys())[0] if PRINT_MODES else None)
    speed    = PRINT_MODES.get(_mode_key, {}).get("speed", 0.0)

    # Mão de obra variável -> por unidade
    labor_h = float(st.session_state.get(f"{prefix}_lab_h", 0.0))
    if UNIT == "m2":
        labor_var_per_unit = labor_h / max(1e-9, speed)
    else:
        m_per_h = speed / max(1e-9, width_m)
        labor_var_per_unit = labor_h / max(1e-9, m_per_h)

    other_vars_sum = float(other_vars_df["Value"].fillna(0).sum()) + labor_var_per_unit

    # Fixed allocation: direct vs monthly helper
    fix_mode_val = (st.session_state.get(f"{prefix}_fix_mode") or "Direct per unit")
    if str(fix_mode_val).lower().startswith("monthly"):
        fix_labor_m   = float(st.session_state.get(f"{prefix}_fix_labor_month", 0.0))
        fix_leasing_m = float(st.session_state.get(f"{prefix}_fix_leasing_month", 0.0))
        fix_depr_m    = float(st.session_state.get(f"{prefix}_fix_depr_month", 0.0))
        fix_over_m    = float(st.session_state.get(f"{prefix}_fix_over_month", 0.0))
        fix_others_df = ensure_df(st.session_state.get(f"{prefix}_fix_others", [{"Name":"—","Value":0.0}]), ["Name","Value"])
        fix_others_m  = float(fix_others_df["Value"].fillna(0).sum())
        prod_month_u  = float(st.session_state.get(f"{prefix}_fix_prod_month_units", DEFAULTS.get("prod_month_units", 30000.0)))
        fixed_per_unit_used = (fix_labor_m + fix_leasing_m + fix_depr_m + fix_over_m + fix_others_m) / prod_month_u if prod_month_u > 0 else 0.0
    else:
        fixed_per_unit_used = float(st.session_state.get(k_fixed, 0.0))

    res = simulate(
        UNIT, width_m, length_m, waste,
        speed, mlmap_use,
        ink_c, ink_w, fof,
        media, other_vars_sum, 0.0,
        fixed_per_unit_used,
        show_time_metrics=False,
    )

    qty = max(1e-9, float(res.get("qty_units", 0.0)))
    ink_total   = float(res.get("cost_ink", 0.0))
    fabric_cost = fabric_total(res)
    other_var   = float(res.get("cost_other", 0.0))
    fixed_cost  = float(res.get("cost_fixed", 0.0))
    total_cost  = float(res.get("total_cost", 0.0))
    variable_total = ink_total + fabric_cost + other_var
    variable_per_unit = variable_total / qty
    fixed_per_unit_card = fixed_cost / qty if qty > 0 else 0.0
    cost_unit_calc = total_cost / qty

    # Precificação
    margin = float(st.session_state.get(k_margin, 20.0))
    tax    = float(st.session_state.get(k_tax,    10.0))
    terms  = float(st.session_state.get(k_terms,   2.1))
    rnd    = float(st.session_state.get(k_round,  0.05))
    price_input = float(st.session_state.get(k_price, 0.0))

    suggested   = price_round(cost_unit_calc*(1 + margin/100 + tax/100), rnd)
    suggested   = price_round(suggested*(1 + terms/100), rnd)
    effective_price = price_input if price_input>0 else suggested

    rows_tot, rows_unit = build_cost_rows_from_sim(res, unit_lbl, sym, fx, price=effective_price)

    st.session_state[f"{prefix}_panels"] = {
        "rows_tot": rows_tot,
        "rows_unit": rows_unit,
        "unit_lbl": unit_lbl,
        "kpis": {
            "qty": qty,
            "area_waste_m2": res.get("area_waste_m2", 0.0),
            "total_ml_per_unit": res.get("total_ml_per_unit", 0.0),
            "time_print_h": res.get("time_print_h", 0.0),
            "time_total_h": res.get("time_total_h", 0.0),
        },
        "be": {
            "variable_per_unit": variable_per_unit,
            "effective_price": effective_price,
            "fixed_per_unit": fixed_per_unit_card,
        },
        "raw": res,
        "ml_map": dict(mlmap_use or {}),
        "label": label,
    }

# =========================
# A×B PDF — robusto a canais faltantes
# =========================
def build_comparison_pdf_matplotlib(channels: List[str], yA: List[float], yB: List[float],
                                    mlA_map: dict, mlB_map: dict,
                                    labelA: str | None = None, labelB: str | None = None,
                                    zA_bytes: bytes | None = None, zB_bytes: bytes | None = None,
                                    selected_channel: str | None = None,
                                    show_comp: bool = True,
                                    preview_size: str = "M",
                                    show_totals: bool = True) -> bytes:
    ch = list(channels or [])
    if not ch:
        ch = ["Cyan","Magenta","Yellow","Black","Red","Green","FOF","White"]

    # Normaliza tamanhos de yA e yB
    yA = list(yA or [])
    yB = list(yB or [])
    if len(yA) < len(ch): yA += [0.0]*(len(ch)-len(yA))
    if len(yB) < len(ch): yB += [0.0]*(len(ch)-len(yB))
    if len(yA) > len(ch): yA = yA[:len(ch)]
    if len(yB) > len(ch): yB = yB[:len(ch)]

    totalA = float(sum(yA)); totalB = float(sum(yB))
    delta_pct = 0.0 if totalA==0 else (totalB-totalA)/totalA*100.0

    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        fig = plt.figure(figsize=(8.27,11.69), dpi=150)  # A4 retrato
        fig.suptitle("A × B Comparison — Consumption per Channel (ml/m²)", fontsize=16, fontweight="bold", y=0.98)
        fig.text(0.08, 0.955, dt.datetime.now().strftime("%Y-%m-%d %H:%M"), fontsize=9, color="#7aa4ff")
        # Labels (use file names if provided)
        nameA = (labelA or "Job A")
        nameB = (labelB or "Job B")
        def _short(s: str, maxlen: int = 28) -> str:
            s = (s or "").split("/")[-1]
            return s if len(s) <= maxlen else (s[:maxlen-1] + "…")
        # Totals moved to previews (optional)
        # Move %Δ up to avoid overlapping previews
        fig.text(0.92, 0.955, f"%Δ vs A: {delta_pct:+.1f}%", fontsize=12,
                 color=("#2E7D32" if delta_pct<=0 else "#C62828"), ha='right')

        # Optional thumbnails (small previews)
        def _load_thumb(zbytes: bytes | None) -> np.ndarray | None:
            try:
                if not zbytes:
                    return None
                files, xmls, jpgs, tifs, _ = read_zip_listing(zbytes)
                cmap = {}
                for p in tifs:
                    ch = get_channel_from_filename(p.split("/")[-1])
                    if ch:
                        cmap[ch] = p
                sel = selected_channel or "Preview"
                path, typ = choose_path(sel, jpgs, cmap)
                if not path:
                    path = jpgs[0] if jpgs else (tifs[0] if tifs else None)
                    if not path:
                        return None
                im = load_preview_light(zbytes, path, max_side=420)
                thumb = letterbox(im, 320, 180)
                return np.asarray(thumb)
            except Exception:
                return None

        imgA = _load_thumb(zA_bytes)
        imgB = _load_thumb(zB_bytes)
        # Layout presets for preview & charts
        pz = (preview_size or "M").upper()
        if pz == "S":
            prev_rects = ([0.08, 0.81, 0.36, 0.10], [0.56, 0.81, 0.36, 0.10])
            bars_rect   = [0.08, 0.56, 0.84, 0.18]
            comp_rect   = [0.08, 0.40, 0.84, 0.10]
            table_rect  = [0.04, 0.07, 0.92, 0.32] if show_comp else [0.04, 0.07, 0.92, 0.36]
        elif pz == "L":
            prev_rects = ([0.08, 0.78, 0.40, 0.13], [0.52, 0.78, 0.40, 0.13])
            bars_rect   = [0.08, 0.54, 0.84, 0.20]
            comp_rect   = [0.08, 0.36, 0.84, 0.12]
            table_rect  = [0.04, 0.06, 0.92, 0.29] if show_comp else [0.04, 0.06, 0.92, 0.33]
        else:  # Medium
            prev_rects = ([0.08, 0.79, 0.38, 0.12], [0.54, 0.79, 0.38, 0.12])
            bars_rect   = [0.08, 0.54, 0.84, 0.20]
            comp_rect   = [0.08, 0.38, 0.84, 0.11]
            table_rect  = [0.04, 0.06, 0.92, 0.27] if show_comp else [0.04, 0.06, 0.92, 0.33]

        if imgA is not None:
            axA = fig.add_axes(prev_rects[0])
            axA.imshow(imgA)
            axA.axis('off')
            axA.set_title(_short(nameA, 36), fontsize=8)
            if show_totals:
                axA.text(0.5, 0.02, f"Total: {totalA:.2f} ml/m²", ha='center', va='bottom', fontsize=8,
                        transform=axA.transAxes, bbox=dict(facecolor='white', alpha=0.65, edgecolor='none', pad=2))
        if imgB is not None:
            axB = fig.add_axes(prev_rects[1])
            axB.imshow(imgB)
            axB.axis('off')
            axB.set_title(_short(nameB, 36), fontsize=8)
            if show_totals:
                axB.text(0.5, 0.02, f"Total: {totalB:.2f} ml/m²", ha='center', va='bottom', fontsize=8,
                        transform=axB.transAxes, bbox=dict(facecolor='white', alpha=0.65, edgecolor='none', pad=2))

        # Barras agrupadas
        ax1 = fig.add_axes(bars_rect)
        x = np.arange(len(ch)); width = 0.38
        colors = [CHANNEL_COLORS.get(c,"#888") for c in ch]
        bars1 = ax1.bar(x - width/2, yA, width, color=colors, label=_short(nameA))
        bars2 = ax1.bar(x + width/2, yB, width, color=colors, hatch="//", edgecolor="black", linewidth=0.6, alpha=0.85, label=_short(nameB))
        ax1.set_xticks(x); ax1.set_xticklabels(ch)
        ax1.set_ylabel("ml/m²"); ax1.set_title("Clustered bars")
        ax1.legend(loc="upper right", frameon=False)
        ymax = max([*yA,*yB,1e-9])*1.15; ax1.set_ylim(0, ymax)
        for b in list(bars1)+list(bars2):
            h = b.get_height()
            if h>0: ax1.text(b.get_x()+b.get_width()/2, h, f"{h:.2f}", ha="center", va="bottom", fontsize=6)

        # 100% composition (optional)
        if show_comp:
            ax2 = fig.add_axes(comp_rect)
            x2 = np.array([0,1]); bottoms = np.array([0.0,0.0])
            for c in ch:
                shareA = 0 if totalA==0 else (mlA_map.get(c,0.0)/totalA*100.0 if totalA else 0)
                shareB = 0 if totalB==0 else (mlB_map.get(c,0.0)/totalB*100.0 if totalB else 0)
                ax2.bar(x2, [shareA,shareB], bottom=bottoms, color=CHANNEL_COLORS.get(c,"#888"), label=c)
                bottoms += np.array([shareA,shareB])
            ax2.set_xticks(x2); ax2.set_xticklabels([_short(nameA), _short(nameB)])
            ax2.set_ylabel("% of total"); ax2.set_title("100% composition")
            ax2.set_ylim(0,100)
            ax2.legend(ncol=4, bbox_to_anchor=(0.0,-0.55,1.0,.102), loc="upper left", frameon=False, fontsize=7)

        # Tabela
        diff = [b-a for a,b in zip(yA,yB)]
        pct  = [ (0.0 if a==0 else (b-a)/a*100.0) for a,b in zip(yA,yB) ]
        ax3 = fig.add_axes(table_rect); ax3.axis("off")
        # Build header labels with smart wrapping to avoid overlap
        def _wrap_width_for(name: str) -> int:
            # Allow wider lines to use more of the column width
            L = len(name or "")
            if L > 45: return 20
            if L > 38: return 22
            if L > 30: return 24
            return 26
        def _wrap_name_for_header(name: str, width: int | None = None) -> str:
            base = _short(name, 56)
            w = width if width else _wrap_width_for(base)
            return textwrap.fill(base, width=w) + "\n(ml/m²)"
        col_labels = [
            "Channel",
            _wrap_name_for_header(nameA),
            _wrap_name_for_header(nameB),
            "Δ (B−A)",
            "%Δ vs A",
        ]
        cell_text = [[c, f"{yA[i]:.2f}", f"{yB[i]:.2f}", f"{diff[i]:+.2f}", f"{pct[i]:+.1f}%"] for i,c in enumerate(ch)]
        # Total row
        cell_text.append(["Total", f"{totalA:.2f}", f"{totalB:.2f}", f"{(totalB-totalA):+.2f}", f"{delta_pct:+.1f}%"])
        # Column widths tuned to avoid header overlap
        if len(col_labels) == 5:
            # Allocate most width to A/B; Δ and %Δ compact; Channel smaller
            # Distribute A/B width based on name lengths (bounded 40–60%)
            baseA = _short(nameA, 56); baseB = _short(nameB, 56)
            lenA = max(1, len(baseA)); lenB = max(1, len(baseB))
            shareA = min(0.60, max(0.40, lenA/(lenA+lenB)))
            total_ab = 0.68
            colA = total_ab * shareA
            colB = total_ab * (1.0 - shareA)
            col_widths = [0.12, colA, colB, 0.10, 0.10]
        else:
            col_widths = [1.0/len(col_labels)]*len(col_labels)
        table = ax3.table(cellText=cell_text, colLabels=col_labels, colWidths=col_widths, loc="center")
        table.auto_set_font_size(False)
        table.set_fontsize(6.5)
        table.scale(1.03, 1.12)
        # Center align all text to reduce clipping
        for (r, c), cell in table.get_celld().items():
            cell.get_text().set_ha('center')
            cell.get_text().set_va('center')
        # Increase header row height for more breathing room (names + unit)
        # and adapt header font size to very long names
        baseA = _short(nameA, 56)
        baseB = _short(nameB, 56)
        linesA = max(1, math.ceil(len(baseA) / _wrap_width_for(baseA)))
        linesB = max(1, math.ceil(len(baseB) / _wrap_width_for(baseB)))
        max_lines = max(linesA, linesB)
        hdr_factor = 1.60 + max(0, (max_lines - 2)) * 0.15  # grows for 3+ lines
        hdr_font = 6.1 if max_lines <= 2 else (5.8 if max_lines == 3 else 5.5)
        try:
            # Increase all row heights slightly, and header a bit more
            ncols = len(col_labels)
            # Determine total rows by probing indices in cell dict
            rows = [r for (r, _c) in table.get_celld().keys()]
            max_r = max(rows) if rows else 0
            for r in range(max_r + 1):
                for c in range(ncols):
                    cell = table[(r, c)]
                    h = cell.get_height()
                    if r == 0:
                        cell.set_height(h * hdr_factor)
                        cell.get_text().set_fontsize(hdr_font)
                    else:
                        cell.set_height(h * 1.18)
        except Exception:
            pass

        pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)
    return buf.getvalue()

# =========================
# Compare — Job inputs (module-level helper)
# =========================
def compare_job_inputs(prefix: str, label: str, zbytes: bytes):
    """Render inputs for a Compare job (A or B). Extracted from ui_compare_option_b for reuse."""
    files, xmls, jpgs, tifs, _ = read_zip_listing(zbytes, cache_ns=prefix)
    submitted = False
    with st.form(key=f"{prefix}_form"):
    
        # XML selection
        xml_default = 0 if not st.session_state.get(f"{prefix}_xml_sel") else max(0, min(len(xmls)-1, xmls.index(st.session_state.get(f"{prefix}_xml_sel")))) if st.session_state.get(f"{prefix}_xml_sel") in xmls else 0
        xml_sel = st.selectbox("XML (ml/m² base)", options=xmls, index=xml_default, key=f"{prefix}_xml_sel")
        xml_bytes_hdr = read_bytes_from_zip(zbytes, st.session_state.get(f"{prefix}_xml_sel", xml_sel), cache_ns=prefix)
        w_xml_def, h_xml_def, area_xml_m2_def = get_xml_dims_m(xml_bytes_hdr)
    
        # Print mode (lock when XML exact)
        auto_mode = infer_mode_from_xml(xml_bytes_hdr)
        white_in = has_white_in_xml(xml_bytes_hdr)
        PRINT_MODE_OPTIONS = list(PRINT_MODES.keys())
        # Resolve a safe default mode key
        mode_default = auto_mode if auto_mode in PRINT_MODES else (PRINT_MODE_OPTIONS[0] if PRINT_MODE_OPTIONS else None)
        idx_mode = PRINT_MODE_OPTIONS.index(mode_default) if (mode_default in PRINT_MODE_OPTIONS) else 0
    
        # Consumption source first, so we can decide whether to lock the print mode
        cons_src = st.radio(
            "Consumption source (ml/m²)",
            ["XML (exact)", "XML + mode multiplier (%)", "Manual"],
            index=0,
            key=f"{prefix}_cons_source", help="Choose the source of ml/m²: exact XML, XML scaled by print mode multipliers, or manual values.",
        )
    
        lock_mode = str(cons_src).startswith("XML (exact)")
        # Ensure session state holds a valid option; otherwise Streamlit shows "Choose an option"
        if (st.session_state.get(f"{prefix}_mode_sel") not in PRINT_MODE_OPTIONS) or lock_mode:
            st.session_state[f"{prefix}_mode_sel"] = mode_default
    
        mode_sel = st.selectbox(
            "Print mode",
            PRINT_MODE_OPTIONS,
            index=idx_mode,
            key=f"{prefix}_mode_sel",
            format_func=lambda m: mode_option_label(m, white_in, get_unit(), w_xml_def),
            disabled=lock_mode,
            help=("Locked to the XML-inferred mode when using XML (exact)." if lock_mode else None),
        )
        # Safe effective mode (avoid KeyError when widget returns None)
        # Effective mode with robust fallback
        mode_eff = mode_sel if mode_sel in PRINT_MODES else (mode_default if mode_default in PRINT_MODES else None)
        mode_for_caption = mode_eff if mode_eff in PRINT_MODES else (PRINT_MODE_OPTIONS[0] if PRINT_MODE_OPTIONS else None)
        if mode_for_caption in PRINT_MODES:
            st.caption(
                f"XML area: **{area_xml_m2_def:.3f} m²** • Speed: **{speed_label(get_unit(), PRINT_MODES[mode_for_caption]['speed'], w_xml_def)}**"
            )
        # Resolution caption — fall back to mode_for_caption when auto inference is unavailable
        res_key = auto_mode if auto_mode in PRINT_MODES else mode_for_caption
        if res_key in PRINT_MODES:
            st.caption(
                f"XML resolution: **{PRINT_MODES[res_key]['res_color']} (color){' • ' + WHITE_RES + ' (white)' if white_in else ''}**"
            )
    
        # Geometry & waste
        with st_div("ink-fixed-grid"):
            a1, a2, a3 = st.columns(3)
            a1.number_input("Usable width (m)", value=float(round(w_xml_def, 3)), min_value=0.0, step=0.01, format="%.3f", key=f"{prefix}_width_m",
                            help="Printable width used for this job.")
            a2.number_input("Length (m)",        value=float(round(h_xml_def, 3)), min_value=0.0, step=0.01, format="%.3f", key=f"{prefix}_length_m",
                            help="Length to be produced for this job.")
            a3.number_input("Waste (%)",         value=2.0,                        min_value=0.0, step=0.5,                key=f"{prefix}_waste",
                            help="Allowance for setup, trims and reprints.")
    
        # Details for source
        if cons_src.startswith("XML + mode multiplier"):
            st.info("Using XML + mode multipliers. The selected print mode applies Color/White/FOF factors.")
            render_mode_multiplier_controls(use_expander=False, show_presets=True, key_prefix=prefix, sync_to_shared=True)
        elif cons_src == "Manual":
            with st_div("ink-fixed-grid"):
                mcols = st.columns(3)
                mcols[0].number_input(
                f"Manual — Color (ml{per_unit('m2')})",
                value=float(st.session_state.get(f"{prefix}_man_c", 0.0)),
                min_value=0.0, step=0.1, key=f"{prefix}_man_c"
            )
                mcols[1].number_input(
                f"Manual — White (ml{per_unit('m2')})",
                value=float(st.session_state.get(f"{prefix}_man_w", 0.0)),
                min_value=0.0, step=0.1, key=f"{prefix}_man_w"
            )
                mcols[2].number_input(
                f"Manual — FOF (ml{per_unit('m2')})",
                value=float(st.session_state.get(f"{prefix}_man_f", 0.0)),
                min_value=0.0, step=0.1, key=f"{prefix}_man_f"
            )
    
        # Variable labor + other variables
        lab1, _ = st.columns([1,1])
        lab1.number_input("Variable labor ($/h) — use only if NOT in Fixed", min_value=0.0, value=float(st.session_state.get(f"{prefix}_lab_h", 0.0)), step=0.5, key=f"{prefix}_lab_h",
                          help="Hourly variable labor. Do not use if it is already included in monthly fixed costs.")
        st.caption(f"Other variables ({per_unit(get_unit())}) — optional")
        _vars_input = ensure_df(st.session_state.get(f"{prefix}_other_vars", [{"Name": "—", "Value": 0.0}]), ["Name","Value"])
        df_vars = st.data_editor(_vars_input, num_rows="dynamic", use_container_width=True, key=f"{prefix}_other_vars_editor")
        st.session_state[f"{prefix}_other_vars"] = ensure_df(df_vars, ["Name","Value"]).to_dict(orient="records")
    
        # Fixed costs & pricing
        fix_mode = st.radio(
            "Fixed costs mode",
            ["Direct per unit", "Monthly helper"],
            index=0 if (str(st.session_state.get(f"{prefix}_fix_mode", "Direct per unit")).startswith("Direct")) else 1,
            horizontal=True,
            key=f"{prefix}_fix_mode",
            help="Choose direct fixed allocation per unit, or compute $/unit by entering monthly fixed costs + monthly production.",
        )
        if fix_mode.startswith("Direct"):
            with st_div("ink-fixed-grid"):
                mv1, mv2, mv3, mv4, mv5 = st.columns(5)
                mv1.number_input(
                    f"Fixed allocation\u00A0(/"+unit_label_short(get_unit())+")",
                    min_value=0.0,
                    value=float(st.session_state.get(f"{prefix}_fixed_unit", 0.0)),
                    step=0.05,
                    key=f"{prefix}_fixed_unit",
                    help="Fixed cost per unit if not using the monthly helper.",
                )
                mv2.number_input(f"Price {per_unit(get_unit())}", min_value=0.0, value=float(st.session_state.get(f"{prefix}_price", 0.0)), step=0.10, key=f"{prefix}_price",
                                 help="Selling price per unit in the chosen unit.")
                mv3.number_input("Target margin (%)", min_value=0.0, value=float(st.session_state.get(f"{prefix}_margin", 20.0)), step=0.5, key=f"{prefix}_margin",
                                 help="Target markup over cost before taxes and fees.")
                mv4.number_input("Taxes (%)",         min_value=0.0, value=float(st.session_state.get(f"{prefix}_tax", 10.0)),    step=0.5, key=f"{prefix}_tax",
                                 help="Taxes or withholdings applied to price.")
                mv5.number_input("Fees/Terms (%)",    min_value=0.0, value=float(st.session_state.get(f"{prefix}_terms", 2.10)),  step=0.05, key=f"{prefix}_terms",
                                 help="Payment terms, card fees, financing, etc.")
            # Round to — keep within grid styling to align labels across A & B
            with st_div("ink-fixed-grid"):
                rcol = st.columns(1)[0]
                rcol.selectbox("Round to", ["0.01", "0.05", "0.10"], index={"0.01":0,"0.05":1,"0.10":2}.get(str(st.session_state.get(f"{prefix}_round", 0.05)),1), key=f"{prefix}_round",
                                help="Rounding step for suggested price.")
        else:
            st.markdown('<div class="ink-callout"><b>Monthly fixed costs</b> — labor, leasing, depreciation, overheads and other items.</div>', unsafe_allow_html=True)
            with st_div("ink-fixed-grid"):
                fx1, fx2, fx3, fx4 = st.columns(4)
                fx1.number_input("Labor (monthly)",        min_value=0.0, value=float(st.session_state.get(f"{prefix}_fix_labor_month", 0.0)),   step=10.0, key=f"{prefix}_fix_labor_month", help="Salaries or fixed staff per month.")
                fx2.number_input("Leasing/Rent (monthly)", min_value=0.0, value=float(st.session_state.get(f"{prefix}_fix_leasing_month", 0.0)), step=10.0, key=f"{prefix}_fix_leasing_month", help="Printer leasing, rent, subscriptions, RIP, etc.")
                fx3.number_input("Depreciation (monthly)", min_value=0.0, value=float(st.session_state.get(f"{prefix}_fix_depr_month", 0.0)),    step=10.0, key=f"{prefix}_fix_depr_month", help="Monthly CAPEX (depreciation).")
                fx4.number_input("Overheads (monthly)",    min_value=0.0, value=float(st.session_state.get(f"{prefix}_fix_over_month", 0.0)),    step=10.0, key=f"{prefix}_fix_over_month", help="Base energy, insurance, maintenance, overheads.")
            st.caption("Other fixed (monthly)")
            _fix_input = ensure_df(st.session_state.get(f"{prefix}_fix_others", [{"Name":"—","Value":0.0}]), ["Name","Value"])
            df_fix = st.data_editor(_fix_input, num_rows="dynamic", use_container_width=True, key=f"{prefix}_fix_others_editor")
            st.session_state[f"{prefix}_fix_others"] = ensure_df(df_fix, ["Name","Value"]).to_dict(orient="records")
            # Monthly production helper
            prod_m = monthly_production_inputs(get_unit(), unit_label_short(get_unit()), state_prefix=f"{prefix}_fix")
            # Allocation
            sum_others = ensure_df(st.session_state.get(f"{prefix}_fix_others", []), ["Name","Value"]).get("Value", pd.Series(dtype=float)).fillna(0).sum() if st.session_state.get(f"{prefix}_fix_others") else 0.0
            total_fix_m = (
                float(st.session_state.get(f"{prefix}_fix_labor_month", 0.0))
                + float(st.session_state.get(f"{prefix}_fix_leasing_month", 0.0))
                + float(st.session_state.get(f"{prefix}_fix_depr_month", 0.0))
                + float(st.session_state.get(f"{prefix}_fix_over_month", 0.0))
                + float(sum_others)
            )
            alloc = (total_fix_m / prod_m) if prod_m > 0 else 0.0
            st.metric(f"Fixed allocation ({per_unit(get_unit())})", f"{alloc:.4f}")
            st.caption(f"Monthly fixed total: US$ {total_fix_m:,.2f} • Production: {prod_m:,.0f} {unit_label_short(get_unit())}/month")
            # Pricing controls
            with st_div("ink-fixed-grid"):
                pv2, pv3, pv4, pv5 = st.columns(4)
                pv2.number_input(f"Price {per_unit(get_unit())}", min_value=0.0, value=float(st.session_state.get(f'{prefix}_price', 0.0)), step=0.10, key=f"{prefix}_price")
                pv3.number_input("Target margin (%)", min_value=0.0, value=float(st.session_state.get(f'{prefix}_margin', 20.0)), step=0.5, key=f"{prefix}_margin")
                pv4.number_input("Taxes (%)",         min_value=0.0, value=float(st.session_state.get(f'{prefix}_tax', 10.0)),    step=0.5, key=f"{prefix}_tax")
                pv5.number_input("Fees/Terms (%)",    min_value=0.0, value=float(st.session_state.get(f'{prefix}_terms', 2.10)),  step=0.05, key=f"{prefix}_terms")
            with st_div("ink-fixed-grid"):
                st.columns(1)[0].selectbox("Round to", ["0.01", "0.05", "0.10"], index={"0.01":0,"0.05":1,"0.10":2}.get(str(st.session_state.get(f"{prefix}_round", 0.05)),1), key=f"{prefix}_round", help="Rounding step for suggested price.")
    
            submitted = st.form_submit_button(f"Apply {label}")

        if submitted:
            if str(st.session_state.get(f"{prefix}_cons_source", "")).startswith("XML + mode"):
                sync_mode_scalers_from_prefix(prefix)
            st.success(f"{label} saved. Now click 'Calculate A and B'.")

# =========================
# Single PDF — same visual language as A×B
# =========================
def build_single_pdf_matplotlib(channels: List[str], y: List[float], ml_map: dict,
                                label: str | None = None,
                                z_bytes: bytes | None = None,
                                selected_channel: str | None = None,
                                show_comp: bool = True,
                                preview_size: str = "M",
                                show_totals: bool = True) -> bytes:
    ch = list(channels or [])
    if not ch:
        ch = ["Cyan","Magenta","Yellow","Black","Red","Green","FOF","White"]
    y = list(y or [])
    if len(y) < len(ch): y += [0.0]*(len(ch)-len(y))
    if len(y) > len(ch): y = y[:len(ch)]

    total = float(sum(y))

    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        fig = plt.figure(figsize=(8.27,11.69), dpi=150)
        fig.suptitle("Single — Consumption per Channel (ml/m²)", fontsize=16, fontweight="bold", y=0.98)
        fig.text(0.08, 0.955, dt.datetime.now().strftime("%Y-%m-%d %H:%M"), fontsize=9, color="#7aa4ff")
        name = (label or "Job")
        def _short(s: str, maxlen: int = 34) -> str:
            s = (s or "").split("/")[-1]
            return s if len(s) <= maxlen else (s[:maxlen-1] + "…")

        # Layout presets
        pz = (preview_size or "M").upper()
        if pz == "S":
            prev_rect = [0.30, 0.81, 0.40, 0.10]
            bars_rect = [0.08, 0.56, 0.84, 0.18]
            comp_rect = [0.08, 0.40, 0.84, 0.10]
            table_rect= [0.06, 0.07, 0.88, 0.30] if show_comp else [0.06, 0.07, 0.88, 0.36]
        elif pz == "L":
            prev_rect = [0.28, 0.78, 0.44, 0.13]
            bars_rect = [0.08, 0.54, 0.84, 0.20]
            comp_rect = [0.08, 0.36, 0.84, 0.12]
            table_rect= [0.06, 0.06, 0.88, 0.28] if show_comp else [0.06, 0.06, 0.88, 0.33]
        else:
            prev_rect = [0.29, 0.79, 0.42, 0.12]
            bars_rect = [0.08, 0.54, 0.84, 0.20]
            comp_rect = [0.08, 0.38, 0.84, 0.11]
            table_rect= [0.06, 0.06, 0.88, 0.26] if show_comp else [0.06, 0.06, 0.88, 0.31]

        # Preview
        def _load_thumb(zb: bytes | None) -> np.ndarray | None:
            try:
                if not zb: return None
                files, xmls, jpgs, tifs, _ = read_zip_listing(zb)
                cmap = {}
                for p in tifs:
                    chn = get_channel_from_filename(p.split("/")[-1])
                    if chn: cmap[chn] = p
                sel = selected_channel or "Preview"
                path, typ = choose_path(sel, jpgs, cmap)
                if not path:
                    path = jpgs[0] if jpgs else (tifs[0] if tifs else None)
                    if not path: return None
                im = load_preview_light(zb, path, max_side=420)
                thumb = letterbox(im, 360, 200)
                return np.asarray(thumb)
            except Exception:
                return None
        img = _load_thumb(z_bytes)
        if img is not None:
            axp = fig.add_axes(prev_rect)
            axp.imshow(img)
            axp.axis('off')
            axp.set_title(_short(name, 40), fontsize=9)
            if show_totals:
                axp.text(0.5, 0.02, f"Total: {total:.2f} ml/m²", ha='center', va='bottom', fontsize=9,
                        transform=axp.transAxes, bbox=dict(facecolor='white', alpha=0.65, edgecolor='none', pad=2))

        # Bars
        ax1 = fig.add_axes(bars_rect)
        x = np.arange(len(ch)); width = 0.60
        colors = [CHANNEL_COLORS.get(c,"#888") for c in ch]
        bars = ax1.bar(x, y, width, color=colors, label=_short(name))
        ax1.set_xticks(x); ax1.set_xticklabels(ch)
        ax1.set_ylabel("ml/m²"); ax1.set_title("Per-channel consumption")
        ax1.legend(loc="upper right", frameon=False)
        ymax = max([*y, 1e-9]) * 1.15; ax1.set_ylim(0, ymax)
        for b in bars:
            h = b.get_height()
            if h>0: ax1.text(b.get_x()+b.get_width()/2, h, f"{h:.2f}", ha="center", va="bottom", fontsize=7)

        # 100% composition
        if show_comp:
            ax2 = fig.add_axes(comp_rect)
            x2 = np.array([0]); bottom = 0.0
            for c in ch:
                share = 0 if total==0 else (ml_map.get(c,0.0)/total*100.0)
                ax2.bar(x2, [share], bottom=[bottom], color=CHANNEL_COLORS.get(c,"#888"), label=c)
                bottom += share
            ax2.set_xticks(x2); ax2.set_xticklabels([_short(name)])
            ax2.set_ylabel("% of total"); ax2.set_title("100% composition")
            ax2.set_ylim(0,100)
            ax2.legend(ncol=4, bbox_to_anchor=(0.0,-0.55,1.0,.102), loc="upper left", frameon=False, fontsize=7)

        # Table
        ax3 = fig.add_axes(table_rect); ax3.axis('off')
        # Header labels
        def _wrap_width_for(n: str) -> int:
            L = len(n or "")
            if L > 38: return 22
            if L > 30: return 24
            return 26
        def _wrap_name(n: str) -> str:
            base = _short(n, 56)
            return textwrap.fill(base, width=_wrap_width_for(base)) + "\n(ml/m²)"
        col_labels = ["Channel", _wrap_name(name), "% of total"]
        pct = [ (0.0 if total==0 else (ml_map.get(c,0.0)/total*100.0)) for c in ch ]
        cell_text = [[c, f"{y[i]:.2f}", f"{pct[i]:.1f}%"] for i,c in enumerate(ch)]
        # Total row
        cell_text.append(["Total", f"{total:.2f}", "100.0%"])
        col_widths = [0.22, 0.54, 0.24]
        table = ax3.table(cellText=cell_text, colLabels=col_labels, colWidths=col_widths, loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(6.6)
        table.scale(1.03, 1.12)
        for (r,c), cell in table.get_celld().items():
            cell.get_text().set_ha('center'); cell.get_text().set_va('center')
        try:
            ncols = len(col_labels)
            rows = [r for (r,_c) in table.get_celld().keys()]
            max_r = max(rows) if rows else 0
            for r in range(max_r+1):
                for c in range(ncols):
                    cell = table[(r,c)]
                    h = cell.get_height()
                    if r == 0:
                        cell.set_height(h*1.55)
                        # smaller header font for long names
                        cell.get_text().set_fontsize(6.0)
                    else:
                        cell.set_height(h*1.12)
        except Exception:
            pass

        pdf.savefig(fig, bbox_inches='tight'); plt.close(fig)
    return buf.getvalue()
# ===========================================
# FLUXO: COMPARE A×B — Option B (forms + Apply + global calculate)
# ===========================================
def ui_compare_option_b():
    UNIT = get_unit()
    unit_lbl = unit_label_short(UNIT)

    section("Compare A×B", "Fill A and B. Each side has its **Apply**; then use the global **Calculate A and B** button.")


    # Shared preview size (applies to A and B) — mirrors Single
    st.markdown("---")
    pv1, pv2 = st.columns(2)
    pv1.slider(
        "Preview box width (px)", 320, 900,
        int(st.session_state.get("cmp_prev_w", st.session_state.get("single_prev_w", 560))), 10,
        key="cmp_prev_w", help="Applies to both A and B.")
    pv2.slider(
        "Preview box height (px)", 260, 900,
        int(st.session_state.get("cmp_prev_h", st.session_state.get("single_prev_h", 460))), 10,
        key="cmp_prev_h")
    # Defaults restored to previous behavior: no crop (letterbox)
    st.checkbox("Fill channel previews (crop to area)", value=st.session_state.get("cmp_fill_preview", False), key="cmp_fill_preview",
                 help="When viewing channel separations (TIFF), scale to fill the preview box (center crop).")
    st.checkbox("Fill preview image (JPG)", value=st.session_state.get("cmp_fill_preview_jpg", False), key="cmp_fill_preview_jpg",
                 help="Scale JPG preview to fill the box (center crop).")
    st.checkbox("Auto-trim white margins (channels)", value=st.session_state.get("cmp_trim_channels", True), key="cmp_trim_channels",
                 help="Remove uniform white margins around TIFF channels before rendering.")
    st.markdown("---")
    # Shared per-mode multipliers (applied to both A and B)
    render_mode_multiplier_controls(use_expander=True, expanded=False, show_presets=True)
    st.markdown("---")

    # =========================
    # Builders: PREVIEW (sem inputs) e INPUTS (para exibir após o PDF A×B)
    # =========================
    def job_preview(prefix: str, label: str, zbytes: bytes, show_ml: bool = True, show_px: bool = True):
        """Show preview, per-channel (ml/m²) chart and Fire pixels — no inputs here."""
        files, xmls, jpgs, tifs, ad = read_zip_listing(zbytes)
        c1, c2, c3 = st.columns(3)
        c1.metric("XML files", len(xmls)); c2.metric("JPG files", len(jpgs)); c3.metric("TIFF files", len(tifs))
        # Silently ignore AppleDouble entries if present

        # ---------- PREVIEW (usa seleção de canal compartilhada) ----------
        # Title omitted here to keep the shared channel buttons visually closer to the previews.
        prev_w = int(st.session_state.get("cmp_prev_w", 560))
        prev_h = int(st.session_state.get("cmp_prev_h", 460))

        # Mapa canal -> TIFF para este job
        chan_map = {}
        for p in tifs:
            ch = get_channel_from_filename(p.split("/")[-1])
            if ch:
                chan_map[ch] = p

        selected_channel = st.session_state.get("cmp_chan_sel", "Preview")

        # XML para legenda do gráfico (ml/m²)
        xml_legend_idx = 0
        if st.session_state.get(f"{prefix}_xml_legend") in xmls:
            xml_legend_idx = xmls.index(st.session_state.get(f"{prefix}_xml_legend"))
        xml_for_legend = st.selectbox(
            f"{label} — XML for legend (ml/m²)",
            xmls,
            index=xml_legend_idx,
            help="Used only for the per-channel chart below.",
            key=f"{prefix}_xml_legend",
        )
        mlm2 = {}
        mlm2 = ml_per_m2_from_xml_bytes(read_bytes_from_zip(zbytes, xml_for_legend, cache_ns=prefix))
        if not has_color_channels(mlm2):
            fb = pick_first_with_colors(zbytes, cache_ns=prefix)
            if fb:
                mlm2 = fb
        # guarda para o gráfico global A×B
        st.session_state[f"{prefix}_legend_ml_map"] = dict(mlm2 or {})

        # Always render previews and charts (no manual Update button)
        do_render = True

        leftC, rightC = st.columns([1.15, 1.0])
        with leftC:
            path, _ = choose_path(selected_channel, jpgs, chan_map)
            fill_flag = bool(st.session_state.get("cmp_fill_preview_jpg", True)) if selected_channel == "Preview" else bool(st.session_state.get("cmp_fill_preview", True))
            trim_flag = bool(st.session_state.get("cmp_trim_channels", True)) if selected_channel != "Preview" else False
            preview_fragment(
                f"{prefix}_preview",
                zbytes,
                path,
                width=prev_w,
                height=prev_h,
                fill_flag=fill_flag,
                trim_flag=trim_flag,
                max_side=int(prev_w * 1.35),
                caption=path or "Preview",
            )
            if selected_channel != "Preview" and mlm2:
                v = mlm2.get(selected_channel)
                if v is not None:
                    st.caption(f"**{selected_channel}**: {v:.2f} ml/m²")
            if mlm2:
                st.markdown(f"Total consumption: **{total_ml_per_m2_from_map(mlm2):.2f} ml/m²**")
        with rightC:
            st.empty()

        # === Per-channel consumption (ml/m²) — largura total ===
        if show_ml:
            render_title_with_hint(
                "Per-channel consumption (ml/m²)",
                "ml/m² = file coverage × base channel factor × mode multipliers (Color/White/FOF) × user adjustments."
            )
            if mlm2:
                items = sorted(mlm2.items(), key=lambda kv: kv[1], reverse=True)
                labels = [k for k, _ in items]
                values = [v for _, v in items]
                colors = [CHANNEL_COLORS.get(k, "#888") for k in labels]

                fig_ch = go.Figure()
                _show_vals = bool(st.session_state.get("cmp_job_show_vals", False))
                fig_ch.add_trace(go.Bar(
                    x=labels, y=values, marker=dict(color=colors),
                    text=[f"{v:.2f}" for v in values] if _show_vals else None,
                    textposition="outside" if _show_vals else None,
                    cliponaxis=False if _show_vals else None,
                ))
                fig_ch.update_layout(
                    template="plotly_white",
                    height=prev_h,
                    margin=dict(l=10, r=10, t=30, b=10),
                    yaxis_title="ml/m²",
                    xaxis_title="Channel",
                )
                st.plotly_chart(fig_ch, use_container_width=True, key=f"{prefix}_ml_chart", config=plotly_cfg())
            else:
                st.info("Select an XML to display the chart.")

        # --- Fire pixels per channel (K) ---
        pxm2 = {}
        try:
            pxm2 = fire_pixels_map_from_xml_bytes(read_bytes_from_zip(zbytes, xml_for_legend, cache_ns=prefix))
        except Exception:
            pxm2 = {}

        if show_px:
            render_title_with_hint(
                "Fire pixels per channel (K)",
                "K pixels fired per channel, read from NumberOfFirePixelsPerSeparation in the XML."
            )
            if pxm2:
                items_px = sorted(pxm2.items(), key=lambda kv: kv[1], reverse=True)
                labels_px = [k for k, _ in items_px]
                values_px = [float(v)/1000.0 for _, v in items_px]  # K pixels
                colors_px = [CHANNEL_COLORS.get(k, "#888") for k in labels_px]

                fig_px = go.Figure()
                fig_px.add_trace(go.Bar(x=labels_px, y=values_px, marker=dict(color=colors_px), text=[f"{v:.1f}" for v in values_px], textposition="outside", cliponaxis=False))
                fig_px.update_layout(
                    template="plotly_white",
                    height=prev_h,
                    margin=dict(l=10, r=10, t=30, b=10),
                    yaxis_title="K pixels",
                    xaxis_title="Channel",
                )
                st.plotly_chart(fig_px, use_container_width=True, key=f"{prefix}_px_chart", config=plotly_cfg())
            else:
                st.info("This XML does not contain 'NumberOfFirePixelsPerSeparation'.")

        # --- Size-based ink consumption (per job) ---
        st.markdown("---")
        st.markdown(f"**Ink consumption by size — {label}**")
        # Read original dims from the selected XML
        w0 = h0 = 0.0
        try:
            xml_bytes_sz = read_bytes_from_zip(zbytes, xml_for_legend, cache_ns=prefix)
            w0, h0, _ = get_xml_dims_m(xml_bytes_sz)
        except Exception:
            pass

        unit_key = f"{prefix}_size_unit"
        src_key  = f"{prefix}_size_source"
        st.radio("Unit", ["m", "cm"], index=1, horizontal=True, key=unit_key)
        st.radio(
            "Size source",
            ["XML original", "Custom"],
            index=0 if (w0>0 and h0>0) else 1,
            horizontal=True,
            key=src_key,
        )
        u = st.session_state.get(unit_key, "cm")
        s1,s2,s3 = st.columns(3)
        if st.session_state.get(src_key) == "XML original":
            width_m  = float(w0 or 0.0)
            length_m = float(h0 or 0.0)
            disp_w = width_m if u=="m" else width_m*100.0
            disp_h = length_m if u=="m" else length_m*100.0
            s1.metric(f"Width ({u})", f"{disp_w:.3f}")
            s2.metric(f"Length ({u})", f"{disp_h:.3f}")
            waste = s3.number_input("Waste (%)", min_value=0.0, value=float(st.session_state.get(f"{prefix}_size_waste", 0.0)), step=0.5, key=f"{prefix}_size_waste")
        else:
            if u == "m":
                default_w = float(round(w0 or 1.45, 3))
                default_h = float(round(h0 or 1.00, 3))
                in_w = s1.number_input("Width (m)",  min_value=0.0, value=default_w, step=0.01, format="%.3f", key=f"{prefix}_size_w")
                in_h = s2.number_input("Length (m)", min_value=0.0, value=default_h, step=0.01, format="%.3f", key=f"{prefix}_size_h")
                width_m, length_m = float(in_w), float(in_h)
            else:
                default_w = float(round((w0 or 1.45)*100.0, 1)) if (w0 or 0.0) > 0 else 145.0
                default_h = float(round((h0 or 1.00)*100.0, 1)) if (h0 or 0.0) > 0 else 100.0
                in_w = s1.number_input("Width (cm)",  min_value=0.0, value=default_w, step=0.5, format="%.1f", key=f"{prefix}_size_w_cm")
                in_h = s2.number_input("Length (cm)", min_value=0.0, value=default_h, step=0.5, format="%.1f", key=f"{prefix}_size_h_cm")
                width_m, length_m = float(in_w)/100.0, float(in_h)/100.0
            waste = s3.number_input("Waste (%)", min_value=0.0, value=float(st.session_state.get(f"{prefix}_size_waste", 0.0)), step=0.5, key=f"{prefix}_size_waste")

        if mlm2:
            area = max(0.0, width_m * length_m) * (1.0 + float(waste or 0.0)/100.0)
            rows_sz = []
            total_ml = 0.0
            total_linear_per_m = 0.0
            total_linear_ml = 0.0
            color_total = white_total = fof_total = 0.0
            for ch_name, ml_per_m2 in sorted(mlm2.items(), key=lambda kv: kv[1], reverse=True):
                ml_per_m2 = float(ml_per_m2)
                ml_total = ml_per_m2 * area
                linear_per_m = ml_per_m2 * float(width_m or 0.0)
                linear_total = linear_per_m * float(length_m or 0.0)
                rows_sz.append({
                    "Channel": ch_name,
                    "ml/m²": round(ml_per_m2, 3),
                    "Area (m²)": round(area, 3),
                    "Ink (ml)": round(ml_total, 2),
                    "Linear (ml/m)": round(linear_per_m, 2),
                    "Linear total (ml)": round(linear_total, 2),
                })
                total_ml += ml_total
                total_linear_per_m += linear_per_m
                total_linear_ml += linear_total
                low = (ch_name or '').lower()
                if low in CHANNELS_WHITE:
                    white_total += ml_total
                elif low in CHANNELS_FOF:
                    fof_total += ml_total
                else:
                    color_total += ml_total
            df_sz = pd.DataFrame(rows_sz)
            st.caption(f"Area (m²): {area:.3f}")
            cols_order = [c for c in ["Channel","ml/m²","Ink (ml)","Linear (ml/m)","Linear total (ml)"] if c in df_sz.columns]
            st.dataframe(
                df_sz[cols_order],
                use_container_width=True,
                hide_index=True,
                column_config=ml_table_column_config(),
            )
            m1,m2,m3,m4 = st.columns(4)
            m1.metric("Color ink (ml)", f"{color_total:,.2f}")
            m2.metric("White ink (ml)", f"{white_total:,.2f}")
            m3.metric("FOF ink (ml)", f"{fof_total:,.2f}")
            m4.metric("Total ink (ml)", f"{total_ml:,.2f}")
            l1,l2 = st.columns(2)
            l1.metric("Linear (ml/m) — total", f"{total_linear_per_m:,.2f}")
            l2.metric("Linear total (ml)", f"{total_linear_ml:,.2f}")
            # Export CSV
            try:
                csv_data = pd.DataFrame(rows_sz).to_csv(index=False).encode('utf-8')
                st.download_button("Download size table (CSV)", data=csv_data, file_name=f"{_slug(label.lower())}_size_table.csv", mime="text/csv", key=f"{prefix}_size_csv")
            except Exception:
                pass

    # =========================
    # Uploaders — always two ZIPs (A and B)
    # =========================
    zA = zB = None
    upA_col, upB_col = st.columns(2)
    with upA_col:
        upA = st.file_uploader("Job A (ZIP)", type="zip", key="cmp_up_zipA")
        if upA is not None:
            st.session_state["cmpA_zip_bytes"] = upA.getvalue()
            try:
                st.session_state["cmpA_zip_name"] = upA.name
            except Exception:
                pass
    with upB_col:
        upB = st.file_uploader("Job B (ZIP)", type="zip", key="cmp_up_zipB")
        if upB is not None:
            st.session_state["cmpB_zip_bytes"] = upB.getvalue()
            try:
                st.session_state["cmpB_zip_name"] = upB.name
            except Exception:
                pass

    zA = st.session_state.get("cmpA_zip_bytes")
    zB = st.session_state.get("cmpB_zip_bytes")

    if not zA or not zB:
        if not zA and not zB:
            st.info("Upload both ZIPs (A and B) to continue.")
        elif not zA:
            st.info("Upload Job A ZIP to continue.")
        else:
            st.info("Upload Job B ZIP to continue.")
        return

    # === Shared channel selector (controls A & B) ===
    st.markdown("**Channel preview — shared for A & B**")

    # Use shared preview size (no per-job sliders here)
    prev_w = int(st.session_state.get("cmp_prev_w", 560))
    prev_h = int(st.session_state.get("cmp_prev_h", 460))

    # Build availability from both ZIPs
    filesA, xmlsA, jpgsA, tifsA, _ = read_zip_listing(zA)
    filesB, xmlsB, jpgsB, tifsB, _ = read_zip_listing(zB)

    chan_map_A = {}
    for p in tifsA:
        ch = get_channel_from_filename(p.split("/")[-1])
        if ch: chan_map_A[ch] = p
    chan_map_B = {}
    for p in tifsB:
        ch = get_channel_from_filename(p.split("/")[-1])
        if ch: chan_map_B[ch] = p

    has_prev_A = len([p for p in jpgsA if re.search(r"preview", p, re.I)]) > 0
    has_prev_B = len([p for p in jpgsB if re.search(r"preview", p, re.I)]) > 0

    ordered_all = ["Preview","Cyan","Magenta","Yellow","Black","Red","Green","FOF","White"]
    union_available = []
    for c in ordered_all:
        if c == "Preview":
            if has_prev_A or has_prev_B:
                union_available.append("Preview")
        else:
            if (c in chan_map_A) or (c in chan_map_B):
                union_available.append(c)

    if "cmp_chan_sel" not in st.session_state or st.session_state["cmp_chan_sel"] not in union_available:
        st.session_state["cmp_chan_sel"] = union_available[0] if union_available else "Preview"

    # Render a single row of channel chips controlling both sides
    if union_available:
            btn_cols = st.columns(len(union_available))
            for i, ch in enumerate(union_available):
                with btn_cols[i]:
                    chip_button(ch, CHANNEL_COLORS.get(ch, "#666666"),
                                st.session_state.get("cmp_chan_sel") == ch,
                                qp_key="chan", state_key="cmp_chan_sel")
            st.caption(f"Selected: **{st.session_state.get('cmp_chan_sel')}**")
            # <<< fora do loop / with >>>
            display_map = {c: c for c in union_available}
            style_channel_buttons_by_aria(display_map, selected_display=st.session_state.get("cmp_chan_sel"))
        

    # =========================
    # Form builder + PREVIEW (cada lado)
    # =========================

    # Toggles for per-job charts (apply to both A and B)
    if "cmp_job_show_ml" not in st.session_state:
        st.session_state["cmp_job_show_ml"] = True
    if "cmp_job_show_px" not in st.session_state:
        st.session_state["cmp_job_show_px"] = True
    tj1, tj2, tj3 = st.columns(3)
    tj1.checkbox("Show per-job ml/m² charts", key="cmp_job_show_ml")
    tj2.checkbox("Show per-job pixels charts (K)", key="cmp_job_show_px")
    tj3.checkbox("Show per-job values on bars", value=st.session_state.get("cmp_job_show_vals", False), key="cmp_job_show_vals")

    # Render dos dois blocos (A e B)
    colA, colB = st.columns(2)
    with colA: job_preview("cmpA", "Job A", zA, show_ml=st.session_state.get("cmp_job_show_ml", True), show_px=st.session_state.get("cmp_job_show_px", True))
    with colB: job_preview("cmpB", "Job B", zB, show_ml=st.session_state.get("cmp_job_show_ml", True), show_px=st.session_state.get("cmp_job_show_px", True))

    # --- A×B combined per-channel chart (right below the per-job charts) ---
    mlA_map = dict(st.session_state.get("cmpA_legend_ml_map", {}) or {})
    mlB_map = dict(st.session_state.get("cmpB_legend_ml_map", {}) or {})
    if mlA_map or mlB_map:
        st.markdown("**A×B — Per-channel consumption (ml/m²)**")

        # ---- Controls: ordering + insights toggle (shared state) ----
        if "cmp_sort_choice" not in st.session_state:
            st.session_state["cmp_sort_choice"] = "By Δ (B−A)"
        if "cmp_show_insights" not in st.session_state:
            st.session_state["cmp_show_insights"] = True

        ctrl1, ctrl2 = st.columns([1.6, 1.0])
        sort_choice = ctrl1.radio(
            "Order channels",
            ["Original", "By Δ (B−A)", "Alphabetical"],
            horizontal=True,
            key="cmp_sort_choice",
            help="Choose how to order the channels in the A×B chart.",
        )
        ctrl2.checkbox(
            "Show insights",
            key="cmp_show_insights",
        )

        # ---- Base order (CMYKRG + FOF + White), fall back to union/alphabetical ----
        ordered = ["Cyan","Magenta","Yellow","Black","Red","Green","FOF","White"]
        ch_order = [c for c in ordered if (c in mlA_map) or (c in mlB_map)]
        if not ch_order:
            ch_order = sorted(set(list(mlA_map.keys()) + list(mlB_map.keys())))

        # Optional re-ordering per user's choice
        if sort_choice == "Alphabetical":
            ch_order = sorted(ch_order)
        elif sort_choice == "By Δ (B−A)":
            deltas = {c: float(mlB_map.get(c, 0.0)) - float(mlA_map.get(c, 0.0)) for c in ch_order}
            ch_order = sorted(ch_order, key=lambda c: deltas[c], reverse=True)

        # Series aligned to final order
        yA_ord = [float(mlA_map.get(c, 0.0)) for c in ch_order]
        yB_ord = [float(mlB_map.get(c, 0.0)) for c in ch_order]
        # Optional normalization by channel (%)
        if st.checkbox("Normalize by channel (%)", value=st.session_state.get("cmp_norm_by_channel", False), key="cmp_norm_by_channel"):
            sums = [a+b for a,b in zip(yA_ord, yB_ord)]
            yA_ord = [ (0.0 if s==0 else a/s*100.0) for a,s in zip(yA_ord, sums) ]
            yB_ord = [ (0.0 if s==0 else b/s*100.0) for b,s in zip(yB_ord, sums) ]
            y_label = "% of channel"
        else:
            y_label = "ml/m²"
        show_vals = st.checkbox("Show values on bars", value=st.session_state.get("cmp_show_values", False), key="cmp_show_values")
        bar_colors = [CHANNEL_COLORS.get(c, "#888") for c in ch_order]
        h_cmp = int(st.session_state.get("cmp_prev_h", 460))

        fig_cmp = go.Figure()
        nameA = st.session_state.get("cmpA_zip_name", "Job A")
        nameB = st.session_state.get("cmpB_zip_name", "Job B")
        # Job A — sólido
        textA = [ (f"{v:.1f}%" if y_label.startswith('%') else f"{v:.2f}") for v in yA_ord ] if show_vals else None
        fig_cmp.add_trace(
            go.Bar(
                name=nameA,
                x=ch_order,
                y=yA_ord,
                marker=dict(color=bar_colors),
                text=textA,
                textposition=("outside" if show_vals else None),
                cliponaxis=False,
            )
        )
        # Job B — com ranhuras (pattern)
        textB = [ (f"{v:.1f}%" if y_label.startswith('%') else f"{v:.2f}") for v in yB_ord ] if show_vals else None
        fig_cmp.add_trace(
            go.Bar(
                name=nameB,
                x=ch_order,
                y=yB_ord,
                marker=dict(
                    color=bar_colors,
                    pattern=dict(shape="/")  # <<< hachuras para diferenciar
                ),
                marker_line=dict(color="rgba(17,24,39,.8)", width=1.0),
                text=textB,
                textposition=("outside" if show_vals else None),
                cliponaxis=False,
            )
        )
        fig_cmp.update_layout(
            template="plotly_white",
            barmode="group",
            height=h_cmp,
            margin=dict(l=10, r=10, t=30, b=10),
            yaxis_title=y_label,
            xaxis_title="Channel",
            legend_title=None,
        )
        # Toggle for combined ml/m² chart
        if "cmp_combined_show_ml" not in st.session_state:
            st.session_state["cmp_combined_show_ml"] = True
        if st.session_state.get("cmp_combined_show_ml", True):
            st.plotly_chart(fig_cmp, use_container_width=True, key="cmp_combined_ml_chart", config=plotly_cfg())

        # Heatmap option for compact comparison
        if st.checkbox("Show per-channel heatmap", value=st.session_state.get("cmp_show_heatmap", False), key="cmp_show_heatmap"):
            import numpy as np
            z = np.array([yA_ord, yB_ord])
            fig_h = go.Figure(data=go.Heatmap(z=z, x=ch_order, y=[nameA, nameB], colorscale='Blues', colorbar=dict(title=y_label)))
            fig_h.update_layout(template='plotly_white', height=h_cmp, margin=dict(l=10,r=10,t=30,b=10), xaxis_title='Channel', yaxis_title='File')
            st.plotly_chart(fig_h, use_container_width=True, key="cmp_heatmap_chart", config=plotly_cfg())

        # Key insights (below the chart) — optional via toggle
        if st.session_state.get("cmp_show_insights", True):
            tips = insights_for_compare_maps(mlA_map, mlB_map)
            if tips:
                st.markdown("**Key insights**")
                for t in tips:
                    st.markdown("- " + t)

        # Optional PDF export of this comparison (respects the current ordering)
        # PDF layout controls
        if "cmp_pdf_show_comp" not in st.session_state:
            st.session_state["cmp_pdf_show_comp"] = True
        if "cmp_pdf_show_totals" not in st.session_state:
            st.session_state["cmp_pdf_show_totals"] = True
        cpdf1, cpdf2, cpdf3 = st.columns([1.2, 1.0, 1.2])
        size_opt = cpdf1.selectbox(
            "PDF preview size",
            ["Small", "Medium", "Large"],
            index={"Small":0,"Medium":1,"Large":2}.get(st.session_state.get("cmp_pdf_size","Medium"),1),
            key="cmp_pdf_size",
            help="Defines thumbnail size and chart/table layout."
        )
        show_comp = cpdf2.checkbox("Show 100% composition", key="cmp_pdf_show_comp")
        show_totals = cpdf3.checkbox("Totals below previews", key="cmp_pdf_show_totals")

        try:
            nameA = st.session_state.get("cmpA_zip_name", "Job A")
            nameB = st.session_state.get("cmpB_zip_name", "Job B")
            with st.spinner("Building A×B PDF…"):
                pdf_bytes = build_comparison_pdf_matplotlib(
                    ch_order, yA_ord, yB_ord, mlA_map, mlB_map,
                    labelA=nameA, labelB=nameB,
                    zA_bytes=zA, zB_bytes=zB,
                    selected_channel=st.session_state.get("cmp_chan_sel", "Preview"),
                    show_comp=show_comp,
                    preview_size={"Small":"S","Medium":"M","Large":"L"}[size_opt],
                    show_totals=show_totals,
                )
            st.download_button("A×B PDF", data=pdf_bytes, file_name="compare_AxB.pdf", mime="application/pdf")
        except Exception as e:
            st.info(f"PDF not available: {e}")

        # === Inputs A e B — agora realmente logo abaixo do botão A×B PDF ===
        st.markdown("---")
        inpA, inpB = st.columns(2)
        with inpA:
            st.markdown('<div class="ink-callout"><b>Job A — Inputs (Apply)</b> — Fill and click <b>Apply</b> to save A.</div>', unsafe_allow_html=True)
            with st.expander("Job A — Inputs (Apply)", expanded=False):
                compare_job_inputs("cmpA", "Job A", zA)
        with inpB:
            st.markdown('<div class="ink-callout"><b>Job B — Inputs (Apply)</b> — Fill and click <b>Apply</b> to save B.</div>', unsafe_allow_html=True)
            with st.expander("Job B — Inputs (Apply)", expanded=False):
                compare_job_inputs("cmpB", "Job B", zB)

    # =========================
    # Custos compartilhados e moeda (abaixo dos previews, como no Single)
    # =========================
    section("Shared costs & currency", "Applies to both jobs.")
    cc1, cc2, cc3, cc4 = st.columns(4)
    cc1.number_input(
        "Color ink ($/L)",
        min_value=0.0,
        value=float(st.session_state.get("cmp_ink_c", DEFAULTS["ink_color_per_l"])),
        step=1.0,
        key="cmp_ink_c",
    )
    cc2.number_input(
        "White ink ($/L)",
        min_value=0.0,
        value=float(st.session_state.get("cmp_ink_w", DEFAULTS["ink_white_per_l"])),
        step=1.0,
        key="cmp_ink_w",
    )
    cc3.number_input(
        "FOF / Pretreat ($/L)",
        min_value=0.0,
        value=float(st.session_state.get("cmp_fof", DEFAULTS["fof_per_l"])),
        step=1.0,
        key="cmp_fof",
    )
    cc4.number_input(
        f"Substrate ({per_unit(UNIT)})",
        min_value=0.0,
        value=float(st.session_state.get("cmp_fabric", DEFAULTS["fabric_per_unit"])),
        step=0.10,
        key="cmp_fabric",
    )

    cur1, cur2, cur3 = st.columns(3)
    local_symbol  = cur1.text_input("Local currency symbol", value=st.session_state.get("single_local_sym", DEFAULTS["local_symbol"]), key="single_local_sym")
    usd_to_local  = cur2.number_input("USD → Local (FX)", min_value=0.0, value=float(st.session_state.get("single_fx", DEFAULTS["usd_to_local"])), step=0.01, key="single_fx")
    currency_out  = cur3.radio("Output currency", ["USD", "Local"], index=1 if st.session_state.get("cmp_curr_out", "Local")=="Local" else 0, horizontal=True, key="cmp_curr_out")
    FX, SYM       = (1.0, "US$") if currency_out=="USD" else (usd_to_local, local_symbol)

    def run_compare_job(prefix: str, label: str, uploaded_zip_bytes: bytes, sym: str, fx: float):
        """
        Executa a simulação para A ou B, lendo st.session_state pelos keys com prefixo
        (ex.: 'cmpA_*' ou 'cmpB_*'). Salva os painéis formatados em st.session_state[f"{prefix}_panels"].
            """
        UNIT = get_unit()
        unit_lbl = unit_label_short(UNIT)

        # Keys (prefixados)
        k_xml     = f"{prefix}_xml_sel"
        k_mode    = f"{prefix}_mode_sel"
        k_width   = f"{prefix}_width_m"
        k_length  = f"{prefix}_length_m"
        k_waste   = f"{prefix}_waste"
        k_cons    = f"{prefix}_cons_source"
        k_man_c   = f"{prefix}_man_c"
        k_man_w   = f"{prefix}_man_w"
        k_man_f   = f"{prefix}_man_f"
        k_fixed   = f"{prefix}_fixed_unit"
        k_price   = f"{prefix}_price"
        k_margin  = f"{prefix}_margin"
        k_tax     = f"{prefix}_tax"
        k_terms   = f"{prefix}_terms"
        k_round   = f"{prefix}_round"

        # Compartilhados do Compare
        ink_c = float(st.session_state.get("cmp_ink_c",  DEFAULTS["ink_color_per_l"]))
        ink_w = float(st.session_state.get("cmp_ink_w",  DEFAULTS["ink_white_per_l"]))
        fof   = float(st.session_state.get("cmp_fof",    DEFAULTS["fof_per_l"]))
        media = float(st.session_state.get("cmp_fabric", DEFAULTS["fabric_per_unit"]))

        # Tabela de outros variáveis (por job) + mão de obra variável/h
        other_vars_df = ensure_df(st.session_state.get(f"{prefix}_other_vars", [{"Name":"—","Value":0.0}]), ["Name","Value"])

        # XML do ZIP
        xml_inner_path = st.session_state.get(k_xml)
        if not xml_inner_path:
            _, xmls, *_ = read_zip_listing(uploaded_zip_bytes, cache_ns=prefix)
            xml_inner_path = xmls[0] if xmls else None
        if not xml_inner_path:
            st.session_state[f"{prefix}_panels"] = {"error": "No XML in ZIP."}
            return
        xml_bytes = read_bytes_from_zip(uploaded_zip_bytes, xml_inner_path, cache_ns=prefix)

        # Fatores (reaproveita os do Single)
        factors = {
            "fast":      {"color": st.session_state.get("single_mul_fc", 100.0)/100.0, "white": 1.00, "fof": st.session_state.get("single_mul_ff", 100.0)/100.0},
            "standard":  {"color": st.session_state.get("single_mul_sc", 100.0)/100.0, "white": (st.session_state.get("single_mul_sw", 100.0)/100.0), "fof": st.session_state.get("single_mul_sf", 100.0)/100.0},
            "saturation":{"color": st.session_state.get("single_mul_tc", 100.0)/100.0, "white": (st.session_state.get("single_mul_tw", 100.0)/100.0), "fof": st.session_state.get("single_mul_tf", 100.0)/100.0},
        }

        # Mapa de consumo
        mlmap_use = apply_consumption_source(
            xml_bytes,
            st.session_state.get(k_cons, "XML (exact)"),
            st.session_state.get(k_mode),
            factors,
            st.session_state.get(k_man_c, 0.0),
            st.session_state.get(k_man_w, 0.0),
            st.session_state.get(k_man_f, 0.0),
        )

        # >>> Fallback: se a fonte selecionada for XML e o mapa tiver só White/FOF,
        # usa o primeiro XML do ZIP que contenha canais de cor (e aplica multiplicadores se for o modo “XML + mode …”)
        if str(st.session_state.get(k_cons, "XML (exact)")).startswith("XML") and not has_color_channels(mlmap_use):
            fb = pick_first_with_colors(uploaded_zip_bytes, cache_ns=prefix)
            if fb:
                if str(st.session_state.get(k_cons)).startswith("XML + mode"):
                    group_key = MODE_GROUP.get(st.session_state.get(k_mode), "").lower()
                    mlmap_use = apply_mode_factors(fb, group_key, factors)
                else:
                    mlmap_use = fb
        # <<< fim do fallback

        width_m  = float(st.session_state.get(k_width,  1.0))
        length_m = float(st.session_state.get(k_length, 1.0))
        waste    = float(st.session_state.get(k_waste,  0.0))
        # Resolve speed from a robust mode key
        _mode_key = st.session_state.get(k_mode)
        if _mode_key not in PRINT_MODES:
            _mode_key = infer_mode_from_xml(xml_bytes) if infer_mode_from_xml(xml_bytes) in PRINT_MODES else (list(PRINT_MODES.keys())[0] if PRINT_MODES else None)
        speed    = PRINT_MODES.get(_mode_key, {}).get("speed", 0.0)

        # Mão de obra variável -> por unidade
        labor_h = float(st.session_state.get(f"{prefix}_lab_h", 0.0))
        if UNIT == "m2":
            labor_var_per_unit = labor_h / max(1e-9, speed)
        else:
            m_per_h = speed / max(1e-9, width_m)
            labor_var_per_unit = labor_h / max(1e-9, m_per_h)

        other_vars_sum = float(other_vars_df["Value"].fillna(0).sum()) + labor_var_per_unit

        # --- Fixed allocation per job: resolve direct vs monthly helper ---
        fix_mode_val = (st.session_state.get(f"{prefix}_fix_mode") or "Direct per unit")
        if str(fix_mode_val).lower().startswith("monthly"):
            fix_labor_m   = float(st.session_state.get(f"{prefix}_fix_labor_month", 0.0))
            fix_leasing_m = float(st.session_state.get(f"{prefix}_fix_leasing_month", 0.0))
            fix_depr_m    = float(st.session_state.get(f"{prefix}_fix_depr_month", 0.0))
            fix_over_m    = float(st.session_state.get(f"{prefix}_fix_over_month", 0.0))
            fix_others_df = ensure_df(st.session_state.get(f"{prefix}_fix_others", [{"Name":"—","Value":0.0}]), ["Name","Value"])
            fix_others_m  = float(fix_others_df["Value"].fillna(0).sum())
            prod_month_u  = float(st.session_state.get(f"{prefix}_fix_prod_month_units", DEFAULTS.get("prod_month_units", 30000.0)))
            fixed_per_unit_used = (fix_labor_m + fix_leasing_m + fix_depr_m + fix_over_m + fix_others_m) / prod_month_u if prod_month_u > 0 else 0.0
        else:
            fixed_per_unit_used = float(st.session_state.get(k_fixed, 0.0))

        res = simulate(
            UNIT,
            width_m, length_m, waste,
            speed,
            mlmap_use,
            ink_c, ink_w, fof,
            media,
            other_vars_sum,
            0.0,
            fixed_per_unit_used,
            show_time_metrics=False,
        )

        qty = max(1e-9, float(res.get("qty_units", 0.0)))
        ink_total   = float(res.get("cost_ink", 0.0))
        fabric_cost = fabric_total(res)
        other_var   = float(res.get("cost_other", 0.0))
        fixed_cost  = float(res.get("cost_fixed", 0.0))
        total_cost  = float(res.get("total_cost", 0.0))
        variable_total = ink_total + fabric_cost + other_var
        variable_per_unit = variable_total / qty
        fixed_per_unit_card = fixed_cost / qty if qty > 0 else 0.0
        cost_unit_calc = total_cost / qty

        # Precificação
        margin = float(st.session_state.get(k_margin, 20.0))
        tax    = float(st.session_state.get(k_tax,    10.0))
        terms  = float(st.session_state.get(k_terms,   2.1))
        rnd    = float(st.session_state.get(k_round,  0.05))

        price_input = float(st.session_state.get(k_price, 0.0))
        suggested   = price_round(cost_unit_calc*(1 + margin/100 + tax/100), rnd)
        suggested   = price_round(suggested*(1 + terms/100), rnd)
        effective_price = price_input if price_input>0 else suggested

        rows_tot, rows_unit = build_cost_rows_from_sim(res, unit_lbl, sym, fx, price=effective_price)

        st.session_state[f"{prefix}_panels"] = {
            "rows_tot": rows_tot,
            "rows_unit": rows_unit,
            "unit_lbl": unit_lbl,
            "kpis": {
                "qty": qty,
                "area_waste_m2": res.get("area_waste_m2", 0.0),
                "total_ml_per_unit": res.get("total_ml_per_unit", 0.0),
                "time_print_h": res.get("time_print_h", 0.0),
                "time_total_h": res.get("time_total_h", 0.0),
            },
            "be": {
                "variable_per_unit": variable_per_unit,
                "effective_price": effective_price,
                "fixed_per_unit": fixed_per_unit_card,
            },
            "raw": res,
            "ml_map": dict(mlmap_use or {}),
            "label": label,
        }
    st.markdown("---")
    if st.button("Calculate A and B", type="primary", key="cmp_btn_calc_both"):
        run_compare_job("cmpA", "Job A", zA, SYM, FX)
        run_compare_job("cmpB", "Job B", zB, SYM, FX)
        st.success("A and B calculated.")


    # Render dos painéis salvos
    A = st.session_state.get("cmpA_panels")
    B = st.session_state.get("cmpB_panels")
    if A or B:
        with st_div("cmp-compact"):
            leftP, rightP = st.columns(2)

            if A:
                with leftP:
                    st.markdown("### A — Results")
                    # dois blocos lado a lado: (1) cards de custos (2) métricas
                    cards_col, kpi_col = st.columns([1.5, 1.0])
            with cards_col:
                render_info_table("Total ($)", A["rows_tot"])
                render_info_table(f"Per unit (/{A.get('unit_lbl', unit_lbl)})", A["rows_unit"])
            with kpi_col:
                unitA = A.get("unit_lbl", unit_lbl)
                kA = A.get("kpis", {})
                st.metric(f"Qty ({unitA})", f"{float(kA.get('qty', 0.0)):.2f}")
                st.metric(f"Total ml{per_unit(get_unit())}", f"{float(kA.get('total_ml_per_unit', 0.0)):.2f}")
                st.metric("Print time (h)", f"{float(kA.get('time_print_h', (A.get('raw') or {}).get('time_print_h', 0.0))):.2f}")
                st.metric("Total time (h)", f"{float(kA.get('time_total_h', (A.get('raw') or {}).get('time_total_h', 0.0))):.2f}")

            if B:
                with rightP:
                    st.markdown("### B — Results")
                    cards_col, kpi_col = st.columns([1.5, 1.0])
            with cards_col:
                render_info_table("Total ($)", B["rows_tot"])
                render_info_table(f"Per unit (/{B.get('unit_lbl', unit_lbl)})", B["rows_unit"])
            with kpi_col:
                unitB = B.get("unit_lbl", unit_lbl)
                kB = B.get("kpis", {})
                st.metric(f"Qty ({unitB})", f"{float(kB.get('qty', 0.0)):.2f}")
                st.metric(f"Total ml{per_unit(get_unit())}", f"{float(kB.get('total_ml_per_unit', 0.0)):.2f}")
                st.metric("Print time (h)", f"{float(kB.get('time_print_h', (B.get('raw') or {}).get('time_print_h', 0.0))):.2f}")
                st.metric("Total time (h)", f"{float(kB.get('time_total_h', (B.get('raw') or {}).get('time_total_h', 0.0))):.2f}")

    # ================
    # Break-even (opcional)
    # ================
    try:
        UNIT = get_unit()
        unit_lbl = unit_label_short(UNIT)
        section("Break-even (A & B)", "Estimate monthly volume needed to cover fixed costs. Use price, variable cost and monthly fixed cost.")
        be_cols = st.columns(2)
        for pref, lab, panel, col in [
            ("cmpA", "Job A", A, be_cols[0]),
            ("cmpB", "Job B", B, be_cols[1]),
        ]:
            with col:
                st.markdown(f"**{lab}**")
                if panel and panel.get("be"):
                    var_u = float(panel["be"].get("variable_per_unit", 0.0))
                    price_u = float(panel["be"].get("effective_price", 0.0))
                    # Monthly fixed source
                    fixed_month = 0.0
                    if str(st.session_state.get(f"{pref}_fix_mode", "")).lower().startswith("monthly"):
                        # Sum of the monthly fixed inputs from the helper
                        sum_others = 0.0
                        if st.session_state.get(f"{pref}_fix_others"):
                            sum_others = ensure_df(st.session_state.get(f"{pref}_fix_others", []), ["Name","Value"])["Value"].fillna(0).sum()
                        fixed_month = (
                            float(st.session_state.get(f"{pref}_fix_labor_month", 0.0))
                            + float(st.session_state.get(f"{pref}_fix_leasing_month", 0.0))
                            + float(st.session_state.get(f"{pref}_fix_depr_month", 0.0))
                            + float(st.session_state.get(f"{pref}_fix_over_month", 0.0))
                            + float(sum_others)
                        )
                        st.caption(f"Monthly fixed (from helper): **{pretty_money(fixed_month, SYM, FX)}**")
                    else:
                        fixed_month = st.number_input(
                            "Monthly fixed (enter)",
                            min_value=0.0,
                            value=float(st.session_state.get(f"{pref}_be_fixed_month", 0.0)),
                            step=50.0,
                            key=f"{pref}_be_fixed_month",
                        )
                    fig_be = breakeven_figure(
                        price_u=price_u,
                        variable_u=var_u,
                        fixed_month=fixed_month,
                        unit_lbl=unit_lbl,
                        sym=SYM,
                        fx=FX,
                        title=f"Break-even — {lab}",
                    )
                    st.plotly_chart(fig_be, use_container_width=True, key=f"{pref}_be_chart", config=plotly_cfg())
                    try:
                        render_break_even_insights(price_u, var_u, fixed_month, unit_lbl, SYM, FX, label=lab)
                    except Exception:
                        pass
                else:
                    st.info("Click **Calculate A and B** to generate the break-even inputs.")
    except Exception as _e:
        st.info(f"Break-even unavailable: {_e}")

# =========================
# Helpers compartilhados
# =========================

# --- Column help for ml/m² tables ---
def ml_table_column_config():
    """Shared column tooltips for Channel/ml-based tables.
    Use in st.dataframe(..., column_config=ml_table_column_config())."""
    try:
        return {
            "Channel": st.column_config.TextColumn(
                "Channel",
                help="Color/ink channel (includes FOF).",
            ),
            "ml/m²": st.column_config.NumberColumn(
                "ml/m²",
                help=(
                    "Expected density for the channel: file coverage × base channel factor (ml/m² at 100%)"
                    " × mode multipliers (Color/White/FOF) × any user adjustments."
                ),
                format="%.3f",
            ),
            "Area (m²)": st.column_config.NumberColumn(
                "Area (m²)",
                help="Effective job area after waste (%).",
                format="%.3f",
            ),
            "Ink (ml)": st.column_config.NumberColumn(
                "Ink (ml)",
                help="Job ink for the channel: Ink (ml) = (ml/m²) × area (m²).",
                format="%.2f",
            ),
            "Linear (ml/m)": st.column_config.NumberColumn(
                "Linear (ml/m)",
                help="Linear consumption: Linear (ml/m) = (ml/m²) × width (m).",
                format="%.2f",
            ),
            "Linear total (ml)": st.column_config.NumberColumn(
                "Linear total (ml)",
                help=(
                    "Total linear consumption: Linear total = (Linear ml/m) × length (m)."
                    " Mathematically equals Ink (ml); just a different view."
                ),
                format="%.2f",
            ),
            # Batch summary uses these as well
            "Total (ml/m²)": st.column_config.NumberColumn(
                "Total (ml/m²)",
                help="Sum of ml/m² across channels for the selected file.",
                format="%.3f",
            ),
        }
    except Exception:
        # Fallback if column_config API is unavailable
        return {}

# --- Insights helper for A×B per-channel comparison ---
from typing import List

def insights_for_compare_maps(mlA: dict, mlB: dict) -> List[str]:
    """Return short, high-signal insights comparing per-channel ml/m² between A and B."""
    tips: List[str] = []
    try:
        ch_all = sorted(set(list((mlA or {}).keys()) + list((mlB or {}).keys())))
        if not ch_all:
            return tips
        totA = float(sum(float(mlA.get(c, 0.0)) for c in ch_all))
        totB = float(sum(float(mlB.get(c, 0.0)) for c in ch_all))
        if totA > 0 or totB > 0:
            if totA > 0:
                delta = totB - totA
                delta_pct = 0.0 if totA == 0 else (delta / totA * 100.0)
                tips.append(f"Total density: A = {totA:.2f} ml/m² vs B = {totB:.2f} ml/m² ({delta:+.2f}, {delta_pct:+.1f}%).")
            else:
                tips.append(f"Total density: A = {totA:.2f} ml/m² vs B = {totB:.2f} ml/m².")
        diffs = []
        for c in ch_all:
            a = float(mlA.get(c, 0.0))
            b = float(mlB.get(c, 0.0))
            pct = 0.0 if a == 0 else (b - a) / a * 100.0
            diffs.append((c, b - a, pct))
        if diffs:
            inc = max(diffs, key=lambda t: t[1])
            dec = min(diffs, key=lambda t: t[1])
            if inc[1] > 0:
                tips.append(f"Largest increase: {inc[0]} (+{inc[1]:.2f} ml/m², {inc[2]:+.1f}%).")
            if dec[1] < 0:
                tips.append(f"Largest decrease: {dec[0]} ({dec[1]:+.2f} ml/m², {dec[2]:+.1f}%).")
        def top_share(mm: dict):
            if not mm:
                return None
            tot = float(sum(mm.values()))
            if tot <= 0:
                return None
            top_c, top_v = max(mm.items(), key=lambda kv: float(kv[1]))
            return top_c, (float(top_v) / tot * 100.0)
        la = top_share(mlA)
        lb = top_share(mlB)
        if la and lb:
            if la[0] == lb[0]:
                tips.append(f"Top channel unchanged: {la[0]} (~{la[1]:.0f}% of total).")
            else:
                tips.append(f"Top channel shifts: A→{la[0]} (~{la[1]:.0f}%) vs B→{lb[0]} (~{lb[1]:.0f}%).")
        for special in ["White", "FOF"]:
            a = float(mlA.get(special, 0.0))
            b = float(mlB.get(special, 0.0))
            if (a == 0 and b > 0) or (a > 0 and b == 0) or abs(b - a) > 0.10:
                tips.append(f"{special}: A {a:.2f} → B {b:.2f} ml/m² ({(b - a):+.2f}).")
    except Exception:
        pass
    return tips
def render_axb_per_channel_chart(height=None):
    """Desenha o gráfico A×B (ml/m²) usando os ml_map salvos nos states cmpA_legend_ml_map / cmpB_legend_ml_map."""
    mlA_map = dict(st.session_state.get("cmpA_legend_ml_map", {}) or {})
    mlB_map = dict(st.session_state.get("cmpB_legend_ml_map", {}) or {})
    if not (mlA_map or mlB_map):
        return

    st.markdown("**A×B — Per-channel consumption (ml/m²)**")

    # estados/controles (mesmos nomes do bloco original)
    if "cmp_sort_choice" not in st.session_state:
        st.session_state["cmp_sort_choice"] = "By Δ (B−A)"
    if "cmp_show_insights" not in st.session_state:
        st.session_state["cmp_show_insights"] = True

    ctrl1, ctrl2 = st.columns([1.6, 1.0])
    sort_choice = ctrl1.radio(
        "Order channels",
        ["Original", "By Δ (B−A)", "Alphabetical"],
        horizontal=True,
        key="cmp_sort_choice",
        help="Choose how to order the channels in the A×B chart.",
    )
    ctrl2.checkbox("Show insights", key="cmp_show_insights")

    # ordem base e reordenação opcional
    ordered = ["Cyan","Magenta","Yellow","Black","Red","Green","FOF","White"]
    ch_order = [c for c in ordered if (c in mlA_map) or (c in mlB_map)]
    if not ch_order:
        ch_order = sorted(set(list(mlA_map.keys()) + list(mlB_map.keys())))

    if sort_choice == "Alphabetical":
        ch_order = sorted(ch_order)
    elif sort_choice == "By Δ (B−A)":
        deltas = {c: float(mlB_map.get(c, 0.0)) - float(mlA_map.get(c, 0.0)) for c in ch_order}
        ch_order = sorted(ch_order, key=lambda c: deltas[c], reverse=True)

    yA = [float(mlA_map.get(c, 0.0)) for c in ch_order]
    yB = [float(mlB_map.get(c, 0.0)) for c in ch_order]
    colors = [CHANNEL_COLORS.get(c, "#888") for c in ch_order]
    h = int(height or st.session_state.get("cmp_prev_h", 460))

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Job A", x=ch_order, y=yA, marker=dict(color=colors)))
    fig.add_trace(
        go.Bar(
            name="Job B",
            x=ch_order,
            y=yB,
            marker=dict(color=colors, pattern=dict(shape="/")),
            marker_line=dict(color="rgba(17,24,39,.8)", width=1.0),
        )
    )
    fig.update_layout(
        template="plotly_white",
        barmode="group",
        height=h,
        margin=dict(l=10, r=10, t=30, b=10),
        yaxis_title="ml/m²",
        xaxis_title="Channel",
        legend_title=None,
    )
    st.plotly_chart(fig, use_container_width=True, key="cmp_ab_ml_chart", config=plotly_cfg())

    if st.session_state.get("cmp_show_insights", True):
        tips = insights_for_compare_maps(mlA_map, mlB_map)
        if tips:
            st.markdown("**Key insights**")
            for t in tips:
                st.markdown("- " + t)

def total_ml_per_m2_from_map(ml_map: dict) -> float:
    try: return float(sum(float(v) for v in (ml_map or {}).values()))
    except Exception: return 0.0

def choose_path(channel, jpgs, chan_map):
    if channel == "Preview":
        if jpgs:
            cand = [p for p in jpgs if re.search(r"preview", p, re.I)]
            return (cand[0] if cand else jpgs[0]), "jpg"
        return None, None
    if channel in chan_map: return chan_map[channel], "tif"
    return None, None

def _slug(s: str) -> str:
    return re.sub(r'[^A-Za-z0-9]+', '_', s or '').strip('_')

def chip_button(
    label: str,
    color_hex: str,
    selected: bool,
    qp_key: str = "chan",
    state_key: str = "chan_sel",
    display_label: str | None = None,
):
    """
    Renderiza um chip como st.button (100% width) que altera o estado e o query param
    sem abrir nova aba. As cores/estilos são aplicadas globalmente via CSS por aria-label
    (ver helper style_channel_buttons_by_aria).
    """
    show_label = display_label if display_label else label
    slug = _slug(label)
    btn_key = f"btn_{state_key}_{slug}"

    clicked = st.button(show_label, key=btn_key, use_container_width=True)

    if clicked:
        st.session_state[state_key] = label
        try:
            set_qp(qp_key, slug)
        except Exception:
            pass

    # Linha/etiqueta colorida abaixo do botão
    show_name = show_label
    st.markdown(
        f'''
        <div class="chan-swatch">
            <div class="bar" style="background:{color_hex};"></div>
            <div class="label">{show_name}</div>
        </div>
        ''',
        unsafe_allow_html=True
    )

# Helper para sincronizar session_state a partir do query param
def sync_state_from_qp(state_key: str, qp_key: str, options: List[str], default_val: str):
    """
    Se o query param estiver presente, atualiza st.session_state[state_key] para corresponder.
    """
    qp = get_qp(qp_key, _slug(default_val))
    found = next((c for c in options if _slug(c).lower() == (qp or "").lower()), None)
    if found and st.session_state.get(state_key) != found:
        st.session_state[state_key] = found

def get_qp(key: str, default: str = "") -> str:
    try:
        val = st.query_params.get(key, default)
        if isinstance(val, list):
            return val[0] if val else default
        return val
    except Exception:
        q = st.experimental_get_query_params()
        v = q.get(key, [default])
        return v[0] if isinstance(v, list) else v


# Helper para setar query param de forma segura (Streamlit >=1.29 via st.query_params, legado via experimental)
def set_qp(key: str, value: str):
    """Safely set a single query param (Streamlit >=1.29 via st.query_params, older via experimental)."""
    try:
        # New API
        st.query_params[key] = value
    except Exception:
        # Legacy fallback
        try:
            st.experimental_set_query_params(**{key: value})
        except Exception:
            pass

def get_unit() -> str:
    """Modo único de unidade: sempre m²."""
    return "m2"

def apply_consumption_source(xml_bytes, cons_src, mode_key, factors_dict, man_c=0.0, man_w=0.0, man_f=0.0):
    mlmap_xml = ml_per_m2_from_xml_bytes(xml_bytes)
    opt = (cons_src or "").strip().lower()

    if opt in {"xml (exact)", "xml (exato)"}:
        return mlmap_xml
    elif opt.startswith("xml + mode multiplier") or opt.startswith("xml + multiplicador de modo"):
        grp = MODE_GROUP.get(mode_key, "standard")
        return apply_mode_factors(mlmap_xml, grp, factors_dict)
    else:
        out = {}
        if man_c > 0: out["Color"] = man_c
        if man_w > 0: out["White"] = man_w
        if man_f > 0: out["FOF"]   = man_f
        return out

# ========= Quick insights for A×B =========
def insights_for_compare(all_channels: List[str], yA: List[float], yB: List[float]) -> List[str]:
    tips = []
    def safe(v): 
        try: return float(v)
        except: return 0.0
    diffs = {c: safe(b)-safe(a) for c,a,b in zip(all_channels, yA, yB)}
    # Largest increase in B vs A
    if diffs:
        c_up = max(diffs, key=lambda k: diffs[k])
        if diffs[c_up] > 0:
            tips.append(f"Channel **{c_up}**: Job B used **{diffs[c_up]:.2f} ml/m²** more than Job A.")
    # Largest reduction
    if diffs:
        c_down = min(diffs, key=lambda k: diffs[k])
        if diffs[c_down] < 0:
            tips.append(f"Channel **{c_down}**: Job B used **{abs(diffs[c_down]):.2f} ml/m²** less than Job A.")
    # Lowest average consumption channel
    if all_channels:
        medias = {c: (safe(a)+safe(b))/2.0 for c,a,b in zip(all_channels, yA, yB)}
        c_min = min(medias, key=lambda k: medias[k])
        tips.append(f"Lowest average density: **{c_min}** ({medias[c_min]:.2f} ml/m²).")
    return tips

# ====== Cabeçalho simples
def render_header():
    """Compact header with a small image to the left of the title."""
    img = _load_asset_image("header_banner") or _load_asset_image("page_icon")
    # Allow overrides from session state
    app_title = st.session_state.get("app_title", DEFAULT_APP_TITLE)
    app_sub = st.session_state.get("app_subtitle", DEFAULT_APP_SUBTITLE)
    if img is None:
        st.markdown(f"<h1 style='margin:0 0 6px 0;'>{app_title}</h1>", unsafe_allow_html=True)
        st.caption(app_sub)
        return
    left, right = st.columns([1, 18])
    with left:
        st.image(img, width=56, caption=None)
    with right:
        st.markdown(f"<h1 style='margin: 0 0 2px 0;'>{app_title}</h1>", unsafe_allow_html=True)
        st.caption(app_sub)

render_header()

# =========================
# Help glossary (shown where helpful)
# =========================
def render_help_glossary():
    with st.expander("Help — concepts and formulas", expanded=False):
        st.markdown("- ml/m²: ink usage per square meter, from XML.")
        st.markdown("- Pixels (K): fire pixels per channel (thousands) extracted from XML.")
        st.markdown("- Price per unit: selling price per unit (m² or m), before/after rounding.")
        st.markdown("- Target margin (%): markup applied to cost before taxes/fees.")
        st.markdown("- Taxes (%): taxes/withholdings applied to price.")
        st.markdown("- Fees/Terms (%): payment terms, card fees, financing, etc.")
        st.markdown("- Fixed allocation (/unit): fixed cost per unit. Use Monthly helper to compute it.")
        st.markdown("- Monthly helper: enter monthly fixed costs and monthly production; we compute $/unit.")
        st.markdown("- XML (exact): uses XML consumption as-is; print mode is locked to XML-inferred resolution.")
        st.markdown("- XML + mode multiplier: scales XML consumption by per-mode factors (Color/White/FOF).")


# Botão global de reset
cl1, cl2 = st.columns([6, 1])
with cl2:
    if st.button("🧹 Reset", help="Clears all inputs and the app state.", key="btn_reset_all"):
        st.session_state.clear()
        st.rerun()

st.caption("ZIP/XML • Channel preview • XML analysis • A×B comparison • Production/ROI & Break-even • Batch (multiple files)")

# =========================
# Global settings
# =========================
section("Global settings", "Applies to all flows.")
st.session_state["global_unit"] = "m2"
st.caption("Base unit: m²")
st.markdown("---")

# =========================
# Flow selector
# =========================
section("Workflow", "Choose o que deseja fazer.")
flow = st.radio(
    "Choose flow",
    ["Single job", "Compare A×B", "Batch — multiple files", "Sales — Quick quote (manual)"],
    index=0,
    horizontal=True,
    help="Select the desired flow.",
    key="workflow_selector",
)
st.markdown("---")


# ===========================================
# FLUXO: SINGLE JOB
# ===========================================
def ui_single():
    """Single mode mirrored from Compare A×B — same layout and flow, but for one ZIP only."""
    UNIT = get_unit()
    unit_lbl = unit_label_short(UNIT)

    section("Single", "Same layout as Compare A×B — but for a single job.")

    # ---------- Preview size controls (same as Compare) ----------
    st.markdown("---")
    pv1, pv2 = st.columns(2)
    pv1.slider(
        "Preview box width (px)", 320, 900,
        int(st.session_state.get("single_prev_w", 560)), 10,
        key="single_prev_w",
        help="Preview box width (image and charts).",
    )
    pv2.slider(
        "Preview box height (px)", 260, 900,
        int(st.session_state.get("single_prev_h", 460)), 10,
        key="single_prev_h",
    )
    st.checkbox(
        "Fill channel previews (crop to area)",
        value=st.session_state.get("single_fill_preview", False),
        key="single_fill_preview",
        help="When viewing channel separations (TIFF), scale to fill the preview box (center crop).",
    )
    st.checkbox(
        "Fill preview image (JPG)",
        value=st.session_state.get("single_fill_preview_jpg", False),
        key="single_fill_preview_jpg",
        help="Scale JPG preview to fill the box (center crop).",
    )
    st.checkbox(
        "Auto-trim white margins (channels)",
        value=st.session_state.get("single_trim_channels", False),
        key="single_trim_channels",
        help="Remove uniform white margins around TIFF channels before rendering.",
    )
    st.markdown("---")

    # ---------- Uploader ----------
    up = st.file_uploader("Job (ZIP)", type="zip", key="single_up_zip")
    if up is not None:
        st.session_state["single_zip_bytes"] = up.getvalue()
        try:
            st.session_state["single_zip_name"] = up.name
        except Exception:
            pass
    z = st.session_state.get("single_zip_bytes")
    if not z:
        st.info("Upload the Job ZIP to continue.")
        return

    # ---------- Basic listing + counters ----------
    files, xmls, jpgs, tifs, ad = read_zip_listing(z)
    c1, c2, c3 = st.columns(3)
    c1.metric("XML files", len(xmls)); c2.metric("JPG files", len(jpgs)); c3.metric("TIFF files", len(tifs))
    # Silently ignore AppleDouble entries if present

    # ---------- Channel selector (chips), mirrored from Compare ----------
    prev_w = int(st.session_state.get("single_prev_w", 560))
    prev_h = int(st.session_state.get("single_prev_h", 460))

    # Map TIFFs to channels
    chan_map = {}
    for p in tifs:
        ch = get_channel_from_filename(p.split("/")[-1])
        if ch:
            chan_map[ch] = p

    has_prev = any(re.search(r"preview", p, re.I) for p in jpgs)
    ordered_all = ["Preview","Cyan","Magenta","Yellow","Black","Red","Green","FOF","White"]
    available = []
    for c in ordered_all:
        if c == "Preview":
            if has_prev:
                available.append("Preview")
        else:
            if c in chan_map:
                available.append(c)

    if "single_chan_sel" not in st.session_state or st.session_state["single_chan_sel"] not in available:
        st.session_state["single_chan_sel"] = available[0] if available else "Preview"

    if available:
        btn_cols = st.columns(len(available))
        for i, ch in enumerate(available):
            with btn_cols[i]:
                chip_button(ch, CHANNEL_COLORS.get(ch, "#666666"),
                            st.session_state.get("single_chan_sel") == ch,
                            qp_key="chan", state_key="single_chan_sel")
        st.caption(f"Selected: **{st.session_state.get('single_chan_sel')}**")
        display_map = {c: c for c in available}
        style_channel_buttons_by_aria(display_map, selected_display=st.session_state.get("single_chan_sel"))

    # ---------- Small helper: choose XML for legend/graphs ----------
    def select_xml_for_legend(prefix_key: str) -> tuple[str, dict]:
        if not xmls:
            return "", {}
        xml_default = 0
        if st.session_state.get(prefix_key) in xmls:
            xml_default = xmls.index(st.session_state.get(prefix_key))
        xml_for_legend = st.selectbox(
            "XML for legend (ml/m²)", xmls, index=xml_default,
            help="Used to extract per-channel consumption and pixels.",
            key=prefix_key,
        )
        try:
            mlm2 = ml_per_m2_from_xml_bytes(read_bytes_from_zip(z, xml_for_legend, cache_ns="single"))
        except Exception:
            mlm2 = {}
        return xml_for_legend, mlm2

    # ---------- Preview block (image + captions) ----------
    st.markdown("**Channel preview — Job**")
    xml_for_legend, mlm2 = select_xml_for_legend("single_xml_legend")

    leftC, rightC = st.columns([1.15, 1.0])
    with leftC:
        path, _ = choose_path(st.session_state.get("single_chan_sel", "Preview"), jpgs, chan_map)
        if path:
            fill_flag = bool(st.session_state.get("single_fill_preview_jpg", True)) if st.session_state.get("single_chan_sel") == "Preview" else bool(st.session_state.get("single_fill_preview", True))
            trim_flag = bool(st.session_state.get("single_trim_channels", True)) if st.session_state.get("single_chan_sel") != "Preview" else False
            preview_fragment(
                "single_preview",
                z,
                path,
                width=prev_w,
                height=prev_h,
                fill_flag=fill_flag,
                trim_flag=trim_flag,
                max_side=int(prev_w * 1.35),
                caption=path,
            )
            sel = st.session_state.get("single_chan_sel")
            if sel != "Preview" and mlm2:
                v = mlm2.get(sel)
                if v is not None:
                    st.caption(f"**{sel}**: {v:.2f} ml/m²")
            if mlm2:
                st.markdown(f"Total consumption: **{total_ml_per_m2_from_map(mlm2):.2f} ml/m²**")
        else:
            st.info(f"This job does not contain '{st.session_state.get('single_chan_sel')}'.")
    with rightC:
        st.empty()

    # ---------- Charts (exactly like per-job in Compare) ----------
    # Toggles for Single charts
    if "single_show_ml" not in st.session_state:
        st.session_state["single_show_ml"] = True
    if "single_show_px" not in st.session_state:
        st.session_state["single_show_px"] = True
    sct1, sct2 = st.columns(2)
    sct1.checkbox("Show ml/m² chart", key="single_show_ml")
    sct2.checkbox("Show pixels chart (K)", key="single_show_px")
    # Per-channel consumption (ml/m²) — auto render (no Update button)
    if st.session_state.get("single_show_ml", True):
        render_title_with_hint(
            "Per-channel consumption (ml/m²)",
            "ml/m² = file coverage × base channel factor × mode multipliers (Color/White/FOF) × user adjustments."
        )
        if mlm2:
            items = sorted(mlm2.items(), key=lambda kv: kv[1], reverse=True)
            labels = [k for k, _ in items]
            values = [v for _, v in items]
            colors = [CHANNEL_COLORS.get(k, "#888") for k in labels]
            fig_ch = go.Figure()
            fig_ch.add_trace(go.Bar(x=labels, y=values, marker=dict(color=colors), text=[f"{v:.2f}" for v in values], textposition="outside", cliponaxis=False))
            fig_ch.update_layout(template="plotly_white", height=prev_h, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="ml/m²", xaxis_title="Channel")
            st.plotly_chart(fig_ch, use_container_width=True, key="single_ml_chart", config=plotly_cfg())
        else:
            st.info("Select an XML to display the chart.")

    # Fire pixels per channel (K) — auto render
    if st.session_state.get("single_show_px", True):
        render_title_with_hint(
            "Fire pixels per channel (K)",
            "K pixels fired per channel, from NumberOfFirePixelsPerSeparation in the XML."
        )
        try:
            pxm2 = fire_pixels_map_from_xml_bytes(read_bytes_from_zip(z, xml_for_legend, cache_ns="single"))
        except Exception:
            pxm2 = {}
        if pxm2:
            items_px = sorted(pxm2.items(), key=lambda kv: kv[1], reverse=True)
            labels_px = [k for k, _ in items_px]
            values_px = [float(v)/1000.0 for _, v in items_px]
            colors_px = [CHANNEL_COLORS.get(k, "#888") for k in labels_px]
            fig_px = go.Figure()
            fig_px.add_trace(go.Bar(x=labels_px, y=values_px, marker=dict(color=colors_px), text=[f"{v:.1f}" for v in values_px], textposition="outside", cliponaxis=False))
            fig_px.update_layout(template="plotly_white", height=prev_h, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="K pixels", xaxis_title="Channel")
            st.plotly_chart(fig_px, use_container_width=True, key="single_px_chart", config=plotly_cfg())
        else:
            st.info("This XML does not contain 'NumberOfFirePixelsPerSeparation'.")

    # ---------- Size-based ink consumption (use XML size or simulate custom) ----------
    st.markdown("---")
    st.markdown("**Ink consumption by size**")
    # Always compute the size table (auto)
    # Get XML original dimensions
    w0 = h0 = 0.0
    try:
        xml_bytes_sz = read_bytes_from_zip(z, xml_for_legend, cache_ns="single")
        w0, h0, _ = get_xml_dims_m(xml_bytes_sz)
    except Exception:
        pass

    # Unit for input/display
    unit_choice = st.radio("Unit", ["m", "cm"], index=1, horizontal=True, key="single_size_unit")

    src = st.radio(
        "Size source",
        ["XML original", "Custom"],
        index=0 if (w0>0 and h0>0) else 1,
        horizontal=True,
        key="single_size_source",
    )
    c1, c2, c3 = st.columns(3)
    if src == "XML original":
        width_m  = float(w0 or 0.0)
        length_m = float(h0 or 0.0)
        disp_w = width_m if unit_choice=="m" else width_m*100.0
        disp_h = length_m if unit_choice=="m" else length_m*100.0
        c1.metric(f"Width ({unit_choice})", f"{disp_w:.3f}")
        c2.metric(f"Length ({unit_choice})", f"{disp_h:.3f}")
        waste = c3.number_input("Waste (%)", min_value=0.0, value=float(st.session_state.get("single_size_waste", 0.0)), step=0.5, key="single_size_waste")
    else:
        if unit_choice == "m":
            default_w = float(round(w0 or 1.45, 3))
            default_h = float(round(h0 or 1.00, 3))
            in_w = c1.number_input("Width (m)",  min_value=0.0, value=default_w, step=0.01, format="%.3f", key="single_size_w")
            in_h = c2.number_input("Length (m)", min_value=0.0, value=default_h, step=0.01, format="%.3f", key="single_size_h")
            width_m, length_m = float(in_w), float(in_h)
        else:
            default_w = float(round((w0 or 1.45)*100.0, 1)) if (w0 or 0.0) > 0 else 145.0
            default_h = float(round((h0 or 1.00)*100.0, 1)) if (h0 or 0.0) > 0 else 100.0
            in_w = c1.number_input("Width (cm)",  min_value=0.0, value=default_w, step=0.5, format="%.1f", key="single_size_w_cm")
            in_h = c2.number_input("Length (cm)", min_value=0.0, value=default_h, step=0.5, format="%.1f", key="single_size_h_cm")
            width_m, length_m = float(in_w)/100.0, float(in_h)/100.0
        waste    = c3.number_input("Waste (%)",  min_value=0.0, value=float(st.session_state.get("single_size_waste", 0.0)), step=0.5, key="single_size_waste")

    if mlm2:
        area = max(0.0, width_m * length_m) * (1.0 + float(waste or 0.0)/100.0)
        rows_sz = []
        total_ml = 0.0
        total_linear_per_m = 0.0
        total_linear_ml = 0.0
        color_total = 0.0
        white_total = 0.0
        fof_total = 0.0
        for ch_name, ml_per_m2 in sorted(mlm2.items(), key=lambda kv: kv[1], reverse=True):
            ml_per_m2 = float(ml_per_m2)
            ml_total = ml_per_m2 * area
            linear_per_m = ml_per_m2 * float(width_m or 0.0)
            linear_total = linear_per_m * float(length_m or 0.0)
            rows_sz.append({
                "Channel": ch_name,
                "ml/m²": round(ml_per_m2, 3),
                "Area (m²)": round(area, 3),
                "Ink (ml)": round(ml_total, 2),
                "Linear (ml/m)": round(linear_per_m, 2),
                "Linear total (ml)": round(linear_total, 2),
            })
            total_ml += ml_total
            total_linear_per_m += linear_per_m
            total_linear_ml += linear_total
            low = (ch_name or '').lower()
            if low in CHANNELS_WHITE:
                white_total += ml_total
            elif low in CHANNELS_FOF:
                fof_total += ml_total
            else:
                color_total += ml_total
        df_sz = pd.DataFrame(rows_sz)
        st.caption(f"Area (m²): {area:.3f}")
        cols_order = [c for c in ["Channel","ml/m²","Ink (ml)","Linear (ml/m)","Linear total (ml)"] if c in df_sz.columns]
        st.dataframe(
            df_sz[cols_order],
            use_container_width=True,
            hide_index=True,
            column_config=ml_table_column_config(),
        )
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Color ink (ml)", f"{color_total:,.2f}")
        m2.metric("White ink (ml)", f"{white_total:,.2f}")
        m3.metric("FOF ink (ml)", f"{fof_total:,.2f}")
        m4.metric("Total ink (ml)", f"{total_ml:,.2f}")
        l1, l2 = st.columns(2)
        l1.metric("Linear (ml/m) — total", f"{total_linear_per_m:,.2f}")
        l2.metric("Linear total (ml)", f"{total_linear_ml:,.2f}")
        # Export CSV
        try:
            csv_data = pd.DataFrame(rows_sz).to_csv(index=False).encode('utf-8')
            st.download_button("Download size table (CSV)", data=csv_data, file_name="single_size_table.csv", mime="text/csv", key="single_size_csv")
        except Exception:
            pass

    # ---------- PDF controls + export (Single) ----------
    if "cmp_pdf_size" not in st.session_state:
        st.session_state["cmp_pdf_size"] = "Medium"
    if "cmp_pdf_show_comp" not in st.session_state:
        st.session_state["cmp_pdf_show_comp"] = True
    if "cmp_pdf_show_totals" not in st.session_state:
        st.session_state["cmp_pdf_show_totals"] = True

    sp1, sp2, sp3 = st.columns([1.2, 1.0, 1.2])
    size_opt = sp1.selectbox(
        "PDF preview size",
        ["Small", "Medium", "Large"],
        index={"Small":0,"Medium":1,"Large":2}.get(st.session_state.get("cmp_pdf_size","Medium"),1),
        key="cmp_pdf_size",
        help="Defines thumbnail size and chart/table layout.")
    show_comp = sp2.checkbox("Show 100% composition", key="cmp_pdf_show_comp")
    show_totals = sp3.checkbox("Totals below previews", key="cmp_pdf_show_totals")

    try:
        # Use current mlm2 directly to avoid dependency on chart state
        if mlm2:
            items_single = sorted(mlm2.items(), key=lambda kv: kv[1], reverse=True)
            labels_single = [k for k, _ in items_single]
            values_single = [v for _, v in items_single]
        else:
            labels_single, values_single = [], []
        with st.spinner("Building PDF…"):
            pdf_single = build_single_pdf_matplotlib(
                labels_single, values_single, mlm2,
                label=st.session_state.get("single_zip_name", "Job"),
                z_bytes=z,
                selected_channel=st.session_state.get("single_chan_sel", "Preview"),
                show_comp=show_comp,
                preview_size={"Small":"S","Medium":"M","Large":"L"}[size_opt],
                show_totals=show_totals,
            )
        st.download_button("Job PDF", data=pdf_single, file_name="single_job.pdf", mime="application/pdf")
    except Exception as e:
        st.info(f"PDF not available: {e}")

    # ---------- Job — Inputs (Apply), placed right below charts ----------
    def job_inputs_single(prefix: str, label: str):
        files_, xmls_, jpgs_, tifs_, _ = read_zip_listing(z, cache_ns="single")
        submitted = False
        with st.form(key=f"{prefix}_form"):
            xml_default = 0 if not st.session_state.get(f"{prefix}_xml_sel") else max(0, min(len(xmls_)-1, xmls_.index(st.session_state.get(f"{prefix}_xml_sel")))) if st.session_state.get(f"{prefix}_xml_sel") in xmls_ else 0
            xml_sel = st.selectbox("XML (ml/m² base)", options=xmls_, index=xml_default, key=f"{prefix}_xml_sel")
            xml_bytes_hdr = read_bytes_from_zip(z, st.session_state.get(f"{prefix}_xml_sel", xml_sel), cache_ns="single")
            w_xml_def, h_xml_def, area_xml_m2_def = get_xml_dims_m(xml_bytes_hdr)
    
            auto_mode = infer_mode_from_xml(xml_bytes_hdr)
            white_in = has_white_in_xml(xml_bytes_hdr)
            PRINT_MODE_OPTIONS = list(PRINT_MODES.keys())
            mode_default = auto_mode if auto_mode in PRINT_MODES else (PRINT_MODE_OPTIONS[0] if PRINT_MODE_OPTIONS else None)
            idx_mode = PRINT_MODE_OPTIONS.index(mode_default) if (mode_default in PRINT_MODE_OPTIONS) else 0
    
            # Source first to decide locking
            cons_src = st.radio(
                "Consumption source (ml/m²)",
                ["XML (exact)", "XML + mode multiplier (%)", "Manual"],
                index=0,
                key=f"{prefix}_cons_source", help="Choose the source of ml/m²: exact XML, XML scaled by print mode multipliers, or manual values.",
            )
            lock_mode = str(cons_src).startswith("XML (exact)")
            # Ensure valid selection to avoid "Choose an option" disabled selectbox
            if (st.session_state.get(f"{prefix}_mode_sel") not in PRINT_MODE_OPTIONS) or lock_mode:
                st.session_state[f"{prefix}_mode_sel"] = mode_default
    
            mode_sel = st.selectbox(
                "Print mode",
                PRINT_MODE_OPTIONS,
                index=idx_mode,
                key=f"{prefix}_mode_sel",
                format_func=lambda m: mode_option_label(m, white_in, get_unit(), w_xml_def),
                disabled=lock_mode,
                help=("Locked to the XML-inferred mode when using XML (exact)." if lock_mode else None),
            )
            mode_eff = mode_sel if mode_sel in PRINT_MODES else (mode_default if mode_default in PRINT_MODES else None)
            mode_for_caption = mode_eff if mode_eff in PRINT_MODES else (PRINT_MODE_OPTIONS[0] if PRINT_MODE_OPTIONS else None)
            if mode_for_caption in PRINT_MODES:
                st.caption(f"XML area: **{area_xml_m2_def:.3f} m²** • Speed: **{speed_label(get_unit(), PRINT_MODES[mode_for_caption]['speed'], w_xml_def)}**")
            res_key = auto_mode if auto_mode in PRINT_MODES else mode_for_caption
            if res_key in PRINT_MODES:
                st.caption(f"XML resolution: **{PRINT_MODES[res_key]['res_color']} (color){' • ' + WHITE_RES + ' (white)' if white_in else ''}**")
    
            a1, a2, a3 = st.columns(3)
            a1.number_input("Usable width (m)", value=float(round(w_xml_def, 3)), min_value=0.0, step=0.01, format="%.3f", key=f"{prefix}_width_m", help="Printable width used for this job.")
            a2.number_input("Length (m)",        value=float(round(h_xml_def, 3)), min_value=0.0, step=0.01, format="%.3f", key=f"{prefix}_length_m", help="Length to be produced for this job.")
            a3.number_input("Waste (%)",         value=2.0,                        min_value=0.0, step=0.5,                key=f"{prefix}_waste", help="Allowance for setup, trims and reprints.")
            # Details for source
            if cons_src.startswith("XML + mode multiplier"):
                st.info("Using XML + mode multipliers. The selected print mode applies Color/White/FOF factors.")
                # Inline per-mode scalers (Single) — use unique keys and sync to shared
                render_mode_multiplier_controls(use_expander=False, show_presets=True, key_prefix=prefix, sync_to_shared=True)
            elif cons_src == "Manual":
                mcols = st.columns(3)
                mcols[0].number_input(
                    f"Manual — Color (ml{per_unit('m2')})",
                    value=float(st.session_state.get(f"{prefix}_man_c", 0.0)),
                    min_value=0.0, step=0.1, key=f"{prefix}_man_c"
                )
                mcols[1].number_input(
                    f"Manual — White (ml{per_unit('m2')})",
                    value=float(st.session_state.get(f"{prefix}_man_w", 0.0)),
                    min_value=0.0, step=0.1, key=f"{prefix}_man_w"
                )
                mcols[2].number_input(
                    f"Manual — FOF (ml{per_unit('m2')})",
                    value=float(st.session_state.get(f"{prefix}_man_f", 0.0)),
                    min_value=0.0, step=0.1, key=f"{prefix}_man_f"
                )
    
    
            lab1, _ = st.columns([1,1])
            lab1.number_input("Variable labor ($/h) — use only if NOT in Fixed", min_value=0.0, value=float(st.session_state.get(f"{prefix}_lab_h", 0.0)), step=0.5, key=f"{prefix}_lab_h", help="Hourly variable labor. Do not use if already included in monthly fixed costs.")
    
            st.caption(f"Other variables ({per_unit(get_unit())}) — optional")
            _vars_input = ensure_df(st.session_state.get(f"{prefix}_other_vars", [{"Name": "—", "Value": 0.0}]), ["Name","Value"])
            df_vars = st.data_editor(_vars_input, num_rows="dynamic", use_container_width=True, key=f"{prefix}_other_vars_editor")
            st.session_state[f"{prefix}_other_vars"] = ensure_df(df_vars, ["Name","Value"]).to_dict(orient="records")
    
            fix_mode = st.radio("Fixed costs mode", ["Direct per unit", "Monthly helper"], index=0 if (str(st.session_state.get(f"{prefix}_fix_mode", "Direct per unit")).startswith("Direct")) else 1, horizontal=True, key=f"{prefix}_fix_mode", help="Choose direct fixed allocation per unit, or compute $/unit by entering monthly fixed costs + monthly production.")
    
            if fix_mode.startswith("Direct"):
                with st_div("ink-fixed-grid"):
                    mv1, mv2, mv3, mv4, mv5 = st.columns(5)
                    mv1.number_input(
                        f"Fixed allocation\u00A0(/"+unit_label_short(get_unit())+")",
                        min_value=0.0,
                        value=float(st.session_state.get(f"{prefix}_fixed_unit", 0.0)),
                        step=0.05,
                        key=f"{prefix}_fixed_unit",
                        help="Fixed cost per unit if not using the monthly helper.")
                    mv2.number_input(f"Price {per_unit(get_unit())}", min_value=0.0, value=float(st.session_state.get(f"{prefix}_price", 0.0)), step=0.10, key=f"{prefix}_price", help="Selling price per unit.")
                    mv3.number_input("Target margin (%)", min_value=0.0, value=float(st.session_state.get(f"{prefix}_margin", 20.0)), step=0.5, key=f"{prefix}_margin", help="Target markup over cost before taxes and fees.")
                    mv4.number_input("Taxes (%)",         min_value=0.0, value=float(st.session_state.get(f"{prefix}_tax", 10.0)),    step=0.5, key=f"{prefix}_tax", help="Taxes or withholdings applied to price.")
                    mv5.number_input("Fees/Terms (%)",    min_value=0.0, value=float(st.session_state.get(f"{prefix}_terms", 2.10)),  step=0.05, key=f"{prefix}_terms", help="Payment terms, card fees, financing, etc.")
                    st.selectbox("Round to", ["0.01", "0.05", "0.10"], index={"0.01":0,"0.05":1,"0.10":2}.get(str(st.session_state.get(f"{prefix}_round", 0.05)),1), key=f"{prefix}_round", help="Rounding step for suggested price.")
            else:
                st.markdown('<div class="ink-callout"><b>Monthly fixed costs</b> — labor, leasing, depreciation, overheads and other items.</div>', unsafe_allow_html=True)
                fx1, fx2, fx3, fx4 = st.columns(4)
                fx1.number_input("Labor (monthly)",        min_value=0.0, value=float(st.session_state.get(f"{prefix}_fix_labor_month", 0.0)),   step=10.0, key=f"{prefix}_fix_labor_month", help="Salaries or fixed staff per month.")
                fx2.number_input("Leasing/Rent (monthly)", min_value=0.0, value=float(st.session_state.get(f"{prefix}_fix_leasing_month", 0.0)), step=10.0, key=f"{prefix}_fix_leasing_month", help="Printer leasing, rent, subscriptions, RIP, etc.")
                fx3.number_input("Depreciation (monthly)", min_value=0.0, value=float(st.session_state.get(f"{prefix}_fix_depr_month", 0.0)),    step=10.0, key=f"{prefix}_fix_depr_month", help="Monthly CAPEX (depreciation).")
                fx4.number_input("Overheads (monthly)",    min_value=0.0, value=float(st.session_state.get(f"{prefix}_fix_over_month", 0.0)),    step=10.0, key=f"{prefix}_fix_over_month", help="Base energy, insurance, maintenance, overheads.")
    
                st.caption("Other fixed (monthly)")
                _fix_input = ensure_df(st.session_state.get(f"{prefix}_fix_others", [{"Name":"—","Value":0.0}]), ["Name","Value"])
                df_fix = st.data_editor(_fix_input, num_rows="dynamic", use_container_width=True, key=f"{prefix}_fix_others_editor")
                st.session_state[f"{prefix}_fix_others"] = ensure_df(df_fix, ["Name","Value"]).to_dict(orient="records")
    
                prod_m = monthly_production_inputs(get_unit(), unit_label_short(get_unit()), state_prefix=f"{prefix}_fix")
    
                sum_others = ensure_df(st.session_state.get(f"{prefix}_fix_others", []), ["Name","Value"]).get("Value", pd.Series(dtype=float)).fillna(0).sum() if st.session_state.get(f"{prefix}_fix_others") else 0.0
                total_fix_m = (
                    float(st.session_state.get(f"{prefix}_fix_labor_month", 0.0))
                    + float(st.session_state.get(f"{prefix}_fix_leasing_month", 0.0))
                    + float(st.session_state.get(f"{prefix}_fix_depr_month", 0.0))
                    + float(st.session_state.get(f"{prefix}_fix_over_month", 0.0))
                    + float(sum_others)
                )
                alloc = (total_fix_m / prod_m) if prod_m > 0 else 0.0
                st.metric(f"Fixed allocation ({per_unit(get_unit())})", f"{alloc:.4f}")
                st.caption(f"Monthly fixed total: US$ {total_fix_m:,.2f} • Production: {prod_m:,.0f} {unit_label_short(get_unit())}/month")
    
                pv2, pv3, pv4, pv5 = st.columns(4)
                pv2.number_input(f"Price {per_unit(get_unit())}", min_value=0.0, value=float(st.session_state.get(f'{prefix}_price', 0.0)), step=0.10, key=f"{prefix}_price")
                pv3.number_input("Target margin (%)", min_value=0.0, value=float(st.session_state.get(f'{prefix}_margin', 20.0)), step=0.5, key=f"{prefix}_margin")
                pv4.number_input("Taxes (%)",         min_value=0.0, value=float(st.session_state.get(f'{prefix}_tax', 10.0)),    step=0.5, key=f"{prefix}_tax")
                pv5.number_input("Fees/Terms (%)",    min_value=0.0, value=float(st.session_state.get(f'{prefix}_terms', 2.10)),  step=0.05, key=f"{prefix}_terms")
                st.selectbox("Round to", ["0.01", "0.05", "0.10"], index={"0.01":0,"0.05":1,"0.10":2}.get(str(st.session_state.get(f"{prefix}_round", 0.05)),1), key=f"{prefix}_round", help="Rounding step for suggested price.")
    
            submitted = st.form_submit_button(f"Apply {label}")
        if submitted:
            if str(st.session_state.get(f"{prefix}_cons_source", "")).startswith("XML + mode"):
                sync_mode_scalers_from_prefix(prefix)
            st.success(f"{label} saved. Now click 'Calculate'.")

    st.markdown('<div class="ink-callout"><b>Job — Inputs (Apply)</b> — Fill and click <b>Apply</b> to save.</div>', unsafe_allow_html=True)
    with st.expander("Job — Inputs (Apply)", expanded=False):
        job_inputs_single("single", "Job")

    # ---------- Shared costs & currency (Single) ----------
    section("Costs & currency", "Applies to the job.")
    cc1, cc2, cc3, cc4 = st.columns(4)
    cc1.number_input("Color ink ($/L)",  min_value=0.0, value=float(st.session_state.get("single_ink_c", DEFAULTS["ink_color_per_l"])),  step=1.0, key="single_ink_c")
    cc2.number_input("White ink ($/L)",  min_value=0.0, value=float(st.session_state.get("single_ink_w", DEFAULTS["ink_white_per_l"])),  step=1.0, key="single_ink_w")
    cc3.number_input("FOF / Pretreat ($/L)", min_value=0.0, value=float(st.session_state.get("single_fof", DEFAULTS["fof_per_l"])), step=1.0, key="single_fof")
    cc4.number_input(f"Substrate ({per_unit(UNIT)})", min_value=0.0, value=float(st.session_state.get("single_fabric", DEFAULTS["fabric_per_unit"])), step=0.10, key="single_fabric")

    cur1, cur2, cur3 = st.columns(3)
    local_symbol  = cur1.text_input("Local currency symbol", value=st.session_state.get("single_local_sym", DEFAULTS["local_symbol"]), key="single_local_sym")
    usd_to_local  = cur2.number_input("USD → Local (FX)", min_value=0.0, value=float(st.session_state.get("single_fx", DEFAULTS["usd_to_local"])), step=0.01, key="single_fx")
    currency_out  = cur3.radio("Output currency", ["USD", "Local"], index=1 if st.session_state.get("single_curr_out", "Local")=="Local" else 0, horizontal=True, key="single_curr_out")
    # Help glossary for costs
    render_help_glossary()
    FX, SYM       = (1.0, "US$") if currency_out=="USD" else (usd_to_local, local_symbol)

    # ---------- Runner: calculate single job ----------
    def run_single_job(sym: str, fx: float):
        prefix = "single"
        UNIT_l = get_unit()
        # prices shared
        ink_c = float(st.session_state.get("single_ink_c", DEFAULTS["ink_color_per_l"]))
        ink_w = float(st.session_state.get("single_ink_w", DEFAULTS["ink_white_per_l"]))
        fof   = float(st.session_state.get("single_fof",   DEFAULTS["fof_per_l"]))
        media = float(st.session_state.get("single_fabric", DEFAULTS["fabric_per_unit"]))

        other_vars_df = ensure_df(st.session_state.get(f"{prefix}_other_vars", [{"Name":"—","Value":0.0}]), ["Name","Value"])

        xml_inner_path = st.session_state.get(f"{prefix}_xml_sel")
        if not xml_inner_path:
            _, xmls_i, *_ = read_zip_listing(z, cache_ns="single")
            xml_inner_path = xmls_i[0] if xmls_i else None
        if not xml_inner_path:
            st.session_state["single_panels"] = {"error": "No XML in ZIP."}
            return
        xml_bytes = read_bytes_from_zip(z, xml_inner_path, cache_ns="single")

        factors = get_mode_factors_from_state()

        mlmap_use = apply_consumption_source(
            xml_bytes,
            st.session_state.get(f"{prefix}_cons_source", "XML (exact)"),
            st.session_state.get(f"{prefix}_mode_sel"),
            factors,
            st.session_state.get(f"{prefix}_man_c", 0.0),
            st.session_state.get(f"{prefix}_man_w", 0.0),
            st.session_state.get(f"{prefix}_man_f", 0.0),
        )

        width_m  = float(st.session_state.get(f"{prefix}_width_m",  1.0))
        length_m = float(st.session_state.get(f"{prefix}_length_m", 1.0))
        waste    = float(st.session_state.get(f"{prefix}_waste",    0.0))
        # Safe speed resolution from selected/auto/default mode
        _mode_key = st.session_state.get(f"{prefix}_mode_sel")
        if _mode_key not in PRINT_MODES:
            # try to infer from current XML, else pick the first available
            inferred = infer_mode_from_xml(xml_bytes)
            _mode_key = inferred if inferred in PRINT_MODES else (list(PRINT_MODES.keys())[0] if PRINT_MODES else None)
        speed = PRINT_MODES.get(_mode_key, {}).get("speed", 0.0)

        labor_h = float(st.session_state.get(f"{prefix}_lab_h", 0.0))
        if UNIT_l == "m2":
            labor_var_per_unit = labor_h / max(1e-9, speed)
        else:
            m_per_h = speed / max(1e-9, width_m)
            labor_var_per_unit = labor_h / max(1e-9, m_per_h)

        other_vars_sum = float(other_vars_df["Value"].fillna(0).sum()) + labor_var_per_unit

        fix_mode_val = (st.session_state.get(f"{prefix}_fix_mode") or "Direct per unit")
        if str(fix_mode_val).lower().startswith("monthly"):
            fix_labor_m   = float(st.session_state.get(f"{prefix}_fix_labor_month", 0.0))
            fix_leasing_m = float(st.session_state.get(f"{prefix}_fix_leasing_month", 0.0))
            fix_depr_m    = float(st.session_state.get(f"{prefix}_fix_depr_month", 0.0))
            fix_over_m    = float(st.session_state.get(f"{prefix}_fix_over_month", 0.0))
            fix_others_df = ensure_df(st.session_state.get(f"{prefix}_fix_others", [{"Name":"—","Value":0.0}]), ["Name","Value"])
            fix_others_m  = float(fix_others_df["Value"].fillna(0).sum())
            prod_month_u  = float(st.session_state.get(f"{prefix}_fix_prod_month_units", DEFAULTS.get("prod_month_units", 30000.0)))
            fixed_per_unit_used = (fix_labor_m + fix_leasing_m + fix_depr_m + fix_over_m + fix_others_m) / prod_month_u if prod_month_u > 0 else 0.0
        else:
            fixed_per_unit_used = float(st.session_state.get(f"{prefix}_fixed_unit", 0.0))

        res = simulate(
            UNIT_l,
            width_m, length_m, waste,
            speed,
            mlmap_use,
            ink_c, ink_w, fof,
            media,
            other_vars_sum,
            0.0,
            fixed_per_unit_used,
            show_time_metrics=False,
        )

        qty = max(1e-9, float(res.get("qty_units", 0.0)))
        variable_per_unit = (float(res.get("cost_ink",0))+fabric_total(res)+float(res.get("cost_other",0))) / qty
        fixed_per_unit_card = float(res.get("cost_fixed",0))/qty if qty>0 else 0.0
        cost_unit_calc = float(res.get("total_cost",0))/qty if qty>0 else 0.0

        margin = float(st.session_state.get(f"{prefix}_margin", 20.0))
        tax    = float(st.session_state.get(f"{prefix}_tax",    10.0))
        terms  = float(st.session_state.get(f"{prefix}_terms",   2.1))
        rnd    = float(st.session_state.get(f"{prefix}_round",  0.05))
        price_input = float(st.session_state.get(f"{prefix}_price", 0.0))
        suggested   = price_round(cost_unit_calc*(1 + margin/100 + tax/100), rnd)
        suggested   = price_round(suggested*(1 + terms/100), rnd)
        effective_price = price_input if price_input>0 else suggested

        rows_tot, rows_unit = build_cost_rows_from_sim(res, unit_lbl, sym, fx, price=effective_price)

        st.session_state["single_panels"] = {
        "rows_tot": rows_tot,
        "rows_unit": rows_unit,
        "unit_lbl": unit_lbl,
        "kpis": {
            "qty": qty,
            "area_waste_m2": res.get("area_waste_m2", 0.0),
            "total_ml_per_unit": res.get("total_ml_per_unit", 0.0),
            "time_print_h": res.get("time_print_h", 0.0),
            "time_total_h": res.get("time_total_h", 0.0),
        },
        "raw": res,
        "ml_map": dict(mlmap_use or {}),
        # 👉 INSUMOS PARA O BREAK-EVEN (idêntico ao Compare)
        "be": {
            "variable_per_unit": float(variable_per_unit),
            "effective_price":   float(effective_price),
            "fixed_per_unit":    float(fixed_per_unit_card),
        },
    }

    st.markdown("---")
    if st.button("Calcular", type="primary", key="single_btn_calc"):
        run_single_job(SYM, FX)
        st.success("Job calculado.")

    # ---------- Render panels ----------
    P = st.session_state.get("single_panels")
    if P:
        with st_div("cmp-compact"):
            st.markdown("### Results")
            cards_col, kpi_col = st.columns([1.5, 1.0])
            with cards_col:
                render_info_table("Total ($)", P["rows_tot"])
                render_info_table(f"Per unit (/{P.get('unit_lbl', unit_lbl)})", P["rows_unit"])
            with kpi_col:
                unitS = P.get("unit_lbl", unit_lbl)
                kS = P.get("kpis", {})
                st.metric(f"Qty ({unitS})", f"{float(kS.get('qty', 0.0)):.2f}")
                st.metric(f"Total ml{per_unit(get_unit())}", f"{float(kS.get('total_ml_per_unit', 0.0)):.2f}")
                st.metric("Print time (h)", f"{float(kS.get('time_print_h', (P.get('raw') or {}).get('time_print_h', 0.0))):.2f}")
                st.metric("Total time (h)", f"{float(kS.get('time_total_h', (P.get('raw') or {}).get('time_total_h', 0.0))):.2f}")
                    # -----------------------------
    # Break-even — Single (idêntico ao Compare A×B)
    # -----------------------------
    try:
        section(
            "Break-even — Single",
            "Estimate monthly volume needed to cover fixed costs. Use price, variable cost and monthly fixed cost."
        )

        # Precisamos dos insumos salvos no PATCH 1
        if P and P.get("be"):
            var_u  = float(P["be"].get("variable_per_unit", 0.0))
            price_u = float(P["be"].get("effective_price", 0.0))

            # Mesma definição de moeda usada no Single
            currency_out = st.session_state.get("single_curr_out", "Local")
            if currency_out == "USD":
                FX, SYM = 1.0, "US$"
            else:
                FX  = float(st.session_state.get("single_fx", DEFAULTS.get("usd_to_local", 5.57)))
                SYM = st.session_state.get("single_local_sym", DEFAULTS.get("local_symbol", "R$"))

            UNIT = get_unit()
            unit_lbl = unit_label_short(UNIT)

            # Monthly fixed source: se estiver usando Monthly helper, somamos; senão, input manual
            if str(st.session_state.get("single_fix_mode", "")).lower().startswith("monthly"):
                sum_others = 0.0
                if st.session_state.get("single_fix_others"):
                    sum_others = ensure_df(
                        st.session_state.get("single_fix_others", []),
                        ["Name", "Value"]
                    )["Value"].fillna(0).sum()

                fixed_month = (
                    float(st.session_state.get("single_fix_labor_month", 0.0))
                    + float(st.session_state.get("single_fix_leasing_month", 0.0))
                    + float(st.session_state.get("single_fix_depr_month", 0.0))
                    + float(st.session_state.get("single_fix_over_month", 0.0))
                    + float(sum_others)
                )
                st.caption(f"Monthly fixed (from helper): **{pretty_money(fixed_month, SYM, FX)}**")
            else:
                fixed_month = st.number_input(
                    "Monthly fixed (enter)",
                    min_value=0.0,
                    value=float(st.session_state.get("single_be_fixed_month", 0.0)),
                    step=50.0,
                    key="single_be_fixed_month",
                )

            # Mesmo gráfico usado no Compare
            fig_be = breakeven_figure(
                price_u=price_u,
                variable_u=var_u,
                fixed_month=fixed_month,
                unit_lbl=unit_lbl,
                sym=SYM,
                fx=FX,
                title="Break-even — Job"
            )
            st.plotly_chart(fig_be, use_container_width=True, key="single_be_chart", config=plotly_cfg())
            try:
                render_break_even_insights(price_u, var_u, fixed_month, unit_lbl, SYM, FX, label="Job")
            except Exception:
                pass
        else:
            st.info("Click **Calculate** to generate the break-even inputs.")
    except Exception as _e:
        st.info(f"Break-even unavailable: {_e}")
                
# ===========================================
# Helpers específicos do Compare A×B
# ===========================================
def safe_union_channels_sorted(mapA: dict, mapB: dict):
    """
    Retorna a lista de canais presentes em A ou B ordenada de forma estável.
    Sempre prioriza CMYK + Red + Green + FOF + White.
    """
    pref = ["Cyan", "Magenta", "Yellow", "Black", "Red", "Green", "FOF", "White", "Color"]
    raw = []
    for k in list((mapA or {}).keys()) + list((mapB or {}).keys()):
        if k and (k not in raw):
            raw.append(k)
    return sorted(raw, key=lambda c: (pref.index(c) if c in pref else 99, str(c)))



# ===========================================
# FLUXO: COMPARE A × B  — ÚNICA VERSÃO CORRIGIDA
# ===========================================
def ui_compare():
    UNIT = get_unit()
    unit_lbl = unit_label_short(UNIT)

    # ---------- Uploads
    section("Upload jobs A and B", "Upload two ZIPs (each must include an XML; TIFF/JPG are optional for preview).")
    upA, upB = st.columns(2)
    zipA = upA.file_uploader("Job A (ZIP)", type="zip", key="cmp_zip_A")
    zipB = upB.file_uploader("Job B (ZIP)", type="zip", key="cmp_zip_B")

    if not zipA or not zipB:
        st.info("Upload **both** ZIPs to continue.")
        return

    # Listagem de conteúdo
    zipA_bytes = zipA.getvalue()
    zipB_bytes = zipB.getvalue()
    filesA, xmlsA, jpgsA, tifsA, adA = read_zip_listing(zipA_bytes, cache_ns="cmpA")
    filesB, xmlsB, jpgsB, tifsB, adB = read_zip_listing(zipB_bytes, cache_ns="cmpB")
    mA1, mA2, mA3, mB1, mB2, mB3 = st.columns(6)
    mA1.metric("A — XML", len(xmlsA)); mA2.metric("A — JPG", len(jpgsA)); mA3.metric("A — TIFF", len(tifsA))
    mB1.metric("B — XML", len(xmlsB)); mB2.metric("B — JPG", len(jpgsB)); mB3.metric("B — TIFF", len(tifsB))
    # Silently ignore AppleDouble entries if present
    if not xmlsA or not xmlsB:
        st.error("Each ZIP must contain at least one XML.")
        return
    st.markdown('<div class="cmp-compact">', unsafe_allow_html=True)
    

    # ---------- Job setup (define XMLs e lê ml/m²)
    section("Job setup", "Choose the XML for each job (used for per-channel consumption, dimensions and metadata).")
    jbA, jbB = st.columns(2)

    with jbA:
        st.subheader("Job A")
        xmlA = st.selectbox("XML (A)", xmlsA, index=0, key="cmp_xml_A")
        xmlA_bytes = read_bytes_from_zip(zipA_bytes, xmlA, cache_ns="cmpA")
        mlm2A = ml_per_m2_from_xml_bytes(xmlA_bytes) or {}
        wA_xml, hA_xml, areaA_xml_m2 = get_xml_dims_m(xmlA_bytes)

    with jbB:
        st.subheader("Job B")
        xmlB = st.selectbox("XML (B)", xmlsB, index=0, key="cmp_xml_B")
        xmlB_bytes = read_bytes_from_zip(zipB_bytes, xmlB, cache_ns="cmpB")
        mlm2B = ml_per_m2_from_xml_bytes(xmlB_bytes) or {}
        wB_xml, hB_xml, areaB_xml_m2 = get_xml_dims_m(xmlB_bytes)

    # --- FALLBACK (A × B): se o XML escolhido só tem White/FOF, somar todos os XMLs do ZIP
    if not has_color_channels(mlm2A):
        mlm2A = ml_map_union_all_xmls(zipA_bytes, cache_ns="cmpA")
    if not has_color_channels(mlm2B):
        mlm2B = ml_map_union_all_xmls(zipB_bytes, cache_ns="cmpB")

    # Pixels (por Selected XML)
    pxA = fire_pixels_map_from_xml_bytes(xmlA_bytes)
    pxB = fire_pixels_map_from_xml_bytes(xmlB_bytes)

    # --- FALLBACK para pixels: se só houver White/FOF, somar os pixels de todos os XMLs do ZIP
    if not has_color_channels(pxA):
        pxA = fire_pixels_union_all_xmls(zipA_bytes, cache_ns="cmpA")
    if not has_color_channels(pxB):
        pxB = fire_pixels_union_all_xmls(zipB_bytes, cache_ns="cmpB")

    # ---------- Mapas de TIFF por canal (para preview)
    chan_mapA, chan_mapB = {}, {}
    for p in tifsA:
        ch = get_channel_from_filename(p.split("/")[-1])
        if ch: chan_mapA[ch] = p
    for p in tifsB:
        ch = get_channel_from_filename(p.split("/")[-1])
        if ch: chan_mapB[ch] = p

    # ---- Injetar CSS para colorir só os botões de canais

    # ---------- Conjunto ÚNICO de canais = TIFFs ∪ XML ∪ Preview
    # Ordem preferida (CMYK + extras + FOF + White)
    pref_order = ["Preview","Cyan","Magenta","Yellow","Black","Red","Green","FOF","White"]

    avail = set()
    avail.update(chan_mapA.keys())
    avail.update(chan_mapB.keys())
    avail.update({k for k in (mlm2A or {}).keys() if k})
    avail.update({k for k in (mlm2B or {}).keys() if k})

    # Tem JPG de preview em A ou B?
    has_prev = any(re.search(r"preview", j, re.I) for j in (jpgsA or [])) or \
            any(re.search(r"preview", j, re.I) for j in (jpgsB or []))
    if has_prev:
        avail.add("Preview")

    # Lista final na ordem preferida + sobras ordenadas
    all_channels = [c for c in pref_order if c in avail] + \
                sorted([c for c in avail if c not in pref_order], key=str)

    if not all_channels:
        all_channels = ["Preview"]  # fallback seguro


    section("Per-channel preview (A × B)", "A single selector switches both jobs.")
    # Sliders de preview (mesma ideia do Single job)
    sl1, sl2 = st.columns(2)
    preview_w = sl1.slider(
        "Preview box width (px)", 320, 900, 560, 10,
        help="Images are letterboxed for consistent dimensions.",
        key="cmp_prev_w",
    )
    preview_h = sl2.slider(
        "Preview box height (px)", 260, 900, 460, 10,
        key="cmp_prev_h",
    )
    if "cmp_unified_chan" not in st.session_state:
        st.session_state["cmp_unified_chan"] = "Preview" if "Preview" in all_channels else (all_channels[0] if all_channels else "Preview")
    # Sincroniza com ?cmpch= (link pills)
    if all_channels:
        sync_state_from_qp("cmp_unified_chan", "cmpch", all_channels, st.session_state["cmp_unified_chan"])

    # "Botões" em linhas de até 6 — usamos anchors estilizados (link-pills)
    if all_channels:
        i = 0
        disp_map = {}
        while i < len(all_channels):
            row = all_channels[i:i+6]
            cols = st.columns(len(row))
            for k, ch in enumerate(row):
                with cols[k]:
                    disp = "FOF (DuoSoft)" if ch == "FOF" else ch
                    disp_map[disp] = ch
                    chip_button(
                        label=ch,
                        color_hex=CHANNEL_COLORS.get(ch, "#666666"),
                        selected=(st.session_state["cmp_unified_chan"] == ch),
                        qp_key="cmpch",
                        state_key="cmp_unified_chan",
                        display_label=disp,
                    )
            i += 6
            # Cores: a linha colorida abaixo de cada botão substitui a estilização do botão.
            # Apply CSS styling to channel buttons (by aria-label)
            sel_disp = "FOF (DuoSoft)" if st.session_state.get("cmp_unified_chan") == "FOF" else st.session_state.get("cmp_unified_chan")
            style_channel_buttons_by_aria(disp_map, selected_display=sel_disp)
    else:
        st.info("No channel available for preview.")

    sel_ch = st.session_state.get("cmp_unified_chan", "Preview")


    # ---------- Previews lado a lado
    st.markdown(" ")
    colL, colR = st.columns(2)

    def render_side(label, zip_bytes, jpgs, chan_map, ml_map, px_map, ch, preview_w=560, preview_h=460, cache_ns="cmpA"):
        st.markdown(f"**Selected ({label})**: {ch}")
        path, _ = choose_path(ch, jpgs, chan_map)
        preview_fragment(
            f"{cache_ns}_{label}",
            zip_bytes,
            path,
            width=preview_w,
            height=preview_h,
            fill_flag=False,
            trim_flag=False,
            max_side=int(preview_w * 1.35),
            caption=path or f"{label} preview",
        )
        # ml/m² for the current channel (if present in XML)
        v = ml_map.get(ch)
        if v is not None:
            st.caption(f"**{ch}**: {v:.2f} ml/m²")
        st.markdown(f"**Total consumption**: {total_ml_per_m2_from_map(ml_map):.2f} ml/m²")

        # Gráfico individual (ml/m² do job)
        if ml_map:
            items = sorted(ml_map.items(), key=lambda kv: kv[1], reverse=True)
            labels = [k for k,_ in items]; values = [v for _,v in items]
            colors = [CHANNEL_COLORS.get(k, "#888") for k in labels]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=labels, y=values, marker=dict(color=colors)))
            fig.update_layout(template="plotly_white", height=340, margin=dict(l=10, r=10, t=30, b=10),
                              yaxis_title="ml/m²", xaxis_title="Channel", title=f"Per-channel consumption (ml/m²) — {label}")
            st.plotly_chart(fig, use_container_width=True, key=f"cmp_side_ml_{label}", config=plotly_cfg())

            # --- Pixels per channel (K) — same format/colors
            if px_map:
                items_px = sorted(px_map.items(), key=lambda kv: kv[1], reverse=True)
                labels_px = [k for k, _ in items_px]
                values_px = [float(v)/1000.0 for _, v in items_px]  # K pixels
                colors_px = [CHANNEL_COLORS.get(k, "#888") for k in labels_px]

                figp = go.Figure()
                figp.add_trace(go.Bar(x=labels_px, y=values_px, marker=dict(color=colors_px)))
                figp.update_layout(template="plotly_white", height=340,
                                margin=dict(l=10, r=10, t=30, b=10),
                                yaxis_title="K pixels", xaxis_title="Channel",
                                title=f"Fire pixels per channel (K) — {label}")
                st.plotly_chart(figp, use_container_width=True, key=f"cmp_side_px_{label}", config=plotly_cfg())

    with colL:
            render_side(
                "Job A", zipA_bytes, jpgsA, chan_mapA, mlm2A, pxA, sel_ch,
                preview_w=st.session_state.get("cmp_prev_w", 560),
                preview_h=st.session_state.get("cmp_prev_h", 460),
                cache_ns="cmpA",
            )
    with colR:
        render_side(
            "Job B", zipB_bytes, jpgsB, chan_mapB, mlm2B, pxB, sel_ch,
            preview_w=st.session_state.get("cmp_prev_w", 560),
            preview_h=st.session_state.get("cmp_prev_h", 460),
            cache_ns="cmpB",
        )

    # ---------- Simulação de custos & BEP (A×B)
    st.markdown("---")

    # ---------- Gráfico combinado A×B
    st.markdown("---")
    st.markdown("### A × B comparison — Per-channel consumption (ml/m²)")

    chart_order_pref = ["Cyan","Magenta","Yellow","Black","Red","Green","FOF","White"]

    raw = {c for c in mlm2A.keys() if c} | {c for c in mlm2B.keys() if c}
    channels_ordered = [c for c in chart_order_pref if c in raw]
    extra = sorted([c for c in raw if (c not in chart_order_pref and c != "Preview")], key=str)
    channels_ordered += extra

    yA = [float(mlm2A.get(c, 0.0) or 0.0) for c in channels_ordered]
    yB = [float(mlm2B.get(c, 0.0) or 0.0) for c in channels_ordered]
    colors = [CHANNEL_COLORS.get(c, "#888") for c in channels_ordered]

    fig_cmp = go.Figure()
    nameA = st.session_state.get("cmpA_zip_name", "Job A")
    nameB = st.session_state.get("cmpB_zip_name", "Job B")
    fig_cmp.add_trace(go.Bar(name=nameA, x=channels_ordered, y=yA, marker=dict(color=colors)))
    fig_cmp.add_trace(go.Bar(
        name=nameB, x=channels_ordered, y=yB,
        marker=dict(color=colors, pattern_shape="/"),
        marker_line=dict(color="rgba(0,0,0,.55)", width=0.6), opacity=0.92
    ))
    fig_cmp.update_layout(template="plotly_white", barmode="group", height=460,
                          margin=dict(l=10, r=10, t=50, b=10),
                            xaxis_title="Channel", yaxis_title="ml/m²", legend_title="")
    
    st.plotly_chart(fig_cmp, use_container_width=True, key="cmp_pair_ml_chart", config=plotly_cfg())
    # — Quick insights A×B
    tips = insights_for_compare(channels_ordered, yA, yB)
    if tips:
        with st.expander("Quick insights", expanded=True):
            for t in tips:
                st.write("•", t)

    # PDF layout controls (Single A×B section) — same UI as Compare
    if "cmp_pdf_size" not in st.session_state:
        st.session_state["cmp_pdf_size"] = "Medium"
    if "cmp_pdf_show_comp" not in st.session_state:
        st.session_state["cmp_pdf_show_comp"] = True
    if "cmp_pdf_show_totals" not in st.session_state:
        st.session_state["cmp_pdf_show_totals"] = True
    spdf1, spdf2, spdf3 = st.columns([1.2, 1.0, 1.2])
    size_opt = spdf1.selectbox(
        "PDF preview size",
        ["Small", "Medium", "Large"],
        index={"Small":0,"Medium":1,"Large":2}.get(st.session_state.get("cmp_pdf_size","Medium"),1),
        key="cmp_pdf_size",
        help="Defines thumbnail size and chart/table layout."
    )
    show_comp = spdf2.checkbox("Show 100% composition", key="cmp_pdf_show_comp")
    show_totals = spdf3.checkbox("Totals below previews", key="cmp_pdf_show_totals")

    with st.spinner("Building A×B PDF…"):
        pdf_bytes = build_comparison_pdf_matplotlib(
            channels_ordered, yA, yB, mlm2A, mlm2B,
            labelA=nameA,
            labelB=nameB,
            zA_bytes=zA, zB_bytes=zB,
            selected_channel=st.session_state.get("cmp_chan_sel", "Preview"),
            show_comp=show_comp,
            preview_size={"Small":"S","Medium":"M","Large":"L"}[size_opt],
            show_totals=show_totals,
        )
    st.download_button("Export A×B PDF", data=pdf_bytes,
                    file_name="compare_AxB.pdf", mime="application/pdf")
    # === Inputs A and B just below the A×B PDF button ===
    st.markdown("---")
    inpA, inpB = st.columns(2)
    with inpA:
        st.markdown('<div class="ink-callout"><b>Job A — Inputs (Apply)</b> — Fill and click <b>Apply</b> to save A.</div>', unsafe_allow_html=True)
        with st.expander("Job A — Inputs (Apply)", expanded=False):
            compare_job_inputs("cmpA", "Job A", zA)
    with inpB:
        st.markdown('<div class="ink-callout"><b>Job B — Inputs (Apply)</b> — Fill and click <b>Apply</b> to save B.</div>', unsafe_allow_html=True)
        with st.expander("Job B — Inputs (Apply)", expanded=False):
            compare_job_inputs("cmpB", "Job B", zB)
    

    # --- A×B comparison — Fire pixels (K)
    if "cmp_combined_show_px" not in st.session_state:
        st.session_state["cmp_combined_show_px"] = True
    if st.session_state.get("cmp_combined_show_px", True):
        st.markdown("### A × B comparison — Fire pixels per channel (K)")

     # --- NEW: Comparativo A×B — Fire pixels
    raw_pix = {c for c in pxA.keys() if c} | {c for c in pxB.keys() if c}
    channels_pix_ordered = [c for c in chart_order_pref if c in raw_pix]
    channels_pix_ordered += sorted([c for c in raw_pix if c not in chart_order_pref and c != "Preview"], key=str)

    yAp = [float(pxA.get(c, 0.0))/1000.0 for c in channels_pix_ordered]  # K pixels
    yBp = [float(pxB.get(c, 0.0))/1000.0 for c in channels_pix_ordered]
    colors_pix = [CHANNEL_COLORS.get(c, "#888") for c in channels_pix_ordered]

    fig_pixcmp = go.Figure()
    fig_pixcmp.add_trace(go.Bar(name="Job A", x=channels_pix_ordered, y=yAp, marker=dict(color=colors_pix)))
    fig_pixcmp.add_trace(go.Bar(
        name="Job B", x=channels_pix_ordered, y=yBp,
        marker=dict(color=colors_pix, pattern_shape="/"),
        marker_line=dict(color="rgba(0,0,0,.55)", width=0.6), opacity=0.92
    ))
    fig_pixcmp.update_layout(template="plotly_white", barmode="group", height=460,
                            margin=dict(l=10, r=10, t=50, b=10),
                            xaxis_title="Channel", yaxis_title="K pixels", legend_title="",
                title="A × B comparison — Fire pixels per channel (K)")
    st.plotly_chart(fig_pixcmp, use_container_width=True, key="cmp_pair_px_chart", config=plotly_cfg())
    
    # --------------------
    # Simulação de custos — A×B (mesma lógica do Single)
    # --------------------
    st.markdown("---")
    section("Operational simulation — A×B", "Same logic as Single (costs and break-even per job).")

    # Callout com o toggle — a ordem correta é: abre DIV → checkbox → fecha DIV
    st.markdown('<div class="ink-callout">', unsafe_allow_html=True)
    calc_costs_cmp = st.checkbox(
        "Enable cost simulation? (A×B)",
        value=False,
        help="Opens monthly fixed costs, variable costs and break-even for A and B.",
        key="cmp_toggle_costs",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    if calc_costs_cmp:
    
        # ----- Fixed (monthly) + monthly production → allocation per unit (same as Single)
        section("Fixed (monthly) → allocation per unit", "“Enter USD/month and monthly production. We calculate $/unit and apply it to A and B.”.")
        fx1, fx2, fx3, fx4 = st.columns(4)
        fix_labor_month = fx1.number_input(
            "Fixed labor — USD/month",
            value=float(st.session_state.get("fix_labor_month", DEFAULTS["fix_labor_month"])),
            min_value=0.0,
            step=50.0,
            help="Salaries or fixed staff per month.",
            key="cmp_fix_labor",
        )
        fix_leasing_month = fx2.number_input(
            "Leasing/Subscriptions — USD/month",
            value=float(st.session_state.get("fix_leasing_month", DEFAULTS["fix_leasing_month"])),
            min_value=0.0,
            step=50.0,
            help="Printer leasing, RIP, contracts, etc.",
            key="cmp_fix_leasing",
        )
        fix_capex_month = fx3.number_input(
            "Depreciation — USD/month",
            value=float(st.session_state.get("fix_capex_month", DEFAULTS["fix_capex_month"])),
            min_value=0.0,
            step=50.0,
            help="Monthly CAPEX (depreciation).",
            key="cmp_fix_capex",
        )
        fix_indust_month = fx4.number_input(
            "Overheads — USD/month",
            value=float(st.session_state.get("fix_indust_month", DEFAULTS["fix_indust_month"])),
            min_value=0.0,
            step=50.0,
            help="Base energy, insurance, rent, maintenance, etc.",
            key="cmp_fix_indust",
        )

        st.caption("**Other fixed (monthly) — optional**")
        _fix_others_input = ensure_df(
            st.session_state.get("cmp_fix_others", [{"Name": "—", "Amount (USD)": 0.0}]),
            cols=["Name", "Amount (USD)"],
        )
        fix_others_df = st.data_editor(_fix_others_input, num_rows="dynamic", use_container_width=True, key="cmp_fix_others_editor")
        st.session_state["cmp_fix_others"] = ensure_df(fix_others_df, ["Name", "Amount (USD)"]).to_dict(orient="records")
        fix_total_month = (
            fix_labor_month
            + fix_leasing_month
            + fix_capex_month
            + fix_indust_month
            + float(ensure_df(fix_others_df)["Amount (USD)"].fillna(0).sum())
        )


        # === Monthly production (for fixed allocation — A×B) — movido para cá
        section(
            "Monthly production (for fixed allocation — A×B)",
            "Used when 'Monthly helper' is selected to allocate monthly fixed costs across A and B."
        )
        prod_month_units = monthly_production_inputs(UNIT, unit_lbl, "cmp")
        st.caption("Used when 'Monthly helper' is selected to allocate monthly fixed costs across A and B.")

        fix_per_unit = (fix_total_month / prod_month_units) if prod_month_units > 0 else 0.0

        fxm3, fxm4, fxm5 = st.columns(3)
        fxm3.metric("Fixed — monthly (USD)", pretty_money(fix_total_month, "US$", 1.0))
        fxm4.metric(f"Monthly production ({unit_lbl})", f"{prod_month_units:,.0f}")
        fxm5.metric(f"Fixed allocation ({per_unit(UNIT)})", pretty_money(fix_per_unit, "US$", 1.0))

        if st.button("Aplicar FIXED nos simuladores A e B", key="cmp_btn_apply_fixed"):
            st.session_state["cmp_fixed_per_unit"] = float(fix_per_unit)
            # mantém compatível com Single
            st.session_state["fixed_per_unit"]   = float(fix_per_unit)
            st.session_state["fix_labor_month"]  = float(fix_labor_month)
            st.session_state["fix_leasing_month"]= float(fix_leasing_month)
            st.session_state["fix_capex_month"]  = float(fix_capex_month)
            st.session_state["fix_indust_month"] = float(fix_indust_month)
            st.session_state["prod_month_units"] = float(prod_month_units)
            st.session_state["fix_total_month"]  = float(fix_total_month)
            st.success("Fixed costs applied to simulators A and B.")


        # ----- Production / ROI — entradas comuns (moeda e custos por litro/mídia)
        st.markdown("---")
        section("Production / ROI — simulator (A×B)", "Inputs in USD; choose output currency below.")

        cfg2, cfg3 = st.columns([1, 1])
        local_symbol = cfg2.text_input(
            "Local currency symbol",
            value=st.session_state.get("local_symbol", DEFAULTS["local_symbol"]),
            help="Ex.: R$, €",
            key="cmp_local_sym",
        )
        usd_to_local = cfg3.number_input(
            "USD → Local (FX)",
            min_value=0.0,
            value=float(st.session_state.get("usd_to_local", DEFAULTS["usd_to_local"])),
            step=0.01,
            key="cmp_fx",
        )
        currency_out = st.radio("Output currency", ["USD", "Local"], index=1, horizontal=True, key="cmp_curr_out")
        FX = 1.0 if currency_out == "USD" else usd_to_local
        SYM = "US$" if currency_out == "USD" else local_symbol

        v1, v2, v3 = st.columns(3)
        ink_color_per_l = v1.number_input(
            "Color ink ($/L)", value=float(st.session_state.get("ink_color_per_l", DEFAULTS["ink_color_per_l"])), min_value=0.0, step=1.0, key="cmp_ink_c"
        )
        ink_white_per_l = v2.number_input(
            "White ink ($/L)", value=float(st.session_state.get("ink_white_per_l", DEFAULTS["ink_white_per_l"])), min_value=0.0, step=1.0, key="cmp_ink_w"
        )
        fof_per_l = v3.number_input(
            "FOF / Pretreat ($/L)", value=float(st.session_state.get("fof_per_l", DEFAULTS["fof_per_l"])), min_value=0.0, step=1.0, key="cmp_fof"
        )

        mv1, _mv2 = st.columns(2)
        fabric_per_unit = mv1.number_input(
            f"Substrate ({per_unit(UNIT)})",
            value=float(st.session_state.get("fabric_per_unit", DEFAULTS["fabric_per_unit"])),
            min_value=0.0,
            step=0.10,
            key="cmp_fabric",
        )

        # ---------- Config por JOB (A e B lado a lado)
        st.markdown("### Production and pricing parameters per job")
        colA2, colB2 = st.columns(2)

        def job_panel(label, xml_bytes, w_xml_def, h_xml_def, mlm2_base, key_prefix):
            st.subheader(label)
            white_in_this_xml = has_white_in_xml(xml_bytes)
            PRINT_MODE_OPTIONS = list(PRINT_MODES.keys())
            auto_mode = infer_mode_from_xml(xml_bytes)
            state_key_mode = f"{key_prefix}_mode_sel"
            idx_default = PRINT_MODE_OPTIONS.index(auto_mode) if auto_mode in PRINT_MODES else 0

            mode_sel = st.selectbox(
                "Print mode (affects time)",
                PRINT_MODE_OPTIONS,
                index=idx_default,
                key=state_key_mode,
                format_func=lambda m: mode_option_label(m, white_in_this_xml, UNIT, w_xml_def),
                help="Used to compute time and, if enabled, consumption multipliers.",
            )
            st.caption(
                f"Mode: **{PRINT_MODES[mode_sel]['res_color']} (color){' • ' + WHITE_RES + ' (white)' if white_in_this_xml else ''}** • "
                f"Speed: **{speed_label(UNIT, PRINT_MODES[mode_sel]['speed'], w_xml_def)}**"
            )

            with st.form(f"{key_prefix}_sim_form", clear_on_submit=False):
                st.markdown("**Production dimensions (confirm/adjust)**")
                a1, a2, a3 = st.columns(3)
                width_m = a1.number_input(
                    "Usable width (m)", value=float(round(w_xml_def, 3)), min_value=0.0, step=0.01, format="%.3f", key=f"{key_prefix}_width_m"
                )
                length_m = a2.number_input(
                    "Length (m)", value=float(round(h_xml_def, 3)), min_value=0.0, step=0.01, format="%.3f", key=f"{key_prefix}_length_m"
                )
                waste_pct = a3.number_input("Waste (%)", value=2.0, min_value=0.0, step=0.5, key=f"{key_prefix}_waste")

                cons_source = st.radio(
                    "Consumption source (ml/m²)",
                    ["XML (exact)", "XML + mode multiplier", "Manual"],
                    index=0,
                    key=f"{key_prefix}_cons_source",
                )

                # Multiplicadores por modo (compartilhados via session, iguais ao Single)
                factors = {
                    "fast": {"color": st.session_state.get("single_mul_fc", 100.0) / 100.0,
                             "white": 1.00,
                             "fof": st.session_state.get("single_mul_ff", 100.0) / 100.0},
                    "standard": {"color": st.session_state.get("single_mul_sc", 100.0) / 100.0,
                                 "white": st.session_state.get("single_mul_sw", 100.0) / 100.0,
                                 "fof": st.session_state.get("single_mul_sf", 100.0) / 100.0},
                    "saturation": {"color": st.session_state.get("single_mul_tc", 100.0) / 100.0,
                                   "white": st.session_state.get("single_mul_tw", 100.0) / 100.0,
                                   "fof": st.session_state.get("single_mul_tf", 100.0) / 100.0},
                }

                man_color = man_white = man_fof = 0.0
                if cons_source == "Manual":
                    mcols = st.columns(3)
                    man_color = mcols[0].number_input(f"Manual — Color (ml{per_unit('m2')})", value=0.0, min_value=0.0, step=0.1, key=f"{key_prefix}_man_c")
                    man_white = mcols[1].number_input(f"Manual — White (ml{per_unit('m2')})", value=0.0, min_value=0.0, step=0.1, key=f"{key_prefix}_man_w")
                    man_fof   = mcols[2].number_input(f"Manual — FOF (ml{per_unit('m2')})", value=0.0, min_value=0.0, step=0.1, key=f"{key_prefix}_man_f")

                # Variable labor por unidade (usa velocidade do modo)
                lab1, lab2 = st.columns([1, 1])
                labor_hour_usd = lab1.number_input(
                    "Variable labor ($/h) — use only if NOT in Fixed",
                    value=float(st.session_state.get("labor_hour_usd", 0.0)),
                    min_value=0.0,
                    step=0.50,
                    key=f"{key_prefix}_lab_h",
                )
                # Resolve a safe speed for variable labor metric
                _mk = st.session_state.get(state_key_mode, mode_sel)
                if _mk not in PRINT_MODES:
                    _mk = mode_sel
                current_speed = PRINT_MODES.get(_mk, {}).get("speed", 0.0)
                if UNIT == "m2":
                    labor_var_per_unit = (labor_hour_usd / max(1e-9, current_speed))
                else:
                    m_per_h = current_speed / max(1e-9, width_m or 1e-9)
                    labor_var_per_unit = (labor_hour_usd / max(1e-9, m_per_h))
                lab2.metric(f"Variable labor ({per_unit(UNIT)})", pretty_money(labor_var_per_unit, "US$", 1.0))

                st.caption(f"Other variables ({per_unit(UNIT)}) — optional")
                _vars_input = ensure_df(
                    st.session_state.get(f"{key_prefix}_other_vars", [{"Name": "—", "Value": 0.0}]),
                    cols=["Name", "Value"],
                )
                df_vars = st.data_editor(_vars_input, num_rows="dynamic", use_container_width=True, key=f"{key_prefix}_vars_editor")
                st.session_state[f"{key_prefix}_other_vars"] = ensure_df(df_vars, ["Name", "Value"]).to_dict(orient="records")
                others_var_sum = float(ensure_df(df_vars, ["Name", "Value"])['Value'].fillna(0).sum()) + float(labor_var_per_unit)

                fixed_default = st.session_state.get("cmp_fixed_per_unit", st.session_state.get("fixed_per_unit", 0.0))
                fixed_per_unit_used = st.number_input(
                    f"Fixed allocation ({per_unit(UNIT)})",
                    value=float(fixed_default),
                    min_value=0.0,
                    step=0.05,
                    key=f"{key_prefix}_fixed_unit",
                )

                # Precificação
                st.markdown("**Selling price**")
                p1, p2, p3, p4, p5 = st.columns(5)
                selling_price = p1.number_input(f"Price {per_unit(UNIT)}", value=0.0, min_value=0.0, step=0.10, key=f"{key_prefix}_price")
                margin_pct    = p2.number_input("Target margin (%)", value=20.0, min_value=0.0, step=0.5, key=f"{key_prefix}_margin")
                tax_pct       = p3.number_input("Taxes (%)", value=10.0, min_value=0.0, step=0.5, key=f"{key_prefix}_tax")
                terms_pct     = p4.number_input("Fees/Terms (%)", value=2.10, min_value=0.0, step=0.05, key=f"{key_prefix}_terms")
                round_step    = float(p5.selectbox("Round to", ["0.01", "0.05", "0.10"], index=1, key=f"{key_prefix}_round"))

                submitted = st.form_submit_button(f"Calculate production — {label}", type="primary")

            result_payload = None
            if submitted:
                try:
                    # 1) monta mapa de consumo, roda simulate() (como você já faz)
                    mlmap_use = apply_consumption_source(
                        xml_bytes,
                        st.session_state.get(f"{key_prefix}_cons_source", "XML (exact)"),
                        st.session_state[state_key_mode],
                        {
                            "fast": {"color": st.session_state.get("single_mul_fc", 100.0) / 100.0,
                                     # Fast — White fixed at 100%
                                     "white": 1.00,
                                     "fof": st.session_state.get("single_mul_ff", 100.0) / 100.0},
                            "standard": {"color": st.session_state.get("single_mul_sc", 100.0) / 100.0,
                                         "white": st.session_state.get("single_mul_sw", 100.0) / 100.0,
                                         "fof": st.session_state.get("single_mul_sf", 100.0) / 100.0},
                            "saturation": {"color": st.session_state.get("single_mul_tc", 100.0) / 100.0,
                                           "white": st.session_state.get("single_mul_tw", 100.0) / 100.0,
                                           "fof": st.session_state.get("single_mul_tf", 100.0) / 100.0},
                        },
                        st.session_state.get(f"{key_prefix}_man_c", 0.0),
                        st.session_state.get(f"{key_prefix}_man_w", 0.0),
                        st.session_state.get(f"{key_prefix}_man_f", 0.0),
                    )
                    _mk2 = st.session_state.get(state_key_mode, mode_sel)
                    if _mk2 not in PRINT_MODES:
                        _mk2 = mode_sel
                    speed = PRINT_MODES.get(_mk2, {}).get("speed", 0.0)
                    res = simulate(
                        UNIT,
                        float(st.session_state.get(f"{key_prefix}_width_m", w_xml_def)),
                        float(st.session_state.get(f"{key_prefix}_length_m", h_xml_def)),
                        float(st.session_state.get(f"{key_prefix}_waste", 2.0)),
                        speed,
                        mlmap_use,
                        float(st.session_state.get("cmp_ink_c", DEFAULTS["ink_color_per_l"])),
                        float(st.session_state.get("cmp_ink_w", DEFAULTS["ink_white_per_l"])),
                        float(st.session_state.get("cmp_fof", DEFAULTS["fof_per_l"])),
                        float(st.session_state.get("cmp_fabric", DEFAULTS["fabric_per_unit"])),
                        float(ensure_df(st.session_state.get(f"{key_prefix}_other_vars", [{"Name":"—","Value":0.0}]), ["Name","Value"])["Value"].fillna(0).sum()) + float(st.session_state.get(f"{key_prefix}_lab_h", 0.0)) / max(1e-9, speed),
                        0.0,
                        float(st.session_state.get(f"{key_prefix}_fixed_unit", st.session_state.get("cmp_fixed_per_unit", st.session_state.get("fixed_per_unit", 0.0)))),
                    )

                    qty = max(1e-9, float(res.get("qty_units", 0.0)))
                    ink_total   = float(res.get("cost_ink", 0.0))
                    fabric_cost = fabric_total(res)
                    other_var   = float(res.get("cost_other", 0.0))
                    fixed_cost  = float(res.get("cost_fixed", 0.0))
                    total_cost  = float(res.get("total_cost", 0.0))
                    variable_total = ink_total + fabric_cost + other_var
                    variable_per_unit = variable_total / qty
                    fixed_per_unit_card = fixed_cost / qty if qty > 0 else 0.0
                    cost_unit_calc = total_cost / qty

                    suggested_price = price_round(
                        cost_unit_calc + cost_unit_calc * (st.session_state.get(f"{key_prefix}_margin", 20.0) / 100.0) + cost_unit_calc * (st.session_state.get(f"{key_prefix}_tax", 10.0) / 100.0),
                        float(st.session_state.get(f"{key_prefix}_round", 0.05)),
                    )
                    suggested_price = price_round(suggested_price + suggested_price * (st.session_state.get(f"{key_prefix}_terms", 2.10) / 100.0), float(st.session_state.get(f"{key_prefix}_round", 0.05)))
                    effective_price = st.session_state.get(f"{key_prefix}_price", 0.0) if st.session_state.get(f"{key_prefix}_price", 0.0) > 0 else suggested_price

                    # 2) monta painéis e SALVA no estado
                    rows_tot, rows_unit = build_cost_rows_from_sim(res, unit_lbl, SYM, FX, price=effective_price)
                    st.session_state[f"{key_prefix}_panels"] = {
                        "rows_tot": rows_tot,
                        "rows_unit": rows_unit,
                        "unit_lbl": unit_lbl,
                        "kpis": {
                            "qty": qty,
                            "area_waste_m2": res.get("area_waste_m2", 0.0),
                            "total_ml_per_unit": res.get("total_ml_per_unit", 0.0),
                        },
                        "be": {
                            "variable_per_unit": variable_per_unit,
                            "effective_price": effective_price,
                        },
                    }
                    result_payload = res
                except Exception as e:
                    st.error(f"Simulation error ({label}): {e}")

            # 3) SEMPRE mostrar o último resultado calculado para este job
            saved = st.session_state.get(f"{key_prefix}_panels")
            if saved:
                k = saved.get("kpis", {})
                ctx = st.columns(3)
                ctx[0].metric(f"Quantity ({unit_lbl})", f"{k.get('qty',0):,.2f}")
                ctx[1].metric("Area w/ waste (m²)", f"{k.get('area_waste_m2',0):,.2f}")
                ctx[2].metric(f"Total consumption (ml/{unit_lbl})", f"{k.get('total_ml_per_unit',0):,.2f}")

                left, right = st.columns(2)
                with left:
                    render_info_table("Total ($)", saved["rows_tot"])
                with right:
                    render_info_table(f"Per unit (/{saved.get('unit_lbl', unit_lbl)})", saved["rows_unit"])

                # BEP reusando o que já foi salvo
                fix_month_total = float(st.session_state.get("fix_total_month", 0.0))
                if fix_month_total > 0:
                    be = saved.get("be", {})
                    fig_be = breakeven_figure(
                        price_u=be.get("effective_price", 0.0),
                        variable_u=be.get("variable_per_unit", 0.0),
                        fixed_month=fix_month_total,
                        unit_lbl=unit_lbl,
                        sym=SYM,
                        fx=FX,
                        title=f"Break-even — {label}",
                    )
                    st.plotly_chart(fig_be, use_container_width=True, key=f"{key_prefix}_be_chart", config=plotly_cfg())

            return result_payload

        with colA2:
            _resA = job_panel("Job A", xmlA_bytes, wA_xml, hA_xml, mlm2A, "cmpA")
        with colB2:
            _resB = job_panel("Job B", xmlB_bytes, wB_xml, hB_xml, mlm2B, "cmpB")
            st.markdown('</div>', unsafe_allow_html=True)

# ===========================
# BATCH — multiple files (ZIPs)
# ===========================
def ui_batch():
    section("Batch — multiple files", "Upload multiple ZIPs and get a per-job summary, aggregated channels and PDFs.")

    ups = st.file_uploader("Jobs (ZIP) — multiple", type="zip", accept_multiple_files=True, key="batch_up")
    if not ups:
        st.info("Upload at least one ZIP to continue.")
        return

    # Shared controls
    st.markdown("---")
    st.markdown("**Consumption source (ml/m²)**")
    cons_src = st.radio(
        "Consumption source (applies to all files)",
        ["XML (exact)", "XML + mode multiplier (%)"],
        index=0,
        key="batch_cons_src",
        horizontal=True,
    )
    if cons_src.startswith("XML + mode"):
        st.info("Using XML + mode multipliers. Each job's inferred mode will apply Color/White/FOF factors.")
        render_mode_multiplier_controls(use_expander=False, show_presets=True, key_prefix="batch", sync_to_shared=True)

    st.markdown("---")

    # Process files
    rows = []
    agg_map = {}
    agg_pix = {}
    per_file_maps = []  # keep for PDFs
    per_file_names = []
    per_file_totals_ml = []
    per_file_totals_pxK = []
    factors = get_mode_factors_from_state()

    total_files = len(ups)
    progress = st.progress(0, text="Processing files…")
    for i, up in enumerate(ups, start=1):
        with st.spinner(f"Processing {getattr(up, 'name', 'job.zip')} ({i}/{total_files})"):
            try:
                zbytes = up.getvalue()
            except Exception:
                zbytes = up.read() if hasattr(up, 'read') else None
            name = getattr(up, 'name', 'job.zip')
        cache_ns = f"batch_{name}"
        files, xmls, jpgs, tifs, _ = read_zip_listing(zbytes, cache_ns=cache_ns)
        if not xmls:
            rows.append({"File": name, "Status": "No XML in ZIP"})
            continue
        # Pick XML: prefer first with colors
        picked_ml = None; picked_xml = xmls[0]
        for xp in xmls:
            raw = read_bytes_from_zip(zbytes, xp, cache_ns=cache_ns)
            mm = ml_per_m2_from_xml_bytes(raw)
            if has_color_channels(mm):
                picked_ml = mm; picked_xml = xp; break
        if picked_ml is None:
            picked_ml = ml_per_m2_from_xml_bytes(read_bytes_from_zip(zbytes, picked_xml, cache_ns=cache_ns))
        xml_bytes = read_bytes_from_zip(zbytes, picked_xml, cache_ns=cache_ns)

        # Apply source/multipliers
        mode_auto = infer_mode_from_xml(xml_bytes)
        mlmap_use = apply_consumption_source(
            xml_bytes,
            cons_src,
            mode_auto,
            factors,
            0.0, 0.0, 0.0,
        ) if cons_src else picked_ml

        # Summaries (ml/m²) + original dimensions
        total = total_ml_per_m2_from_map(mlmap_use)
        cml = wml = fml = 0.0
        for k,v in (mlmap_use or {}).items():
            low = (k or '').strip().lower()
            if low in CHANNELS_WHITE: wml += float(v)
            elif low in CHANNELS_FOF: fml += float(v)
            else: cml += float(v)
        try:
            w_xml_def, h_xml_def, _area_xml = get_xml_dims_m(xml_bytes)
        except Exception:
            w_xml_def = h_xml_def = 0.0

        # Aggregate per-channel for overall chart
        for ch, val in (mlmap_use or {}).items():
            agg_map[ch] = agg_map.get(ch, 0.0) + float(val)

        rows.append({
            "File": name,
            "Inferred mode": mode_auto,
            "Width (m)": round(float(w_xml_def), 3),
            "Length (m)": round(float(h_xml_def), 3),
            "Custom width (m)": round(float(w_xml_def), 3),
            "Custom length (m)": round(float(h_xml_def), 3),
            "Total (ml/m²)": round(total, 3),
            "Color (ml/m²)": round(cml, 3),
            "White (ml/m²)": round(wml, 3),
            "FOF (ml/m²)": round(fml, 3),
            "White %": round(0 if total==0 else wml/total*100.0, 1),
            "FOF %": round(0 if total==0 else fml/total*100.0, 1),
            "Status": "OK",
        })

        per_file_maps.append((name, zbytes, dict(mlmap_use or {})))

        # Aggregate fire pixels (if available)
        try:
            px_map = fire_pixels_map_from_xml_bytes(xml_bytes) or {}
        except Exception:
            px_map = {}
        px_total_k = 0.0
        for ch, val in (px_map or {}).items():
            agg_pix[ch] = agg_pix.get(ch, 0.0) + float(val)
            px_total_k += float(val) / 1000.0

        # Per-file totals
        per_file_names.append(name)
        per_file_totals_ml.append(float(total))
        per_file_totals_pxK.append(float(px_total_k))
        # Update progress
        try:
            progress.progress(i/total_files)
        except Exception:
            pass

    # Show table
    st.markdown("**Summary (per file)**")
    if rows:
        df = pd.DataFrame(rows)
        # Remove XML column (if present) and present editable custom sizes
        ordered_cols = [c for c in [
            "File","Inferred mode","Width (m)","Length (m)",
            "Custom width (m)","Custom length (m)",
            "Total (ml/m²)","Color (ml/m²)","White (ml/m²)","FOF (ml/m²)","White %","FOF %","Status"
        ] if c in df.columns]
        df = df[ordered_cols]
        edited = st.data_editor(
            df,
            use_container_width=True,
            num_rows="fixed",
            key="batch_summary_editor",
            column_config=ml_table_column_config(),
        )
        # Compute area and ink using edited custom sizes
        try:
            out = edited.copy()
            cw = pd.to_numeric(edited.get("Custom width (m)", 0), errors='coerce').fillna(0.0)
            cl = pd.to_numeric(edited.get("Custom length (m)", 0), errors='coerce').fillna(0.0)
            mlm2 = pd.to_numeric(edited.get("Total (ml/m²)", 0), errors='coerce').fillna(0.0)
            out["Area (m²)"] = cw * cl
            out["Ink (ml)"] = mlm2 * out["Area (m²)"]
            # Linear consumption: ml/m = (ml/m²) × width (m)
            out["Linear (ml/m)"] = mlm2 * cw
            out["Linear total (ml)"] = out["Linear (ml/m)"] * cl
        except Exception:
            out = edited
        st.dataframe(out, use_container_width=True, hide_index=True, column_config=ml_table_column_config())
        csv = out.to_csv(index=False).encode('utf-8')
        st.download_button("Download summary CSV", data=csv, file_name="batch_summary.csv", mime="text/csv", key="batch_summary_csv")
    else:
        st.info("No valid files to summarize.")

    # Aggregated charts + CSV
    if agg_map or agg_pix:
        st.markdown("---")
        st.markdown("**Aggregated charts**")
        # Help glossary under aggregated charts
        render_help_glossary()
        ach1, ach2, ach3, ach4 = st.columns([1,1,1,1])
        show_ml = ach1.checkbox("Show ml/m²", value=st.session_state.get("batch_show_ml", True), key="batch_show_ml")
        show_px = ach2.checkbox("Show pixels (K)", value=st.session_state.get("batch_show_px", True), key="batch_show_px")
        show_shares = ach3.checkbox("Show % shares", value=st.session_state.get("batch_show_shares", True), key="batch_show_shares")
        show_vals   = ach4.checkbox("Show value labels", value=st.session_state.get("batch_show_values", False), key="batch_show_values")

        # Order channels using the same preference as A×B helpers
        try:
            channels_ordered = safe_union_channels_sorted(agg_map, agg_pix)
        except Exception:
            channels_ordered = sorted(set(list((agg_map or {}).keys()) + list((agg_pix or {}).keys())))

        if show_ml and agg_map:
            items = [(c, float(agg_map.get(c, 0.0))) for c in channels_ordered]
            # Keep original order, not resorting by value
            labels = [c for c,_ in items]
            values = [v for _,v in items]
            total_ml = sum(values) if values else 0.0
            shares = [ (v/total_ml*100.0 if total_ml>0 else 0.0) for v in values ]
            # Auto text position: inside if share >= 12%, else outside
            pos = [ ('inside' if s >= 12.0 else 'outside') for s in shares ]
            # Text color: white when inside bars, otherwise dark
            txt_colors = [ ('#FFFFFF' if p=='inside' else '#111827') for p in pos ]
            decimals = 0 if len(labels) >= 10 else 1
            if show_vals:
                txt = [f"{v:.2f}" for v in values]
            elif show_shares:
                txt = [ (f"{s:.0f}%" if decimals==0 else f"{s:.1f}%") for s in shares ]
            else:
                txt = None
            colors = [CHANNEL_COLORS.get(k, '#888') for k in labels]
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=labels, y=values,
                marker=dict(color=colors),
                text=txt,
                textposition=pos if txt else None,
                textfont=dict(color=txt_colors) if txt else None,
                insidetextanchor='middle' if txt else None,
                cliponaxis=False if txt else None,
            ))
            fig.update_layout(template='plotly_white', height=420, margin=dict(l=10,r=10,t=40,b=10), yaxis_title='ml/m²', xaxis_title='Channel')
            st.plotly_chart(fig, use_container_width=True, key="batch_agg_ml_chart", config=plotly_cfg())

        if show_px and agg_pix:
            itemsP = [(c, float(agg_pix.get(c, 0.0))) for c in channels_ordered]
            labelsP = [c for c,_ in itemsP]
            valuesP = [v/1000.0 for _,v in itemsP]  # K pixels
            totalK = sum(valuesP) if valuesP else 0.0
            sharesP = [ (v/totalK*100.0 if totalK>0 else 0.0) for v in valuesP ]
            posP = [ ('inside' if s >= 12.0 else 'outside') for s in sharesP ]
            txt_colorsP = [ ('#FFFFFF' if p=='inside' else '#111827') for p in posP ]
            decimalsP = 0 if len(labelsP) >= 10 else 1
            if show_vals:
                txtP = [f"{v:.1f}" for v in valuesP]
            elif show_shares:
                txtP = [ (f"{s:.0f}%" if decimalsP==0 else f"{s:.1f}%") for s in sharesP ]
            else:
                txtP = None
            colorsP = [CHANNEL_COLORS.get(k, '#888') for k in labelsP]
            figP = go.Figure()
            figP.add_trace(go.Bar(
                x=labelsP, y=valuesP,
                marker=dict(color=colorsP),
                text=txtP,
                textposition=posP if txtP else None,
                textfont=dict(color=txt_colorsP) if txtP else None,
                insidetextanchor='middle' if txtP else None,
                cliponaxis=False if txtP else None,
            ))
            figP.update_layout(template='plotly_white', height=420, margin=dict(l=10,r=10,t=40,b=10), yaxis_title='K pixels', xaxis_title='Channel')
            st.plotly_chart(figP, use_container_width=True, key="batch_agg_px_chart", config=plotly_cfg())

        # Aggregated CSV (per channel)
        try:
            chs = channels_ordered
            data = []
            # Totals for share calculations
            total_ml = sum(float((agg_map or {}).get(c, 0.0)) for c in chs)
            total_pxK = sum(float((agg_pix or {}).get(c, 0.0))/1000.0 for c in chs)
            for c in chs:
                ml = float((agg_map or {}).get(c, 0.0))
                pxK = float((agg_pix or {}).get(c, 0.0)) / 1000.0
                ml_share = (ml/total_ml*100.0) if total_ml > 0 else 0.0
                px_share = (pxK/total_pxK*100.0) if total_pxK > 0 else 0.0
                data.append({
                    "Channel": c,
                    "Total (ml/m²)": round(ml, 3),
                    "ml share (%)": round(ml_share, 2),
                    "Pixels (K)": round(pxK, 3),
                    "pixels share (%)": round(px_share, 2),
                })
            if data:
                df_agg = pd.DataFrame(data)
                st.download_button(
                    "Download aggregated CSV",
                    data=df_agg.to_csv(index=False).encode('utf-8'),
                    file_name="batch_aggregated.csv",
                    mime="text/csv",
                )
        except Exception as e:
            st.info(f"Aggregated CSV not available: {e}")

        # Per-channel — grouped by file (identify who uses more of each channel)
        st.markdown("---")
        st.markdown("**Per-channel — grouped by file**")
        gb1, gb2 = st.columns(2)
        norm_share = gb1.checkbox("Normalize by channel (%)", value=st.session_state.get("batch_group_norm", False), key="batch_group_norm")
        show_heat = gb2.checkbox("Show heatmap", value=st.session_state.get("batch_group_heat", True), key="batch_group_heat")

        # Build matrix: files × channels
        file_names = [name for (name, _zb, _mm) in per_file_maps]
        values_matrix = []  # rows = files, cols = channels_ordered
        for (_name, _zb, mm) in per_file_maps:
            row = [float(mm.get(c, 0.0)) for c in channels_ordered]
            values_matrix.append(row)

        # Optionally normalize each column to 100%
        if norm_share:
            col_sums = [sum(r[j] for r in values_matrix) for j in range(len(channels_ordered))]
            norm = []
            for r in values_matrix:
                norm.append([ (0.0 if col_sums[j]==0 else r[j]/col_sums[j]*100.0) for j in range(len(channels_ordered)) ])
            values_matrix = norm

        # Grouped bars: one trace per file
        file_palette = ["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd","#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf"]
        fig_g = go.Figure()
        for i, name in enumerate(file_names):
            fig_g.add_trace(go.Bar(
                name=name,
                x=channels_ordered,
                y=values_matrix[i],
                marker=dict(color=file_palette[i % len(file_palette)]),
            ))
        fig_g.update_layout(
            template='plotly_white',
            barmode='group',
            height=460,
            margin=dict(l=10,r=10,t=40,b=10),
            yaxis_title=('%' if norm_share else 'ml/m²'),
            xaxis_title='Channel',
            legend_title='File',
        )
        st.plotly_chart(fig_g, use_container_width=True, key="batch_group_bars_chart", config=plotly_cfg())

        # Optional heatmap for a compact overview
        if show_heat:
            fig_h = go.Figure(data=go.Heatmap(
                z=values_matrix,
                x=channels_ordered,
                y=file_names,
                colorscale='Blues',
                colorbar=dict(title=('%' if norm_share else 'ml/m²'))
            ))
            fig_h.update_layout(template='plotly_white', height=460, margin=dict(l=10,r=10,t=30,b=10), xaxis_title='Channel', yaxis_title='File')
            st.plotly_chart(fig_h, use_container_width=True, key="batch_group_heatmap_chart", config=plotly_cfg())

        # CSV — per-file per-channel (wide)
        try:
            df_wide = pd.DataFrame(values_matrix, columns=channels_ordered)
            df_wide.insert(0, 'File', file_names)
            st.download_button(
                "Download per-file×channel CSV",
                data=df_wide.to_csv(index=False).encode('utf-8'),
                file_name='batch_perfile_perchannel.csv',
                mime='text/csv',
            )
        except Exception as e:
            st.info(f"Per-file×channel CSV not available: {e}")

    # PDFs (ZIP)
    if per_file_maps:
        try:
            with st.spinner("Building PDFs (ZIP)…"):
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, 'w', compression=zipfile.ZIP_DEFLATED) as zpf:
                    for name, zbytes, mlm in per_file_maps:
                        items = sorted((mlm or {}).items(), key=lambda kv: kv[1], reverse=True)
                        chs = [k for k,_ in items]
                        ys  = [float(v) for _,v in items]
                        pdf = build_single_pdf_matplotlib(
                            chs, ys, mlm,
                            label=name, z_bytes=zbytes,
                            selected_channel='Preview',
                            show_comp=True,
                            preview_size={"Small":"S","Medium":"M","Large":"L"}.get(st.session_state.get("cmp_pdf_size","Medium"),"M"),
                            show_totals=True,
                        )
                        safe_name = _slug(name) or 'job'
                        zpf.writestr(f"{safe_name}.pdf", pdf)
            st.download_button("Download PDFs (ZIP)", data=zip_buf.getvalue(), file_name="batch_pdfs.zip", mime="application/zip")
        except Exception as e:
            st.info(f"PDF ZIP not available: {e}")

    try:
        progress.empty()
    except Exception:
        pass

    # Per-file bars (totals)
    if per_file_names:
        if "batch_show_perfile_ml" not in st.session_state:
            st.session_state["batch_show_perfile_ml"] = True
        if "batch_show_perfile_px" not in st.session_state:
            st.session_state["batch_show_perfile_px"] = True
        pf1, pf2 = st.columns(2)
        pf1.checkbox("Show per-file ml/m² totals", key="batch_show_perfile_ml")
        pf2.checkbox("Show per-file pixels totals (K)", key="batch_show_perfile_px")
        st.markdown("---")
        st.markdown("**Per file — totals**")
        # ml/m² per file
        try:
            tot_ml = sum(per_file_totals_ml) if per_file_totals_ml else 0.0
            sharesF = [(v/tot_ml*100.0 if tot_ml>0 else 0.0) for v in per_file_totals_ml]
            decimals = 0 if len(per_file_names) >= 12 else 1
            txt = [(f"{s:.0f}%" if decimals==0 else f"{s:.1f}%") for s in sharesF]
            if st.session_state.get("batch_show_perfile_ml", True):
                figF = go.Figure()
                figF.add_trace(go.Bar(
                    x=per_file_names,
                    y=per_file_totals_ml,
                    marker=dict(color="#2563eb"),
                    text=txt,
                    textposition="outside",
                    cliponaxis=False,
                ))
                figF.update_layout(template='plotly_white', height=440, margin=dict(l=10,r=10,t=40,b=110), yaxis_title='ml/m²', xaxis_title='File', xaxis_tickangle=-30)
                st.plotly_chart(figF, use_container_width=True, key="batch_perfile_ml_chart", config=plotly_cfg())
        except Exception as e:
            st.info(f"Per-file ml/m² chart not available: {e}")

        # Pixels per file (K)
        try:
            tot_pk = sum(per_file_totals_pxK) if per_file_totals_pxK else 0.0
            sharesPk = [(v/tot_pk*100.0 if tot_pk>0 else 0.0) for v in per_file_totals_pxK]
            decimalsP = 0 if len(per_file_names) >= 12 else 1
            txtP = [(f"{s:.0f}%" if decimalsP==0 else f"{s:.1f}%") for s in sharesPk]
            if st.session_state.get("batch_show_perfile_px", True):
                figFP = go.Figure()
                figFP.add_trace(go.Bar(
                    x=per_file_names,
                    y=per_file_totals_pxK,
                    marker=dict(color="#10b981"),
                    text=txtP,
                    textposition="outside",
                    cliponaxis=False,
                ))
                figFP.update_layout(template='plotly_white', height=440, margin=dict(l=10,r=10,t=40,b=110), yaxis_title='K pixels', xaxis_title='File', xaxis_tickangle=-30)
                st.plotly_chart(figFP, use_container_width=True, key="batch_perfile_px_chart", config=plotly_cfg())
        except Exception as e:
            st.info(f"Per-file pixels chart not available: {e}")

# =========================
# Router: call UI for selected flow
# (moved to end so all UIs are defined before being called)
# =========================
try:
    # Sidebar tools (reset & clear cache)
    render_tools_sidebar()
    sel = (flow or st.session_state.get("workflow_selector") or "")
except Exception:
    sel = ""

sel_low = str(sel).lower()
if "single" in sel_low:
    ui_single()
elif "compare" in sel_low or "a×b" in sel_low or "axb" in sel_low:
    ui_compare_option_b()
elif "sales" in sel_low or "quote" in sel_low:
    try:
        ui_sales_quick_quote()
    except NameError:
        st.info("Sales — Quick quote: coming soon.")
else: 
    # Batch flow (if implemented)
    try:
        ui_batch()  # defined elsewhere
    except NameError:
        st.info("Batch — multiple files: em breve.")