from __future__ import annotations

import csv
import math
from datetime import timedelta
from pathlib import Path
from typing import Iterable

from .models import EvaluationResult, HistoricalProject, ProjectInput


MATERIAL_LEAD_TIMES_WEEKS = {
    "Standard aluminum profiles": 4,
    "Non-standard aluminum profiles": 8,
    "Steel elements": 6,
    "Glass-heavy facade": 8,
    "Timber-aluminum windows": 7,
}

PREPARATION_WEEKS_BY_COMPLEXITY = {
    "Low": 2,
    "Medium": 4,
    "High": 6,
}

DESIGN_REPETITION_SCORE = {
    "Repeated": 90,
    "Partially similar": 70,
    "New design": 45,
}

SCORE_WEIGHTS = {
    "financial": 0.30,
    "technical": 0.25,
    "schedule": 0.25,
    "environment": 0.10,
    "similarity": 0.10,
}

DAYS_PER_WEEK = 7


def load_historical_projects(path: str | Path) -> list[HistoricalProject]:
    path = Path(path)
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [
            HistoricalProject(
                project_id=row["project_id"],
                project_type=row["project_type"],
                material_type=row["material_type"],
                region=row["region"],
                wind_exposure=row["wind_exposure"],
                technical_complexity=row["technical_complexity"],
                design_repetition=row["design_repetition"],
                installation_model=row["installation_model"],
                actual_margin_percent=float(row["actual_margin_percent"]),
                outcome=row["outcome"],
                notes=row.get("notes", ""),
            )
            for row in csv.DictReader(file)
        ]


def evaluate_project(
    project: ProjectInput,
    historical_projects: Iterable[HistoricalProject] | None = None,
) -> EvaluationResult:
    historical_projects = list(historical_projects or [])
    alerts: list[str] = []
    checklist: list[str] = []
    explanations: dict[str, str] = {}

    margin_percent = _calculate_margin(project.contract_value, project.estimated_cost)
    financial_score = _financial_score(margin_percent, alerts, explanations)

    material_lead_time_weeks = _estimate_material_lead_time(project)
    preparation_hours = _estimate_preparation_hours(project)
    preparation_weeks = _estimate_preparation_weeks(project, preparation_hours)
    total_preparation_weeks = material_lead_time_weeks + preparation_weeks
    readiness_days = math.ceil(total_preparation_weeks * DAYS_PER_WEEK)
    readiness_date = project.evaluation_date + timedelta(days=readiness_days)
    material_ready_date = project.evaluation_date + timedelta(weeks=material_lead_time_weeks)
    schedule_score = _schedule_score(project, readiness_date, material_ready_date, alerts, explanations)

    technical_score = _technical_score(project, alerts, checklist, explanations)
    protection_requirement = _protection_requirement(project)
    environment_score = _environment_score(project, alerts, checklist, explanations)

    similar_projects = _find_similar_projects(project, historical_projects)
    similarity_score = _similarity_score(project, similar_projects, explanations)

    score_breakdown = {
        "financial": financial_score,
        "technical": technical_score,
        "schedule": schedule_score,
        "environment": environment_score,
        "similarity": similarity_score,
    }
    efficiency_score = round(
        sum(score_breakdown[name] * SCORE_WEIGHTS[name] for name in SCORE_WEIGHTS),
        1,
    )
    risk_level = _risk_level(efficiency_score)

    _extend_checklist(project, readiness_date, protection_requirement, similar_projects, checklist)

    return EvaluationResult(
        margin_percent=round(margin_percent, 1),
        efficiency_score=efficiency_score,
        risk_level=risk_level,
        readiness_date=readiness_date,
        material_lead_time_weeks=material_lead_time_weeks,
        preparation_hours=round(preparation_hours, 1),
        preparation_weeks=round(preparation_weeks, 1),
        total_preparation_weeks=round(total_preparation_weeks, 1),
        protection_requirement=protection_requirement,
        score_breakdown={name: round(score, 1) for name, score in score_breakdown.items()},
        explanations=explanations,
        alerts=alerts,
        checklist=_unique(checklist),
        similar_projects=similar_projects,
    )


def _calculate_margin(contract_value: float, estimated_cost: float) -> float:
    if contract_value <= 0:
        return 0.0
    return (contract_value - estimated_cost) / contract_value * 100


def _financial_score(
    margin_percent: float,
    alerts: list[str],
    explanations: dict[str, str],
) -> float:
    if margin_percent >= 20:
        score = 100
        message = "Margin is strong for early-stage project screening."
    elif margin_percent >= 15:
        score = 85
        message = "Margin is acceptable, but should be monitored against technical risks."
    elif margin_percent >= 10:
        score = 65
        message = "Margin is moderate and leaves limited room for uncertainty."
    elif margin_percent >= 5:
        score = 40
        message = "Margin is low and should be reviewed before tender submission."
        alerts.append("Project margin is below 10%; perform pricing and contingency review.")
    else:
        score = 20
        message = "Margin is critical and may not absorb execution risks."
        alerts.append("Project margin is below 5%; commercial approval is recommended.")

    explanations["financial"] = message
    return score


