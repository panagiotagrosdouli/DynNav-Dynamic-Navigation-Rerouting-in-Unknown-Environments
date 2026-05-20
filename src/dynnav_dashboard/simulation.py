"""
DynNav Dashboard — Synthetic Simulation Engine

Provides a lightweight, dependency-free (NumPy + standard library) simulation
of a robot navigating an unknown grid environment with:

* static and dynamic obstacles
* a perception-uncertainty field
* two planners — classical A* and a risk-aware A* variant — sharing the same
  search infrastructure so comparisons are fair
* a replanning loop that mimics the discover-update-replan cycle of a real
  mobile robot

The module deliberately avoids any ROS2, Gazebo, or torch dependency so the
dashboard runs anywhere Python + Streamlit do.
"""

from __future__ import annotations

import copy
import heapq
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .config import ScenarioConfig

Coord = Tuple[int, int]


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------


@dataclass
class Environment:
    """Static + dynamic obstacle map plus an uncertainty field.

    All grids are float32, oriented so ``grid[y, x]`` matches the natural
    Plotly heatmap convention.
    """

    grid_size: int
    static: np.ndarray                       # (H, W) in {0, 1}
    dynamic: np.ndarray                      # (H, W) in {0, 1}
    uncertainty: np.ndarray                  # (H, W) in [0, 1]
    risk: np.ndarray                         # (H, W) in [0, 1]
    dynamic_obstacles: List[Dict]            # tracked moving obstacles

    @property
    def occupancy(self) -> np.ndarray:
        """Combined static + dynamic occupancy (binary)."""
        return np.clip(self.static + self.dynamic, 0, 1)

    def is_free(self, cell: Coord) -> bool:
        x, y = cell
        if not (0 <= x < self.grid_size and 0 <= y < self.grid_size):
            return False
        return self.occupancy[y, x] < 0.5


# ---------------------------------------------------------------------------
# Environment factory
# ---------------------------------------------------------------------------


