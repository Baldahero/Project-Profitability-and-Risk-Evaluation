from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class ProjectInput:
    project_name: str
    project_type: str
    contract_value: float
    estimated_cost: float
    evaluation_date: date
    requested_deadline: date
    material_type: str
    region: str
    wind_exposure: str
    technical_complexity: str
    design_repetition: str
    installation_model: str
    element_quantity: int = 1
    package_area_m2: float = 0.0
    production_hours_per_unit: float = 0.0
    production_capacity_hours_per_week: float = 40.0
    material_lead_time_weeks: int | None = None
    non_standard_profiles: bool = False
    incomplete_drawings: bool = False
    missing_installation_details: bool = False


@dataclass(frozen=True)
class PricingInput:
    element_type: str
    width_m: float
    height_m: float
    quantity: int
    glass_supply_model: str
    wind_load: str
    thermal_performance: str
    coating_type: str


@dataclass(frozen=True)
class PricingEstimate:
    source_item: str
    source_dimensions: str
    width_m: float
    height_m: float
    area_m2: float
    quantity: int
    fabrication_time_hours_per_unit: float
    total_fabrication_time_hours: float
    material_gbp: float
    glass_gbp: float
    labour_gbp: float
    coating_gbp: float
    margin_gbp: float
    final_price_gbp: float
    total_material_gbp: float
    total_glass_gbp: float
    total_labour_gbp: float
    total_coating_gbp: float
    total_margin_gbp: float
    total_final_price_gbp: float
    total_cost_before_margin_gbp: float
    margin_rate: float
    source_row: dict[str, Any]


@dataclass(frozen=True)
class AggregatedPricingEstimate:
    estimates: tuple[PricingEstimate, ...]
    total_quantity: int
    total_area_m2: float
    fabrication_time_hours_per_unit: float
    total_fabrication_time_hours: float
    material_gbp: float
    glass_gbp: float
    labour_gbp: float
    coating_gbp: float
    margin_gbp: float
    final_price_gbp: float
    total_material_gbp: float
    total_glass_gbp: float
    total_labour_gbp: float
    total_coating_gbp: float
    total_margin_gbp: float
    total_final_price_gbp: float
    total_cost_before_margin_gbp: float
    margin_rate: float

    @property
    def package_count(self) -> int:
        return len(self.estimates)


@dataclass(frozen=True)
class HistoricalProject:
    project_id: str
    project_type: str
    material_type: str
    region: str
    wind_exposure: str
    technical_complexity: str
    design_repetition: str
    installation_model: str
    actual_margin_percent: float
    outcome: str
    notes: str = ""


@dataclass(frozen=True)
class EvaluationResult:
    margin_percent: float
    efficiency_score: float
    risk_level: str
    readiness_date: date
    material_lead_time_weeks: int
    preparation_hours: float
    preparation_weeks: float
    total_preparation_weeks: float
    protection_requirement: str
    score_breakdown: dict[str, float]
    explanations: dict[str, str]
    alerts: list[str] = field(default_factory=list)
    checklist: list[str] = field(default_factory=list)
    similar_projects: list[dict[str, Any]] = field(default_factory=list)
