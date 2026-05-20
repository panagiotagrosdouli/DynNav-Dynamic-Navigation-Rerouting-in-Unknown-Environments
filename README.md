
# DynNav

## Dynamic Navigation & Rerouting in Unknown Environments

Uncertainty-aware, risk-sensitive, learning-augmented autonomous navigation framework for dynamic and partially observable environments.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![ROS2](https://img.shields.io/badge/ROS2-Humble-22314E?style=for-the-badge&logo=ros&logoColor=white)](https://docs.ros.org/en/humble/)
[![Streamlit](https://img.shields.io/badge/Dashboard-Live-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://dynnav-dynamic-navigation-rerouting-in-unknown-environments-fq.streamlit.app/)
[![License](https://img.shields.io/badge/License-Apache%202.0-4CAF50?style=for-the-badge)](LICENSE)
[![Research Modules](https://img.shields.io/badge/Research%20Modules-26-9C27B0?style=for-the-badge)](#research-modules)

---

## Live Dashboard

Interactive research dashboard:

https://dynnav-dynamic-navigation-rerouting-in-unknown-environments-fq.streamlit.app/

---

## Overview

DynNav is a modular autonomous navigation research framework designed for operation in dynamic, uncertain, partially observable, and safety-critical environments.

The project combines:

- uncertainty-aware robotics
- probabilistic planning
- risk-sensitive optimisation
- formal safety verification
- reinforcement learning
- foundation-model reasoning
- multi-robot coordination
- adversarial robustness
- neuromorphic perception
- causal reasoning

into a unified experimental platform for autonomous systems research.

DynNav is built around reproducible research principles, modular experimentation, and interpretable system design.

---

## Research Positioning

DynNav explores how autonomous systems can navigate safely and intelligently under uncertainty while balancing:

- performance
- safety
- robustness
- explainability
- resource constraints
- coordination complexity

The framework integrates both classical robotics methods and modern machine-learning approaches, including:

- A* and belief-space planning
- CVaR-based risk optimisation
- Control Barrier Functions
- Signal Temporal Logic
- reinforcement learning
- diffusion occupancy prediction
- latent world models
- LLM/VLM agents
- federated learning
- Byzantine swarm consensus

The project is intended as both:
- a research framework
- and an interactive research portfolio platform.

---

## Interactive Dashboard

DynNav includes a fully interactive Streamlit dashboard that exposes the core research concepts through browser-based simulations.

The dashboard runs entirely on synthetic environments and requires:
- no GPU
- no ROS2 runtime
- no Gazebo
- no real robot hardware

### Dashboard Pages

| Page | Description |
|---|---|
| Home | Project overview, KPIs, system summary |
| Architecture | Layered system architecture and stack visualisation |
| Navigation Demo | Closed-loop navigation with online replanning |
| Risk Map | Uncertainty fields and CVaR-style planning |
| Planner Comparison | Classical vs risk-aware planner analysis |
| Research Modules | Searchable catalogue of all 26 research contributions |
| Contribution Simulations | Interactive mini-simulations for all C01–C26 modules |

---

## Interactive Contribution Simulations

DynNav includes 26 interactive simulations representing the core research contributions of the framework.

Each contribution includes:
- interactive controls
- synthetic environments
- quantitative metrics
- planner analysis
- visual simulation
- research interpretation

### Simulated Topics

| Contribution | Topic |
|---|---|
| C01 | Learned A* |
| C02 | EKF / UKF localisation |
| C03 | CVaR risk-aware planning |
| C04 | Returnability analysis |
| C05 | Safe-mode finite-state switching |
| C06 | Energy-aware routing |
| C07 | Next-Best-View exploration |
| C08 | Intrusion detection systems |
| C09 | Multi-robot coordination |
| C10 | Human-aware navigation |
| C11 | Twin-critic reinforcement learning |
| C12 | Diffusion occupancy prediction |
| C13 | Latent world models |
| C14 | Causal structural reasoning |
| C15 | Neuromorphic event perception |
| C16 | Federated robotic learning |
| C17 | Topological semantic mapping |
| C18 | STL + CBF safety shields |
| C19 | LLM mission planning |
| C20 | Failure explanation systems |
| C21 | PPO navigation learning |
| C22 | Curriculum reinforcement learning |
| C23 | Gaussian splatting |
| C24 | NeRF uncertainty estimation |
| C25 | Adversarial robustness |
| C26 | Byzantine swarm consensus |

---

## Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                         DynNav Stack                            │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│ Foundation   │ Learning     │ Safety       │ Coordination       │
│ Models       │ Layer        │ Layer        │ Layer              │
│              │              │              │                    │
│ VLM Agent    │ Learned A*   │ STL + CBF    │ Swarm BFT          │
│ LLM Planner  │ PPO          │ Safe Mode    │ Federated Learning │
│ World Models │ CurriculumRL │ Returnability│ Multi-Robot        │
├──────────────┴──────────────┴──────────────┴────────────────────┤
│                      Planning Core                              │
│        A* · Belief Space · Risk Planning · Exploration          │
├──────────────────────────────────────────────────────────────────┤
│                      Perception Layer                            │
│   LiDAR · EKF · Semantic Maps · NeRF · Gaussian Splatting       │
├──────────────────────────────────────────────────────────────────┤
│                       Security Layer                             │
│       IDS · Adversarial Robustness · Causal Attribution         │
├──────────────────────────────────────────────────────────────────┤
│                         ROS2 Humble                              │
│          TurtleBot3 · Gazebo · Nav2 · slam_toolbox              │
└──────────────────────────────────────────────────────────────────┘
````

---

## Dashboard Features

* Multi-page Streamlit research dashboard
* Plotly-based interactive visualisations
* Dynamic obstacle simulation
* Online replanning
* CVaR-style risk maps
* Planner benchmarking
* Monte-Carlo experimentation
* Safety metrics
* Modular contribution explorer
* Synthetic reproducible environments
* Interactive robotics demonstrations

---

## Project Structure

```text
DynNav/
├── app/
│   ├── dashboard.py
│   └── pages/
│       ├── 1_Architecture.py
│       ├── 2_Navigation_Demo.py
│       ├── 3_Risk_Map.py
│       ├── 4_Planner_Comparison.py
│       ├── 5_Research_Modules.py
│       └── 6_Contribution_Simulations.py
│
├── src/
│   └── dynnav_dashboard/
│       ├── config.py
│       ├── simulation.py
│       ├── metrics.py
│       ├── visualization.py
│       └── contributions/
│
├── contributions/
├── ros2/
├── research_experiments/
├── docs/
└── requirements.txt
```

---

## Quick Start

### Clone Repository

```bash
git clone https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments.git

cd DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments
```

### Create Virtual Environment

```bash
python3 -m venv venv

source venv/bin/activate
```

### Install Requirements

```bash
pip install -r requirements.txt
```

---

## Run Dashboard

```bash
PYTHONPATH=src streamlit run app/dashboard.py
```

Open:

```text
http://localhost:8501
```

---

## Selected Research Results

### STL + CBF Safety Shields

| Metric                | Without Shield | With Shield   |
| --------------------- | -------------- | ------------- |
| Constraint Violations | 4.2 / episode  | 0.3 / episode |
| Path Overhead         | —              | < 8%          |
| Avg Correction        | —              | 0.026 m/s     |

---

### Byzantine Swarm Consensus

| Metric              | Majority Voting | BFT Consensus |
| ------------------- | --------------- | ------------- |
| Detection Rate      | 60%             | 91%           |
| Correct Decision    | 71%             | 96%           |
| Byzantine Tolerance | f < N/2         | f < N/3       |

---

### Curriculum Reinforcement Learning

| Training Mode | Success Rate |
| ------------- | ------------ |
| Flat RL       | 23%          |
| Curriculum RL | 61%          |

---

## Hardware & Platform Support

| Platform            | Status    |
| ------------------- | --------- |
| ROS2 Humble         | Supported |
| TurtleBot3          | Tested    |
| Gazebo              | Tested    |
| Ubuntu 22.04        | Supported |
| WSL2                | Supported |
| Dashboard-only Mode | Supported |

---

## Citation

```bibtex
@software{dynnav2025,
  author    = {Grosdouli, Panagiota},
  title     = {{DynNav}: Dynamic Navigation & Rerouting in Unknown Environments},
  year      = {2025},
  publisher = {GitHub},
  url       = {https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments},
  license   = {Apache-2.0},
  note      = {Autonomous navigation research framework with 26 research contributions and interactive simulations}
}
```

---

## Author

Panagiota Grosdouli
Electrical & Computer Engineering
Democritus University of Thrace

---

## License

Licensed under the Apache License 2.0.

See `LICENSE` for details.

```
```
