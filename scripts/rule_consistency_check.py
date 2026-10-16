"""Command-line version of the scenario-based consistency check (thesis, Section 4.9).
Usage (from the repository root): python scripts/rule_consistency_check.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from project_evaluator import load_historical_projects  # noqa: E402
from project_evaluator.scenarios import load_scenarios, run_consistency_check  # noqa: E402

result = run_consistency_check(load_scenarios(ROOT / "data" / "illustrative_scenarios.xlsx"),
                               load_historical_projects(ROOT / "data" / "historical_projects.csv"))
table = result["table"]
print(f"Scenarios: {len(table)}  Risk: {result['risk_counts']}")
print(f"Score: median {table['Score'].median():.1f}, min {table['Score'].min():.1f}, max {table['Score'].max():.1f}")
print(f"Metamorphic checks: {result['total_checks']}, violations: {result['violations']}")
for name, (n, v) in result["checks"].items():
    print(f"  {name}: {n} checks, {v} violations")
