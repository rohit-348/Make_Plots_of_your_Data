"""
PlantWatch - Full-Canvas Multi-Tag Trend Explorer with On-Graph Time Controls
Built by Rohit Tiwaskar

Install:  python -m pip install "streamlit>=1.40" plotly pandas numpy openpyxl
Run:      python -m streamlit run trends.py
"""
from __future__ import annotations

import html
import inspect
import io
import warnings

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="PlantWatch - Trend Explorer | Built by Rohit Tiwaskar",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
AUTHOR_NAME = "Rohit Tiwaskar"

PALETTE = [
    "#5367FF",  # Indigo Blue
    "#00B386",  # Mint Teal
    "#F59E0B",  # Amber
    "#EC4899",  # Pink
    "#8B5CF6",  # Violet
    "#06B6D4",  # Cyan
    "#EF4444",  # Coral Red
    "#10B981",  # Emerald
]
SLATE = "#44475B"
GREY = "#7C7E8C"
BORDER = "#ECEDEF"
FAINT = "#F4F5F7"

FILL_MODES = ["Linear interpolation", "Forward fill", "None (show gaps)"]
CHART_TYPES = [
    "Line",
    "Smooth Line (Spline)",
    "Line with Markers",
    "Area (Filled)",
    "Scatter (Points Only)",
    "Step (Hold Last Value)",
    "Column / Bar",
]


def _stretch(fn) -> dict:
    """Full-width kwarg that works on old and new Streamlit versions."""
    try:
        if "width" in inspect.signature(fn).parameters:
            return {"width": "stretch"}
    except (TypeError, ValueError):
        pass
    return {"use_container_width": True}


BTN_KW = _stretch(st.button)
PLOT_KW = _stretch(st.plotly_chart)

# --------------------------------------------------------------------------- #
# Styling (Fixed Viewport — Full Canvas + Collapsible Drawer)
# --------------------------------------------------------------------------- #
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, .stApp, .stApp p, .stApp label, .stApp button, .stApp input, .stApp textarea,
.stApp h1, .stApp h2, .stApp h3, .stApp [data-testid="stMarkdownContainer"] * {
  font-family: 'Inter', 'Roboto', -apple-system, 'Segoe UI', sans-serif !important;
}

/* Lock outer viewport to prevent page scrolling */
html, body, .stApp {
  height: 100vh !important;
  overflow: hidden !important;
  background: #fff !important;
  color: #44475B;
}
[data-testid="stAppViewContainer"], section.main {
  height: 100vh !important;
  overflow: hidden !important;
}
/* Completely hide left sidebar & collapse control */
[data-testid="stSidebar"], [data-testid="collapsedControl"], [data-testid="stHeader"] {
  display: none !important;
}
#MainMenu, footer, [data-testid="stDecoration"], [data-testid="stAppDeployButton"] { display: none !important; }

.block-container {
  padding: 0.6rem 1.35rem 0.6rem 1.35rem !important;
  max-width: 100% !important;
  height: 100vh !important;
}

/* Brand & Author Signature */
.gw-brand-wrap {
  display: flex;
  flex-direction: column;
  justify-content: center;
  line-height: 1.1;
  min-height: 2.35rem;
}
.gw-brand {
  display: flex;
  align-items: center;
  gap: .45rem;
  font-weight: 700;
  font-size: 1.12rem;
  color: #44475B;
}
.gw-brand .dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #5367FF;
  display: inline-block;
  flex-shrink: 0;
}
.gw-author {
  font-size: 0.68rem;
  font-weight: 500;
  color: #7C7E8C;
  padding-left: 0.95rem;
  margin-top: 1px;
  white-space: nowrap;
}
.gw-author b {
  color: #5367FF;
  font-weight: 600;
}

