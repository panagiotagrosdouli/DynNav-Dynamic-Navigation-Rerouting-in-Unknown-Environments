"""
DynNav Dashboard — Planner Comparison Page
==========================================

Head-to-head comparison of the classical A* baseline vs the risk-aware
A* variant (a tractable CVaR proxy for contribution 03). Shows paths
side-by-side, the per-step risk profile, a metrics table, a normalised
radar profile, and a Monte-Carlo sweep across multiple seeds for
statistical context.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from dynnav_dashboard.config import (  # noqa: E402
    APP_ICON, APP_TITLE, COLORS, DEFAULT_SCENARIO, ScenarioConfig,
)
from dynnav_dashboard.simulation import (  # noqa: E402
    build_environment, plan_astar, plan_risk_aware,
)
from dynnav_dashboard.metrics import planner_metrics  # noqa: E402
from dynnav_dashboard.visualization import (  # noqa: E402
    plot_navigation_map, plot_planner_comparison_bars,
    plot_radar_comparison, plot_risk_profile,
)


st.set_page_config(
    page_title=f"Planner Comparison · {APP_TITLE}",
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
        .stDataFrame {{ border: 1px solid {COLORS['border']}; border-radius: 8px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="dyn-section-title">📊 Planner Comparison · A* vs Risk-Aware A*</div>',
            unsafe_allow_html=True)
st.markdown(
    '<p class="dyn-section-sub">'
    'Two planners, same start, same goal, same world. The classical A* baseline '
    'minimises path length over an 8-connected grid; the risk-aware variant adds '
    'a weighted CVaR-proxy penalty to each edge, which bends the route away from '
    'obstacles and high-uncertainty corridors.'
    '</p>',
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Sidebar — controls
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### Comparison controls")
    seed = st.number_input("Random seed", value=DEFAULT_SCENARIO.random_seed,
                           min_value=0, max_value=9999)
    grid_size = st.slider("Grid size", 20, 60, DEFAULT_SCENARIO.grid_size, step=5)
    n_static = st.slider("Static obstacles", 5, 30,
                         DEFAULT_SCENARIO.n_static_obstacles)
    risk_weight = st.slider("Risk weight", 0.0, 5.0,
                            DEFAULT_SCENARIO.risk_weight, step=0.25)
    n_seeds = st.slider("Monte-Carlo seeds", 5, 40, 12,
                        help="Number of random environments used for the "
                             "statistical comparison below.")


# ---------------------------------------------------------------------------
# Single-environment comparison
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Planning…")
def _single(seed: int, grid_size: int, n_static: int, risk_weight: float):
    cfg = ScenarioConfig(
        grid_size=grid_size,
        start=(2, 2),
        goal=(grid_size - 3, grid_size - 3),
        n_static_obstacles=n_static,
        n_dynamic_obstacles=0,   # static comparison for clarity
        risk_weight=risk_weight,
        random_seed=seed,
    )
    env = build_environment(cfg, seed=seed)
    base = plan_astar(env, cfg.start, cfg.goal)
    risk = plan_risk_aware(env, cfg.start, cfg.goal, risk_weight)
    return cfg, env, base, risk


cfg, env, base, risk = _single(seed, grid_size, n_static, risk_weight)
base_m = planner_metrics("A* baseline", base, cfg)
risk_m = planner_metrics("Risk-Aware A*", risk, cfg)

col_map, col_profile = st.columns([1.4, 1.0], gap="large")

with col_map:
    fig = plot_navigation_map(
        env,
        paths=[
            ("A* baseline", base.path, COLORS["info"]),
            ("Risk-Aware A*", risk.path, COLORS["secondary"]),
        ],
        start=cfg.start, goal=cfg.goal,
        show_risk=True,
        title="Paths overlaid on the risk field",
    )
    st.plotly_chart(fig, use_container_width=True)

with col_profile:
    base_risks = [float(env.risk[y, x]) for x, y in base.path]
    risk_risks = [float(env.risk[y, x]) for x, y in risk.path]
    st.plotly_chart(
        plot_risk_profile(
            base.path, base_risks, "A* baseline", COLORS["info"],
            risk.path, risk_risks, "Risk-Aware A*", COLORS["secondary"],
        ),
        use_container_width=True,
    )

    radar_metrics = {
        "A* baseline": [
            min(1.0, base_m.path_length_m / max(risk_m.path_length_m, 1e-6) * 0.8),
            1.0 - min(1.0, base_m.avg_risk * 2),
            1.0 - min(1.0, base_m.cvar_risk * 1.5),
            base_m.safety_score,
            min(1.0, base_m.compute_ms / max(risk_m.compute_ms, 1e-6) * 0.6),
        ],
        "Risk-Aware A*": [
            min(1.0, risk_m.path_length_m / max(risk_m.path_length_m, 1e-6) * 0.8),
            1.0 - min(1.0, risk_m.avg_risk * 2),
            1.0 - min(1.0, risk_m.cvar_risk * 1.5),
            risk_m.safety_score,
            min(1.0, risk_m.compute_ms / max(risk_m.compute_ms, 1e-6) * 0.6),
        ],
    }
    st.plotly_chart(
        plot_radar_comparison(
            labels=["Efficiency", "Low avg risk", "Low CVaR risk",
                    "Safety score", "Compute speed"],
            metrics_by_planner=radar_metrics,
            colors=[COLORS["info"], COLORS["secondary"]],
            title="Normalised planner profile (higher is better)",
        ),
        use_container_width=True,
    )


# ---------------------------------------------------------------------------
# Side-by-side metrics table
# ---------------------------------------------------------------------------

st.markdown("### Metrics — single environment")

df = pd.DataFrame([
    {
        "Planner": base_m.name,
        "Path length (m)": round(base_m.path_length_m, 2),
        "Avg risk": round(base_m.avg_risk, 3),
        "CVaR risk": round(base_m.cvar_risk, 3),
        "Safety score": round(base_m.safety_score, 3),
        "Compute (ms)": round(base_m.compute_ms, 1),
        "Reached goal": "✓" if base_m.reached_goal else "✗",
    },
    {
        "Planner": risk_m.name,
        "Path length (m)": round(risk_m.path_length_m, 2),
        "Avg risk": round(risk_m.avg_risk, 3),
        "CVaR risk": round(risk_m.cvar_risk, 3),
        "Safety score": round(risk_m.safety_score, 3),
        "Compute (ms)": round(risk_m.compute_ms, 1),
        "Reached goal": "✓" if risk_m.reached_goal else "✗",
    },
])
st.dataframe(df, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Monte-Carlo sweep
# ---------------------------------------------------------------------------

st.markdown("### Statistical comparison (Monte-Carlo sweep)")
st.markdown(
    f"<p style='color:{COLORS['text_muted']};font-size:0.9rem;margin-top:-4px'>"
    f"Re-running both planners on <b>{n_seeds} independent</b> randomised environments. "
    f"Bar heights show the mean; differences in path length and risk are the headline trade-off."
    "</p>",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Running Monte-Carlo sweep…")
def _sweep(seed_base: int, grid_size: int, n_static: int, risk_weight: float,
           n_seeds: int) -> pd.DataFrame:
    rows = []
    for s in range(n_seeds):
        seed = seed_base + s * 7 + 1
        cfg = ScenarioConfig(
            grid_size=grid_size,
            start=(2, 2),
            goal=(grid_size - 3, grid_size - 3),
            n_static_obstacles=n_static,
            n_dynamic_obstacles=0,
            risk_weight=risk_weight,
            random_seed=seed,
        )
        env = build_environment(cfg, seed=seed)
        b = plan_astar(env, cfg.start, cfg.goal)
        r = plan_risk_aware(env, cfg.start, cfg.goal, risk_weight)
        bm = planner_metrics("A*", b, cfg)
        rm = planner_metrics("Risk-Aware A*", r, cfg)
        rows.append({"seed": seed, "planner": "A*",
                     "path_m": bm.path_length_m, "avg_risk": bm.avg_risk,
                     "cvar_risk": bm.cvar_risk, "safety": bm.safety_score,
                     "compute_ms": bm.compute_ms,
                     "success": int(bm.reached_goal)})
        rows.append({"seed": seed, "planner": "Risk-Aware A*",
                     "path_m": rm.path_length_m, "avg_risk": rm.avg_risk,
                     "cvar_risk": rm.cvar_risk, "safety": rm.safety_score,
                     "compute_ms": rm.compute_ms,
                     "success": int(rm.reached_goal)})
    return pd.DataFrame(rows)


sweep = _sweep(seed, grid_size, n_static, risk_weight, n_seeds)

agg = (sweep.groupby("planner")
       .agg(path_m_mean=("path_m", "mean"),
            path_m_std=("path_m", "std"),
            avg_risk_mean=("avg_risk", "mean"),
            cvar_risk_mean=("cvar_risk", "mean"),
            safety_mean=("safety", "mean"),
            compute_ms_mean=("compute_ms", "mean"),
            success_rate=("success", "mean"))
       .round(3)
       .reset_index())
st.dataframe(agg, use_container_width=True, hide_index=True)


# Bar charts
c1, c2, c3 = st.columns(3)
planners = agg["planner"].tolist()
palette = [COLORS["info"] if p == "A*" else COLORS["secondary"] for p in planners]

with c1:
    st.plotly_chart(
        plot_planner_comparison_bars(
            planners, agg["path_m_mean"].tolist(),
            "Mean path length", "meters", palette,
        ),
        use_container_width=True,
    )
with c2:
    st.plotly_chart(
        plot_planner_comparison_bars(
            planners, agg["avg_risk_mean"].tolist(),
            "Mean average risk", "risk (0–1)", palette,
        ),
        use_container_width=True,
    )
with c3:
    st.plotly_chart(
        plot_planner_comparison_bars(
            planners, agg["safety_mean"].tolist(),
            "Mean safety score", "score (0–1)", palette,
        ),
        use_container_width=True,
    )

c4, c5 = st.columns(2)
with c4:
    st.plotly_chart(
        plot_planner_comparison_bars(
            planners, agg["cvar_risk_mean"].tolist(),
            "Mean CVaR risk", "risk (0–1)", palette,
        ),
        use_container_width=True,
    )
with c5:
    st.plotly_chart(
        plot_planner_comparison_bars(
            planners, agg["compute_ms_mean"].tolist(),
            "Mean compute time", "ms", palette,
        ),
        use_container_width=True,
    )


# ---------------------------------------------------------------------------
# Discussion
# ---------------------------------------------------------------------------

st.divider()

with st.expander("Reading the comparison", expanded=False):
    st.markdown(
        f"""
        **Expected pattern.** The risk-aware planner should produce *slightly
        longer* paths in meters but *meaningfully lower* average and CVaR
        risk. This is the entire premise of risk-sensitive planning: pay a
        small efficiency tax for a large safety win. The radar chart makes
        this trade-off visible at a glance.

        **Compute time.** The risk-aware variant typically takes a similar
        amount of time to A* in this demo — both perform an A* search on the
        same grid, the cost function is just heavier. In the full DynNav
        system, contribution 01 (Learned A* Heuristics) accelerates these
        searches by ~35% on average.

        **Statistical confidence.** With 12 seeds the bar heights are only an
        estimate of the population mean. The standard deviations in the
        aggregate table give you a sense of the spread; in practice you'd
        run hundreds of seeds and report confidence intervals.

        **Why this matters for unknown environments.** When the robot does
        not have a complete map, every step is an opportunity for a surprise.
        Risk-aware planning keeps the robot *closer to the centreline* of
        free corridors, which leaves more options open when the next
        observation reveals a previously-unseen obstacle — the same property
        that drives the *returnability* constraint in contribution 04.
        """
    )
