import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from project_evaluator import load_historical_projects  # noqa: E402
from project_evaluator.scenarios import load_scenarios, run_consistency_check  # noqa: E402


def test_illustrative_scenarios_satisfy_all_metamorphic_relations():
    scenarios = load_scenarios(ROOT / "data" / "illustrative_scenarios.xlsx")
    result = run_consistency_check(scenarios, load_historical_projects(ROOT / "data" / "historical_projects.csv"))
    assert len(scenarios) == 100
    assert result["total_checks"] == 640
    assert result["violations"] == 0