/* Unified Live-Search Multiselect Dropdown */
div[data-baseweb="select"] > div {
  border-radius: 10px !important;
  background: #F4F5F7 !important;
  border: 1px solid transparent !important;
  min-height: 2.35rem !important;
  transition: all 0.15s ease;
}
div[data-baseweb="select"] > div:focus-within {
  background: #fff !important;
  border-color: #5367FF !important;
  box-shadow: 0 0 0 2px rgba(83, 103, 255, 0.12) !important;
}
span[data-baseweb="tag"] {
  background-color: #EEF0FF !important;
  color: #44475B !important;
  border-radius: 6px !important;
  font-weight: 600 !important;
  font-size: 0.8rem !important;
}
ul[data-baseweb="menu"] {
  border-radius: 10px !important;
  border: 1px solid #ECEDEF !important;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08) !important;
}
[data-testid="stExpander"] details { border:1px solid #ECEDEF; border-radius:8px; background:#FAFAFB; }
[data-testid="stExpander"] summary { padding: .35rem .75rem !important; font-size:.83rem !important; font-weight:600 !important; }

/* Buttons, Popover & Drawer Toggle */
.stApp .stButton > button,
.stApp [data-testid="stPopover"] > button {
  border-radius:10px; border:1px solid #ECEDEF; background:#fff; color:#44475B;
  font-weight:600; padding:.3rem .75rem; font-size:.82rem; min-height:2.35rem;
}
.stApp .stButton > button:hover,
.stApp [data-testid="stPopover"] > button:hover {
  border-color:#5367FF; color:#5367FF; background:#F8F9FF;
}
.stApp button[data-testid="stBaseButton-primary"] {
  background:#5367FF !important; color:#fff !important; border-color:#5367FF !important;
}

/* Active Trends Legend Strip */
.gw-legend-strip {
  display:flex; flex-wrap:wrap; align-items:center; gap:.55rem;
  margin: .2rem 0 .1rem 0; min-height: 1.95rem;
}
.gw-leg-item {
  display:inline-flex; align-items:center; gap:.45rem;
  border:1px solid #ECEDEF; background:#FAFAFB; border-radius:8px;
  padding: 3px 10px; font-size:.8rem; color:#44475B;
}
.gw-leg-dot { width:9px; height:9px; border-radius:50%; display:inline-block; flex-shrink:0; }
.gw-leg-name { font-weight:600; color:#44475B; }
.gw-leg-stat { color:#7C7E8C; font-size:.76rem; }
.gw-leg-stat b { color:#44475B; font-weight:600; }
.gw-window-badge {
  margin-left:auto; font-size:.78rem; color:#7C7E8C;
}

/* Right Collapsible Drawer Styling */
.gw-pane-title {
  font-size:.9rem; font-weight:700; color:#44475B;
  margin-bottom:.3rem; padding-bottom:.2rem; border-bottom:1px solid #ECEDEF;
}
.gw-grid-pane { display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:.35rem; margin-top:.35rem; }
.gw-card { border:1px solid #ECEDEF; border-radius:8px; padding:6px 9px; background:#fff; }
.gw-label { font-size:.69rem; color:#7C7E8C; margin-bottom:.08rem; }
.gw-value { font-size:.95rem; font-weight:600; color:#44475B; line-height:1.15; }
.gw-sub { font-size:.67rem; color:#7C7E8C; margin-top:.1rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.gw-sub b { color:#44475B; font-weight:600; }

/* Compact Operating Range Bar */
.gw-range-box { border:1px solid #ECEDEF; border-radius:8px; padding:7px 10px; margin-top:.35rem; background:#fff; }
.gw-range-row { display:flex; align-items:flex-end; gap:.65rem; }
.gw-range-end { min-width:60px; }
.gw-range-end.right { text-align:right; }
.gw-range-end .gw-value { font-size:.86rem; }
.gw-range-mid { position:relative; flex:1; height:2.1rem; }
.gw-track { position:absolute; left:0; right:0; bottom:.35rem; height:4px; border-radius:4px;
  background:linear-gradient(90deg, rgba(83,103,255,.25), rgba(83,103,255,.65)); }
.gw-pointer { position:absolute; top:0; transform:translateX(-50%); display:flex; flex-direction:column; align-items:center; }
.gw-bubble { font-size:.68rem; font-weight:600; color:#44475B; background:#fff; border:1px solid #ECEDEF;
  border-radius:5px; padding:0px 5px; white-space:nowrap; }
.gw-tri { width:0; height:0; border-left:4px solid transparent; border-right:4px solid transparent; border-top:5px solid #5367FF; margin-top:1px; }
</style>
"""


# --------------------------------------------------------------------------- #
# Formatting helpers
# --------------------------------------------------------------------------- #
def fmt(v, d: int = 2) -> str:
    if v is None or (isinstance(v, (float, np.floating)) and (np.isnan(v) or np.isinf(v))):
        return "—"
    a = abs(float(v))
    if a == 0 or a >= 1:
        return f"{v:,.{d}f}"
    if a >= 0.01:
        return f"{v:,.4f}"
    return f"{v:.3e}"


def fmt_ts(t) -> str:
    return pd.Timestamp(t).strftime("%d %b %Y, %H:%M")


def fmt_ts_short(t) -> str:
    return pd.Timestamp(t).strftime("%d %b %H:%M")


def esc(x) -> str:
    return html.escape(str(x))


# --------------------------------------------------------------------------- #
# Data layer
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def sample_raw() -> pd.DataFrame:
    """Synthetic plant data (8 tags, 400 days, 30-min samples, a few gaps)."""
    rng = np.random.default_rng(42)
    end = pd.Timestamp.now().floor("30min")
    idx = pd.date_range(end=end, periods=48 * 400, freq="30min")
    n = len(idx)
    t = np.arange(n)

    specs = [
        ("FT-101 Feed Flow", 420.0, 35.0, 18.0, 3.0, 0.05),
        ("TI-203 Reactor Temp", 182.0, -9.0, 2.5, 0.35, 0.04),
        ("PT-305 Header Pressure", 12.4, 0.9, 0.25, 0.05, 0.06),
        ("LI-410 Tank Level", 58.0, -6.0, 7.0, 0.9, 0.03),
        ("AI-512 Outlet pH", 7.1, 0.35, 0.12, 0.03, 0.08),
        ("VT-620 Vibration", 2.4, 1.3, 0.2, 0.08, 0.05),
        ("PWR-701 Power kW", 640.0, -45.0, 40.0, 6.0, 0.05),
        ("CT-808 Cooling Water Temp", 31.0, 2.4, 3.2, 0.3, 0.05),
    ]
    data = {"Timestamp": idx}
    for k, (name, base, drift, amp, sigma, theta) in enumerate(specs):
        eps = rng.normal(0, sigma, n)
        ou = np.zeros(n)
        for i in range(1, n):
            ou[i] = ou[i - 1] * (1 - theta) + eps[i]
        vals = (
            base
            + drift * t / n
            + amp * np.sin(2 * np.pi * t / 48 + k)
            + 0.4 * amp * np.sin(2 * np.pi * t / (48 * 7))
            + ou
        )
        for pos in rng.integers(500, n - 100, 6):
            width = int(rng.integers(6, 30))
            vals[pos:pos + width] += rng.choice([-1, 1]) * sigma * rng.uniform(6, 14)
        if "Level" in name:
            vals = np.clip(vals, 2, 98)
        s = pd.Series(vals)
        s[rng.random(n) < 0.004] = np.nan
        if k == 1:
            s.iloc[n - 600:n - 588] = np.nan
        data[name] = s.round(3).values
    return pd.DataFrame(data)


@st.cache_data(show_spinner=False)
def list_sheets(file_bytes: bytes) -> list[str]:
    return pd.ExcelFile(io.BytesIO(file_bytes)).sheet_names


@st.cache_data(show_spinner="Reading file…")
def read_table(file_bytes: bytes, filename: str, sheet: str | None) -> pd.DataFrame:
    bio = io.BytesIO(file_bytes)
    if filename.lower().endswith((".xlsx", ".xlsm")):
        df = pd.read_excel(bio, sheet_name=sheet if sheet is not None else 0)
    else:
        try:
            df = pd.read_csv(bio, low_memory=False)
        except Exception:
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), sep=None, engine="python")
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(file_bytes), low_memory=False, encoding="latin-1")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def detect_ts(raw: pd.DataFrame) -> str:
    for c in raw.columns:
        if pd.api.types.is_datetime64_any_dtype(raw[c]):
            return c
    for c in raw.columns:
        if any(h in str(c).lower() for h in ("timestamp", "datetime", "date", "time")):
            return c
    for c in raw.columns:
        if raw[c].dtype == object:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                p = pd.to_datetime(raw[c].head(50), errors="coerce")
            if p.notna().mean() > 0.9:
                return c
    return raw.columns[0]


def parse_ts(s: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(s):
        ts = s
    elif pd.api.types.is_numeric_dtype(s):
        med = s.dropna().median() if s.notna().any() else 0
        if 20000 < med < 80000:
            ts = pd.to_datetime(s, unit="D", origin="1899-12-30", errors="coerce")
        else:
            ts = pd.to_datetime(s, errors="coerce")
    else:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ts = pd.to_datetime(s, errors="coerce")
            if ts.isna().mean() > 0.2:
                try:
                    ts2 = pd.to_datetime(s, errors="coerce", format="mixed")
                    if ts2.isna().sum() < ts.isna().sum():
                        ts = ts2
                except (ValueError, TypeError):
                    pass
    if getattr(ts.dt, "tz", None) is not None:
        ts = ts.dt.tz_localize(None)
    return ts


@st.cache_data(show_spinner="Preparing data…")
def prepare(raw: pd.DataFrame, ts_col: str, fill_mode: str) -> pd.DataFrame:
    ts = parse_ts(raw[ts_col])
    nums = {}
    for c in raw.columns:
        if c == ts_col:
            continue
        col = raw[c]
        if pd.api.types.is_datetime64_any_dtype(col) or pd.api.types.is_bool_dtype(col):
            continue
        num = pd.to_numeric(col, errors="coerce")
        if num.notna().sum() >= 2 and num.notna().mean() >= 0.5:
            nums[c] = num.astype(float)
    if not nums:
        return pd.DataFrame()
    out = pd.DataFrame(nums)
    out.index = pd.DatetimeIndex(ts)
    out = out[~out.index.isna()]
    if out.empty:
        return out
    out = out.groupby(level=0).mean().sort_index()
    if fill_mode.startswith("Linear"):
        out = out.interpolate(method="time", limit_direction="both")
    elif fill_mode.startswith("Forward"):
        out = out.ffill().bfill()
    return out


def downsample(s: pd.Series, max_pts: int = 15000) -> pd.Series:
    n = len(s)
    if n <= max_pts:
        return s
    keep = [np.linspace(0, n - 1, max_pts).astype(int)]
    if s.notna().any():
        keep.append(np.array([int(np.nanargmin(s.values)), int(np.nanargmax(s.values))]))
    return s.iloc[np.unique(np.concatenate(keep))]


def toggle_drawer() -> None:
    st.session_state["drawer_open"] = not st.session_state.get("drawer_open", False)


# Synchronized Y-axis state callbacks (On-Chart Merge Toggle <-> Drawer Separate Toggle)
def _on_merge_toggle() -> None:
    merged = st.session_state.get("merge_y_axes_quick", False)
    st.session_state["separate_axes"] = not merged


def _on_separate_toggle() -> None:
    sep = st.session_state.get("separate_axes", True)
    st.session_state["merge_y_axes_quick"] = not sep


# --------------------------------------------------------------------------- #
# Chart + components
# --------------------------------------------------------------------------- #
def rgba(hex_color: str, a: float) -> str:
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{a})"


def _scatter_style(chart_type: str, color: str, n_pts: int) -> dict:
    """Map Excel-style chart selection to Plotly Scatter parameters."""
    mk_size = 6 if n_pts <= 150 else (4.5 if n_pts <= 600 else 3.2)

    if chart_type == "Smooth Line (Spline)":
        return dict(mode="lines", line=dict(color=color, width=2.2, shape="spline", smoothing=0.85))
    if chart_type == "Line with Markers":
        return dict(
            mode="lines+markers",
            line=dict(color=color, width=1.8),
            marker=dict(size=mk_size, color=color, line=dict(color="#fff", width=0.8)),
        )
    if chart_type == "Area (Filled)":
        return dict(
            mode="lines",
            line=dict(color=color, width=2.0),
            fill="tozeroy",
            fillcolor=rgba(color, 0.16),
        )
    if chart_type == "Scatter (Points Only)":
        return dict(
            mode="markers",
            marker=dict(size=mk_size + 1.2, color=color, opacity=0.85),
        )
    if chart_type == "Step (Hold Last Value)":
        return dict(mode="lines", line=dict(color=color, width=2.0, shape="hv"))
    return dict(mode="lines", line=dict(color=color, width=2.1))


def build_multi_figure(
    df: pd.DataFrame,
    selected_tags: list[str],
    show_mean: bool,
    separate_axes: bool,
    chart_type: str,
    chart_height: int,
) -> go.Figure:
    fig = go.Figure()
    n_tags = len(selected_tags)
    is_bar = chart_type == "Column / Bar"
    max_pts = 500 if is_bar else 15000

    if separate_axes and n_tags > 1:
        axis_step = 0.058
        x_start = min(0.45, (n_tags - 1) * axis_step)
    else:
        axis_step = 0.0
        x_start = 0.0

    # Default initial view: trailing 30 days (unless dataset is shorter)
    end_ts = df.index[-1]
    start_ts = max(df.index[0], end_ts - pd.Timedelta(days=30))

    extra_yaxes: dict[str, dict] = {}

    if n_tags == 1:
        tag = selected_tags[0]
        color = PALETTE[0]
        s_plot = df[tag]
        s = s_plot.dropna()
        if len(s) >= 2:
            y_min, y_max = float(s.min()), float(s.max())
            pad = (y_max - y_min) * 0.12 or abs(y_max) * 0.05 or 1.0
            lo = min(0.0, y_min - pad) if is_bar else (y_min - pad)
            hi = y_max + pad
            sp = downsample(s_plot, max_pts=max_pts)
            safe = tag.replace("<", "‹").replace(">", "›")

            if is_bar:
                fig.add_trace(go.Bar(
                    x=sp.index, y=sp.values, name=tag,
                    marker_color=rgba(color, 0.85),
                    hovertemplate=f"%{{y:,.2f}}<extra>{safe}</extra>",
                    showlegend=True,
                ))
            elif chart_type == "Line":
                fig.add_trace(go.Scatter(
                    x=sp.index, y=np.full(len(sp), lo), mode="lines",
                    line=dict(width=0), hoverinfo="skip", showlegend=False
                ))
                main_kwargs = dict(
                    x=sp.index, y=sp.values, mode="lines", name=tag,
                    line=dict(color=color, width=2.2),
                    hovertemplate=f"%{{y:,.2f}}<extra>{safe}</extra>",
                    fill="tonexty", showlegend=True,
                )
                try:
                    fig.add_trace(go.Scatter(
                        **main_kwargs,
                        fillgradient=dict(
                            type="vertical", start=lo, stop=y_max,
                            colorscale=[[0, rgba(color, 0.0)], [1, rgba(color, 0.22)]]
                        ),
                    ))
                except (ValueError, TypeError):
                    fig.add_trace(go.Scatter(**main_kwargs, fillcolor=rgba(color, 0.08)))
            else:
                style_kw = _scatter_style(chart_type, color, len(sp))
                if chart_type == "Area (Filled)":
                    fig.add_trace(go.Scatter(
                        x=sp.index, y=np.full(len(sp), lo), mode="lines",
                        line=dict(width=0), hoverinfo="skip", showlegend=False
                    ))
                    style_kw["fill"] = "tonexty"
                fig.add_trace(go.Scatter(
                    x=sp.index, y=sp.values, name=tag,
                    hovertemplate=f"%{{y:,.2f}}<extra>{safe}</extra>",
                    showlegend=True,
                    **style_kw,
                ))

            if not is_bar:
                fig.add_trace(go.Scatter(
                    x=[s.index[-1]], y=[s.iloc[-1]], mode="markers", hoverinfo="skip",
                    marker=dict(size=7, color=color, line=dict(color="#fff", width=2)),
                    cliponaxis=False, showlegend=False
                ))

            if show_mean:
                m_val = float(s.mean())
                fig.add_hline(
                    y=m_val, line_dash="dash", line_color="#9A9CA8", line_width=1.2,
                    annotation_text=f"Mean: {fmt(m_val)}",
                    annotation_position="top right",
                    annotation_font=dict(size=11, color=GREY),
                )
            y_axis_cfg = dict(
                range=[lo, hi], side="left", showgrid=True, gridcolor=FAINT, gridwidth=1,
                zeroline=False, showline=True, linecolor=rgba(color, 0.45), linewidth=1.5,
                fixedrange=False, tickfont=dict(color=color, size=11)
            )
        else:
            y_axis_cfg = dict(side="left", showgrid=True, gridcolor=FAINT)
    else:
        for idx, tag in enumerate(selected_tags):
            color = PALETTE[idx % len(PALETTE)]
            s_plot = df[tag]
            s = s_plot.dropna()
            if len(s) < 2:
                continue
            sp = downsample(s_plot, max_pts=max_pts)
            safe = tag.replace("<", "‹").replace(">", "›")

            y_min, y_max = float(s.min()), float(s.max())
            pad = (y_max - y_min) * 0.10 or abs(y_max) * 0.05 or 1.0
            lo = min(0.0, y_min - pad) if is_bar else (y_min - pad)
            hi = y_max + pad

            use_sep = separate_axes and idx > 0
            yaxis_id = f"y{idx + 1}" if use_sep else "y"
            yref_id = f"y{idx + 1}" if use_sep else "y"

            if is_bar:
                bar_kwargs = dict(
                    x=sp.index, y=sp.values, name=tag,
                    marker_color=rgba(color, 0.82),
                    hovertemplate=f"%{{y:,.2f}}<extra>{safe}</extra>",
                    showlegend=True,
                )
                if use_sep:
                    bar_kwargs["yaxis"] = yaxis_id
                fig.add_trace(go.Bar(**bar_kwargs))
            else:
                style_kw = _scatter_style(chart_type, color, len(sp))
                trace_kwargs = dict(
                    x=sp.index, y=sp.values, name=tag,
                    hovertemplate=f"%{{y:,.2f}}<extra>{safe}</extra>",
                    showlegend=True,
                    **style_kw,
                )
                if use_sep:
                    trace_kwargs["yaxis"] = yaxis_id
                fig.add_trace(go.Scatter(**trace_kwargs))

                mk_kwargs = dict(
                    x=[s.index[-1]], y=[s.iloc[-1]], mode="markers", hoverinfo="skip",
                    marker=dict(size=6, color=color, line=dict(color="#fff", width=1.5)),
                    cliponaxis=False, showlegend=False,
                )
                if use_sep:
                    mk_kwargs["yaxis"] = yaxis_id
                fig.add_trace(go.Scatter(**mk_kwargs))

            if show_mean:
                m_val = float(s.mean())
                fig.add_hline(
                    y=m_val, yref=yref_id,
                    line_dash="dot", line_color=rgba(color, 0.55), line_width=1.1
                )

            if use_sep:
                ax_pos = max(0.0, x_start - idx * axis_step)
                extra_yaxes[f"yaxis{idx + 1}"] = dict(
                    overlaying="y",
                    side="left",
                    anchor="free",
                    position=ax_pos,
                    range=[lo, hi],
                    showgrid=False,
                    zeroline=False,
                    showline=True,
                    linecolor=rgba(color, 0.55),
                    linewidth=1.5,
                    fixedrange=False,
                    tickfont=dict(color=color, size=10.5),
                )

        first_color = PALETTE[0] if separate_axes else SLATE
        y_axis_cfg = dict(
            side="left",
            showgrid=True,
            gridcolor=FAINT,
            gridwidth=1,
            zeroline=False,
            showline=True,
            linecolor=rgba(first_color, 0.55) if separate_axes else "#DCDEE4",
            linewidth=1.5 if separate_axes else 1.2,
            fixedrange=False,
            tickfont=dict(color=first_color, size=11),
            title=dict(text="Shared Y-Axis", font=dict(size=11, color=GREY)) if not separate_axes else None,
        )
        if separate_axes:
            s0 = df[selected_tags[0]].dropna()
            if len(s0) >= 2:
                y0_min, y0_max = float(s0.min()), float(s0.max())
                pad0 = (y0_max - y0_min) * 0.10 or abs(y0_max) * 0.05 or 1.0
                lo0 = min(0.0, y0_min - pad0) if is_bar else (y0_min - pad0)
                y_axis_cfg["range"] = [lo0, y0_max + pad0]

    layout = dict(
        height=chart_height,
        margin=dict(l=12, r=12, t=38, b=16),
        paper_bgcolor="#fff",
        plot_bgcolor="#fff",
        barmode="group",
        hovermode="x unified",
        spikedistance=-1,
        hoverdistance=-1,
        dragmode="zoom",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="left",
            x=x_start,
            bgcolor="rgba(255,255,255,0.85)",
            font=dict(size=12, color=SLATE),
            itemclick="toggle",
            itemdoubleclick="toggleothers",
        ),
        font=dict(family="Inter, Roboto, sans-serif", color=GREY, size=12),
        hoverlabel=dict(bgcolor="#fff", bordercolor=BORDER, font=dict(color=SLATE, size=12)),
        xaxis=dict(
            domain=[x_start, 1.0],
            range=[start_ts, end_ts],
            type="date",
            visible=True,
            showticklabels=True,
            showgrid=True,
            gridcolor="#F8F9FA",
            gridwidth=1,
            zeroline=False,
            showline=True,
            linecolor="#DCDEE4",
            linewidth=1.2,
            ticks="outside",
            ticklen=4,
            tickcolor="#DCDEE4",
            fixedrange=False,
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            spikethickness=1,
            spikedash="dot",
            spikecolor="#B5B7C0",
            hoverformat="%d %b %Y, %H:%M",
            tickfont=dict(color="#5A5D6E", size=11),
            automargin=True,
            rangeselector=dict(
                bgcolor="#F4F5F7",
                activecolor="#5367FF",
                bordercolor="#ECEDEF",
                borderwidth=1,
                font=dict(size=11, color=SLATE),
                x=x_start,
                y=1.01,
                xanchor="left",
                yanchor="bottom",
                buttons=[
                    dict(count=1, label="1D", step="day", stepmode="backward"),
                    dict(count=7, label="1W", step="day", stepmode="backward"),
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(step="all", label="ALL"),
                ],
            ),
            rangeslider=dict(
                visible=True,
                thickness=0.08,
                bgcolor="#F8F9FB",
                bordercolor="#ECEDEF",
                borderwidth=1,
            ),
        ),
        yaxis=y_axis_cfg,
        **extra_yaxes,
    )

    fig.update_layout(**layout)
    return fig


def stat_card(label: str, value: str, sub: str = "") -> str:
    return (
        f'<div class="gw-card"><div class="gw-label">{label}</div>'
        f'<div class="gw-value">{value}</div><div class="gw-sub">{sub}</div></div>'
    )


def range_bar(low: float, high: float, cur: float, color: str) -> str:
    pos = 50.0 if high == low else (cur - low) / (high - low) * 100
    pos = min(max(pos, 4.0), 96.0)
    return (
        '<div class="gw-range-box"><div class="gw-range-row">'
        f'<div class="gw-range-end"><div class="gw-label">Dataset Min</div><div class="gw-value">{fmt(low)}</div></div>'
        '<div class="gw-range-mid">'
        f'<div class="gw-pointer" style="left:{pos:.1f}%"><span class="gw-bubble">Latest: {fmt(cur)}</span>'
        f'<span class="gw-tri" style="border-top-color:{color}"></span></div>'
        '<div class="gw-track"></div></div>'
        f'<div class="gw-range-end right"><div class="gw-label">Dataset Max</div><div class="gw-value">{fmt(high)}</div></div>'
        '</div></div>'
    )


def _handle_upload(up_file) -> None:
    if up_file is None:
        return
    file_sig = (up_file.name, up_file.size)
    if st.session_state.get("last_uploaded_sig") == file_sig:
        return
    st.session_state["last_uploaded_sig"] = file_sig
    st.session_state["uploaded_bytes"] = up_file.getvalue()
    st.session_state["uploaded_name"] = up_file.name
    if up_file.name.lower().endswith((".xlsx", ".xlsm")):
        sheets = list_sheets(up_file.getvalue())
        st.session_state["active_sheet"] = sheets[0]
    else:
        st.session_state["active_sheet"] = None
    st.session_state.pop("selected_tags", None)
    st.session_state.pop("inspect_tag", None)
    st.rerun()


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #
def main() -> None:
    st.markdown(CSS, unsafe_allow_html=True)

    if "drawer_open" not in st.session_state:
        st.session_state["drawer_open"] = False
    if "separate_axes" not in st.session_state:
        st.session_state["separate_axes"] = True
    if "merge_y_axes_quick" not in st.session_state:
        st.session_state["merge_y_axes_quick"] = not st.session_state["separate_axes"]

    # Load data from session state if uploaded, else sample
    up_bytes = st.session_state.get("uploaded_bytes")
    up_name = st.session_state.get("uploaded_name")
    sheet = st.session_state.get("active_sheet")
    try:
        if up_bytes is not None and up_name:
            raw = read_table(up_bytes, up_name, sheet)
            src = up_name
        else:
            raw, src = sample_raw(), "Built-in sample data"
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not read file: {exc}")
        st.stop()

    cols = list(raw.columns)
    default_ts = detect_ts(raw)
    ts_col = st.session_state.get("ts_col") if st.session_state.get("ts_col") in cols else default_ts
    fill_mode = st.session_state.get("fill_mode", FILL_MODES[0])

    df = prepare(raw, ts_col, fill_mode)
    if df.empty or len(df) < 2:
        st.session_state["drawer_open"] = True
        st.error("No usable numeric tags found. Click **📂 Upload** or open **Data & settings** to pick the timestamp column.")

    tags = list(df.columns) if not df.empty else []

    # Sanitize multi-select tag list in session_state BEFORE creating the widget
    if "selected_tags" in st.session_state:
        valid_sel = [t for t in st.session_state["selected_tags"] if t in tags]
        if valid_sel:
            st.session_state["selected_tags"] = valid_sel
        elif tags:
            st.session_state["selected_tags"] = [tags[0]]
        else:
            st.session_state["selected_tags"] = []
    elif tags:
        st.session_state["selected_tags"] = [tags[0]]

    # ---- Top Bar: Brand + Author | Live Multi-Select | Upload | Parameters -- #
    c_brand, c_search_drop, c_up, c_menu = st.columns([1.25, 4.15, 0.95, 1.05], vertical_alignment="center")
    c_brand.markdown(
        f'<div class="gw-brand-wrap">'
        f'<div class="gw-brand"><span class="dot"></span>PlantWatch</div>'
        f'<div class="gw-author">by <b>{esc(AUTHOR_NAME)}</b></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    selected_tags = c_search_drop.multiselect(
        "Search and select tags",
        options=tags,
        key="selected_tags",
        placeholder="🔍 Type to search & select multiple tags (e.g., TI-203, Pressure, Flow)...",
        label_visibility="collapsed",
    )
    if not selected_tags and tags:
        selected_tags = [tags[0]]

    with c_up.popover("📂 Upload", **BTN_KW):
        up_top = st.file_uploader(
            "Upload Excel (.xlsx) or CSV",
            type=["xlsx", "xlsm", "csv"],
            key="uploader_top",
        )
        _handle_upload(up_top)
        if up_bytes is not None and up_name and up_name.lower().endswith((".xlsx", ".xlsm")):
            sheets_top = list_sheets(up_bytes)
            if len(sheets_top) > 1:
                st.selectbox("Select Sheet", sheets_top, key="active_sheet")
        st.caption(f"Loaded: **{src}** ({len(raw):,} rows)")

    drawer_open = st.session_state.get("drawer_open", False)
    c_menu.button(
        "✕ Close" if drawer_open else "☰ Parameters",
        key="toggle_drawer_btn",
        on_click=toggle_drawer,
        type="primary" if drawer_open else "secondary",
        **BTN_KW,
    )

    if df.empty or len(df) < 2:
        return

    show_mean = st.session_state.get("show_mean", True)
    separate_axes = st.session_state.get("separate_axes", True)
    chart_type = st.session_state.get("chart_type", CHART_TYPES[0])

    # ---- Layout: Full-Width Canvas OR Canvas + Collapsible Right Drawer --- #
    if drawer_open:
        chart_pane, drawer_pane = st.columns([2.15, 1.0], gap="large", vertical_alignment="top")
    else:
        chart_pane = st.container()
        drawer_pane = None

    # ---- Collapsible Right Pane (Only rendered when user clicks Parameters) - #
    if drawer_open and drawer_pane is not None:
        with drawer_pane:
            with st.expander("📂 Data & settings", expanded=False):
                up_side = st.file_uploader(
                    "Upload .xlsx or .csv",
                    type=["xlsx", "xlsm", "csv"],
                    key="uploader_side",
                )
                _handle_upload(up_side)

                sc1, sc2 = st.columns(2)
                sc1.selectbox("Timestamp col", cols, index=cols.index(ts_col), key="ts_col")
                sc2.selectbox("Missing values", FILL_MODES, key="fill_mode")
                st.caption(f"**{src}** · {len(raw):,} rows")

            st.markdown('<div class="gw-pane-title">Chart Style, Axes & Statistics</div>', unsafe_allow_html=True)

            # Row 1: Chart Type selector + Inspect Tag selector
            ct_col, ins_col = st.columns(2)
            chart_type = ct_col.selectbox(
                "Trend Type",
                CHART_TYPES,
                key="chart_type",
                label_visibility="collapsed",
            )
            inspect_tag = (
                ins_col.selectbox("Inspect tag", selected_tags, key="inspect_tag", label_visibility="collapsed")
                if len(selected_tags) > 1 else selected_tags[0]
            )

            # Row 2: Axis & Mean toggles (Synced with quick Merge Y-axes handle)
            t_ax, t_mn = st.columns(2)
            separate_axes = t_ax.toggle(
                "Separate Y-axes",
                key="separate_axes",
                on_change=_on_separate_toggle,
            )
            show_mean = t_mn.toggle("Show mean lines", value=show_mean, key="show_mean")

            idx_color = PALETTE[selected_tags.index(inspect_tag) % len(PALETTE)]
            s_stat = df[inspect_tag].dropna()
            if len(s_stat) >= 2:
                end_val = float(s_stat.iloc[-1])
                mean_val = float(s_stat.mean())
                mn_val = float(s_stat.min())
                mx_val = float(s_stat.max())
                n = len(s_stat)
                q25, q75 = float(s_stat.quantile(0.25)), float(s_stat.quantile(0.75))
                std = float(s_stat.std(ddof=1))
                var = float(s_stat.var(ddof=1))

                st.markdown(range_bar(mn_val, mx_val, end_val, idx_color), unsafe_allow_html=True)
                cards = [
                    stat_card("Mean (Average)", fmt(mean_val), "Arithmetic average"),
                    stat_card("Median", fmt(s_stat.median()), "50th percentile"),
                    stat_card("Dataset Min", fmt(mn_val), f"{fmt_ts_short(s_stat.idxmin())}"),
                    stat_card("Dataset Max", fmt(mx_val), f"{fmt_ts_short(s_stat.idxmax())}"),
                    stat_card("Std Deviation (σ)", fmt(std), "Sample (n − 1)"),
                    stat_card("Variance (σ²)", fmt(var), "Sample (n − 1)"),
                    stat_card("Range (Max − Min)", fmt(mx_val - mn_val), f"IQR <b>{fmt(q75 - q25)}</b>"),
                    stat_card("95th Percentile", fmt(s_stat.quantile(0.95)), f"Samples (N) <b>{n:,}</b>"),
                ]
                st.markdown(f'<div class="gw-grid-pane">{"".join(cards)}</div>', unsafe_allow_html=True)

    # ---- Main Trend Canvas ------------------------------------------------ #
    with chart_pane:
        badges = []
        for idx, t in enumerate(selected_tags):
            color = PALETTE[idx % len(PALETTE)]
            st_ser = df[t].dropna()
            if len(st_ser) >= 1:
                last_v = fmt(float(st_ser.iloc[-1]))
                avg_v = fmt(float(st_ser.mean()))
                badges.append(
                    f'<div class="gw-leg-item">'
                    f'<span class="gw-leg-dot" style="background:{color}"></span>'
                    f'<span class="gw-leg-name">{esc(t)}</span>'
                    f'<span class="gw-leg-stat">Latest <b>{last_v}</b> · Mean <b>{avg_v}</b></span>'
                    f'</div>'
                )
        axis_mode_label = "Shared Y-Axis" if (len(selected_tags) > 1 and not separate_axes) else "Multi Y-Axes"
        window_info = (
            f"{chart_type} · {axis_mode_label if len(selected_tags) > 1 else 'Single Y-Axis'} · "
            f"{fmt_ts(df.index[0])} → {fmt_ts(df.index[-1])}"
        )
        legend_html = (
            f'<div class="gw-legend-strip">{"".join(badges)}'
            f'<span class="gw-window-badge">{window_info}</span></div>'
        )

        # Quick On-Canvas Handle to Merge Y-Axes whenever 2+ trends are plotted
        if len(selected_tags) > 1:
            leg_col, merge_col = st.columns([5.6, 1.15], vertical_alignment="center")
            leg_col.markdown(legend_html, unsafe_allow_html=True)
            merge_col.toggle(
                "Merge Y-axes",
                key="merge_y_axes_quick",
                on_change=_on_merge_toggle,
                help="Combine all selected trends onto one shared Y-axis scale (useful for comparing tags with identical units, e.g. multiple temperatures or pressures).",
            )
            separate_axes = not st.session_state.get("merge_y_axes_quick", False)
        else:
            st.markdown(legend_html, unsafe_allow_html=True)

        fig = build_multi_figure(
            df,
            selected_tags,
            show_mean=show_mean,
            separate_axes=separate_axes,
            chart_type=chart_type,
            chart_height=515,
        )
        st.plotly_chart(
            fig,
            key="main_chart",
            config={
                "displayModeBar": "hover",
                "scrollZoom": True,
                "displaylogo": False,
                "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
            },
            **PLOT_KW,
        )


main()
