"""
DynNav Dashboard — Metrics

Computes the navigation KPIs surfaced across the dashboard:

* path length (meters)
* replanning count
* collision risk (average and CVaR-style tail risk)
* safety score (a normalised composite in [0, 1])
* computation time (mean replan time in ms)

Everything is pure-Python / NumPy — no external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np

from .config import MetricThresholds, ScenarioConfig
from .simulation import PlannerResult, RolloutResult


@dataclass
class NavMetrics:
    """One row of headline navigation metrics."""

    name: str
    path_length_m: float
    replans: int
    collisions: int
    avg_risk: float
    cvar_risk: float
    safety_score: float
    compute_ms: float
    reached_goal: bool
    success_rate: float


def _cvar(values: List[float], alpha: float) -> float:
    """Conditional Value-at-Risk at level ``alpha`` (mean of the worst tail)."""

    if not values:
        return 0.0
    arr = np.asarray(values, dtype=np.float32)
    threshold = np.quantile(arr, alpha)
    tail = arr[arr >= threshold]
    return float(tail.mean()) if tail.size else float(arr.max())


def _safety_score(
    avg_risk: float,
    cvar_risk: float,
    collisions: int,
    replans: int,
    reached_goal: bool,
) -> float:
    """Composite safety score in [0, 1] — higher is safer.

    Combines:
      * how risky the executed path was (avg + tail),
      * whether any collisions occurred,
      * a mild penalty for excessive replanning (signals an unstable policy),
      * a hard penalty for not reaching the goal.
    """

    risk_term = 1.0 - 0.5 * avg_risk - 0.5 * cvar_risk
    risk_term = max(0.0, min(1.0, risk_term))

    collision_penalty = 0.25 * collisions
    replan_penalty = 0.02 * max(0, replans - 2)
    goal_penalty = 0.0 if reached_goal else 0.3

    score = risk_term - collision_penalty - replan_penalty - goal_penalty
    return float(max(0.0, min(1.0, score)))


def rollout_metrics(
    name: str,
    rollout: RolloutResult,
    cfg: ScenarioConfig,
    cvar_alpha: float = 0.90,
) -> NavMetrics:
    """Compute metrics for a closed-loop simulation rollout."""

    path = [f.robot for f in rollout.frames]
    risks: List[float] = []
    for f in rollout.frames:
        x, y = f.robot
        risks.append(float(f.risk_snapshot[y, x]))

    cvar_r = _cvar(risks, cvar_alpha)
    avg_r = float(np.mean(risks)) if risks else 0.0
    length_m = rollout.total_distance * cfg.cell_meters

    return NavMetrics(
        name=name,
        path_length_m=length_m,
        replans=rollout.total_replans,
        collisions=rollout.collisions,
        avg_risk=avg_r,
        cvar_risk=cvar_r,
        safety_score=_safety_score(
            avg_r, cvar_r,
            collisions=rollout.collisions,
            replans=rollout.total_replans,
            reached_goal=rollout.reached_goal,
        ),
        compute_ms=rollout.avg_compute_ms,
        reached_goal=rollout.reached_goal,
        success_rate=1.0 if rollout.reached_goal else 0.0,
    )


def planner_metrics(
    name: str,
    planner: PlannerResult,
    cfg: ScenarioConfig,
    cvar_alpha: float = 0.90,
) -> NavMetrics:
    """Compute metrics from a single planning episode (no rollout)."""

    if not planner.success:
        return NavMetrics(
            name=name, path_length_m=0.0, replans=0, collisions=0,
            avg_risk=1.0, cvar_risk=1.0, safety_score=0.0,
            compute_ms=planner.runtime_ms,
            reached_goal=False, success_rate=0.0,
        )

    # Euclidean length in meters
    pts = np.asarray(planner.path, dtype=np.float32)
    diffs = np.diff(pts, axis=0)
    length_cells = float(np.hypot(diffs[:, 0], diffs[:, 1]).sum())
    length_m = length_cells * cfg.cell_meters

    # Risks along the path were already computed in PlannerResult; recompute
    # CVaR from the avg/max as a fallback.
    risks = [planner.avg_risk, planner.max_risk]
    cvar_r = _cvar(risks, cvar_alpha) if risks else 0.0

    return NavMetrics(
        name=name,
        path_length_m=length_m,
        replans=0,
        collisions=0,
        avg_risk=planner.avg_risk,
        cvar_risk=cvar_r,
        safety_score=_safety_score(
            planner.avg_risk, cvar_r,
            collisions=0, replans=0, reached_goal=True,
        ),
        compute_ms=planner.runtime_ms,
        reached_goal=True,
        success_rate=1.0,
    )


# ---------------------------------------------------------------------------
# Pretty-printing helpers used by the Streamlit pages
# ---------------------------------------------------------------------------


def color_for(value: float, good: float, warn: float, lower_is_better: bool = True) -> str:
    """Return a semantic colour name for a metric value."""

    if lower_is_better:
        if value <= good:
            return "success"
        if value <= warn:
            return "warning"
        return "danger"
    # higher_is_better
    if value >= good:
        return "success"
    if value >= warn:
        return "warning"
    return "danger"


def summary_dict(m: NavMetrics, t: MetricThresholds) -> Dict[str, Dict]:
    """Bundle a metric + its colour tag for downstream rendering."""

    return {
        "Path length (m)": {
            "value": f"{m.path_length_m:.2f}",
            "raw": m.path_length_m,
            "color": "info",
        },
        "Replans": {
            "value": str(m.replans),
            "raw": m.replans,
            "color": color_for(m.replans, t.replans_good, t.replans_warn),
        },
        "Avg collision risk": {
            "value": f"{m.avg_risk:.2%}",
            "raw": m.avg_risk,
            "color": color_for(m.avg_risk, t.collision_risk_good, t.collision_risk_warn),
        },
        "CVaR risk": {
            "value": f"{m.cvar_risk:.2%}",
            "raw": m.cvar_risk,
            "color": color_for(m.cvar_risk, t.collision_risk_good, t.collision_risk_warn),
        },
        "Safety score": {
            "value": f"{m.safety_score:.2f}",
            "raw": m.safety_score,
            "color": color_for(
                m.safety_score, t.safety_score_good, t.safety_score_warn,
                lower_is_better=False,
            ),
        },
        "Compute (ms)": {
            "value": f"{m.compute_ms:.1f}",
            "raw": m.compute_ms,
            "color": color_for(m.compute_ms, t.compute_ms_good, t.compute_ms_warn),
        },
    }