def _place_rect_obstacles(
    grid: np.ndarray,
    rng: np.random.Generator,
    n: int,
    min_size: int,
    max_size: int,
    forbidden: Sequence[Coord],
    forbid_radius: int = 4,
) -> List[Dict]:
    """Drop ``n`` rectangular obstacles avoiding the forbidden cells."""

    H, W = grid.shape
    placed: List[Dict] = []
    attempts = 0
    while len(placed) < n and attempts < n * 50:
        attempts += 1
        w = int(rng.integers(min_size, max_size + 1))
        h = int(rng.integers(min_size, max_size + 1))
        x = int(rng.integers(2, W - w - 2))
        y = int(rng.integers(2, H - h - 2))

        # Don't smother start/goal
        if any(abs((x + w // 2) - fx) < forbid_radius
               and abs((y + h // 2) - fy) < forbid_radius
               for fx, fy in forbidden):
            continue

        grid[y:y + h, x:x + w] = 1.0
        placed.append({"x": x, "y": y, "w": w, "h": h})
    return placed


def _build_uncertainty_field(
    grid_size: int,
    rng: np.random.Generator,
    sigma: float,
    n_peaks: int = 4,
) -> np.ndarray:
    """Smooth, multi-peak uncertainty field in [0, 1]."""

    H = W = grid_size
    yy, xx = np.mgrid[0:H, 0:W]
    field_ = np.zeros((H, W), dtype=np.float32)

    for _ in range(n_peaks):
        cx = rng.integers(3, W - 3)
        cy = rng.integers(3, H - 3)
        amp = float(rng.uniform(0.4, 1.0))
        s = float(rng.uniform(sigma * 0.7, sigma * 1.4))
        field_ += amp * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * s ** 2))

    # Always add a baseline "fog of war" gradient — uncertainty grows with
    # distance from origin (sensor range is finite).
    base = (xx + yy) / (2 * (H + W))
    field_ += 0.25 * base

    field_ = field_ / (field_.max() + 1e-9)
    return field_.astype(np.float32)


def _build_risk_field(
    occupancy: np.ndarray,
    uncertainty: np.ndarray,
    inflation_radius: int,
) -> np.ndarray:
    """Risk = inflated obstacle proximity, modulated by uncertainty.

    This is a tractable proxy for the CVaR-style risk objective used in
    DynNav contribution 03 — close to obstacles ⇒ high risk, and the risk
    grows further where the perception system is less confident.
    """

    H, W = occupancy.shape
    yy, xx = np.mgrid[0:H, 0:W]
    risk = np.zeros_like(occupancy, dtype=np.float32)

    obs_y, obs_x = np.where(occupancy > 0.5)
    if len(obs_x) == 0:
        return risk

    # Distance transform (approximated) — for each cell, distance to nearest
    # obstacle. We do it in chunks to keep memory tame on small grids.
    flat_y = yy.reshape(-1, 1)
    flat_x = xx.reshape(-1, 1)
    # (N_cells, N_obs)
    d2 = (flat_y - obs_y[None, :]) ** 2 + (flat_x - obs_x[None, :]) ** 2
    dist = np.sqrt(d2.min(axis=1)).reshape(H, W)

    # Exponential falloff — strong near obstacles, fades by inflation_radius
    proximity_risk = np.exp(-dist / max(inflation_radius, 1))

    # Modulate by uncertainty (uncertain regions are riskier to traverse)
    risk = 0.7 * proximity_risk + 0.3 * proximity_risk * uncertainty
    risk = np.clip(risk, 0.0, 1.0)
    # Obstacles themselves are maximally risky
    risk[occupancy > 0.5] = 1.0
    return risk.astype(np.float32)


def build_environment(cfg: ScenarioConfig, seed: Optional[int] = None) -> Environment:
    """Construct a randomised but reproducible environment."""

    rng = np.random.default_rng(cfg.random_seed if seed is None else seed)
    H = W = cfg.grid_size

    static = np.zeros((H, W), dtype=np.float32)
    dynamic = np.zeros((H, W), dtype=np.float32)

    _place_rect_obstacles(
        static, rng,
        n=cfg.n_static_obstacles,
        min_size=cfg.obstacle_min_size,
        max_size=cfg.obstacle_max_size,
        forbidden=[cfg.start, cfg.goal],
    )

    # Dynamic obstacles are 2x2 blobs with a velocity vector
    dyn_list: List[Dict] = []
    for _ in range(cfg.n_dynamic_obstacles):
        x = int(rng.integers(6, W - 6))
        y = int(rng.integers(6, H - 6))
        vx = int(rng.choice([-1, 1]))
        vy = int(rng.choice([-1, 1]))
        dyn_list.append({"x": x, "y": y, "vx": vx, "vy": vy, "size": 2})

    # Render the initial dynamic positions
    _render_dynamic(dynamic, dyn_list, H, W)

    uncertainty = _build_uncertainty_field(cfg.grid_size, rng, cfg.uncertainty_sigma)
    risk = _build_risk_field(static + dynamic, uncertainty, cfg.risk_inflation_radius)

    return Environment(
        grid_size=cfg.grid_size,
        static=static,
        dynamic=dynamic,
        uncertainty=uncertainty,
        risk=risk,
        dynamic_obstacles=dyn_list,
    )


def _render_dynamic(grid: np.ndarray, dyn: List[Dict], H: int, W: int) -> None:
    grid.fill(0.0)
    for d in dyn:
        x0 = max(0, d["x"])
        y0 = max(0, d["y"])
        x1 = min(W, d["x"] + d["size"])
        y1 = min(H, d["y"] + d["size"])
        grid[y0:y1, x0:x1] = 1.0


def step_dynamic(env: Environment, cfg: ScenarioConfig) -> None:
    """Advance dynamic obstacles by one step (bouncing off walls / statics)."""

    H = W = env.grid_size
    for d in env.dynamic_obstacles:
        nx = d["x"] + d["vx"]
        ny = d["y"] + d["vy"]

        # Reflect off boundaries
        if nx < 1 or nx + d["size"] >= W - 1:
            d["vx"] *= -1
            nx = d["x"] + d["vx"]
        if ny < 1 or ny + d["size"] >= H - 1:
            d["vy"] *= -1
            ny = d["y"] + d["vy"]

        # Reflect off static obstacles
        if env.static[ny:ny + d["size"], nx:nx + d["size"]].sum() > 0:
            d["vx"] *= -1
            d["vy"] *= -1
            nx = d["x"] + d["vx"]
            ny = d["y"] + d["vy"]

        d["x"], d["y"] = nx, ny

    _render_dynamic(env.dynamic, env.dynamic_obstacles, H, W)
    # Re-bake the risk field — cheap on small grids
    env.risk = _build_risk_field(
        env.static + env.dynamic, env.uncertainty, cfg.risk_inflation_radius
    )


# ---------------------------------------------------------------------------
# Planners
# ---------------------------------------------------------------------------


@dataclass
class PlannerResult:
    name: str
    path: List[Coord]
    expansions: int
    runtime_ms: float
    cost: float
    avg_risk: float
    max_risk: float
    success: bool


def _neighbours(cell: Coord, grid_size: int) -> List[Tuple[Coord, float]]:
    x, y = cell
    out: List[Tuple[Coord, float]] = []
    for dx, dy, c in (
        (1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
        (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142),
    ):
        nx, ny = x + dx, y + dy
        if 0 <= nx < grid_size and 0 <= ny < grid_size:
            out.append(((nx, ny), c))
    return out


def _heuristic(a: Coord, b: Coord) -> float:
    # Octile distance — admissible & consistent for 8-connected grids
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    return (dx + dy) + (1.4142 - 2) * min(dx, dy)


def _reconstruct(came_from: Dict[Coord, Coord], current: Coord) -> List[Coord]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def _astar_core(
    env: Environment,
    start: Coord,
    goal: Coord,
    risk_weight: float,
) -> Tuple[List[Coord], int, float]:
    """Shared A* routine. ``risk_weight`` ≥ 0 enables the risk-aware variant.

    Returns ``(path, n_expansions, accumulated_cost)``. ``path`` is empty
    when the search fails.
    """

    if not env.is_free(start) or not env.is_free(goal):
        return [], 0, float("inf")

    open_heap: List[Tuple[float, Coord]] = []
    heapq.heappush(open_heap, (0.0, start))
    came_from: Dict[Coord, Coord] = {}
    g_score: Dict[Coord, float] = {start: 0.0}
    closed: set = set()
    expansions = 0

    while open_heap:
        _, current = heapq.heappop(open_heap)
        if current in closed:
            continue
        closed.add(current)
        expansions += 1

        if current == goal:
            return _reconstruct(came_from, current), expansions, g_score[current]

        for nb, step_cost in _neighbours(current, env.grid_size):
            if not env.is_free(nb):
                continue
            risk_penalty = risk_weight * float(env.risk[nb[1], nb[0]])
            tentative = g_score[current] + step_cost + risk_penalty
            if tentative < g_score.get(nb, float("inf")):
                g_score[nb] = tentative
                came_from[nb] = current
                f = tentative + _heuristic(nb, goal)
                heapq.heappush(open_heap, (f, nb))

    return [], expansions, float("inf")


def plan_astar(env: Environment, start: Coord, goal: Coord) -> PlannerResult:
    """Classical A* — ignores the risk field entirely."""

    t0 = time.perf_counter()
    path, expansions, cost = _astar_core(env, start, goal, risk_weight=0.0)
    runtime_ms = (time.perf_counter() - t0) * 1000.0
    return _wrap_result("A* (baseline)", env, path, expansions, runtime_ms, cost)


def plan_risk_aware(
    env: Environment,
    start: Coord,
    goal: Coord,
    risk_weight: float,
) -> PlannerResult:
    """Risk-aware A* — adds a weighted risk penalty to the edge cost.

    This is a lightweight stand-in for DynNav's CVaR-A* planner (contribution
    03). It produces qualitatively the same behaviour — paths bend away from
    obstacles into safer, lower-uncertainty corridors — without requiring the
    full belief-space machinery.
    """

    t0 = time.perf_counter()
    path, expansions, cost = _astar_core(env, start, goal, risk_weight=risk_weight)
    runtime_ms = (time.perf_counter() - t0) * 1000.0
    return _wrap_result(
        "Risk-Aware A* (CVaR proxy)", env, path, expansions, runtime_ms, cost,
    )


def _wrap_result(
    name: str,
    env: Environment,
    path: List[Coord],
    expansions: int,
    runtime_ms: float,
    cost: float,
) -> PlannerResult:
    if not path:
        return PlannerResult(
            name=name, path=[], expansions=expansions,
            runtime_ms=runtime_ms, cost=float("inf"),
            avg_risk=1.0, max_risk=1.0, success=False,
        )

    risks = [float(env.risk[y, x]) for x, y in path]
    return PlannerResult(
        name=name,
        path=path,
        expansions=expansions,
        runtime_ms=runtime_ms,
        cost=cost,
        avg_risk=float(np.mean(risks)),
        max_risk=float(np.max(risks)),
        success=True,
    )


# ---------------------------------------------------------------------------
# Closed-loop replanning simulation
# ---------------------------------------------------------------------------


@dataclass
class RolloutFrame:
    step: int
    robot: Coord
    path_remaining: List[Coord]
    dynamic_snapshot: np.ndarray
    risk_snapshot: np.ndarray
    replanned: bool
    replan_count: int
    runtime_ms: float


@dataclass
class RolloutResult:
    frames: List[RolloutFrame] = field(default_factory=list)
    final_robot: Coord = (0, 0)
    reached_goal: bool = False
    total_replans: int = 0
    total_distance: float = 0.0
    avg_risk: float = 0.0
    max_risk: float = 0.0
    avg_compute_ms: float = 0.0
    collisions: int = 0


def simulate_rollout(
    env: Environment,
    cfg: ScenarioConfig,
    use_risk_aware: bool = True,
    dynamic_step_every: int = 2,
) -> RolloutResult:
    """Run a closed-loop navigation episode with online replanning.

    The robot plans a path, executes one step, refreshes its (partial) view of
    the world — which may include a newly-visible dynamic obstacle — and
    replans whenever its remaining path is blocked or fundamentally compromised.

    The supplied ``env`` is **not** mutated: a deep copy is created internally
    so that callers (e.g. Streamlit caches) can safely reuse the environment
    afterwards. Snapshots of the evolving dynamic / risk grids are captured
    per-frame for playback.
    """

    # Work on a private copy so we never poison a cached environment.
    env = copy.deepcopy(env)

    start = cfg.start
    goal = cfg.goal
    robot: Coord = start

    planner = plan_risk_aware if use_risk_aware else plan_astar
    risk_w = cfg.risk_weight

    def _plan() -> PlannerResult:
        if use_risk_aware:
            return planner(env, robot, goal, risk_w)  # type: ignore[arg-type]
        return planner(env, robot, goal)              # type: ignore[misc]

    result = _plan()
    path = list(result.path[1:]) if result.path else []   # drop the current cell
    total_compute = result.runtime_ms
    replans = 0
    risks: List[float] = []
    runtimes: List[float] = [result.runtime_ms]
    distance = 0.0
    collisions = 0
    stuck_counter = 0
    max_stuck = 6  # consecutive failed plans before giving up

    out = RolloutResult()
    out.frames.append(RolloutFrame(
        step=0, robot=robot, path_remaining=list(result.path),
        dynamic_snapshot=env.dynamic.copy(),
        risk_snapshot=env.risk.copy(),
        replanned=True, replan_count=replans,
        runtime_ms=result.runtime_ms,
    ))

    for step in range(1, cfg.max_steps + 1):
        replanned = False
        rt = 0.0

        # --- 1. If we have no path, attempt to recover by replanning -------
        if not path:
            new_result = _plan()
            rt = new_result.runtime_ms
            total_compute += rt
            runtimes.append(rt)
            replans += 1
            replanned = True
            path = list(new_result.path[1:]) if new_result.path else []
            if not path:
                stuck_counter += 1
                if stuck_counter >= max_stuck:
                    # Genuinely blocked — record the frame and stop.
                    out.frames.append(RolloutFrame(
                        step=step, robot=robot,
                        path_remaining=[robot],
                        dynamic_snapshot=env.dynamic.copy(),
                        risk_snapshot=env.risk.copy(),
                        replanned=replanned, replan_count=replans, runtime_ms=rt,
                    ))
                    break
                # Otherwise: let the world move, try again next step.
                if step % max(dynamic_step_every, 1) == 0:
                    step_dynamic(env, cfg)
                out.frames.append(RolloutFrame(
                    step=step, robot=robot,
                    path_remaining=[robot],
                    dynamic_snapshot=env.dynamic.copy(),
                    risk_snapshot=env.risk.copy(),
                    replanned=replanned, replan_count=replans, runtime_ms=rt,
                ))
                continue
            stuck_counter = 0

        # --- 2. Try to execute one step ------------------------------------
        next_cell = path[0]
        if env.dynamic[next_cell[1], next_cell[0]] > 0.5 \
                or env.static[next_cell[1], next_cell[0]] > 0.5:
            # Blocked — count it (only if dynamic), wait this turn, replan next.
            if env.dynamic[next_cell[1], next_cell[0]] > 0.5:
                collisions += 1
            path = []  # force replan on the next iteration
        else:
            path.pop(0)
            distance += float(np.hypot(next_cell[0] - robot[0],
                                       next_cell[1] - robot[1]))
            robot = next_cell
            risks.append(float(env.risk[robot[1], robot[0]]))

        # --- 3. Goal check -------------------------------------------------
        if robot == goal:
            out.reached_goal = True
            out.frames.append(RolloutFrame(
                step=step, robot=robot, path_remaining=[robot],
                dynamic_snapshot=env.dynamic.copy(),
                risk_snapshot=env.risk.copy(),
                replanned=replanned, replan_count=replans, runtime_ms=rt,
            ))
            break

        # --- 4. Advance the world -----------------------------------------
        if step % max(dynamic_step_every, 1) == 0:
            step_dynamic(env, cfg)

        # --- 5. Re-evaluate forward path ----------------------------------
        if path and any(
            env.dynamic[y, x] > 0.5 or env.static[y, x] > 0.5
            for x, y in path[:cfg.sensing_radius]
        ):
            # Lookahead invalidated — replan now, this turn.
            new_result = _plan()
            rt += new_result.runtime_ms
            total_compute += new_result.runtime_ms
            runtimes.append(new_result.runtime_ms)
            replans += 1
            replanned = True
            path = list(new_result.path[1:]) if new_result.path else []

        out.frames.append(RolloutFrame(
            step=step, robot=robot,
            path_remaining=[robot] + path,
            dynamic_snapshot=env.dynamic.copy(),
            risk_snapshot=env.risk.copy(),
            replanned=replanned, replan_count=replans, runtime_ms=rt,
        ))

    out.final_robot = robot
    out.total_replans = replans
    out.total_distance = distance
    out.avg_risk = float(np.mean(risks)) if risks else 0.0
    out.max_risk = float(np.max(risks)) if risks else 0.0
    out.avg_compute_ms = float(np.mean(runtimes)) if runtimes else 0.0
    out.collisions = collisions
    return out
