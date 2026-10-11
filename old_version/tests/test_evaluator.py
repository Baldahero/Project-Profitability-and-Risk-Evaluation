from __future__ import annotations

import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_evaluator import (
    HistoricalProject,
    PricingInput,
    ProjectInput,
    aggregate_pricing_estimates,
    estimate_price,
    evaluate_project,
)


class EvaluatorTest(unittest.TestCase):
    def test_low_margin_triggers_commercial_alert(self) -> None:
        project = _project(contract_value=100000, estimated_cost=96000)

        result = evaluate_project(project)

        self.assertLess(result.score_breakdown["financial"], 40)
        self.assertTrue(any("commercial approval" in alert.lower() for alert in result.alerts))

    def test_coastal_high_wind_requires_qc2_and_wind_verification(self) -> None:
        project = _project(region="Coastal", wind_exposure="High")

        result = evaluate_project(project)

        self.assertEqual(result.protection_requirement, "QC2 coating and wind-load verification")
        self.assertTrue(any("wind-load verification" in item.lower() for item in result.checklist))

    def test_similarity_returns_best_historical_case(self) -> None:
        project = _project(project_type="Windows", material_type="Timber-aluminum windows")
        historical = [
            HistoricalProject(
                project_id="LOW-MATCH",
                project_type="Facade",
                material_type="Glass-heavy facade",
                region="Coastal",
                wind_exposure="High",
                technical_complexity="High",
                design_repetition="New design",
                installation_model="Company installation",
                actual_margin_percent=8.5,
                outcome="High risk",
            ),
            HistoricalProject(
                project_id="BEST-MATCH",
                project_type="Windows",
                material_type="Timber-aluminum windows",
                region="Urban",
                wind_exposure="Medium",
                technical_complexity="Medium",
                design_repetition="Partially similar",
                installation_model="Company installation",
                actual_margin_percent=18.0,
                outcome="Completed profitably",
            ),
        ]

        result = evaluate_project(project, historical)

        self.assertEqual(result.similar_projects[0]["project_id"], "BEST-MATCH")
        self.assertGreater(result.similar_projects[0]["similarity_percent"], 80)

    def test_custom_material_lead_time_drives_readiness_date(self) -> None:
        project = _project(
            material_lead_time_weeks=10,
            technical_complexity="Low",
            installation_model="Client installation",
        )

        result = evaluate_project(project)

        self.assertEqual(result.material_lead_time_weeks, 10)
        self.assertEqual(result.preparation_weeks, 2)
        self.assertEqual(result.readiness_date, date(2026, 4, 12) + timedelta(weeks=12))

    def test_fixed_window_preparation_uses_four_hours_per_unit(self) -> None:
        project = _project(
            element_quantity=1,
            production_hours_per_unit=4,
            production_capacity_hours_per_week=40,
            material_lead_time_weeks=10,
            technical_complexity="Low",
        )

        result = evaluate_project(project)

        self.assertEqual(result.preparation_hours, 4)
        self.assertEqual(result.preparation_weeks, 0.1)
        self.assertEqual(result.readiness_date, date(2026, 4, 12) + timedelta(days=71))

    def test_large_quantity_adds_schedule_and_risk_pressure(self) -> None:
        project = _project(
            element_quantity=500,
            package_area_m2=2000,
            requested_deadline=date(2026, 4, 12) + timedelta(weeks=30),
        )

        result = evaluate_project(project)

        self.assertGreaterEqual(result.preparation_weeks, 11)
        self.assertLessEqual(result.score_breakdown["schedule"], 70)
        self.assertNotEqual(result.risk_level, "Low risk / high efficiency")
        self.assertTrue(any("production" in alert.lower() for alert in result.alerts))

    def test_target_before_material_lead_time_is_schedule_error(self) -> None:
        project = _project(
            material_lead_time_weeks=10,
            requested_deadline=date(2026, 4, 12) + timedelta(weeks=8),
        )

        result = evaluate_project(project)

        self.assertEqual(result.score_breakdown["schedule"], 0)
        self.assertEqual(result.risk_level, "High risk / revise before tender")
        self.assertTrue(any("lead time is too short" in alert.lower() for alert in result.alerts))

    def test_pricing_estimate_scales_excel_source_row(self) -> None:
        pricing_input = PricingInput(
            element_type="Fixed window",
            width_m=2,
            height_m=2,
            quantity=1,
            glass_supply_model="Company supplies glass units (34% full project margin)",
            wind_load="< 1.5 kN/m2",
            thermal_performance="< 0.9 W/m2K",
            coating_type="Pre-anodized + Qualicoat Class 1",
        )
        rows = [
            {
                "item": "1",
                "element_type": "Fixed window",
                "width_m": 1.0,
                "height_m": 1.0,
                "area_m2": 1.0,
                "glass_supply_model": "Company supplies glass units (34% full project margin)",
                "wind_load": "< 1.5 kN/m2",
                "thermal_performance": "< 0.9 W/m2K",
                "price_material_gbp": 285.0,
                "price_glass_unit_gbp": 52.05,
                "labour_work_gbp": 31.0,
                "coating_type": "Pre-anodized + Qualicoat Class 1",
                "coating_total_gbp": 138.0,
                "margin_gbp": 161.517,
                "final_price_gbp": 667.567,
            }
        ]

        estimate = estimate_price(pricing_input, rows)

        self.assertEqual(estimate.area_m2, 4)
        self.assertEqual(estimate.fabrication_time_hours_per_unit, 4)
        self.assertEqual(estimate.material_gbp, 570)
        self.assertEqual(estimate.coating_gbp, 552)
        self.assertEqual(estimate.final_price_gbp, 1704.97)

    def test_customer_supplied_glass_uses_43_percent_material_margin(self) -> None:
        pricing_input = PricingInput(
            element_type="Fixed window",
            width_m=2,
            height_m=2,
            quantity=1,
            glass_supply_model="External supplier provides glass units (43% material margin only)",
            wind_load="< 1.5 kN/m2",
            thermal_performance="< 0.9 W/m2K",
            coating_type="Pre-anodized + Qualicoat Class 1",
        )
        rows = [
            {
                "item": "2",
                "element_type": "Fixed window",
                "width_m": 1.0,
                "height_m": 1.0,
                "area_m2": 1.0,
                "glass_supply_model": "External supplier provides glass units (43% material margin only)",
                "wind_load": "< 1.5 kN/m2",
                "thermal_performance": "< 0.9 W/m2K",
                "price_material_gbp": 285.0,
                "price_glass_unit_gbp": 0.0,
                "labour_work_gbp": 16.0,
                "coating_type": "Pre-anodized + Qualicoat Class 1",
                "coating_total_gbp": 138.0,
                "margin_gbp": 122.55,
                "final_price_gbp": 561.55,
                "fabrication_time_h": 4.0,
            }
        ]

        estimate = estimate_price(pricing_input, rows)

        self.assertEqual(estimate.margin_rate, 0.43)
        self.assertEqual(estimate.fabrication_time_hours_per_unit, 4)
        self.assertEqual(estimate.margin_gbp, 245.1)
        self.assertEqual(estimate.final_price_gbp, 1399.1)

    def test_multiple_constructions_aggregate_into_one_project_package(self) -> None:
        rows = [
            {
                "item": "1",
                "element_type": "Fixed window",
                "width_m": 1.0,
                "height_m": 1.0,
                "area_m2": 1.0,
                "glass_supply_model": "Company supplies glass units (34% full project margin)",
                "wind_load": "< 1.5 kN/m2",
                "thermal_performance": "< 0.9 W/m2K",
                "price_material_gbp": 285.0,
                "price_glass_unit_gbp": 52.05,
                "labour_work_gbp": 31.0,
                "coating_type": "Pre-anodized + Qualicoat Class 1",
                "coating_total_gbp": 138.0,
                "margin_gbp": 161.517,
                "final_price_gbp": 667.567,
                "fabrication_time_h": 4.0,
            },
            {
                "item": "2",
                "element_type": "Single door",
                "width_m": 1.0,
                "height_m": 2.0,
                "area_m2": 2.0,
                "glass_supply_model": "Company supplies glass units (34% full project margin)",
                "wind_load": "< 1.5 kN/m2",
                "thermal_performance": "< 0.9 W/m2K",
                "price_material_gbp": 410.0,
                "price_glass_unit_gbp": 88.0,
                "labour_work_gbp": 75.0,
                "coating_type": "Pre-anodized + Qualicoat Class 1",
                "coating_total_gbp": 190.0,
                "margin_gbp": 233.92,
                "final_price_gbp": 996.92,
                "fabrication_time_h": 6.0,
            },
        ]
        estimates = [
            estimate_price(
                PricingInput(
                    element_type="Fixed window",
                    width_m=1.5,
                    height_m=1.2,
                    quantity=2,
                    glass_supply_model="Company supplies glass units (34% full project margin)",
                    wind_load="< 1.5 kN/m2",
                    thermal_performance="< 0.9 W/m2K",
                    coating_type="Pre-anodized + Qualicoat Class 1",
                ),
                rows,
            ),
            estimate_price(
                PricingInput(
                    element_type="Single door",
                    width_m=1.1,
                    height_m=2.2,
                    quantity=1,
                    glass_supply_model="Company supplies glass units (34% full project margin)",
                    wind_load="< 1.5 kN/m2",
                    thermal_performance="< 0.9 W/m2K",
                    coating_type="Pre-anodized + Qualicoat Class 1",
                ),
                rows,
            ),
        ]

        aggregate = aggregate_pricing_estimates(estimates)

        self.assertEqual(aggregate.package_count, 2)
        self.assertEqual(aggregate.total_quantity, 3)
        self.assertEqual(aggregate.total_area_m2, 6.02)
        self.assertEqual(
            aggregate.total_final_price_gbp,
            round(sum(item.total_final_price_gbp for item in estimates), 2),
        )
        self.assertEqual(
            aggregate.total_fabrication_time_hours,
            round(sum(item.total_fabrication_time_hours for item in estimates), 2),
        )
        self.assertEqual(aggregate.margin_rate, 0.34)


def _project(**overrides) -> ProjectInput:
    values = {
        "project_name": "Test project",
        "project_type": "Facade",
        "contract_value": 100000,
        "estimated_cost": 83000,
        "evaluation_date": date(2026, 4, 12),
        "requested_deadline": date(2026, 4, 12) + timedelta(weeks=14),
        "material_type": "Standard aluminum profiles",
        "region": "Urban",
        "wind_exposure": "Medium",
        "technical_complexity": "Medium",
        "design_repetition": "Partially similar",
        "installation_model": "Company installation",
        "non_standard_profiles": False,
        "incomplete_drawings": False,
        "missing_installation_details": False,
    }
    values.update(overrides)
    return ProjectInput(**values)


if __name__ == "__main__":
    unittest.main()
