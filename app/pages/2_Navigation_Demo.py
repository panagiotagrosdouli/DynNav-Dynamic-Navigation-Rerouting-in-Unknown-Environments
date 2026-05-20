"""
DynNav Dashboard — Navigation Demo Page
=======================================

Step-by-step playback of a closed-loop navigation episode: the robot
plans a path, executes one step, dynamic obstacles move, and the planner
reroutes whenever the path is invalidated. Designed to show — at a
research-talk pace — what online replanning actually looks like.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st  # noqa: E402

from dynnav_dashboard.config import (  # noqa: E402
    APP_ICON, APP_TITLE, COLORS, DEFAULT_SCENARIO, DEFAULT_THRESHOLDS,
    ScenarioConfig,
)
from dynnav_dashboard.simulation import (  # noqa: E402
    build_environment, simulate_rollout,
)
from dynnav_dashboard.metrics import rollout_metrics, summary_dict  # noqa: E402
from dynnav_dashboard.visualization import (  # noqa: E402
    plot_navigation_map, plot_replan_timeline,
)


st.set_page_config(
    page_title=f"Navigation Demo · {APP_TITLE}",
    page_icon=APP_ICON,
    layout="wide",
)


# ---------------------------------------------------------------------------
# Page styling
# ---------------------------------------------------------------------------

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
            margin: 0 0 1.0rem 0;
            max-width: 80ch;
        }}
        .dyn-event {{
            background: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 10px 14px;
            margin-bottom: 6px;
            color: {COLORS['text_muted']};
            font-size: 0.88rem;
        }}
        .dyn-event b {{ color: {COLORS['text']}; }}
        .dyn-event.replan {{ border-left: 3px solid {COLORS['highlight']}; }}
        .dyn-event.goal   {{ border-left: 3px solid {COLORS['success']}; }}
        .dyn-metric-mini {{
            background: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 10px 14px;
        }}
        .dyn-metric-mini .label {{
            color: {COLORS['text_muted']};
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .dyn-metric-mini .value {{
            color: {COLORS['text']};
            font-size: 1.35rem;
            font-weight: 700;
        }}
        .dyn-metric-mini .value.success {{ color: {COLORS['success']}; }}
        .dyn-metric-mini .value.warning {{ color: {COLORS['warning']}; }}
        .dyn-metric-mini .value.danger  {{ color: {COLORS['danger']}; }}
        .dyn-metric-mini .value.info    {{ color: {COLORS['info']}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown('<div class="dyn-section-title">🤖 Closed-Loop Navigation Demo</div>',
            unsafe_allow_html=True)
st.markdown(
    '<p class="dyn-section-sub">'
    'A synthetic robot navigates from start to goal in a partially-unknown '
    'environment with moving obstacles. Use the playback slider to walk through '
    'the episode. Orange highlights mark steps where the planner had to reroute.'
    '</p>',
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### Scenario controls")
    seed = st.number_input("Random seed", value=DEFAULT_SCENARIO.random_seed,
                           min_value=0, max_value=9999, step=1)
    grid_size = st.slider("Grid size", 20, 60, DEFAULT_SCENARIO.grid_size, step=5)
    n_static = st.slider("Static obstacles", 5, 30,
                         DEFAULT_SCENARIO.n_static_obstacles)
    n_dyn = st.slider("Dynamic obstacles", 0, 6,
                      DEFAULT_SCENARIO.n_dynamic_obstacles)
    risk_weight = st.slider("Risk weight (CVaR proxy)",
                            0.0, 5.0, DEFAULT_SCENARIO.risk_weight, step=0.25)
    planner_mode = st.radio("Planner",
                            ["Risk-Aware A*", "Classical A*"],
                            index=0, horizontal=False)
    dyn_step = st.slider("Dynamic step interval", 1, 5, 2,
                         help="How often (in sim steps) moving obstacles update.")

    if st.button("🔄 Regenerate scenario", use_container_width=True):
        for k in list(st.session_state.keys()):
            if k.startswith("nav_demo_"):
                del st.session_state[k]
        st.rerun()


# Build a cached rollout keyed on the controls
@st.cache_data(show_spinner="Simulating rollout…")
def _run_rollout(seed: int, grid_size: int, n_static: int, n_dyn: int,
                 risk_weight: float, planner_mode: str, dyn_step: int):
    cfg = ScenarioConfig(
        grid_size=grid_size,
        start=(2, 2),
        goal=(grid_size - 3, grid_size - 3),
        n_static_obstacles=n_static,
        n_dynamic_obstacles=n_dyn,
        risk_weight=risk_weight,
        random_seed=seed,
    )
    env = build_environment(cfg, seed=seed)
    rollout = simulate_rollout(
        env, cfg,
        use_risk_aware=(planner_mode == "Risk-Aware A*"),
        dynamic_step_every=dyn_step,
    )
    return cfg, env, rollout


cfg, env, rollout = _run_rollout(seed, grid_size, n_static, n_dyn,
                                  risk_weight, planner_mode, dyn_step)
metrics = rollout_metrics(planner_mode, rollout, cfg)
metric_cards = summary_dict(metrics, DEFAULT_THRESHOLDS)


# ---------------------------------------------------------------------------
# Playback row
# ---------------------------------------------------------------------------

total_steps = len(rollout.frames) - 1  # 0..N
step_idx = st.slider(
    "Playback step",
    min_value=0,
    max_value=max(total_steps, 0),
    value=max(total_steps, 0),
    help="Drag to scrub through the simulated rollout.",
)


col_map, col_side = st.columns([1.4, 1.0], gap="large")

frame = rollout.frames[step_idx]
# Build a transient view of the environment for this frame WITHOUT mutating
# the cached `env` object (Streamlit reuses it across reruns).
from dataclasses import replace as _dc_replace
env_view = _dc_replace(
    env,
    dynamic=frame.dynamic_snapshot,
    risk=frame.risk_snapshot,
)

executed = [f.robot for f in rollout.frames[: step_idx + 1]]
remaining = frame.path_remaining

with col_map:
    fig = plot_navigation_map(
        env_view,
        paths=[
            ("Executed path", executed, COLORS["primary"]),
            ("Planned path", remaining, COLORS["secondary"]),
        ],
        start=cfg.start,
        goal=cfg.goal,
        robot=frame.robot,
        show_risk=False,
        title=f"Step {frame.step} / {total_steps}"
              + ("  ·  REPLANNED" if frame.replanned else ""),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_side:
    st.markdown("#### Live metrics")
    grid_cols = st.columns(2)
    items = list(metric_cards.items())
    for i, (label, info) in enumerate(items):
        with grid_cols[i % 2]:
            st.markdown(
                f"""
                <div class="dyn-metric-mini">
                    <div class="label">{label}</div>
                    <div class="value {info['color']}">{info['value']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("#### Episode outcome")
    outcome_color = "success" if rollout.reached_goal else "danger"
    outcome_text = "✓ Goal reached" if rollout.reached_goal else "✗ Goal not reached"
    st.markdown(
        f"""
        <div class="dyn-metric-mini">
            <div class="label">status</div>
            <div class="value {outcome_color}">{outcome_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Replan timeline + recent events log
# ---------------------------------------------------------------------------

st.markdown("### Runtime profile")
st.plotly_chart(plot_replan_timeline(rollout.frames),
                use_container_width=True)

st.markdown("### Event log")

recent = list(rollout.frames[max(0, step_idx - 6): step_idx + 1])[::-1]
for f in recent:
    if f.replanned:
        st.markdown(
            f"<div class='dyn-event replan'>"
            f"<b>Step {f.step}</b> · Replan triggered "
            f"(runtime <b>{f.runtime_ms:.1f} ms</b>, "
            f"robot at <b>({f.robot[0]}, {f.robot[1]})</b>)"
            f"</div>",
            unsafe_allow_html=True,
        )
    elif f.robot == cfg.goal:
        st.markdown(
            f"<div class='dyn-event goal'><b>Step {f.step}</b> · Goal reached.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='dyn-event'>Step {f.step} · "
            f"moved to ({f.robot[0]}, {f.robot[1]})</div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------

st.divider()
with st.expander("What is happening under the hood?", expanded=False):
    st.markdown(
        f"""
        This demo runs a **closed-loop replanning loop** in pure Python — no
        ROS 2, no Gazebo. At every step:

        1. The planner (either classical A* or a risk-aware A* using the
           project's CVaR-proxy cost) finds a path from the robot's current
           cell to the goal.
        2. The robot advances **one cell** along that path.
        3. Dynamic obstacles step forward (bouncing off statics and walls).
        4. The robot inspects the next few cells of its plan. If a moving
           obstacle now blocks the path — or the risk-aware cost exceeds a
           threshold — it **replans**.

        The orange bars in the runtime chart mark replan events. In the full
        DynNav system, these replan calls would be served by the
        **risk-weighted CVaR-A\\* planner** (contribution 03), augmented by a
        **learned heuristic** (contribution 01) to keep latency low even on
        embedded hardware.

        The metrics use a **CVaR-style tail risk** (mean of the worst-10% of
        per-step risk values), which is the more meaningful safety statistic
        than a simple average: it captures *how bad the worst-case looked*,
        not just the average.
        """
    )