def _estimate_material_lead_time(project: ProjectInput) -> int:
    if project.material_lead_time_weeks is not None:
        return max(0, project.material_lead_time_weeks)

    base_weeks = MATERIAL_LEAD_TIMES_WEEKS.get(project.material_type, 6)

    if project.non_standard_profiles:
        base_weeks = max(base_weeks, 8)

    if project.region in {"Coastal", "Industrial"}:
        base_weeks += 1

    return base_weeks


def _estimate_preparation_hours(project: ProjectInput) -> float:
    return max(0.0, project.element_quantity * project.production_hours_per_unit)


def _estimate_preparation_weeks(project: ProjectInput, preparation_hours: float) -> float:
    if preparation_hours:
        return preparation_hours / max(1.0, project.production_capacity_hours_per_week)

    preparation_weeks = PREPARATION_WEEKS_BY_COMPLEXITY.get(project.technical_complexity, 4)

    if project.installation_model in {"Company installation", "Mixed installation"}:
        preparation_weeks += 1
    if project.incomplete_drawings:
        preparation_weeks += 1
    if project.missing_installation_details:
        preparation_weeks += 1
    preparation_weeks += _volume_preparation_weeks(project)

    return float(preparation_weeks)


def _schedule_score(
    project: ProjectInput,
    readiness_date,
    material_ready_date,
    alerts: list[str],
    explanations: dict[str, str],
) -> float:
    if project.requested_deadline < material_ready_date:
        delay_days = (material_ready_date - project.requested_deadline).days
        explanations["schedule"] = (
            f"Target date is {delay_days} days before material can be ready. "
            f"Minimum material readiness date is {material_ready_date.isoformat()}."
        )
        alerts.append(
            "Material lead time is too short for the selected target date; choose a later implementation date."
        )
        return 0

    buffer_days = (project.requested_deadline - readiness_date).days

    if buffer_days >= 28:
        score = 100
        message = f"Schedule has a comfortable implementation buffer of {buffer_days} days."
    elif buffer_days >= 14:
        score = 85
        message = f"Schedule has a positive implementation buffer of {buffer_days} days."
    elif buffer_days >= 0:
        score = 70
        message = f"Implementation schedule is feasible, but buffer is only {buffer_days} days."
    elif buffer_days >= -14:
        score = 45
        message = f"Indicative implementation is {abs(buffer_days)} days after the target date."
        alerts.append("Target implementation date is tight; align customer date with procurement and preparation plan.")
    else:
        score = 20
        message = f"Indicative implementation is {abs(buffer_days)} days after the target date."
        alerts.append("Target implementation date is unrealistic based on material lead time and preparation rules.")

    volume_cap = _volume_schedule_score_cap(project)
    if volume_cap is not None and score > volume_cap:
        score = volume_cap
        message += " Large package volume requires production capacity confirmation."
        alerts.append("Large package volume requires production slot and logistics confirmation.")

    explanations["schedule"] = message
    return score


def _technical_score(
    project: ProjectInput,
    alerts: list[str],
    checklist: list[str],
    explanations: dict[str, str],
) -> float:
    score = {"Low": 90, "Medium": 70, "High": 45}.get(project.technical_complexity, 65)
    reasons = [f"Technical complexity is classified as {project.technical_complexity.lower()}."]

    if project.non_standard_profiles:
        score -= 15
        reasons.append("Non-standard profiles increase engineering and procurement uncertainty.")
        alerts.append("Non-standard profiles require supplier confirmation and technical review.")
        checklist.append("Confirm availability and lead time of non-standard profiles.")

    if project.incomplete_drawings:
        score -= 20
        reasons.append("Incomplete drawings reduce evaluation reliability.")
        alerts.append("Input drawings are incomplete; request missing drawings before final quotation.")
        checklist.append("Request missing architectural and structural drawings.")

    if project.missing_installation_details:
        score -= 10
        reasons.append("Missing installation details increase execution uncertainty.")
        alerts.append("Installation details are missing; clarify scope and responsibility split.")
        checklist.append("Clarify installation scope, access conditions, and responsibility split.")

    volume_penalty = _volume_technical_penalty(project)
    if volume_penalty:
        score -= volume_penalty
        reasons.append(
            f"Package volume is {project.element_quantity} units / {project.package_area_m2:.0f} m2, "
            "which increases production and logistics risk."
        )
        checklist.append("Confirm production slot, packing plan, and site delivery sequence for the full package.")

    explanations["technical"] = " ".join(reasons)
    return _clamp(score)


def _environment_score(
    project: ProjectInput,
    alerts: list[str],
    checklist: list[str],
    explanations: dict[str, str],
) -> float:
    score = 90
    reasons = [f"Region is {project.region.lower()} and wind exposure is {project.wind_exposure.lower()}."]

    if project.region in {"Coastal", "Industrial"}:
        score -= 20
        reasons.append("Environmental exposure increases coating requirements.")
        checklist.append("Confirm coating class and corrosion protection requirements.")

    if project.wind_exposure == "High":
        score -= 25
        reasons.append("High wind exposure requires structural verification.")
        alerts.append("High wind exposure requires additional structural verification.")
        checklist.append("Perform wind-load verification before contract approval.")
    elif project.wind_exposure == "Medium":
        score -= 10

    if project.region == "Mountain":
        score -= 10
        checklist.append("Check snow load and logistics constraints for mountain region.")

    explanations["environment"] = " ".join(reasons)
    return _clamp(score)


