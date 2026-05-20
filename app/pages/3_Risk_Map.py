"""
DynNav Dashboard — Risk Map Page
================================

Visualises the two heatmaps that drive risk-aware planning:

* the **perception uncertainty field** (how confident the sensors are
  about each cell), and
* the **derived risk field** (inflated obstacle proximity, modulated by
  uncertainty — a tractable proxy for the CVaR cost in contribution 03).

Both maps are overlaid with the planned path so the relationship between
the cost surface and the chosen route is immediately legible.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np  # noqa: E402
import streamlit as st  # noqa: E402

from dynnav_dashboard.config import (  # noqa: E402
    APP_ICON, APP_TITLE, COLORS, DEFAULT_SCENARIO,
    PLOTLY_RISK_SCALE, PLOTLY_UNCERTAINTY_SCALE, ScenarioConfig,
)
from dynnav_dashboard.simulation import (  # noqa: E402
    build_environment, plan_astar, plan_risk_aware,
)
from dynnav_dashboard.visualization import plot_risk_heatmap  # noqa: E402


st.set_page_config(
    page_title=f"Risk Map · {APP_TITLE}",
    page_icon=APP_ICON,
    layout="wide",
)


st.markdown(
    f"""
    <style>
        .main .block-container {{ padding-top: 1.2rem; max-width: 1400px; }}
        .dyn-section-title {{
            color: {COLORS['text']};
            font-size: 1.7rem;
            font-weight: 700;
            margin: 0 0 0.2rem 0;
        }}
        .dyn-section-sub {{
            color: {COLORS['text_muted']};
            font-size: 0.95rem;
            margin: 0 0 1.2rem 0;
            max-width: 80ch;
        }}
        .dyn-stat {{
            background: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 12px 16px;
        }}
        .dyn-stat .label {{
            color: {COLORS['text_muted']};
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .dyn-stat .value {{
            color: {COLORS['text']};
            font-size: 1.4rem;
            font-weight: 700;
            margin-top: 4px;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="dyn-section-title">🌡️ Uncertainty & Risk Maps</div>',
            unsafe_allow_html=True)
st.markdown(
    '<p class="dyn-section-sub">'
    'The two fields below are the inputs a risk-sensitive planner actually consumes. '
    'The <b>uncertainty field</b> represents the confidence of the perception stack '
    '(EKF/UKF in contribution 02, MC-dropout NeRF in 24); the <b>risk field</b> '
    'combines obstacle proximity with that uncertainty to produce the cost surface '
    'used by the CVaR-aware planner (contribution 03).'
    '</p>',
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### Field controls")
    seed = st.number_input("Seed", value=DEFAULT_SCENARIO.random_seed,
                           min_value=0, max_value=9999)
    grid_size = st.slider("Grid size", 20, 60, DEFAULT_SCENARIO.grid_size, step=5)
    sigma = st.slider("Uncertainty spread (σ)", 1.0, 10.0,
                      DEFAULT_SCENARIO.uncertainty_sigma, step=0.5)
    inflation = st.slider("Risk inflation radius (cells)", 1, 8,
                          DEFAULT_SCENARIO.risk_inflation_radius)
    show_path = st.checkbox("Overlay planned paths", value=True)


# ---------------------------------------------------------------------------
# Build environment + plans
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Building risk fields…")
def _build(seed: int, grid_size: int, sigma: float, inflation: int):
    cfg = ScenarioConfig(
        grid_size=grid_size,
        start=(2, 2),
        goal=(grid_size - 3, grid_size - 3),
        uncertainty_sigma=sigma,
        risk_inflation_radius=inflation,
        random_seed=seed,
    )
    env = build_environment(cfg, seed=seed)
    base = plan_astar(env, cfg.start, cfg.goal)
    risk = plan_risk_aware(env, cfg.start, cfg.goal, cfg.risk_weight)
    return cfg, env, base, risk


cfg, env, base_plan, risk_plan = _build(seed, grid_size, sigma, inflation)


# ---------------------------------------------------------------------------
# Stats strip
# ---------------------------------------------------------------------------

risk_field = env.risk
uncertainty_field = env.uncertainty

cvar_alpha = DEFAULT_SCENARIO.cvar_alpha
risk_vals_flat = risk_field.flatten()
threshold = float(np.quantile(risk_vals_flat, cvar_alpha))
tail = risk_vals_flat[risk_vals_flat >= threshold]
cvar_value = float(tail.mean()) if tail.size else 0.0

c1, c2, c3, c4 = st.columns(4)


def _stat(col, label: str, value: str) -> None:
    col.markdown(
        f"<div class='dyn-stat'><div class='label'>{label}</div>"
        f"<div class='value'>{value}</div></div>",
        unsafe_allow_html=True,
    )


_stat(c1, "Mean risk", f"{float(risk_field.mean()):.2%}")
_stat(c2, "Max risk", f"{float(risk_field.max()):.2%}")
_stat(c3, f"CVaR @ {int(cvar_alpha*100)}%", f"{cvar_value:.2%}")
_stat(c4, "Mean uncertainty", f"{float(uncertainty_field.mean()):.2%}")

st.write("")


# ---------------------------------------------------------------------------
# Two side-by-side heatmaps
# ---------------------------------------------------------------------------

overlay_base = base_plan.path if show_path else None
overlay_risk = risk_plan.path if show_path else None

col_unc, col_risk = st.columns(2, gap="large")

with col_unc:
    st.plotly_chart(
        plot_risk_heatmap(
            field=uncertainty_field,
            title="Perception uncertainty",
            colorscale=PLOTLY_UNCERTAINTY_SCALE,
            overlay_path=overlay_base,
        ),
        use_container_width=True,
    )
    st.caption(
        "Higher values (violet) indicate cells where the robot's belief state "
        "is less confident — typically far from the start, in occluded regions, "
        "or where recent sensor returns disagree."
    )

with col_risk:
    st.plotly_chart(
        plot_risk_heatmap(
            field=risk_field,
            title="Composite risk (CVaR-A* cost)",
            colorscale=PLOTLY_RISK_SCALE,
            overlay_path=overlay_risk,
        ),
        use_container_width=True,
    )
    st.caption(
        "Risk = proximity-to-obstacle (exponential falloff) × uncertainty. "
        "This is the cost surface added on top of the classical A* edge cost "
        "to produce the risk-aware plan."
    )


# ---------------------------------------------------------------------------
# Risk histogram & explanation
# ---------------------------------------------------------------------------

st.markdown("### Risk distribution")
import plotly.graph_objects as go  # local import keeps the page imports tidy

hist_fig = go.Figure(data=go.Histogram(
    x=risk_vals_flat,
    nbinsx=40,
    marker=dict(color=COLORS["secondary"],
                line=dict(color=COLORS["border"], width=1)),
    hovertemplate="risk=%{x:.2f}<br>cells=%{y}<extra></extra>",
))
hist_fig.add_vline(
    x=threshold, line=dict(color=COLORS["highlight"], width=2, dash="dash"),
    annotation_text=f"CVaR @ {int(cvar_alpha*100)}% threshold",
    annotation_position="top right",
    annotation_font=dict(color=COLORS["highlight"]),
)
hist_fig.update_layout(
    height=320,
    margin=dict(l=20, r=20, t=40, b=30),
    paper_bgcolor=COLORS["surface"],
    plot_bgcolor=COLORS["surface"],
    font=dict(color=COLORS["text"], family="Inter, sans-serif"),
    xaxis=dict(title=dict(text="Risk value",
                          font=dict(color=COLORS["text_muted"])),
               gridcolor=COLORS["border"], color=COLORS["text_muted"]),
    yaxis=dict(title=dict(text="Cell count",
                          font=dict(color=COLORS["text_muted"])),
               gridcolor=COLORS["border"], color=COLORS["text_muted"]),
    showlegend=False,
)
st.plotly_chart(hist_fig, use_container_width=True)


with st.expander("Why CVaR instead of mean risk?", expanded=False):
    st.markdown(
        f"""
        For safety-critical navigation, we care about **how bad the worst-case
        looks**, not just the average. The Conditional Value-at-Risk at level
        α (CVaR<sub>α</sub>) is the **mean of the worst (1 − α)% of outcomes**
        — in this dashboard, α = {int(cvar_alpha*100)}%, so we are looking at
        the mean of the worst 5% of per-cell risk values.

        - **Expected risk** can hide a dangerous tail: a path that's mostly
          safe but spends one cell next to a high-speed obstacle has a low
          average risk but a high CVaR.
        - **Worst-case (max)** is too conservative — a single noisy cell can
          dominate.
        - **CVaR** sits between the two: it is sensitive to the tail without
          collapsing to the maximum, which is why it is the objective used in
          DynNav's risk-sensitive planner (contribution 03 — `CVaR-A*`).
        """,
        unsafe_allow_html=True,
    )
