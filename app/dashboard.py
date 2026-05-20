"""
DynNav · Autonomous Navigation Research Dashboard
=================================================

Main landing page for the multi-page Streamlit app. Provides the project
elevator pitch, headline metrics, an at-a-glance architecture summary, and a
quick-look navigation map.

Run with::

    streamlit run app/dashboard.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make `src/` importable without a package install — keeps the demo
# "just clone and run" friendly.
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st  # noqa: E402

from dynnav_dashboard.config import (  # noqa: E402
    APP_TITLE, APP_ICON, APP_TAGLINE, AUTHOR, AFFILIATION, REPO_URL,
    COLORS, DEFAULT_SCENARIO, RESEARCH_MODULES,
)
from dynnav_dashboard.simulation import (  # noqa: E402
    build_environment, plan_astar, plan_risk_aware,
)
from dynnav_dashboard.metrics import planner_metrics  # noqa: E402
from dynnav_dashboard.visualization import (  # noqa: E402
    plot_navigation_map, plot_category_breakdown,
)


# ---------------------------------------------------------------------------
# Page config & styling
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = f"""
<style>
    .main .block-container {{
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }}
    .dyn-hero {{
        background: linear-gradient(135deg, {COLORS['surface']} 0%, {COLORS['surface_alt']} 100%);
        border: 1px solid {COLORS['border']};
        border-radius: 14px;
        padding: 1.8rem 2rem;
        margin-bottom: 1.4rem;
    }}
    .dyn-hero h1 {{
        color: {COLORS['text']};
        font-size: 2.0rem;
        font-weight: 700;
        margin: 0 0 .4rem 0;
        letter-spacing: -0.01em;
    }}
    .dyn-hero p.tagline {{
        color: {COLORS['secondary']};
        font-size: 1.0rem;
        margin: 0 0 1rem 0;
        font-weight: 500;
    }}
    .dyn-hero p.lead {{
        color: {COLORS['text_muted']};
        font-size: 0.98rem;
        line-height: 1.55;
        margin: 0;
        max-width: 70ch;
    }}
    .dyn-pill {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
        border: 1px solid {COLORS['border']};
        color: {COLORS['text']};
        background: {COLORS['surface_alt']};
    }}
    .dyn-pill.primary {{ background: {COLORS['primary']}22; border-color: {COLORS['primary']}66; color: {COLORS['primary']}; }}
    .dyn-pill.cyan    {{ background: {COLORS['secondary']}22; border-color: {COLORS['secondary']}66; color: {COLORS['secondary']}; }}
    .dyn-pill.accent  {{ background: {COLORS['accent']}22; border-color: {COLORS['accent']}66; color: {COLORS['accent']}; }}
    .dyn-pill.safe    {{ background: {COLORS['success']}22; border-color: {COLORS['success']}66; color: {COLORS['success']}; }}
    .dyn-pill.warn    {{ background: {COLORS['highlight']}22; border-color: {COLORS['highlight']}66; color: {COLORS['highlight']}; }}

    .dyn-metric {{
        background: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 10px;
        padding: 14px 16px;
        height: 100%;
    }}
    .dyn-metric .label {{
        color: {COLORS['text_muted']};
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}
    .dyn-metric .value {{
        color: {COLORS['text']};
        font-size: 1.6rem;
        font-weight: 700;
        margin-top: 4px;
    }}
    .dyn-metric .sub {{
        color: {COLORS['text_muted']};
        font-size: 0.82rem;
        margin-top: 2px;
    }}

    .dyn-card {{
        background: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 14px;
    }}
    .dyn-card h3 {{
        margin: 0 0 .6rem 0;
        color: {COLORS['text']};
        font-size: 1.05rem;
    }}
    .dyn-card p {{
        color: {COLORS['text_muted']};
        margin: 0;
        font-size: 0.92rem;
        line-height: 1.5;
    }}

    section[data-testid="stSidebar"] {{
        background-color: {COLORS['surface']};
        border-right: 1px solid {COLORS['border']};
    }}
    section[data-testid="stSidebar"] .stMarkdown p {{
        color: {COLORS['text_muted']};
    }}

    /* Tighter dataframe look */
    .stDataFrame {{ border: 1px solid {COLORS['border']}; border-radius: 8px; }}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar — global about / navigation hint
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(f"### {APP_ICON} DynNav")
    st.markdown(f"**{AUTHOR}**  \n{AFFILIATION}")
    st.markdown(f"[GitHub repository ↗]({REPO_URL})")
    st.divider()
    st.markdown(
        "**Pages**\n\n"
        "• Architecture\n"
        "• Navigation Demo\n"
        "• Risk Map\n"
        "• Planner Comparison\n"
        "• Research Modules"
    )
    st.divider()
    st.caption(
        "This dashboard runs on synthetic data so it works without ROS 2, "
        "Gazebo, or a real robot."
    )


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

st.markdown(
    f"""
    <div class="dyn-hero">
        <h1>{APP_ICON} DynNav — Autonomous Navigation Research Dashboard</h1>
        <p class="tagline">{APP_TAGLINE}</p>
        <p class="lead">
            DynNav is a modular research framework for robot navigation in
            unknown, dynamic environments — combining classical search,
            risk-sensitive planning, learning-augmented heuristics, and
            formal safety into a single coherent stack. This dashboard is a
            self-contained, browser-based companion: it explores the project's
            architecture, runs a synthetic demo of dynamic rerouting, and
            visualises planner trade-offs the way they appear in the
            full ROS&nbsp;2 system.
        </p>
        <div style="margin-top: 14px;">
            <span class="dyn-pill primary">Risk-aware planning</span>
            <span class="dyn-pill cyan">Uncertainty modelling</span>
            <span class="dyn-pill accent">Learning-augmented</span>
            <span class="dyn-pill safe">Formal safety (STL+CBF)</span>
            <span class="dyn-pill warn">Multi-robot consensus</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Headline KPI strip — computed from a quick deterministic baseline run
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def _baseline_snapshot():
    """Build a deterministic environment + two planning results for the hero KPIs."""
    cfg = DEFAULT_SCENARIO
    env = build_environment(cfg, seed=cfg.random_seed)
    base = plan_astar(env, cfg.start, cfg.goal)
    risk = plan_risk_aware(env, cfg.start, cfg.goal, cfg.risk_weight)
    base_m = planner_metrics("A*", base, cfg)
    risk_m = planner_metrics("Risk-Aware A*", risk, cfg)
    return env, base, risk, base_m, risk_m


env, baseline_plan, risk_plan, base_m, risk_m = _baseline_snapshot()

k1, k2, k3, k4, k5 = st.columns(5)


def _metric(col, label: str, value: str, sub: str) -> None:
    col.markdown(
        f"""
        <div class="dyn-metric">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            <div class="sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


_metric(k1, "Research modules", "26",
        "from learned A* to BFT swarm consensus")
_metric(k2, "Risk-Aware path length", f"{risk_m.path_length_m:.2f} m",
        f"vs A* baseline {base_m.path_length_m:.2f} m")
_metric(k3, "Avg collision risk",
        f"{risk_m.avg_risk:.0%}",
        f"A* baseline {base_m.avg_risk:.0%}")
_metric(k4, "Safety score",
        f"{risk_m.safety_score:.2f}",
        f"A* baseline {base_m.safety_score:.2f}")
_metric(k5, "Plan compute", f"{risk_m.compute_ms:.1f} ms",
        f"A* baseline {base_m.compute_ms:.1f} ms")


st.write("")  # spacer


# ---------------------------------------------------------------------------
# Body — left: nav map, right: research module breakdown
# ---------------------------------------------------------------------------

left, right = st.columns([1.35, 1.0], gap="large")

with left:
    st.markdown("### Quick-look navigation map")
    st.markdown(
        f"<p style='color:{COLORS['text_muted']};font-size:0.92rem;margin-top:-6px'>"
        "Synthetic environment with static (grey) and dynamic (amber) obstacles, "
        "showing A* and risk-aware paths planned from the same start to the same goal."
        "</p>",
        unsafe_allow_html=True,
    )

    fig = plot_navigation_map(
        env,
        paths=[
            ("A* baseline", baseline_plan.path, COLORS["info"]),
            ("Risk-Aware A*", risk_plan.path, COLORS["secondary"]),
        ],
        start=DEFAULT_SCENARIO.start,
        goal=DEFAULT_SCENARIO.goal,
        show_risk=False,
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.markdown("### Research module breakdown")
    st.markdown(
        f"<p style='color:{COLORS['text_muted']};font-size:0.92rem;margin-top:-6px'>"
        "The DynNav repository organises its 26 contributions into the categories below. "
        "Explore each module on the <b>Research Modules</b> page."
        "</p>",
        unsafe_allow_html=True,
    )
    cats = [m.category for m in RESEARCH_MODULES]
    st.plotly_chart(plot_category_breakdown(cats), use_container_width=True)


# ---------------------------------------------------------------------------
# What's inside
# ---------------------------------------------------------------------------

st.markdown("### Inside this dashboard")
c1, c2, c3, c4, c5 = st.columns(5)

cards = [
    (c1, "🏗️ Architecture",
     "Layered view of perception, planning, safety, learning, and coordination, "
     "rendered as a research-style stack diagram."),
    (c2, "🤖 Navigation Demo",
     "Step-through replay of a closed-loop episode — robot, dynamic obstacles, "
     "and online replanning events."),
    (c3, "🌡️ Risk Map",
     "Uncertainty and risk heatmaps overlaid with the planned route — the inputs "
     "the CVaR-A* planner actually sees."),
    (c4, "📊 Planner Comparison",
     "Side-by-side A* vs risk-aware A* on path length, risk, safety, and compute."),
    (c5, "🔬 Research Modules",
     "Searchable catalogue of all 26 contributions from the upstream repository."),
]

for col, title, body in cards:
    with col:
        st.markdown(
            f"<div class='dyn-card'><h3>{title}</h3><p>{body}</p></div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Research positioning
# ---------------------------------------------------------------------------

st.markdown("### Research positioning")
st.markdown(
    f"""
    <div class='dyn-card'>
        <p>
            DynNav sits at the intersection of <b>classical motion planning</b>,
            <b>probabilistic state estimation</b>, and <b>modern learning-based
            robotics</b>. The full system targets the open problem of <i>safe,
            uncertainty-aware navigation in unknown environments</i> — the core
            scenario for service, inspection, and field robotics where the map
            is incomplete and the world changes during execution.
        </p>
        <p style="margin-top:10px;">
            Compared to a plain Nav2 stack, DynNav adds explicit
            <span class="dyn-pill cyan">CVaR risk</span>
            <span class="dyn-pill safe">STL + CBF safety shields</span>
            <span class="dyn-pill accent">learned heuristics</span>
            <span class="dyn-pill primary">multi-robot BFT consensus</span>
            and <span class="dyn-pill warn">causal failure attribution</span> —
            making it a strong foundation for MSc / PhD work in safe autonomy.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    f"© {AUTHOR} · {AFFILIATION} · "
    f"Dashboard runs on synthetic data — see the GitHub repo for the full "
    f"ROS 2 implementation and experimental logs."
)
