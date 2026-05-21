# DynNav

### Dynamic Navigation and Rerouting in Unknown Environments

*An uncertainty-aware, risk-sensitive autonomous navigation framework with formal safety constraints, learning-augmented planning, and twenty-six reproducible research contributions.*

---

**Repository.** [github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments](https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments)
**Live dashboard.** [dynnav-dynamic-navigation-rerouting-in-unknown-environments-fq.streamlit.app](https://dynnav-dynamic-navigation-rerouting-in-unknown-environments-fq.streamlit.app/)
**Latest release.** `v0.3-multi-robot-disagreement` (January 2026)
**License.** Apache-2.0
**Author.** Panagiota Grosdouli — Department of Electrical and Computer Engineering, Democritus University of Thrace (DUTH)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Scientific Motivation](#2-scientific-motivation)
3. [Research Questions](#3-research-questions)
4. [Problem Formulation](#4-problem-formulation)
5. [System Architecture](#5-system-architecture)
6. [Repository Layout](#6-repository-layout)
7. [The Twenty-Six Contributions](#7-the-twenty-six-contributions)
8. [The Research Dashboard](#8-the-research-dashboard)
9. [Technical Stack](#9-technical-stack)
10. [Installation](#10-installation)
11. [Running the Experiments](#11-running-the-experiments)
12. [Running the Dashboard](#12-running-the-dashboard)
13. [ROS 2 Integration](#13-ros-2-integration)
14. [Experimental Methodology](#14-experimental-methodology)
15. [Selected Results](#15-selected-results)
16. [Why a Streamlit Dashboard](#16-why-a-streamlit-dashboard)
17. [Theoretical Background](#17-theoretical-background)
18. [Engineering Challenges Encountered](#18-engineering-challenges-encountered)
19. [Deployment and Debugging Notes](#19-deployment-and-debugging-notes)
20. [Limitations and Honest Disclosures](#20-limitations-and-honest-disclosures)
21. [Research Significance](#21-research-significance)
22. [Future Research Directions](#22-future-research-directions)
23. [Citation](#23-citation)
24. [Author](#24-author)
25. [License](#25-license)
26. [Acknowledgements](#26-acknowledgements)

---

## 1. Overview

DynNav is a research framework for **dynamic navigation and online rerouting in unknown environments** that treats uncertainty and risk as first-class quantities. The framework is organised around twenty-six self-contained research contributions spanning planning, state estimation, formal safety, reinforcement learning, foundation-model integration, federated learning, security, multi-robot coordination, and 3D perception. The contributions are developed under a unified problem formulation in which a mobile agent must reach a goal in a partially observed, possibly adversarial environment while respecting probabilistic safety and resource constraints.

The repository contains four coupled components:

1. A **library of twenty-six research modules** under `contributions/`, each with its own algorithm code, `experiments/` driver, `results/` directory and per-module README.
2. A **ROS 2 stack** organised into perception (`lidar_ros2/`, `neural_uncertainty/`, `photogrammetry_module/`, `ig_explorer/`), navigation (`dynamic_nav/`, `core/`), and security (`cybersecurity_ros2/`) packages, with a TurtleBot3 workspace under `ros2_ws/lidar_slam_tb3/`.
3. A **browser-based research dashboard** built with Streamlit that reproduces every contribution as a synthetic-data simulation requiring no robot, no ROS installation, and no GPU.
4. A **technical-report layer**: twenty-six `DynNav_C##_*_DeepDive.pdf` documents at the repository root, one per contribution, plus the consolidated `TECHNICAL_REPORT.md`.

The framework is positioned as a research artefact, not a deployable product. Several contributions are fully implemented and benchmarked, others are prototypes, and the cross-stack integration is partial. These categories are made explicit throughout this document.

---

## 2. Scientific Motivation

Autonomous navigation has matured in controlled, well-mapped settings. It remains brittle in environments where the map is incomplete or evolving, where perception is noisy, and where rare worst-case events — sensor spoofing, dynamic obstacles, dead-end traps, low battery, communication loss — dominate the failure distribution. Three observations frame the project.

**Average-case planning is insufficient.** Most classical planners optimise expected cost. In safety-critical settings the tail of the cost distribution matters more than the mean. A path that is short on average but exposes the robot to a five-percent chance of collision is unacceptable in many deployments. This motivates the use of coherent tail-risk measures such as Conditional Value-at-Risk (CVaR) inside the planning objective.

**Uncertainty must be first-class.** Downstream decisions — whether to slow down, replan, abort, or hand off to a human supervisor — are only as good as the uncertainty estimates they consume. The framework therefore treats belief-space estimation, ensemble disagreement, NeRF/3DGS uncertainty fields, and diffusion-based occupancy predictions as primary signals rather than diagnostics.

**Safety cannot rely on the policy alone.** Learning-based policies improve average performance but offer no formal guarantees. The framework couples learned components to formal safety filters — Control Barrier Functions (CBFs) and Signal Temporal Logic (STL) shields — so that the output of any upstream controller, classical or neural, is minimally projected onto the safe set before reaching the actuators.

---

## 3. Research Questions

The contributions are organised around the following questions.

1. *How should risk be encoded inside the planner so that the resulting trajectories are robust to the worst α-fraction of perception outcomes?*
2. *How can learned heuristics or learned dynamics models accelerate or improve planning without sacrificing the strict guarantees of classical planners?*
3. *What is the minimal architectural commitment under which a learned policy can be composed with a formal safety filter so that safety is preserved by construction?*
4. *How should mission-level intent — natural language or structured operator commands — be compiled into provably executable, returnable plans?*
5. *Under what assumptions can a multi-robot swarm reach consensus on navigation decisions when an unknown subset of its members is Byzantine?*
6. *How should a robot allocate its perception budget — frontier viewpoints, NeRF queries — to maximise the reduction of decision-relevant uncertainty rather than total entropy?*
7. *Can a research-grade simulation environment, deliberately decoupled from ROS and from physical hardware, accelerate the pace of methodological iteration in this space without compromising the eventual transfer to a real platform?*

---

## 4. Problem Formulation

Let an agent occupy state `s_t` in a partially observed environment with hidden parameters `θ`. At each step it issues an action `a_t` and receives an observation `o_t`. The agent maintains a belief `b_t = p(s_t, θ | o_{1:t}, a_{1:t-1})`. A mission specifies a goal region `G` and a set of safety constraints `Φ` that may be expressed as:

- forward invariance of a safe set `S_safe` (CBF formulation),
- temporal-logic specifications `φ ∈ STL`,
- bounded tail risk `CVaR_α[c_t] ≤ κ` over a step-wise risk signal `c_t`.

The planner seeks a policy `π` that maximises an expected return while satisfying `Φ` and an *additional returnability constraint*: for every reachable belief along the executed trajectory there must exist a feasible plan back to a designated safe state (typically the base station) under the residual energy and connectivity budget. This last constraint distinguishes the framework's notion of safety from the standard collision-avoidance formulation.

---

## 5. System Architecture

The framework is layered. Each layer exposes a typed interface to the layer above and accepts uncertainty estimates from the layer below.

```
+----------------------------------------------------------------+
|  Foundation Models                                              |
|     VLM Navigation Agent (C11)  |  LLM Mission Planner (C19)    |
|     Multimodal Failure Explainer (C20)                          |
+----------------------------------------------------------------+
|  Learning Layer                                                 |
|     Learned A* (C01)  |  PPO (C21)  |  Curriculum RL (C22)      |
|     Federated Nav Learning (C16)  |  Latent World Model (C13)   |
+----------------------------------------------------------------+
|  Safety Layer                                                   |
|     STL + CBF Shields (C18)  |  Safe-Mode FSM (C05)             |
|     Irreversibility / Returnability (C04)                       |
+----------------------------------------------------------------+
|  Coordination Layer                                             |
|     Multi-Robot Allocation (C09)  |  Swarm BFT Consensus (C26)  |
|     Human-Aware Ethical Zones (C10)                             |
+----------------------------------------------------------------+
|  Planning Core                                                  |
|     Belief-Space / CVaR Risk Planning (C03)                     |
|     Next-Best-View Exploration (C07)                            |
|     Topological Semantic Maps (C17)                             |
|     Energy and Connectivity Constraints (C06)                   |
+----------------------------------------------------------------+
|  Perception Layer                                               |
|     EKF / UKF (C02)  |  Diffusion Occupancy (C12)               |
|     3D Gaussian Splatting Mapper (C23)                          |
|     NeRF Uncertainty Maps (C24)                                 |
|     Neuromorphic Sensing (C15)                                  |
+----------------------------------------------------------------+
|  Security Layer                                                 |
|     IDS chi-square / CUSUM (C08)                                |
|     Adversarial Attack Simulator (C25)                          |
|     Causal Risk Attribution (C14)                               |
+----------------------------------------------------------------+
|  ROS 2 Substrate                                                |
|     ROS 2 Humble  |  Nav2  |  slam_toolbox  |  TurtleBot3       |
+----------------------------------------------------------------+
```

Data flows upward: raw sensors → security filter → perception → planning → safety filter → actuators. Uncertainty estimates flow with the data; mission intent flows downward; the safe-mode FSM observes the entire stack and gates its outputs.

---

## 6. Repository Layout

The top-level structure mirrors the architecture above. Folder names are reproduced verbatim from the repository.

```
DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments/
│
├── contributions/                # 26 self-contained research modules
│   ├── 01_learned_astar/         #   each contains:
│   ├── 02_uncertainty_estimation/#     module.py, experiments/, results/, README.md
│   ├── 03_belief_risk_planning/
│   ├── 04_irreversibility_returnability/
│   ├── 05_safe_mode_navigation/
│   ├── 06_energy_connectivity/
│   ├── 07_next_best_view/
│   ├── 08_security_ids/
│   ├── 09_multi_robot/
│   ├── 10_human_language_ethics/
│   ├── 11_vlm_navigation_agent/
│   ├── 12_diffusion_occupancy/
│   ├── 13_latent_world_model/
│   ├── 14_causal_risk_attribution/
│   ├── 15_neuromorphic_sensing/
│   ├── 16_federated_nav_learning/
│   ├── 17_topological_semantic_maps/
│   ├── 18_formal_safety_shields/
│   ├── 19_llm_mission_planner/
│   ├── 20_multimodal_failure_explainer/
│   ├── 21_ppo_navigation_agent/
│   ├── 22_curriculum_rl/
│   ├── 23_gaussian_splatting_mapper/
│   ├── 24_nerf_uncertainty/
│   ├── 25_adversarial_attack_simulator/
│   ├── 26_swarm_consensus/
│   └── tests/                    # pytest suite covering modules 11–26
│
├── core/                         # planner cores (A*, D*, belief search)
├── dynamic_nav/                  # closed-loop navigation stack
├── nav_research/                 # Python package (importable nav_research.*)
├── modules/                      # standalone library modules
├── generators/                   # synthetic scenario generators
├── ig_explorer/                  # information-gain exploration node
├── neural_uncertainty/           # neural uncertainty estimation
├── photogrammetry_module/        # photogrammetry integration
│
├── lidar_ros2/                   # ROS 2 LiDAR + SLAM packages
├── cybersecurity_ros2/nodes/     # ROS 2 IDS / cyber-physical nodes
├── ros2/                         # additional ROS 2 packages
├── ros2_ws/lidar_slam_tb3/       # TurtleBot3 workspace
├── launch/                       # ROS 2 launch files
│
├── analysis/                     # post-hoc analysis scripts
├── code_scripts/                 # one-off experiment scripts
├── scripts/                      # utility scripts
├── tools/                        # tooling
├── utils/                        # shared helpers
├── tests/                        # repo-wide pytest suite
├── test/                         # ROS 2 ament_python test stubs
│
├── data/plots/                   # generated experiment plots
├── data_curriculum/              # curriculum-RL data
├── datasets/                     # raw and processed datasets
├── figures/                      # figures used in reports / papers
├── results/                      # consolidated result artefacts
├── research_experiments/         # standalone experiment runs
├── research_results/             # standalone result archives
├── resource/                     # ROS 2 ament resource markers
├── config/                       # runtime configuration
├── configs/                      # experiment configuration files
├── docs/                         # extended documentation
│
├── logs_ablation/                # ablation-study logs
├── logs_benchmark/               # benchmark-run logs
├── logs_calibration/             # calibration logs
├── logs_calibration_ensemble/    # ensemble-calibration logs
├── logs_ood/                     # out-of-distribution logs
├── logs_real_world/              # real-robot deployment logs
├── log/                          # generic log dir (ROS 2)
│
├── build/  install/              # colcon build artefacts (gitignored upstream)
├── cpp_extension/                # C/C++ extension modules
├── nav_research.egg-info/        # Python packaging metadata
│
├── DynNav_C01_Learned_Astar_DeepDive.pdf       # 26 per-contribution
├── DynNav_C02_EKF_UKF_DeepDive.pdf             # technical deep-dive
├── ...                                          # documents at the repo root
├── DynNav_C26_BFT_DeepDive.pdf
│
├── TECHNICAL_REPORT.md           # consolidated technical report
├── README.md                     # this file
├── readme.md  readme_full.md     # legacy / extended variants
├── ellhnika.md                   # Greek-language notes
├── CITATION.cff
├── LICENSE                       # Apache-2.0
├── pytest.ini
├── setup.py  setup.cfg           # nav_research package metadata
├── requirements.txt              # dashboard runtime (see §10)
├── ethical_zones.json            # ethical no-go zone definitions
└── run_all_contributions.py      # batch driver for all 26 modules
```

A small note: `requirements.txt` currently lists only the dashboard's runtime dependencies (Streamlit, numpy, pandas, plotly, matplotlib, networkx). The full research stack uses additional dependencies (PyTorch, transformers, diffusers, open3d, ROS 2) which are introduced in section 10.

---

## 7. The Twenty-Six Contributions

Each contribution lives in its own directory under `contributions/NN_module_name/` with the same internal layout: `module.py` (or a small package), an `experiments/` subdirectory with one or more `eval_*.py` scripts, a `results/` subdirectory containing CSV outputs and plots, and a per-module `README.md` covering the research question, algorithm and integration points. Each contribution also has a longer technical deep-dive at the repository root (`DynNav_C##_*_DeepDive.pdf`).

The table below lists every contribution, its category, its current implementation status, and the script that reproduces its evaluation.

| Code | Module | Category | Status | Reproduce |
|---|---|---|---|---|
| C01 | Learned A\* Heuristics | Planning | Implemented | `contributions/01_learned_astar/experiments/eval_astar_learned.py` |
| C02 | Uncertainty Estimation (EKF / UKF) | State Estimation | Implemented | `contributions/02_uncertainty_estimation/experiments/eval_uncertainty.py` |
| C03 | Belief-Space and Risk Planning (CVaR A\*) | Planning | Implemented | `contributions/03_belief_risk_planning/experiments/eval_belief_risk.py` |
| C04 | Irreversibility and Returnability | Safety | Implemented | `contributions/04_irreversibility_returnability/experiments/eval_returnability.py` |
| C05 | Safe-Mode Navigation | Safety | Implemented | `contributions/05_safe_mode_navigation/experiments/eval_safe_mode.py` |
| C06 | Energy and Connectivity Constraints | Resources | Implemented | `contributions/06_energy_connectivity/experiments/eval_energy_connectivity.py` |
| C07 | Next-Best-View Exploration | Exploration | Implemented | `contributions/07_next_best_view/experiments/eval_nbv.py` |
| C08 | Security and Intrusion Detection | Robustness | Implemented | `contributions/08_security_ids/experiments/eval_ids.py` |
| C09 | Multi-Robot Coordination | Coordination | Implemented | `contributions/09_multi_robot/experiments/eval_multi_robot.py` |
| C10 | Human-Aware Navigation and Ethical Zones | HRI | Implemented | `contributions/10_human_language_ethics/experiments/eval_human_ethics.py` |
| C11 | VLM Navigation Agent | Foundation Models | Prototype (model stub; requires `ollama` or HF) | `contributions/11_vlm_navigation_agent/experiments/eval_vlm_planner.py` |
| C12 | Diffusion Occupancy Maps | Generative | Implemented | `contributions/12_diffusion_occupancy/experiments/eval_diffusion_occupancy.py` |
| C13 | Latent World Model (Dreamer-style RSSM) | Generative | Prototype | inline driver |
| C14 | Causal Risk Attribution (SCM) | Explainability | Implemented | inline driver |
| C15 | Neuromorphic Sensing (DVS + SNN) | Perception | Prototype (synthetic event streams) | inline driver |
| C16 | Federated Navigation Learning | Coordination | Implemented | inline driver |
| C17 | Topological Semantic Maps | Mapping | Implemented | inline driver |
| C18 | Formal Safety Shields (STL + CBF) | Safety | Implemented | `contributions/18_formal_safety_shields/experiments/eval_safety_shields.py` |
| C19 | LLM Mission Planner | Foundation Models | Prototype (rule-based fallback + LLM hook) | inline driver |
| C20 | Multimodal Failure Explainer | Explainability | Prototype | inline driver |
| C21 | PPO Navigation Agent | Reinforcement Learning | Implemented | inline driver |
| C22 | Curriculum RL | Reinforcement Learning | Implemented | inline driver |
| C23 | Gaussian Splatting Mapper | Perception | Prototype (no differentiable renderer in repo) | inline driver |
| C24 | NeRF Uncertainty Maps | Perception | Prototype (MC-dropout proxy) | inline driver |
| C25 | Adversarial Attack Simulator | Robustness | Implemented | inline driver |
| C26 | Swarm Consensus (BFT) | Coordination | Implemented | inline driver |

*Implemented* means the contribution runs end-to-end on the supplied scripts and produces logged metrics. *Prototype* means the algorithmic core is in place but at least one external dependency (e.g. PyTorch, a local LLM, a differentiable renderer) is required to exercise the full pipeline; a synthetic fallback is provided where applicable.

For every contribution, the corresponding `DynNav_C##_*_DeepDive.pdf` at the repository root provides the long-form technical write-up: mathematical formulation, baseline comparison, ablations and discussion.

---

## 8. The Research Dashboard

The Streamlit dashboard at [dynnav-dynamic-navigation-rerouting-in-unknown-environments-fq.streamlit.app](https://dynnav-dynamic-navigation-rerouting-in-unknown-environments-fq.streamlit.app/) reproduces every contribution as a self-contained, browser-based interactive simulation. The dashboard requires no robot, no ROS installation, and no GPU.

Six pages are exposed in the sidebar:

| # | Page | Purpose |
|---|---|---|
| 0 | `dashboard.py` (home) | Project overview, headline metrics, quick navigation |
| 1 | Architecture | Layered diagram of the DynNav stack |
| 2 | Navigation Demo | Closed-loop episode with online replanning |
| 3 | Risk Map | Uncertainty and risk heatmaps, CVaR threshold visualisation |
| 4 | Planner Comparison | A\* versus risk-aware A\*, Monte-Carlo sweep across seeds |
| 5 | Research Modules | Searchable catalogue of all twenty-six contributions |
| 6 | Contribution Simulations | One interactive mini-simulation per contribution (C01–C26) |

The Contribution Simulations page is the technical centrepiece. A dropdown over `C01`–`C26` dispatches to a self-contained `render(st)` function; each renderer presents:

1. a short research explanation,
2. interactive controls (seed and topic-specific parameters),
3. one or more output plots,
4. quantitative metrics,
5. an interpretation block that comments on the current parameter regime.

The dashboard is **explicit about what is real and what is illustrative**. Each interpretation block names the synthetic proxy in use (for example, a Chebyshev-distance heuristic stands in for a learned cost-to-go network in C01) and the parameter regime in which the proxy behaves like the production version.

---

## 9. Technical Stack

| Layer | Component | Implementation |
|---|---|---|
| **Planning** | A\* core, learned heuristic, risk-aware variant | Pure NumPy; 8-connected; optional heuristic field and risk weight |
| | Topological routing | networkx weighted graph |
| | Next-best-view exploration | Frontier extraction + information-gain scoring |
| **Safety** | CBF shield | Iterative half-space projection on quadratic safety set |
| | STL shield | Bounded-time predicate checking |
| | Safe-mode FSM | Four-state automaton with hysteresis |
| | Returnability check | Bidirectional A\* under risk threshold |
| **Learning** | PPO | Risk-shaped actor-critic |
| | Twin-critic (TD3-style) | min of two Q estimates |
| | Curriculum | Five-stage adaptive difficulty scheduler |
| | World model | Ensemble rollouts with growing process noise |
| | Federated learning | FedAvg with heterogeneity and dropout |
| **Security** | IDS | Sliding-window chi-square and CUSUM |
| | Adversarial defence | Median + MAD outlier suppression on LiDAR scans |
| **Multi-robot** | Assignment | Hungarian (exact); brute permutation for n ≤ 6 |
| | Consensus | Coordinate-wise median, α-trimmed mean, BFT weighted median |
| **Foundation models** | LLM mission planner | LLM call (via Ollama / HF) with deterministic rule-based fallback |
| | VLM agent | LLaVA / GPT-4V hook with stub fallback |
| **Perception** | EKF / UKF | Linear-Gaussian Kalman with sigma-point inflation |
| | Diffusion occupancy | DDPM-style spread of occupancy probability over horizon |
| | NeRF uncertainty | MC-dropout proxy field |
| | 3D Gaussian Splatting | Visual reconstruction; no differentiable renderer in this repo |
| | Neuromorphic | DVS event stream + SNN classifier |
| **Visualisation** | Plotly + Matplotlib | All figures |
| | Streamlit | Multi-page dashboard |
| **Substrate** | ROS 2 Humble | Nav2, slam_toolbox, TurtleBot3 |

---

## 10. Installation

The project supports three installation profiles, depending on what the user wants to run.

### 10.1 Dashboard only (no ROS, no GPU)

Sufficient to reproduce every contribution in the browser and to exercise the synthetic experiments.

```bash
git clone https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments.git
cd DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments

python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate

pip install -r requirements.txt     # streamlit, numpy, pandas, plotly, matplotlib, networkx
pip install pytest                  # for the test suite
```

### 10.2 Full research stack (Python, no ROS)

Required to exercise the learning, generative and foundation-model contributions in non-stub mode.

```bash
pip install -r requirements.txt
pip install \
    torch>=2.0 \
    transformers>=4.40 \
    diffusers>=0.27 \
    open3d>=0.17 \
    scipy>=1.10
# For C11 and C19 in non-stub mode:
#   install Ollama from https://ollama.ai/download
#   pull a small local model, e.g.:  ollama pull llama3
```

### 10.3 ROS 2 stack (Ubuntu 22.04, ROS 2 Humble)

Required for closed-loop experiments on TurtleBot3 (real or Gazebo).

```bash
sudo apt install \
    ros-humble-desktop \
    ros-humble-nav2-bringup \
    ros-humble-slam-toolbox \
    ros-humble-turtlebot3*

mkdir -p ~/dynnav_ws/src && cd ~/dynnav_ws/src
ln -s /path/to/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments ./dynnav
cd .. && rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

---

## 11. Running the Experiments

The repository exposes a single batch driver for the entire suite:

```bash
# Run all 26 contributions in quick-eval mode (~2 seconds end-to-end)
python run_all_contributions.py --quick

# Run all 26 contributions at full evaluation budget (~30 seconds)
python run_all_contributions.py

# Run a specific subset
python run_all_contributions.py --modules 18 25 26

# Run only the test suite
pytest contributions/tests/ -v
pytest tests/ -v
```

Individual contributions can also be run via their dedicated evaluation script. Examples:

```bash
# Formal safety shields (STL + CBF) — 50 episodes
python contributions/18_formal_safety_shields/experiments/eval_safety_shields.py \
    --n_episodes 50 --out_csv results/shield_eval.csv

# Diffusion occupancy risk maps — 30 scenarios, 10 samples each
python contributions/12_diffusion_occupancy/experiments/eval_diffusion_occupancy.py \
    --n_scenarios 30 --n_samples 10

# Swarm BFT consensus — 6 robots, 1 Byzantine
python -c "
import numpy as np, sys
sys.path.insert(0, 'contributions/26_swarm_consensus')
from swarm_consensus import SwarmCoordinator
coord = SwarmCoordinator(n_robots=6, n_byzantine=1)
grid = np.zeros((20, 20)); grid[8:12, 8:12] = 1.0
result = coord.plan(grid, (0, 0), (18, 18))
print(f'Cost: {result.agreed_cost:.2f} | Byzantine detected: {result.n_byzantine_detected}')
"
```

All scripts write CSV logs into the contribution's `results/` directory and plots into `data/plots/`. Repository-wide ablation, benchmark, calibration, OOD and real-world logs are stored in the corresponding `logs_*` folders.

---

## 12. Running the Dashboard

### 12.1 Locally

```bash
streamlit run app/dashboard.py
```

The application opens at `http://localhost:8501`. The **Contribution Simulations** page exposes all twenty-six demos in a single dropdown.

### 12.2 Cloud-hosted

A deployed instance runs on Streamlit Community Cloud:

> [dynnav-dynamic-navigation-rerouting-in-unknown-environments-fq.streamlit.app](https://dynnav-dynamic-navigation-rerouting-in-unknown-environments-fq.streamlit.app/)

---

## 13. ROS 2 Integration

The ROS 2 packages live in three directories:

- `lidar_ros2/` — LiDAR drivers, scan-matching, slam_toolbox integration.
- `cybersecurity_ros2/nodes/` — intrusion-detection nodes wrapping C08's chi-square / CUSUM detectors.
- `ros2_ws/lidar_slam_tb3/` — a TurtleBot3-specific workspace combining LiDAR SLAM and the DynNav planning stack.

The system has been tested on a TurtleBot3 Burger (hardware) and a TurtleBot3 Waffle (Gazebo). Launch files under `launch/` start the relevant stack:

```bash
# Simulation (Gazebo + TurtleBot3 Waffle)
ros2 launch dynamic_nav dynnav_sim.launch.py

# Real robot (TurtleBot3 Burger over ROS 2 network)
ros2 launch dynamic_nav dynnav_real.launch.py use_sim_time:=false
```

The integration is partial. Several launch files orchestrate the perception and planning nodes but the formal-safety shield (C18) and the swarm-consensus node (C26) are currently exercised via their Python evaluators rather than as ROS 2 nodes. Wiring these into the live ROS 2 graph is on the future-work list (section 22).

---

## 14. Experimental Methodology

The experiments reported in the per-module deep-dive PDFs and in section 15 follow a consistent protocol.

**Determinism.** Every contribution accepts an explicit seed. All randomness — obstacle placement, sensor noise, attack injection, federated client samples — derives from `numpy.random.default_rng(seed)`. Two runs with the same seed produce bit-identical plots and metrics.

**Seed sweeps.** Where a single seed could mislead, contributions report a Monte-Carlo sweep over seeds `{1, 7, 13, 21, 42}`. Inter-seed variance is reported alongside the mean.

**Baselines.** Each learning-augmented contribution is compared against a clearly identified classical baseline: learned A\* versus vanilla A\*, CVaR A\* versus shortest-path A\*, twin-critic versus optimistic-max, curriculum versus flat training, robust estimators versus naive mean, BFT-weighted median versus naive majority.

**Logging.** All numerical results land in CSV files under `contributions/##_module_name/results/`. Plots are written to `data/plots/`. Five additional repository-wide log folders capture: ablation (`logs_ablation/`), benchmarks (`logs_benchmark/`), calibration (`logs_calibration/`, `logs_calibration_ensemble/`), out-of-distribution evaluation (`logs_ood/`) and real-world runs (`logs_real_world/`).

---

## 15. Selected Results

The numbers below summarise representative outcomes from the corresponding deep-dive PDFs. They are illustrative rather than headline claims; full tables and ablations live in the per-contribution documents.

### 15.1 Formal safety shields (C18)

| Metric | Without shield | With STL + CBF shield |
|---|---|---|
| Constraint violations per episode (mean) | 4.2 | 0.3 |
| Path-length overhead | — | < 8 % |
| Average command correction | — | 0.026 m/s |

### 15.2 Swarm consensus (C26)

| Metric | Naive majority | BFT weighted median |
|---|---|---|
| Byzantine detection rate | 60 % | 91 % |
| Correct plan selected | 71 % | 96 % |
| Byzantine tolerance | f < N/2 | f < N/3 |

### 15.3 Federated learning (C16)

| Round | Centralised val MSE | Federated val MSE (6 robots) |
|---|---|---|
| 1 | 0.41 | 0.37 |
| 10 | 0.18 | 0.21 |
| 20 | 0.12 | 0.14 |

### 15.4 Curriculum reinforcement learning (C22)

| Training regime | Episodes to reach "hard" stage | Final success rate |
|---|---|---|
| Flat | n/a | 23 % |
| Adaptive five-stage curriculum | ~200 | 61 % |

### 15.5 Learned A\* (C01)

On a 35×35 grid with 18 obstacles, the learned-heuristic variant typically reduces node expansions by 25–45 % at a path-cost penalty under 5 %. The reduction grows with clutter density and vanishes in open space.

### 15.6 CVaR A\* (C03)

Setting α = 0.95 with a risk weight of 3.0 reduces the worst 5 % of per-step risks by 30–60 % at a 5–15 % path-length penalty.

All values are reproducible from the corresponding seeds, either via `run_all_contributions.py --modules N` or via the Streamlit dashboard.

---

## 16. Why a Streamlit Dashboard

A non-trivial engineering decision was to build a browser-based research dashboard as a first-class artefact rather than as an afterthought. The rationale is threefold.

**Reproducibility.** A robotics repository that ships only a ROS package and no installation script is difficult to verify. The dashboard exposes every contribution as a deterministic synthetic experiment — given a seed, the figures, metrics and verdicts are bit-for-bit reproducible. A reviewer can confirm an effect in seconds.

**Accessibility.** Reviewers and collaborators do not need to install ROS 2, build a Gazebo world, or own a TurtleBot3 to inspect the framework's claims. The dashboard turns the research portfolio into a self-contained read-only experiment that opens in a browser.

**Methodological velocity.** Decoupling algorithmic ideas from the friction of robotic integration shortens the iteration cycle. A risk-aware planner can be specified, tested across seeds, and visually inspected in minutes rather than days. ROS 2 integration follows after the algorithm has stabilised.

The synthetic-simulation philosophy also has a practical justification. A graduate research project should not depend on continuous access to physical robots. By making the framework runnable on a laptop with five Python packages, the work survives the loss of a particular piece of hardware and can be extended by anyone with a browser.

---

## 17. Theoretical Background

This section briefly anchors the framework in its relevant prior art. Per-contribution references are in the deep-dive PDFs.

**Uncertainty-aware navigation.** The framework draws on belief-space planning (Platt, Kaelbling, Lozano-Pérez) and on partially observable MDP formulations. Recent work — notably DYNUS (Kondo et al., 2025) and Map-Predictive Motion Planning (Katyal et al.) — frames the same challenge: trajectories planned under nominal assumptions can become unsafe at any moment because the agent cannot predict ground-truth futures. DynNav's response is to make every layer's uncertainty explicit and consumable by the layer above.

**CVaR-style planning.** Conditional Value-at-Risk is a coherent risk measure standard in finance (Rockafellar and Uryasev). In safe robotics it has been used to replace expected cost with expected cost in the worst α-fraction of outcomes (Chow, Tamar et al.). C03 implements a risk-weighted A\* variant that augments edge cost with a CVaR penalty.

**Formal safety constraints, CBFs and STL.** Control Barrier Functions (Ames, Xu, Tabuada) certify forward invariance of a safe set via affine constraints on the control input. Signal Temporal Logic (Maler, Nickovic) allows time-bounded specifications. C18 composes both: the STL monitor produces a Boolean safety signal, the CBF layer minimally edits the commanded action to maintain forward invariance.

**Reinforcement learning trade-offs.** On-policy PPO (Schulman et al.) is preferred for its trust-region stability; twin-critic estimators (TD3, Fujimoto et al.) mitigate the over-estimation bias of max-over-noisy-Q targets. Curriculum learning (Bengio et al.) trades early-stage performance for late-stage capability on tasks that are otherwise unreachable from a cold start.

**Adversarial robustness.** Sensor spoofing on LiDAR and GPS has been documented in the cyber-physical-systems literature (Cao et al., Shoukry et al.). C25's median + MAD filter is a robust-statistics standard; the chi-square and CUSUM detectors in C08 are textbook tools from change-point detection.

**Swarm coordination.** Byzantine fault tolerance dates back to Lamport, Shostak and Pease. In the continuous-aggregation setting, coordinate-wise median and α-trimmed mean tolerate up to f Byzantine agents when n > 2f (or n > 3f for stronger guarantees in adversarial models). C26 uses both.

**Federated learning.** FedAvg (McMahan et al.) is the de-facto baseline. C16 demonstrates the convergence-versus-heterogeneity trade-off and the effect of client dropout.

**World models.** The Dreamer line of work (Hafner et al.) shows that ensemble rollouts under a learned latent dynamics model can substitute for environment interaction. C13 adopts the same architectural shape.

**Diffusion-based occupancy prediction.** Generative models for occupancy / risk forecasting (Toyungyernsub et al., Bharilya and Kumar) extend single-step prediction to a distribution over futures. C12 uses a Gaussian-spread proxy to keep the simulation lightweight; the production version uses a DDPM.

**Neuromorphic perception.** Event cameras (DVS) emit asynchronous, microsecond-latency, high-dynamic-range pixel-change events. Combined with spiking neural networks (Tavanaei et al.) they offer fast obstacle detection at low power. C15 demonstrates the principle on synthetic event streams.

---

## 18. Engineering Challenges Encountered

The list below records the non-trivial engineering issues that surfaced during development. They are reported here because they are the kind of detail typically omitted from research write-ups, yet they consumed substantial time and shaped the architecture.

**Streamlit caching versus stateful environments.** The original navigation episode runner mutated the environment in place. Streamlit's `@st.cache_data` aggressively serialised the cached instance, and subsequent runs poisoned each other's state, producing non-deterministic plots across reruns. The fix was to deep-copy the environment at the boundary of every cached call and to make the episode runner pure with respect to its inputs.

**Replanning that never reached the goal.** An early version of the closed-loop demo replanned on every step against the same dilated obstacle map and oscillated between two corridors, never converging. The fix was to introduce a hysteresis window on the replanning trigger and to require a strict improvement in the planner's f-score before committing to a new path.

**`scipy` removed from the dashboard runtime.** An early implementation of C01 used `scipy.ndimage.distance_transform_edt` for the learned-heuristic proxy. To keep the dashboard's dependency surface at five packages, the distance transform was reimplemented in pure NumPy using iterative Chebyshev dilation. The result is slower for very large grids but indistinguishable in the dashboard's operating range. SciPy remains a dependency of the full research stack.

**Hungarian assignment for n > 6.** The brute-permutation Hungarian variant in `contributions/09_multi_robot/` is exact but exponential. For larger swarms an O(n³) Munkres implementation is required; the slot is deliberately marked in the module.

**ROS 2 packaging.** The ROS 2 stack was originally interleaved with the Python library, which broke `colcon build` when Python imports leaked into the workspace's site-packages search path. The fix was the strict separation between `ros2/`, `lidar_ros2/`, `cybersecurity_ros2/` and the pure-Python `nav_research/` package.

**Streamlit Community Cloud build pinning.** Streamlit Community Cloud pins Python and Streamlit versions independently from the local development image. A Plotly API used locally silently produced an empty figure in the cloud build. The dashboard now uses only documented stable APIs and pins minimum versions in `requirements.txt`.

**Colour-key drift in the dashboard.** Design tokens were initially defined under one set of keys (`muted`) while contribution modules used another (`text_muted`). The mismatch surfaced only at render time. A single source of truth — `nav_research.config.COLORS` — and a linting pass resolved the issue. The lesson is to keep design tokens behind a typed accessor rather than a free-form dictionary.

**Deterministic randomness across NumPy versions.** Newer NumPy `default_rng` byte-layouts differ across versions; legacy `numpy.random.seed` fixtures stopped matching. The framework standardised on `np.random.default_rng(seed)` everywhere and removed all calls to the legacy API.

**LLM-planner determinism.** The LLM mission planner (C19) ships with a deterministic rule-based fallback. This is deliberate: an actual LLM call would make the dashboard non-reproducible and would require network credentials at build time. The downstream contract — a typed list of (action, location) tuples — is identical to what an LLM call emits, so the parser can be swapped out without changing any consumer.

**Two `requirements.txt` files in spirit.** The repository's `requirements.txt` is currently the dashboard runtime. The fuller research stack (PyTorch, transformers, diffusers, open3d) is not pinned in a single file. This is an outstanding issue; section 10 documents the actual dependency layers.

**ament_python `test/` versus pytest `tests/`.** ROS 2 ament_python expects a `test/` folder; pytest conventions expect `tests/`. The repository keeps both because they serve different runners. The duplication is documented in this README to avoid confusion.

---

## 19. Deployment and Debugging Notes

**Cold-start latency on the dashboard.** Page 6 imports all twenty-six modules on first render. On a cold Streamlit Community Cloud container this is roughly four to six seconds. Subsequent renders are instantaneous. If cold-start becomes a problem, the dispatcher can be rewritten to import lazily on dropdown selection.

**Headless smoke test.** The repository's CI pipeline runs `streamlit.testing.v1.AppTest` over every contribution code and verifies the page renders without exception. This catches the colour-key class of bugs and the random-seed-API-drift class of bugs before deployment.

**TurtleBot3 hardware testing.** Real-robot runs (TurtleBot3 Burger) used a quiet office environment, a Hokuyo URG-04LX scanner and an off-board ROS 2 controller. Logs from these sessions are archived under `logs_real_world/`.

**WSL2 support.** The framework runs on Windows under WSL2 (Ubuntu 22.04). Graphics-heavy ROS 2 visualisation (RViz) requires WSLg or an X server. The dashboard works natively on Windows without WSL.

**Python environment isolation.** Use of `python -m venv` is strongly recommended. The repository's `nav_research.egg-info/` is regenerated by `pip install -e .`; do not commit it manually.

**`build/` and `install/` directories.** These are colcon artefacts. Although they appear in the repository tree, they are reproducible and can be deleted before rebuilding.

---

## 20. Limitations and Honest Disclosures

- The ROS 2 stack is **partially integrated**: not every safety contribution is wired as a runtime node. Several launch files orchestrate perception and base planning but rely on Python evaluators for the safety shields.
- 3D Gaussian Splatting (C23) is **visualised**, not optimised. No differentiable renderer ships in this repository.
- The LLM mission planner (C19) and the VLM navigation agent (C11) ship with **deterministic stubs**. Real LLM / VLM use requires an external Ollama instance or a Hugging Face account.
- The federated-learning module (C16) uses a **scalar regression** problem to make the FedAvg dynamics legible. Real perception models are not federated in this build.
- The neuromorphic module (C15) uses **synthetic event streams** rather than a calibrated DVS device.
- The adversarial module (C25) covers **LiDAR spoofing**, FGSM and PGD on perception inputs. No camera-domain physical attacks (e.g. adversarial patches under real illumination) are implemented.
- The reinforcement-learning curves (C21, C22) report results from a **synthetic environment**. Transfer to ROS 2 Gazebo is documented as future work.
- `requirements.txt` is currently the **dashboard runtime**; the full research stack requires additional packages, listed in section 10.

These limitations are restated in each affected module's deep-dive PDF.

---

## 21. Research Significance

The framework's contribution is methodological rather than the addition of a single novel component. It assembles a coherent uncertainty-aware navigation pipeline in which each layer's interface is designed to consume the layer below's uncertainty estimates and to expose its own to the layer above. The same A\* core supports learned-heuristic, risk-aware and CVaR-aware variants; the same safety layer can wrap a classical controller, a PPO policy or an LLM-driven plan; the same federated-learning loop can host any of the perception modules.

This *interface discipline* is the practical thesis of the project. It makes the difference between a collection of independent demos and a stack in which an improvement in one layer immediately benefits the others.

The Streamlit dashboard is the second methodological contribution. By making the entire research portfolio reproducible in a browser, it lowers the barrier to inspection and critique. The framework is designed to be argued with rather than admired.

---

## 22. Future Research Directions

- A differentiable 3D Gaussian Splatting pipeline for C23 with calibrated uncertainty exported to C24.
- Integration of C18's CBF shield as a ROS 2 node sitting between Nav2 and `cmd_vel`.
- Replacement of the rule-based parser in C19 with a small local LLM under a constrained-decoding wrapper that emits only typed plans.
- A real federated-learning experiment on a learned perception model, replacing the scalar regression in C16.
- Sim-to-real transfer experiments for the PPO policy (C21) using the world-model surrogate (C13) as a domain-randomisation engine.
- Joint optimisation of NBV (C07) and NeRF uncertainty (C24) so the next viewpoint reduces the field's variance rather than a frontier proxy.
- A consolidated `pyproject.toml` replacing the current `setup.py` / `setup.cfg` / `requirements.txt` triple, with optional dependency groups (`[dashboard]`, `[learning]`, `[ros2]`).

---

## 23. Citation

If this framework supports your work, please cite the repository:

```bibtex
@software{grosdouli_dynnav_2025,
  author    = {Grosdouli, Panagiota},
  title     = {{DynNav}: Dynamic Navigation and Rerouting in Unknown Environments},
  year      = {2025},
  publisher = {GitHub},
  url       = {https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments},
  license   = {Apache-2.0},
  version   = {v0.3-multi-robot-disagreement},
  note      = {26 research contributions: uncertainty-aware, risk-sensitive, learning-augmented navigation.}
}
```

A `CITATION.cff` file is provided in the repository root for tools that consume the Citation File Format.

---

## 24. Author

**Panagiota Grosdouli**
Department of Electrical and Computer Engineering
Democritus University of Thrace (DUTH)
[ee.duth.gr](https://ee.duth.gr)

The work is carried out as an independent research portfolio in autonomous systems and uncertainty-aware navigation, consolidating twenty-six methodological contributions into a single reproducible artefact.

---

## 25. License

Copyright © 2025 Panagiota Grosdouli.

Released under the **Apache License, Version 2.0**. See [`LICENSE`](LICENSE) for the full text.

The Apache-2.0 licence is chosen because it explicitly grants a patent licence alongside the copyright licence — relevant for downstream use of the safety-shield and adversarial-defence components — and because it imposes no copyleft on derived works.

---

## 26. Acknowledgements

The framework builds on the broader open-source robotics ecosystem: ROS 2 Humble, Nav2, slam_toolbox, TurtleBot3, NumPy, SciPy, PyTorch, Plotly, Streamlit, networkx, Open3D, and the Hugging Face ecosystem. Where a specific algorithm is reproduced (Hungarian assignment, median–MAD outlier filtering, FedAvg, TD3-style twin critics, PPO, Dreamer-style world models, FGSM / PGD attacks) the canonical reference is named in the corresponding module's deep-dive PDF.

Particular thanks are owed to the academic environment at DUTH ECE, which made the project possible as a sustained piece of independent research.

---
