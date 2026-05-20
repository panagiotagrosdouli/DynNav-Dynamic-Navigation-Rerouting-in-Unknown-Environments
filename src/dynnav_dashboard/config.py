"""
DynNav Dashboard — Central Configuration

Defines the visual identity, default scenario parameters, and reusable constants
used across all Streamlit pages. Centralising these here keeps the look-and-feel
consistent and makes it trivial to retheme the entire app.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Branding / page configuration
# ---------------------------------------------------------------------------

APP_TITLE: str = "DynNav · Autonomous Navigation Research Dashboard"
APP_ICON: str = "🛰️"
APP_TAGLINE: str = (
    "Uncertainty-aware · Risk-sensitive · Learning-augmented · Formally verified"
)
AUTHOR: str = "Panagiota Grosdouli"
AFFILIATION: str = "Democritus University of Thrace — ECE"
REPO_URL: str = (
    "https://github.com/panagiotagrosdouli/"
    "DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments"
)

# ---------------------------------------------------------------------------
# Colour palette — tuned for a clean robotics / research aesthetic
# ---------------------------------------------------------------------------

COLORS: Dict[str, str] = {
    # Backgrounds / surfaces
    "bg":            "#0E1117",
    "surface":       "#161B22",
    "surface_alt":   "#1C2230",
    "border":        "#2A3140",

    # Text
    "text":          "#E6EDF3",
    "text_muted":    "#8B949E",

    # Brand / accents
    "primary":       "#3B82F6",   # vivid blue  — robot, planned path
    "secondary":     "#22D3EE",   # cyan        — risk-aware planner
    "accent":        "#A78BFA",   # violet      — learning modules
    "highlight":     "#F59E0B",   # amber       — replan / event markers

    # Semantic
    "success":       "#22C55E",   # safe / goal
    "warning":       "#F97316",   # caution
    "danger":        "#EF4444",   # collision / obstacle
    "info":          "#60A5FA",

    # Heatmap / map
    "obstacle":      "#1F2937",
    "free_space":    "#0E1117",
    "uncertainty":   "#7C3AED",
}

# Plotly colour scales used across visualisations
PLOTLY_RISK_SCALE: List[List] = [
    [0.00, "#0E1117"],
    [0.25, "#1E3A8A"],
    [0.50, "#7C3AED"],
    [0.75, "#F59E0B"],
    [1.00, "#EF4444"],
]

PLOTLY_UNCERTAINTY_SCALE: List[List] = [
    [0.00, "#0E1117"],
    [0.50, "#3B82F6"],
    [1.00, "#A78BFA"],
]

# ---------------------------------------------------------------------------
# Scenario defaults
# ---------------------------------------------------------------------------


@dataclass
class ScenarioConfig:
    """Default parameters for the synthetic navigation scenario.

    These values are designed so the demo "just works" on first launch while
    still being expressive enough for interesting comparative experiments.
    """

    grid_size: int = 40
    start: Tuple[int, int] = (2, 2)
    goal: Tuple[int, int] = (37, 37)

    # Environment generation
    n_static_obstacles: int = 14
    n_dynamic_obstacles: int = 3
    obstacle_min_size: int = 2
    obstacle_max_size: int = 5

    # Risk / uncertainty model
    risk_inflation_radius: int = 3       # cells around obstacles considered risky
    uncertainty_sigma: float = 4.0       # spread of the perception-uncertainty field
    cvar_alpha: float = 0.95             # CVaR confidence level (contribution 03)

    # Planner weights
    astar_weight: float = 1.0
    risk_weight: float = 2.5             # risk-aware planner trades cost ↔ safety

    # Simulation
    max_steps: int = 200
    sensing_radius: int = 6
    random_seed: int = 7

    # Robot kinematics (purely cosmetic, used for "computation time" feel)
    cell_meters: float = 0.25            # one grid cell ≈ 0.25 m
    nominal_speed_mps: float = 0.35      # TurtleBot3-ish nominal speed


@dataclass
class MetricThresholds:
    """Reference thresholds for the metrics panel (used for colour coding)."""

    safety_score_good: float = 0.80
    safety_score_warn: float = 0.60

    collision_risk_good: float = 0.10
    collision_risk_warn: float = 0.25

    replans_good: int = 2
    replans_warn: int = 5

    compute_ms_good: float = 50.0
    compute_ms_warn: float = 150.0


# ---------------------------------------------------------------------------
# Research module catalogue (mirrors `contributions/` in the upstream repo)
# ---------------------------------------------------------------------------


@dataclass
class ResearchModule:
    """One entry in the DynNav research module catalogue."""

    code: str
    title: str
    category: str
    one_liner: str
    why_it_matters: str


# Twenty-six modules — kept in the same order as the upstream README so the
# dashboard mirrors the repository's research narrative.
RESEARCH_MODULES: List[ResearchModule] = [
    ResearchModule(
        "01", "Learned A* Heuristics", "Planning",
        "Neural heuristic reduces node expansions ~35%.",
        "Faster search without sacrificing optimality is essential for "
        "real-time replanning on resource-constrained robots."),
    ResearchModule(
        "02", "Uncertainty Estimation (EKF/UKF)", "State Estimation",
        "Belief-state filtering for noisy sensors.",
        "Downstream planners can only be risk-aware if they know how "
        "uncertain the state estimate actually is."),
    ResearchModule(
        "03", "Belief-Space & Risk Planning", "Planning",
        "CVaR-optimised risk-weighted A*.",
        "Optimises for tail risk (worst-case 5%) rather than expected cost — "
        "the right objective for safety-critical missions."),
    ResearchModule(
        "04", "Irreversibility & Returnability", "Safety",
        "Plans avoid one-way states the robot cannot escape.",
        "Prevents the classic 'commits to a dead-end' failure mode in "
        "unknown environments."),
    ResearchModule(
        "05", "Safe-Mode Navigation", "Safety",
        "Adaptive risk-triggered conservative mode.",
        "Lets the robot trade speed for safety online, similar to "
        "automotive ADAS degraded modes."),
    ResearchModule(
        "06", "Energy & Connectivity", "Resources",
        "Battery- and WiFi-constrained planning.",
        "Long-horizon missions fail without explicit resource budgeting."),
    ResearchModule(
        "07", "Next-Best-View Exploration", "Exploration",
        "Information-gain maximisation for unknown maps.",
        "Closes the loop between perception and planning during mapping."),
    ResearchModule(
        "08", "Security & Intrusion Detection", "Robustness",
        "χ²/CUSUM anomaly detection for sensor spoofing.",
        "Cyber-physical attacks are an under-studied failure mode in "
        "autonomous mobility."),
    ResearchModule(
        "09", "Multi-Robot Coordination", "Coordination",
        "Decentralised conflict-free path allocation.",
        "Scales single-robot planning to fleets without centralised bottlenecks."),
    ResearchModule(
        "10", "Human-Aware & Ethical Zones", "HRI",
        "Trust-aware planning with ethical no-go zones.",
        "Bridges robotics with responsible AI deployment."),
    ResearchModule(
        "11", "VLM Navigation Agent", "Foundation Models",
        "LLaVA / GPT-4V → semantic navigation goals.",
        "Open-vocabulary goal grounding generalises far beyond closed label sets."),
    ResearchModule(
        "12", "Diffusion Occupancy Maps", "Generative",
        "DDPM-sampled occupancy → CVaR-95 risk maps.",
        "Models the *distribution* of possible worlds, not just a point estimate."),
    ResearchModule(
        "13", "Latent World Model", "Generative",
        "Dreamer-v3 RSSM mental rollouts.",
        "Imagined trajectories enable planning without expensive real rollouts."),
    ResearchModule(
        "14", "Causal Risk Attribution", "Explainability",
        "SCM + counterfactual root-cause ranking.",
        "Turns 'the robot crashed' into actionable engineering insights."),
    ResearchModule(
        "15", "Neuromorphic Sensing", "Perception",
        "DVS event camera + SNN at microsecond latency.",
        "Power and latency benefits matter for small platforms and high-speed motion."),
    ResearchModule(
        "16", "Federated Navigation Learning", "Coordination",
        "FedAvg + differential privacy across robots.",
        "Robots learn from one another without leaking raw sensor data."),
    ResearchModule(
        "17", "Topological Semantic Maps", "Mapping",
        "Zone graph + CLIP open-vocabulary grounding.",
        "Compact, human-meaningful representation suited to long-horizon planning."),
    ResearchModule(
        "18", "Formal Safety Shields (STL + CBF)", "Safety",
        "STL monitor + CBF command filter.",
        "Brings formal guarantees on top of learned controllers."),
    ResearchModule(
        "19", "LLM Mission Planner", "Foundation Models",
        "Natural language → waypoint sequences.",
        "Lowers the bar for non-expert operators to task a robot."),
    ResearchModule(
        "20", "Multimodal Failure Explainer", "Explainability",
        "VLM + SCM → human-readable failure reports.",
        "Closes the gap between post-mortem logs and engineering action items."),
    ResearchModule(
        "21", "PPO Navigation Agent", "Reinforcement Learning",
        "Risk-shaped PPO with actor-critic.",
        "Learned policies that respect the same risk objective as the planner."),
    ResearchModule(
        "22", "Curriculum RL", "Reinforcement Learning",
        "Adaptive 5-stage difficulty curriculum.",
        "61% vs 23% success on hard tasks compared to flat training."),
    ResearchModule(
        "23", "Gaussian Splatting Mapper", "Perception",
        "Incremental 3D-GS map + frontier detection.",
        "State-of-the-art 3D representation for photorealistic mapping."),
    ResearchModule(
        "24", "NeRF Uncertainty Maps", "Perception",
        "MC-Dropout NeRF → exploration weights.",
        "Uncertainty-aware view selection improves coverage efficiency."),
    ResearchModule(
        "25", "Adversarial Attack Simulator", "Robustness",
        "FGSM / PGD + LiDAR spoofing robustness eval.",
        "Stress-tests perception and policy under realistic adversaries."),
    ResearchModule(
        "26", "Swarm Consensus (BFT)", "Coordination",
        "Byzantine fault-tolerant plan consensus.",
        "Tolerates up to f < N/3 malicious or faulty robots — 91% detection rate."),
]


# ---------------------------------------------------------------------------
# Architecture diagram nodes (consumed by the Graphviz view)
# ---------------------------------------------------------------------------


@dataclass
class ArchLayer:
    name: str
    color: str
    modules: List[str] = field(default_factory=list)


ARCH_LAYERS: List[ArchLayer] = [
    ArchLayer("Foundation Models", COLORS["accent"],
              ["VLM (11)", "LLM (19)", "VLM+Fail (20)"]),
    ArchLayer("Learning Layer", COLORS["primary"],
              ["Learned A* (01)", "PPO (21)", "Curriculum (22)",
               "Federated (16)"]),
    ArchLayer("Safety Layer", COLORS["success"],
              ["STL + CBF (18)", "Safe-Mode (05)", "Returnability (04)"]),
    ArchLayer("Coordination Layer", COLORS["secondary"],
              ["Swarm BFT (26)", "Federated (16)", "Multi-Robot (09)"]),
    ArchLayer("Planning Core", COLORS["info"],
              ["A* / D*", "Belief-Space (03)", "Risk Planning (03)",
               "NBV (07)"]),
    ArchLayer("Perception", COLORS["uncertainty"],
              ["LiDAR SLAM", "3D-GS (23)", "NeRF (24)",
               "DVS + SNN (15)", "EKF / UKF (02)"]),
    ArchLayer("Security", COLORS["danger"],
              ["IDS (08)", "Adversarial (25)", "Causal SCM (14)"]),
]

# ---------------------------------------------------------------------------
# Convenience exports
# ---------------------------------------------------------------------------

DEFAULT_SCENARIO = ScenarioConfig()
DEFAULT_THRESHOLDS = MetricThresholds()
