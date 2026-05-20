"""
DynNav Dashboard — Architecture Page
====================================

Renders the DynNav software stack as a layered Graphviz diagram and as an
interactive table-of-layers. Designed to give a visiting reviewer a
five-second mental model of how the project is structured.
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
    APP_ICON, APP_TITLE, COLORS, ARCH_LAYERS, RESEARCH_MODULES, REPO_URL,
)


st.set_page_config(
    page_title=f"Architecture · {APP_TITLE}",
    page_icon=APP_ICON,
    layout="wide",
)


# Re-apply the shared styling
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
        .dyn-layer-card {{
            background: {COLORS['surface']};
            border-left: 4px solid {COLORS['primary']};
            border-radius: 8px;
            padding: 14px 18px;
            margin-bottom: 12px;
        }}
        .dyn-layer-card h4 {{
            margin: 0 0 6px 0;
            color: {COLORS['text']};
            font-size: 1.05rem;
        }}
        .dyn-layer-card p {{
            margin: 0;
            color: {COLORS['text_muted']};
            font-size: 0.9rem;
            line-height: 1.5;
        }}
        .dyn-chip {{
            display: inline-block;
            background: {COLORS['surface_alt']};
            border: 1px solid {COLORS['border']};
            color: {COLORS['text']};
            border-radius: 6px;
            padding: 2px 9px;
            font-size: 0.78rem;
            margin: 4px 4px 0 0;
        }}
        section[data-testid="stSidebar"] {{
            background-color: {COLORS['surface']};
            border-right: 1px solid {COLORS['border']};
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="dyn-section-title">🏗️ DynNav System Architecture</div>',
            unsafe_allow_html=True)
st.markdown(
    '<p class="dyn-section-sub">'
    'A layered view of the DynNav stack — from raw perception at the bottom, '
    'through the planning core, up to learning-based and foundation-model components. '
    'Safety, coordination, and robustness are cross-cutting concerns rendered as '
    'first-class layers.'
    '</p>',
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Graphviz layered diagram
# ---------------------------------------------------------------------------


def build_graphviz_diagram() -> str:
    """Construct the DOT description of the layered DynNav architecture."""

    bg = COLORS["bg"]
    edge = COLORS["border"]
    text = COLORS["text"]
    muted = COLORS["text_muted"]

    lines = [
        "digraph DynNav {",
        f'  bgcolor="{bg}";',
        '  rankdir=TB;',
        '  splines=ortho;',
        '  nodesep=0.35;',
        '  ranksep=0.55;',
        f'  node [shape=box, style="rounded,filled", fontname="Inter", fontsize=11, '
        f'fontcolor="{text}", color="{edge}", penwidth=1.2];',
        f'  edge [color="{muted}", arrowsize=0.7, penwidth=1.2];',
        '',
        '  // ROS 2 baseplate',
        f'  ros2 [label="ROS 2 Humble · Nav2 · TurtleBot3 · Gazebo", '
        f'fillcolor="{COLORS["surface_alt"]}", fontcolor="{muted}", height=0.55, width=4.4];',
    ]

    # One subgraph per layer; modules become children
    for i, layer in enumerate(ARCH_LAYERS):
        sg_id = f"cluster_{i}"
        lines += [
            f'  subgraph {sg_id} {{',
            f'    label="{layer.name}";',
            f'    style="rounded,filled";',
            f'    color="{layer.color}";',
            f'    fillcolor="{COLORS["surface"]}";',
            f'    fontcolor="{layer.color}";',
            f'    fontname="Inter";',
            f'    fontsize=12;',
            f'    margin=10;',
        ]
        for j, mod in enumerate(layer.modules):
            node_id = f"L{i}_M{j}"
            lines.append(
                f'    {node_id} [label="{mod}", fillcolor="{COLORS["surface_alt"]}", '
                f'color="{layer.color}", fontcolor="{COLORS["text"]}"];'
            )
        lines.append("  }")

    # Logical flow edges between successive layers (use the first node of each layer)
    layer_anchors = [f"L{i}_M0" for i in range(len(ARCH_LAYERS))]
    # Bottom-up flow: ROS2 -> perception -> planning -> safety -> learning -> foundation
    # We pick a stable ordering from the catalogue: 5 (perception) -> 4 (planning) ->
    # 2 (safety) -> 1 (learning) -> 0 (foundation), with security feeding planning too.
    order = [5, 4, 2, 3, 1, 0]  # indexes into ARCH_LAYERS
    chain = ["ros2"] + [layer_anchors[i] for i in order]
    for a, b in zip(chain, chain[1:]):
        lines.append(f'  "{a}" -> "{b}";')
    # Security (idx 6) feeds planning
    lines.append(f'  "{layer_anchors[6]}" -> "{layer_anchors[4]}" [style=dashed, label="anomaly", fontsize=9];')

    lines.append("}")
    return "\n".join(lines)


st.graphviz_chart(build_graphviz_diagram(), use_container_width=True)


# ---------------------------------------------------------------------------
# Layer-by-layer cards
# ---------------------------------------------------------------------------

st.markdown('<div class="dyn-section-title" style="margin-top:1.8rem">Layer notes</div>',
            unsafe_allow_html=True)
st.markdown(
    '<p class="dyn-section-sub">'
    'Each layer addresses a distinct concern. Click through to the Research Modules '
    'page for the full set of 26 contributions.'
    '</p>',
    unsafe_allow_html=True,
)

LAYER_BLURBS = {
    "Foundation Models": (
        "Large language and vision-language models translate human intent and "
        "rich visual scenes into navigation primitives — natural-language goals, "
        "semantic landmarks, and post-hoc failure explanations."
    ),
    "Learning Layer": (
        "Data-driven components — neural A* heuristics, PPO policies, "
        "curriculum-driven training, and federated learning — that augment the "
        "classical pipeline without replacing it."
    ),
    "Safety Layer": (
        "Formal and runtime safety mechanisms. Signal Temporal Logic monitors and "
        "Control Barrier Functions filter unsafe commands; safe-mode and "
        "returnability constraints keep the robot recoverable."
    ),
    "Coordination Layer": (
        "Mechanisms for multi-robot operation: Byzantine fault-tolerant plan "
        "consensus, federated training, and conflict-free path allocation."
    ),
    "Planning Core": (
        "The heart of the stack: A*/D* search, belief-space and CVaR risk "
        "planning, and next-best-view exploration."
    ),
    "Perception": (
        "Multi-modal sensing — LiDAR SLAM, Gaussian Splatting, NeRF uncertainty, "
        "event cameras with spiking nets, and EKF/UKF filters."
    ),
    "Security": (
        "Cyber-physical defences: anomaly detection on sensors, adversarial "
        "robustness evaluation, and causal root-cause analysis after failures."
    ),
}

for layer in ARCH_LAYERS:
    chips = "".join(f'<span class="dyn-chip">{m}</span>' for m in layer.modules)
    st.markdown(
        f"""
        <div class="dyn-layer-card" style="border-left-color:{layer.color}">
            <h4>{layer.name}</h4>
            <p>{LAYER_BLURBS.get(layer.name, '')}</p>
            <div style="margin-top:8px">{chips}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.divider()
st.markdown(
    f"<p style='color:{COLORS['text_muted']};font-size:0.85rem'>"
    f"Diagram generated with Graphviz · "
    f"<a href='{REPO_URL}' style='color:{COLORS['secondary']}'>upstream repository ↗</a>"
    "</p>",
    unsafe_allow_html=True,
)
