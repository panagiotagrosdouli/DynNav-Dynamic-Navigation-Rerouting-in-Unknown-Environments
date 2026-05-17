# 🔬 Semiconductor Wafer Defect Classification

<div align="center">

![CI](https://img.shields.io/github/actions/workflow/status/PanagiotaGr/wafer-fault-detection-with-ml/ci.yml?label=CI&style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10%20|%203.11%20|%203.12-blue?style=flat-square&logo=python)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-orange?style=flat-square&logo=pytorch)
![License](https://img.shields.io/badge/License-Apache%202.0-green?style=flat-square)
![Coverage](https://img.shields.io/badge/coverage-checked-brightgreen?style=flat-square)

**Classical ML & deep learning for wafer map defect detection**  
*With a research study on few-shot learning under extreme data scarcity and class imbalance*

[Objective](#-objective) · [Dataset](#-dataset) · [Pipeline](#-pipeline) · [Results](#-results) · [Few-Shot Study](#-few-shot-learning-experiments) · [Install](#-installation--usage) · [Contributing](#-contributing)

</div>

---

## 🎯 Objective

Automatically recognise defect types in semiconductor wafer maps using both classical and deep learning approaches. The project studies classification under:

- **Standard supervised learning** — full dataset, classical ML & CNN variants
- **Few-shot (limited-data) scenarios** — extreme scarcity with only 5–20 samples per class

| Category | Models |
|---|---|
| Classical ML | Logistic Regression, SVM, Random Forest |
| Deep Learning | CNN (baseline, weighted loss, focal loss, focal + augmentation) |
| Research | Few-shot variants across k = 5, 10, 20 samples per class |

---

## 📦 Dataset

- **Source:** [WM-811K](https://www.kaggle.com/qingyi/wm811k-wafer-map) (Kaggle / MIR Lab)
- **Format:** Wafer map images with labeled defect categories, stored as `LSWMD.pkl`

> ⚠️ Dataset not included. Run `python download_dataset.py` or place `LSWMD.pkl` in `data/raw/`.

**Defect classes:** `edge-ring` · `edge-loc` · `center` · `loc` · `scratch` · `random` · `donut` · `near-full`

---

## ⚙️ Pipeline

```
LSWMD.pkl
    │
    ▼
┌───────────────────┐
│   Preprocessing   │  remove invalid labels · resize 64×64 · normalise [0, 1]
└────────┬──────────┘
         │
    ┌────┴──────┐
    ▼           ▼
┌────────┐  ┌─────────────────────────────────────────────────┐
│  ML    │  │                Deep Learning                     │
│  LR    │  │  baseline → weighted → focal → focal + aug       │
│  SVM   │  └───────────────────┬─────────────────────────────┘
│  RF    │                      │
└───┬────┘         ┌────────────▼────────────┐
    │               │   Few-Shot Study         │
    │               │   k = 5 / 10 / 20       │
    │               └────────────┬────────────┘
    └──────────────┬─────────────┘
                   ▼
           ┌───────────────┐
           │   Evaluation  │
           │  accuracy     │
           │  F1 macro/wtd │
           │  ROC-AUC      │
           │  confusion ✦  │
           └───────────────┘
```

All hyperparameters live in `config.yaml` — no hardcoded values in the code.

---

## 📈 Results

### Classical ML

| Model | Accuracy | F1 (macro) | F1 (weighted) |
|---|---|---|---|
| Logistic Regression | 62.7% | — | — |
| SVM | 65.7% | — | — |
| Random Forest | 78.5% | — | — |
| **Random Forest (optimised)** | **79.4%** | — | — |

> F1 scores are computed automatically and saved to `outputs/results/` on each run.

### CNN Deep Learning

| Variant | Loss | Augmentation |
|---|---|---|
| baseline | Cross-entropy | ✗ |
| weighted | Weighted CE | ✗ |
| focal | Focal loss | ✗ |
| focal_aug | Focal loss | ✓ |

---

## 🎯 Few-Shot Learning Experiments

Accuracy under extreme data scarcity (k samples per class):

| Samples / class | Baseline | Weighted loss | Focal loss | Focal + Aug |
|---|---|---|---|---|
| k = 5 | 0.20 | 0.13 | 0.07 | 0.20 |
| k = 10 | 0.43 | 0.43 | 0.37 | 0.10 |
| k = 20 | 0.52 | **0.57 ↑** | 0.18 | 0.47 |

---

## 💡 Key Findings

- ✅ **Weighted loss consistently wins** under class imbalance, even in extreme few-shot scenarios
- ❌ **Focal loss underperforms** at very low data regimes (k = 5, k = 10)
- ❌ **Augmentation can hurt** when samples per class are very limited (k = 10 drops to 0.10)
- 📈 **More data matters most** — the largest accuracy gain comes from increasing k

> **Scientific insight:** In few-shot scenarios, simple approaches (e.g. weighted loss) can outperform architecturally complex solutions. Complexity alone does not equal performance.

---

## 🗂️ Repository Structure

```
wafer-fault-detection-with-ml/
│
├── src/                                    ← shared library (no duplication)
│   ├── data/
│   │   ├── loader.py                       # load, clean, split — single source of truth
│   │   └── augmentation.py                # torchvision transform pipelines
│   ├── models/
│   │   ├── cnn.py                          # WaferCNN architecture
│   │   └── classical.py                   # RF, SVM, LR factories
│   ├── training/
│   │   ├── trainer.py                      # training loop + early stopping
│   │   └── losses.py                       # CE, weighted CE, focal loss
│   ├── eval/
│   │   ├── metrics.py                      # accuracy, F1, ROC-AUC, confusion matrix
│   │   └── plots.py                        # all visualisation helpers
│   └── utils.py                            # config loader, seed, device
│
├── wafer_pipeline.py                       # classical ML entry point
├── wafer_cnn_pipeline.py                   # CNN entry point (all variants)
├── wafer_fewshot_focal_experiment.py       # few-shot experiment
│
├── tests/
│   ├── test_loader.py                      # unit tests (no dataset needed)
│   └── test_metrics.py
│
├── outputs/
│   ├── figures/
│   ├── results/
│   └── models/
│
├── config.yaml                             # all hyperparameters here
├── pyproject.toml                          # ruff + black + pytest config
├── requirements.txt
├── requirements-dev.txt
├── .github/workflows/ci.yml               # lint + test on push/PR
├── CONTRIBUTING.md
└── README.md
```

---

## 🛠️ Technologies

| Tool | Purpose |
|---|---|
| Python 3.10+ | Core language |
| PyTorch 2.0+ | CNN models & training |
| torchvision | Augmentation transforms |
| Scikit-learn | Classical ML & label encoding |
| NumPy / Pandas | Data processing |
| OpenCV | Image resizing |
| Matplotlib / Seaborn | Visualisation |
| PyYAML | Configuration |
| pytest | Unit tests |
| ruff + black | Linting & formatting |

---

## 🚀 Installation & Usage

### Setup

```bash
git clone https://github.com/PanagiotaGr/wafer-fault-detection-with-ml.git
cd wafer-fault-detection-with-ml

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Run pipelines

```bash
# Classical ML (LR + SVM + Random Forest)
python wafer_pipeline.py

# All CNN variants
python wafer_cnn_pipeline.py

# Single CNN variant
python wafer_cnn_pipeline.py --variant focal_aug

# Few-shot experiment
python wafer_fewshot_focal_experiment.py
```

All pipelines read from `config.yaml` — override with `--config my_config.yaml`.

### Run tests

```bash
pytest tests/ -v
pytest tests/ --cov=src --cov-report=term-missing
```

### Outputs

```
outputs/figures/   confusion matrices, training curves, comparison plots
outputs/results/   per-class CSV, summary JSON, confusion matrix CSV
outputs/models/    best model checkpoints (.pt)
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, code style rules, and how to add new models or loss functions.

---

## 📖 Citation

```bibtex
@software{Grosdouli_Wafer_Fault_Detection_2026,
  author  = {Grosdouli, Panagiota},
  title   = {Semiconductor Wafer Defect Classification: A Study on Classical ML and Few-Shot Deep Learning},
  url     = {https://github.com/PanagiotaGr/wafer-fault-detection-with-ml},
  year    = {2026}
}
```

---

## 🙏 Acknowledgments

- [WM-811K / LSWMD dataset](https://www.kaggle.com/qingyi/wm811k-wafer-map)
- Semiconductor defect detection research community

---

## 📄 License

Distributed under the [Apache 2.0 License](LICENSE).
