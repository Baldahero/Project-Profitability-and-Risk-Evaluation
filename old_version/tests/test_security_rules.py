from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
import unittest

from project_evaluator import ProjectInput, evaluate_project


def _base_project() -> ProjectInput:
    evaluation_date = date(2026, 1, 1)
    return ProjectInput(
        project_name="Security rule test",
        project_type="Doors",
        contract_value=100_000,
        estimated_cost=65_000,
        evaluation_date=evaluation_date,
        requested_deadline=evaluation_date + timedelta(weeks=30),
        material_type="Standard aluminum profiles",
        region="Urban",
        wind_exposure="Low",
        technical_complexity="Low",
        design_repetition="Repeated",
        installation_model="Client installation",
        element_quantity=10,
        package_area_m2=20,
        production_hours_per_unit=4,
        production_capacity_hours_per_week=40,
        material_lead_time_weeks=4,
    )


class SecurityRuleTests(unittest.TestCase):
    def test_security_penalties_are_transparent_and_cumulative(self) -> None:
        project = _base_project()

        baseline = evaluate_project(project)
        pas24 = evaluate_project(replace(project, pas24_required=True))
        rc2 = evaluate_project(replace(project, resistance_class="RC2"))
        rc3 = evaluate_project(replace(project, resistance_class="RC3"))
        access = evaluate_project(replace(project, access_control_required=True))
        combined = evaluate_project(
            replace(
                project,
                pas24_required=True,
                resistance_class="RC3",
                access_control_required=True,
            )
        )

        self.assertEqual(baseline.score_breakdown["technical"], 90)
        self.assertEqual(pas24.score_breakdown["technical"], 85)
        self.assertEqual(rc2.score_breakdown["technical"], 80)
        self.assertEqual(rc3.score_breakdown["technical"], 70)
        self.assertEqual(access.score_breakdown["technical"], 82)
        self.assertEqual(combined.score_breakdown["technical"], 57)

    def test_security_requirements_extend_preparation_time(self) -> None:
        project = _base_project()

        self.assertEqual(evaluate_project(project).preparation_weeks, 1.0)
        self.assertEqual(
            evaluate_project(replace(project, pas24_required=True)).preparation_weeks,
            1.5,
        )
        self.assertEqual(
            evaluate_project(replace(project, resistance_class="RC2")).preparation_weeks,
            2.0,
        )
        self.assertEqual(
            evaluate_project(replace(project, resistance_class="RC3")).preparation_weeks,
            3.0,
        )
        self.assertEqual(
            evaluate_project(replace(project, access_control_required=True)).preparation_weeks,
            2.0,
        )

    def test_combined_security_requirement_is_reported_and_actionable(self) -> None:
        result = evaluate_project(
            replace(
                _base_project(),
                pas24_required=True,
                resistance_class="RC3",
                access_control_required=True,
            )
        )

        self.assertEqual(result.security_requirement, "PAS 24 + RC3 + Access control")
        checklist = " ".join(result.checklist)
        alerts = " ".join(result.alerts)
        self.assertIn("PAS 24", checklist)
        self.assertIn("RC3", checklist)
        self.assertIn("access-control", checklist.lower())
        self.assertIn("RC3", alerts)

    def test_invalid_resistance_class_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "resistance_class"):
            evaluate_project(replace(_base_project(), resistance_class="RC4"))


if __name__ == "__main__":
    unittest.main()
