"""
DynNav Dashboard — Research Modules Page
========================================

A searchable, filterable catalogue of the 26 research contributions in the
upstream DynNav repository. Each entry shows its category, a one-line
summary, and a "why it matters" note suitable for a research portfolio or
MSc/PhD application reading.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from dynnav_dashboard.config import (  # noqa: E402
    APP_ICON, APP_TITLE, COLORS, REPO_URL, RESEARCH_MODULES,
)
from dynnav_dashboard.visualization import plot_category_breakdown  # noqa: E402


st.set_page_config(
    page_title=f"Research Modules · {APP_TITLE}",
    page_icon=APP_ICON,
    layout="wide",
)


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

CATEGORY_COLOURS = {
    "Planning":                COLORS["primary"],
    "State Estimation":        COLORS["info"],
    "Safety":                  COLORS["success"],
    "Resources":               COLORS["highlight"],
    "Exploration":             COLORS["secondary"],
    "Robustness":              COLORS["danger"],
    "Coordination":            COLORS["secondary"],
    "HRI":                     COLORS["accent"],
    "Foundation Models":       COLORS["accent"],
    "Generative":              COLORS["accent"],
    "Explainability":          COLORS["warning"],
    "Perception":              COLORS["uncertainty"],
    "Mapping":                 COLORS["primary"],
    "Reinforcement Learning":  COLORS["primary"],
}


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
        .dyn-module {{
            background: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
            padding: 14px 16px;
            margin-bottom: 12px;
            transition: border-color 120ms ease;
        }}
        .dyn-module:hover {{
            border-color: {COLORS['secondary']};
        }}
        .dyn-module .header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 6px;
        }}
        .dyn-module .code {{
            font-family: 'JetBrains Mono', monospace;
            color: {COLORS['text_muted']};
            font-size: 0.78rem;
        }}
        .dyn-module h4 {{
            margin: 0;
            color: {COLORS['text']};
            font-size: 1.02rem;
        }}
        .dyn-module .one-liner {{
            color: {COLORS['text_muted']};
            font-size: 0.9rem;
            margin: 2px 0 8px 0;
            font-style: italic;
        }}
        .dyn-module .why {{
            color: {COLORS['text']};
            font-size: 0.9rem;
            line-height: 1.5;
            margin: 0;
        }}
        .dyn-cat-tag {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 600;
            border: 1px solid;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    '<div class="dyn-section-title">🔬 Research Modules · DynNav Contribution Catalogue</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<p class="dyn-section-sub">'
    f'The upstream DynNav repository ships <b>26 research contributions</b>, each '
    f'with its own algorithm, experiments, and README. The catalogue below mirrors '
    f'that structure — use the filters to narrow by category or search by keyword, '
    f'and visit the <a href="{REPO_URL}" target="_blank" '
    f'style="color:{COLORS["secondary"]};text-decoration:none">source on GitHub</a> '
    f'for the implementation details.'
    f'</p>',
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### Filters")
    categories = sorted({m.category for m in RESEARCH_MODULES})
    selected_cats = st.multiselect(
        "Category",
        options=categories,
        default=categories,
    )
    query = st.text_input("Search", placeholder="e.g. CVaR, swarm, NeRF")
    show_table = st.checkbox("Show as table", value=False)


def _matches(m) -> bool:
    if selected_cats and m.category not in selected_cats:
        return False
    if query:
        q = query.lower()
        haystack = " ".join([m.code, m.title, m.category,
                             m.one_liner, m.why_it_matters]).lower()
        if q not in haystack:
            return False
    return True


filtered = [m for m in RESEARCH_MODULES if _matches(m)]


# ---------------------------------------------------------------------------
# Top overview
# ---------------------------------------------------------------------------

c1, c2, c3 = st.columns([1.1, 1.1, 1.6])

with c1:
    st.markdown(
        f"""
        <div style="background:{COLORS['surface']};border:1px solid {COLORS['border']};
                    border-radius:10px;padding:14px 16px;">
            <div style="color:{COLORS['text_muted']};font-size:0.78rem;
                        text-transform:uppercase;letter-spacing:0.05em">Modules shown</div>
            <div style="color:{COLORS['text']};font-size:1.8rem;font-weight:700">
                {len(filtered)} / {len(RESEARCH_MODULES)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div style="background:{COLORS['surface']};border:1px solid {COLORS['border']};
                    border-radius:10px;padding:14px 16px;">
            <div style="color:{COLORS['text_muted']};font-size:0.78rem;
                        text-transform:uppercase;letter-spacing:0.05em">Distinct categories</div>
            <div style="color:{COLORS['text']};font-size:1.8rem;font-weight:700">
                {len({m.category for m in filtered})}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    cats = [m.category for m in filtered] or ["—"]
    st.plotly_chart(plot_category_breakdown(cats), use_container_width=True)


# ---------------------------------------------------------------------------
# Cards or table
# ---------------------------------------------------------------------------

if not filtered:
    st.info("No modules match the current filters.")
else:
    if show_table:
        df = pd.DataFrame([
            {"#": m.code, "Title": m.title, "Category": m.category,
             "Summary": m.one_liner, "Why it matters": m.why_it_matters}
            for m in filtered
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        # Two-column card layout
        cols = st.columns(2, gap="medium")
        for i, mod in enumerate(filtered):
            color = CATEGORY_COLOURS.get(mod.category, COLORS["primary"])
            with cols[i % 2]:
                st.markdown(
                    f"""
                    <div class="dyn-module" style="border-left:4px solid {color}">
                        <div class="header">
                            <h4>{mod.title}</h4>
                            <span class="dyn-cat-tag" style="
                                background:{color}22;
                                border-color:{color}66;
                                color:{color};
                            ">{mod.category}</span>
                        </div>
                        <div class="code">contribution {mod.code}</div>
                        <p class="one-liner">{mod.one_liner}</p>
                        <p class="why">{mod.why_it_matters}</p>
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
    f"Module summaries are condensed for dashboard use. For algorithm details, "
    f"experiment scripts, and full READMEs see "
    f"<a href='{REPO_URL}' style='color:{COLORS['secondary']}'>the upstream repository ↗</a>."
    "</p>",
    unsafe_allow_html=True,
)
