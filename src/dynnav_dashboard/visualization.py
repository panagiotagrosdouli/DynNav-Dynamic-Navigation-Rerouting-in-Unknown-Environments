"""
DynNav Dashboard — Visualisation Helpers

Plotly-based figures for the navigation grid, risk heatmaps, planner
comparisons, and bar/line charts. All figures share a consistent dark
research-grade theme defined in :mod:`config`.
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

import numpy as np
import plotly.graph_objects as go

from .config import COLORS, PLOTLY_RISK_SCALE, PLOTLY_UNCERTAINTY_SCALE
from .simulation import Environment, PlannerResult, RolloutFrame

Coord = Tuple[int, int]


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------


def _apply_theme(fig: go.Figure, height: int = 540, title: Optional[str] = None) -> go.Figure:
    """Apply the shared dark research theme to a Plotly figure."""

    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=40 if title else 10, b=10),
        paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface"],
        font=dict(color=COLORS["text"], family="Inter, sans-serif", size=13),
        title=dict(text=title, font=dict(size=15, color=COLORS["text"])) if title else None,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor=COLORS["border"],
            borderwidth=1,
        ),
        xaxis=dict(
            showgrid=False, zeroline=False, showticklabels=False,
            scaleanchor="y", scaleratio=1,
        ),
        yaxis=dict(
            showgrid=False, zeroline=False, showticklabels=False,
            autorange="reversed",  # match conventional grid orientation
        ),
    )
    return fig


# ---------------------------------------------------------------------------
# Navigation map (occupancy + paths + robot + goal)
# ---------------------------------------------------------------------------


def plot_navigation_map(
    env: Environment,
    paths: Sequence[Tuple[str, List[Coord], str]],
    start: Coord,
    goal: Coord,
    robot: Optional[Coord] = None,
    show_risk: bool = False,
    show_uncertainty: bool = False,
    title: Optional[str] = None,
) -> go.Figure:
    """Render the environment plus zero-or-more annotated planner paths.

    Parameters
    ----------
    paths
        Iterable of ``(label, [(x, y), ...], color)`` triples.
    show_risk
        Overlay the risk field as a heatmap. Mutually exclusive with
        ``show_uncertainty``.
    """

    fig = go.Figure()

    # Background — either occupancy alone, or a heatmap
    if show_risk:
        fig.add_trace(go.Heatmap(
            z=env.risk,
            colorscale=PLOTLY_RISK_SCALE,
            zmin=0, zmax=1,
            showscale=True,
            colorbar=dict(
                title=dict(text="Risk", side="right"),
                thickness=12, len=0.6,
                bgcolor="rgba(0,0,0,0)",
                tickfont=dict(color=COLORS["text"]),
            ),
            hoverinfo="skip",
        ))
    elif show_uncertainty:
        fig.add_trace(go.Heatmap(
            z=env.uncertainty,
            colorscale=PLOTLY_UNCERTAINTY_SCALE,
            zmin=0, zmax=1,
            showscale=True,
            colorbar=dict(
                title=dict(text="Uncertainty", side="right"),
                thickness=12, len=0.6,
                bgcolor="rgba(0,0,0,0)",
                tickfont=dict(color=COLORS["text"]),
            ),
            hoverinfo="skip",
        ))
    else:
        # Plain occupancy
        occ = env.occupancy.copy()
        fig.add_trace(go.Heatmap(
            z=occ,
            colorscale=[[0, COLORS["surface"]], [1, COLORS["obstacle"]]],
            showscale=False, hoverinfo="skip",
            zmin=0, zmax=1,
        ))

    # Static obstacles outline (always visible)
    sy, sx = np.where(env.static > 0.5)
    if len(sx) > 0:
        fig.add_trace(go.Scatter(
            x=sx, y=sy, mode="markers",
            marker=dict(size=8, color=COLORS["text_muted"], symbol="square", opacity=0.55),
            name="Static obstacle", hoverinfo="skip", showlegend=True,
        ))

    # Dynamic obstacles (highlight)
    dy, dx = np.where(env.dynamic > 0.5)
    if len(dx) > 0:
        fig.add_trace(go.Scatter(
            x=dx, y=dy, mode="markers",
            marker=dict(
                size=11, color=COLORS["highlight"], symbol="square",
                line=dict(color=COLORS["danger"], width=1.5),
            ),
            name="Dynamic obstacle", hoverinfo="skip",
        ))

    # Planner paths
    for label, path, color in paths:
        if not path:
            continue
        xs = [p[0] for p in path]
        ys = [p[1] for p in path]
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines",
            line=dict(color=color, width=3.5),
            name=label, hoverinfo="name",
            opacity=0.95,
        ))

    # Start / Goal markers
    fig.add_trace(go.Scatter(
        x=[start[0]], y=[start[1]], mode="markers+text",
        marker=dict(size=18, color=COLORS["info"], symbol="circle",
                    line=dict(color=COLORS["text"], width=2)),
        text=["Start"], textposition="top center",
        textfont=dict(color=COLORS["text"], size=11),
        name="Start", hoverinfo="name",
    ))
    fig.add_trace(go.Scatter(
        x=[goal[0]], y=[goal[1]], mode="markers+text",
        marker=dict(size=18, color=COLORS["success"], symbol="star",
                    line=dict(color=COLORS["text"], width=2)),
        text=["Goal"], textposition="top center",
        textfont=dict(color=COLORS["text"], size=11),
        name="Goal", hoverinfo="name",
    ))

    # Robot position (rollout playback)
    if robot is not None:
        fig.add_trace(go.Scatter(
            x=[robot[0]], y=[robot[1]], mode="markers",
            marker=dict(
                size=22, color=COLORS["primary"], symbol="diamond",
                line=dict(color=COLORS["text"], width=2),
            ),
            name="Robot", hoverinfo="name",
        ))

    _apply_theme(fig, height=580, title=title)
    fig.update_xaxes(range=[-0.5, env.grid_size - 0.5])
    fig.update_yaxes(range=[env.grid_size - 0.5, -0.5])
    return fig


# ---------------------------------------------------------------------------
# Risk heatmap (standalone view used on the Risk Map page)
# ---------------------------------------------------------------------------


def plot_risk_heatmap(
    field: np.ndarray,
    title: str,
    colorscale: List[List],
    overlay_path: Optional[List[Coord]] = None,
) -> go.Figure:
    fig = go.Figure(data=go.Heatmap(
        z=field,
        colorscale=colorscale,
        zmin=0, zmax=1,
        colorbar=dict(
            title=dict(text=title, side="right"),
            thickness=12, len=0.7,
            tickfont=dict(color=COLORS["text"]),
        ),
        hovertemplate="x=%{x}<br>y=%{y}<br>value=%{z:.3f}<extra></extra>",
    ))
    if overlay_path:
        xs = [p[0] for p in overlay_path]
        ys = [p[1] for p in overlay_path]
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines",
            line=dict(color=COLORS["text"], width=3),
            name="Planned path", hoverinfo="name",
        ))
    _apply_theme(fig, height=520, title=title)
    fig.update_xaxes(range=[-0.5, field.shape[1] - 0.5])
    fig.update_yaxes(range=[field.shape[0] - 0.5, -0.5])
    return fig


# ---------------------------------------------------------------------------
# Planner comparison bar chart
# ---------------------------------------------------------------------------


def plot_planner_comparison_bars(
    labels: Sequence[str],
    metric_values: Sequence[float],
    title: str,
    y_label: str,
    palette: Sequence[str],
) -> go.Figure:
    fig = go.Figure(data=go.Bar(
        x=list(labels),
        y=list(metric_values),
        marker=dict(color=list(palette), line=dict(color=COLORS["border"], width=1)),
        text=[f"{v:.2f}" for v in metric_values],
        textposition="outside",
        textfont=dict(color=COLORS["text"]),
        hovertemplate="%{x}<br>%{y:.3f}<extra></extra>",
    ))
    fig.update_layout(
        height=360,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface"],
        font=dict(color=COLORS["text"], family="Inter, sans-serif"),
        title=dict(text=title, font=dict(size=15, color=COLORS["text"])),
        xaxis=dict(showgrid=False, color=COLORS["text_muted"]),
        yaxis=dict(
            gridcolor=COLORS["border"], color=COLORS["text_muted"],
            title=dict(text=y_label, font=dict(color=COLORS["text_muted"])),
        ),
        showlegend=False,
    )
    return fig


def plot_radar_comparison(
    labels: Sequence[str],
    metrics_by_planner: dict,
    colors: Sequence[str],
    title: str = "Planner profile",
) -> go.Figure:
    """Radar chart comparing planners on normalised metrics (higher = better)."""

    fig = go.Figure()
    for (planner_name, values), color in zip(metrics_by_planner.items(), colors):
        fig.add_trace(go.Scatterpolar(
            r=list(values) + [values[0]],
            theta=list(labels) + [labels[0]],
            fill="toself",
            name=planner_name,
            line=dict(color=color, width=2),
            opacity=0.55,
        ))
    fig.update_layout(
        height=420,
        polar=dict(
            bgcolor=COLORS["surface"],
            radialaxis=dict(
                visible=True, range=[0, 1], showline=False,
                gridcolor=COLORS["border"], color=COLORS["text_muted"],
                tickfont=dict(size=10),
            ),
            angularaxis=dict(
                gridcolor=COLORS["border"], color=COLORS["text_muted"],
            ),
        ),
        paper_bgcolor=COLORS["surface"],
        font=dict(color=COLORS["text"], family="Inter, sans-serif"),
        title=dict(text=title, font=dict(size=15, color=COLORS["text"])),
        showlegend=True,
        legend=dict(orientation="h", y=-0.05),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def plot_risk_profile(
    path_a: List[Coord], risks_a: List[float], label_a: str, color_a: str,
    path_b: List[Coord], risks_b: List[float], label_b: str, color_b: str,
) -> go.Figure:
    """Line plot — risk along path index for two planners."""

    fig = go.Figure()
    if risks_a:
        fig.add_trace(go.Scatter(
            x=list(range(len(risks_a))), y=risks_a, mode="lines",
            line=dict(color=color_a, width=2.5),
            name=label_a, hovertemplate="step=%{x}<br>risk=%{y:.3f}<extra></extra>",
        ))
    if risks_b:
        fig.add_trace(go.Scatter(
            x=list(range(len(risks_b))), y=risks_b, mode="lines",
            line=dict(color=color_b, width=2.5),
            name=label_b, hovertemplate="step=%{x}<br>risk=%{y:.3f}<extra></extra>",
        ))
    fig.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=40, b=30),
        paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface"],
        font=dict(color=COLORS["text"], family="Inter, sans-serif"),
        title=dict(text="Risk along path", font=dict(size=14, color=COLORS["text"])),
        xaxis=dict(gridcolor=COLORS["border"], color=COLORS["text_muted"],
                   title=dict(text="Path index", font=dict(color=COLORS["text_muted"]))),
        yaxis=dict(gridcolor=COLORS["border"], color=COLORS["text_muted"], range=[0, 1],
                   title=dict(text="Risk", font=dict(color=COLORS["text_muted"]))),
        legend=dict(orientation="h", y=-0.2),
    )
    return fig


def plot_replan_timeline(frames: Sequence[RolloutFrame]) -> go.Figure:
    """Step number vs replan events, with compute time as bar height."""

    steps = [f.step for f in frames]
    rts = [f.runtime_ms for f in frames]
    colors = [COLORS["highlight"] if f.replanned else COLORS["primary"] for f in frames]

    fig = go.Figure(data=go.Bar(
        x=steps, y=rts, marker=dict(color=colors),
        hovertemplate="step=%{x}<br>compute=%{y:.2f} ms<extra></extra>",
    ))
    fig.update_layout(
        height=260,
        margin=dict(l=20, r=20, t=40, b=30),
        paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface"],
        font=dict(color=COLORS["text"], family="Inter, sans-serif"),
        title=dict(text="Planner runtime per step (orange = replan)",
                   font=dict(size=14, color=COLORS["text"])),
        xaxis=dict(gridcolor=COLORS["border"], color=COLORS["text_muted"],
                   title=dict(text="Simulation step", font=dict(color=COLORS["text_muted"]))),
        yaxis=dict(gridcolor=COLORS["border"], color=COLORS["text_muted"],
                   title=dict(text="ms", font=dict(color=COLORS["text_muted"]))),
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# Module catalogue summary
# ---------------------------------------------------------------------------


def plot_category_breakdown(categories: Sequence[str]) -> go.Figure:
    from collections import Counter
    counts = Counter(categories)
    labels = list(counts.keys())
    values = list(counts.values())

    fig = go.Figure(data=go.Bar(
        x=values, y=labels, orientation="h",
        marker=dict(color=COLORS["primary"], line=dict(color=COLORS["border"], width=1)),
        text=values, textposition="outside",
        textfont=dict(color=COLORS["text"]),
        hovertemplate="%{y}: %{x} modules<extra></extra>",
    ))
    fig.update_layout(
        height=360,
        margin=dict(l=10, r=20, t=40, b=20),
        paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface"],
        font=dict(color=COLORS["text"], family="Inter, sans-serif"),
        title=dict(text="Research modules per category",
                   font=dict(size=15, color=COLORS["text"])),
        xaxis=dict(gridcolor=COLORS["border"], color=COLORS["text_muted"]),
        yaxis=dict(gridcolor=COLORS["border"], color=COLORS["text_muted"]),
        showlegend=False,
    )
    return fig