def _protection_requirement(project: ProjectInput) -> str:
    if project.region == "Coastal" and project.wind_exposure == "High":
        return "QC2 coating and wind-load verification"
    if project.region in {"Coastal", "Industrial"}:
        return "QC2 coating"
    if project.wind_exposure == "High":
        return "Standard coating with wind-load verification"
    return "Standard coating"


def _similarity_score(
    project: ProjectInput,
    similar_projects: list[dict],
    explanations: dict[str, str],
) -> float:
    repetition_score = DESIGN_REPETITION_SCORE.get(project.design_repetition, 60)
    best_similarity = similar_projects[0]["similarity_percent"] if similar_projects else 0

    if best_similarity:
        score = repetition_score * 0.6 + best_similarity * 0.4
        explanations["similarity"] = (
            f"Design repetition is {project.design_repetition.lower()}; "
            f"best historical similarity is {best_similarity:.0f}%."
        )
    else:
        score = repetition_score
        explanations["similarity"] = (
            f"Design repetition is {project.design_repetition.lower()}; "
            "no historical cases were provided."
        )

    return _clamp(score)


def _find_similar_projects(
    project: ProjectInput,
    historical_projects: list[HistoricalProject],
    limit: int = 3,
) -> list[dict]:
    scored = []
    for historical in historical_projects:
        similarity = _project_similarity(project, historical)
        scored.append(
            {
                "project_id": historical.project_id,
                "similarity_percent": round(similarity, 1),
                "actual_margin_percent": historical.actual_margin_percent,
                "outcome": historical.outcome,
                "notes": historical.notes,
            }
        )

    scored.sort(key=lambda item: item["similarity_percent"], reverse=True)
    return scored[:limit]


def _project_similarity(project: ProjectInput, historical: HistoricalProject) -> float:
    weights = {
        "project_type": 0.25,
        "material_type": 0.20,
        "region": 0.15,
        "wind_exposure": 0.15,
        "technical_complexity": 0.15,
        "installation_model": 0.10,
    }
    score = 0.0

    for attribute, weight in weights.items():
        if _normal(getattr(project, attribute)) == _normal(getattr(historical, attribute)):
            score += weight
        elif attribute == "technical_complexity" and _complexity_distance(
            project.technical_complexity,
            historical.technical_complexity,
        ) == 1:
            score += weight * 0.5

    return score * 100


def _risk_level(score: float) -> str:
    if score >= 75:
        return "Low risk / high efficiency"
    if score >= 55:
        return "Medium risk / acceptable with checks"
    return "High risk / revise before tender"


def _extend_checklist(
    project: ProjectInput,
    readiness_date,
    protection_requirement: str,
    similar_projects: list[dict],
    checklist: list[str],
) -> None:
    checklist.append(f"Validate indicative project implementation date: {readiness_date.isoformat()}.")
    checklist.append(f"Confirm required protection: {protection_requirement}.")
    checklist.append("Review margin assumptions and contingency level before final offer.")

    if similar_projects:
        checklist.append(f"Review lessons learned from historical project {similar_projects[0]['project_id']}.")

    if project.design_repetition == "New design":
        checklist.append("Schedule additional engineering review for new design solution.")


def _volume_preparation_weeks(project: ProjectInput) -> int:
    if project.element_quantity >= 500 or project.package_area_m2 >= 1500:
        return 6
    if project.element_quantity >= 250 or project.package_area_m2 >= 750:
        return 4
    if project.element_quantity >= 100 or project.package_area_m2 >= 300:
        return 2
    if project.element_quantity >= 50 or project.package_area_m2 >= 100:
        return 1
    return 0


def _volume_schedule_score_cap(project: ProjectInput) -> int | None:
    if project.element_quantity >= 500 or project.package_area_m2 >= 1500:
        return 70
    if project.element_quantity >= 250 or project.package_area_m2 >= 750:
        return 85
    return None


def _volume_technical_penalty(project: ProjectInput) -> int:
    if project.element_quantity >= 500 or project.package_area_m2 >= 1500:
        return 20
    if project.element_quantity >= 250 or project.package_area_m2 >= 750:
        return 12
    if project.element_quantity >= 100 or project.package_area_m2 >= 300:
        return 6
    return 0


def _complexity_distance(left: str, right: str) -> int:
    order = {"Low": 1, "Medium": 2, "High": 3}
    return abs(order.get(left, 2) - order.get(right, 2))


def _normal(value: str) -> str:
    return value.strip().casefold()


def _clamp(value: float, lower: float = 0, upper: float = 100) -> float:
    return max(lower, min(upper, value))


def _unique(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
