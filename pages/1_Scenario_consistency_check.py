"""Streamlit page: scenario-based consistency check of the rule-based evaluation (thesis, Section 4.9)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from project_evaluator import load_historical_projects  # noqa: E402
from project_evaluator.scenarios import load_scenarios, run_consistency_check  # noqa: E402

st.set_page_config(page_title="Scenario consistency check", layout="wide")
st.title("Scenario-based consistency check")
st.caption("100 illustrative scenarios defined by the author on the basis of professional experience are evaluated "
           "with the same rules as in the main page. They are not actual projects and have no observed outcomes: "
           "the check verifies that the rules respond in the expected direction (metamorphic testing), "
           "not their accuracy.")


@st.cache_data
def _run():
    scenarios = load_scenarios(ROOT / "data" / "illustrative_scenarios.xlsx")
    historical = load_historical_projects(ROOT / "data" / "historical_projects.csv")
    return run_consistency_check(scenarios, historical)


result = _run()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Scenarios", len(result["table"]))
c2.metric("Low / Medium / High", " / ".join(str(result["risk_counts"][k]) for k in ("Low", "Medium", "High")))
c3.metric("Metamorphic checks", result["total_checks"])
c4.metric("Violations", result["violations"])

left, right = st.columns([1, 1.4])
with left:
    st.markdown("**Risk classification by technical complexity**")
    table = result["table"]
    counts = (pd.crosstab(table["Complexity"], table["Risk"])
              .reindex(index=["Low", "Medium", "High"], columns=["Low", "Medium", "High"], fill_value=0))
    counts.index = [f"{n}. {i}" for n, i in enumerate(counts.index, 1)]
    counts.columns = [f"{c} risk" for c in counts.columns]
    st.bar_chart(counts, color=["#2e7d32", "#f9a825", "#c62828"], x_label="Technical complexity",
                 y_label="Scenarios")
with right:
    st.markdown("**Metamorphic relations**")
    st.dataframe(pd.DataFrame([{"Relation": k, "Checks": n, "Violations": v} for k, (n, v) in result["checks"].items()]),
                 hide_index=True, use_container_width=True)
    st.markdown("**Most frequent alerts**")
    st.dataframe(pd.DataFrame(result["top_alerts"], columns=["Alert", "Scenarios"]), hide_index=True,
                 use_container_width=True)

st.markdown("**Evaluation of each scenario**")
st.dataframe(result["table"], hide_index=True, use_container_width=True)
