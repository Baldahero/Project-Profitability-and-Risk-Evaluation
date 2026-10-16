"""Illustrative scenarios and the scenario-based consistency check of the rule-based evaluation
(thesis, Section 4.9).

The 100 scenarios were defined by the author on the basis of professional experience. They are not
records of actual projects and have no observed outcomes, so they are used only to verify that the
rules respond in the expected direction (metamorphic testing), not to estimate accuracy.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from .evaluator import evaluate_project
from .models import EvaluationResult, HistoricalProject, ProjectInput

EVALUATION_DATE = date(2026, 10, 1)

# Mapping assumptions used to convert the scenario workbook into ProjectInput
PROJECT_TYPES = {
    "Curtain Wall only": "Facade",
    "Windows + Doors (High Insulation)": "Windows + Doors",
    "Windows + Doors (HI)": "Windows + Doors",
    "Windows + Doors + Curtain Wall": "Facade + Windows",
    "Windows + Doors": "Windows + Doors",
    "Windows + Curtain Wall": "Windows + Facade",
}
REPETITION_BY_COMPLEXITY = {"Low": "Repeated", "Medium": "Partially similar", "High": "New design"}
RISK_ORDER = {"Low": 1, "Medium": 2, "High": 3}


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    project: ProjectInput


def load_scenarios(path: str | Path) -> list[Scenario]:
    """Read the scenario workbook (sheets 'Original data' and 'Risk review')."""
    original = pd.read_excel(path, sheet_name="Original data")
    review = pd.read_excel(path, sheet_name="Risk review").rename(columns={"Scenario ID": "Project_ID"})
    data = original.merge(review, on="Project_ID", validate="one_to_one")
    scenarios = []
    for _, s in data.iterrows():
        quantity = int(s["Num_Construction_Types"])
        missing_docs = int(s["Assumed missing document groups"])
        project = ProjectInput(
            project_name=str(s["Project_ID"]),
            project_type=PROJECT_TYPES.get(s["Element_Types"], "Windows + Doors"),
            contract_value=float(s["Total_Value_GBP"]),
            estimated_cost=float(s["Assumed total cost GBP"]),
            evaluation_date=EVALUATION_DATE,
            requested_deadline=EVALUATION_DATE + timedelta(weeks=int(s["Assumed deadline weeks"])),
            material_type="Non-standard aluminum profiles" if s["Profile_Type"] == "Non-standard"
            else "Standard aluminum profiles",
            region=str(s["Region"]),
            wind_exposure=str(s["Wind_Exposure"]),
            technical_complexity=str(s["Technical_Complexity"]),
            design_repetition=REPETITION_BY_COMPLEXITY.get(s["Technical_Complexity"], "Partially similar"),
            installation_model="Company installs",
            element_quantity=quantity,
            production_hours_per_unit=float(s["Fabrication_Hours"]) / quantity,
            production_capacity_hours_per_week=float(s["Assumed capacity h/week"]),
            material_lead_time_weeks=int(s["Assumed supplier lead weeks"]),
            non_standard_profiles=s["Profile_Type"] == "Non-standard",
            incomplete_drawings=missing_docs >= 2 or int(s["Assumed technical issue code"]) == 2,
            missing_installation_details=missing_docs >= 1,
            pas24_required=s["PAS24_Status"] == "Yes",
            resistance_class="RC3" if s["RC3_Status"] == "Yes" else ("RC2" if s["RC2_Status"] == "Yes" else "None"),
            access_control_required=bool(s["Has_Access_Control"]),
        )
        scenarios.append(Scenario(str(s["Project_ID"]), project))
    return scenarios


def _level(result: EvaluationResult) -> int:
    return RISK_ORDER[result.risk_level.split()[0]]


def _checks(project: ProjectInput, base: EvaluationResult, historical) -> list[tuple[str, bool | None]]:
    """Return (check name, passed) for each metamorphic relation; None if not applicable."""
    ev = lambda p: evaluate_project(p, historical)
    out = []
    y = ev(replace(project, estimated_cost=project.estimated_cost + 0.05 * project.contract_value))
    out.append(("Margin −5 pp does not improve financial score or risk class",
                y.score_breakdown["financial"] <= base.score_breakdown["financial"] and _level(y) >= _level(base)))
    y = ev(replace(project, requested_deadline=project.requested_deadline - timedelta(weeks=4)))
    out.append(("Deadline 4 weeks earlier does not improve schedule score or risk class",
                y.score_breakdown["schedule"] <= base.score_breakdown["schedule"] and _level(y) >= _level(base)))
    if project.resistance_class != "RC3":
        y = ev(replace(project, resistance_class="RC3"))
        out.append(("Adding RC3 does not improve technical score or shorten preparation",
                    y.score_breakdown["technical"] <= base.score_breakdown["technical"]
                    and y.total_preparation_weeks >= base.total_preparation_weeks))
    if project.region != "Coastal":
        y = ev(replace(project, region="Coastal"))
        out.append(("Coastal region does not improve environmental score",
                    y.score_breakdown["environment"] <= base.score_breakdown["environment"]))
    if project.design_repetition != "New design":
        y = ev(replace(project, design_repetition="New design"))
        out.append(("New design does not improve similarity score",
                    y.score_breakdown["similarity"] <= base.score_breakdown["similarity"]))
    material_ready = project.evaluation_date + timedelta(weeks=base.material_lead_time_weeks)
    y = ev(replace(project, requested_deadline=material_ready - timedelta(days=7)))
    out.append(("Deadline before material readiness gives high risk", _level(y) == 3))
    y = ev(replace(project, estimated_cost=0.97 * project.contract_value))
    out.append(("Margin of 3% gives high risk", _level(y) == 3))
    return out


def run_consistency_check(scenarios: list[Scenario], historical: list[HistoricalProject] | None = None) -> dict:
    """Evaluate all scenarios and run the metamorphic checks."""
    rows, checks, alerts = [], {}, Counter()
    for sc in scenarios:
        res = evaluate_project(sc.project, historical)
        rows.append({
            "Scenario": sc.scenario_id, "Project type": sc.project.project_type,
            "Region": sc.project.region, "Complexity": sc.project.technical_complexity,
            "Margin %": round(res.margin_percent, 1), "Score": res.efficiency_score,
            "Risk": res.risk_level.split()[0], "Alerts": len(res.alerts),
        })
        for a in res.alerts:
            alerts[a.split(";")[0].split(".")[0]] += 1
        for name, ok in _checks(sc.project, res, historical):
            n, v = checks.get(name, (0, 0))
            checks[name] = (n + 1, v + (0 if ok else 1))
    table = pd.DataFrame(rows)
    return {
        "table": table,
        "risk_counts": table["Risk"].value_counts().reindex(["Low", "Medium", "High"], fill_value=0).to_dict(),
        "checks": checks,
        "total_checks": sum(n for n, _ in checks.values()),
        "violations": sum(v for _, v in checks.values()),
        "top_alerts": alerts.most_common(6),
    }
