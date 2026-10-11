import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from datetime import date
from pathlib import Path

import pytest

from project_evaluator import (DECISION_MATRIX, MarketRiskResult, ProjectInput, TenderInput,
                              assess_market_risk, evaluate_project, recommend_bid)
from project_evaluator.market_risk import DEFAULT_MODEL_PATH, tender_features


def project(**kw):
    base = dict(project_name="Test", project_type="Windows", contract_value=100000, estimated_cost=80000,
                evaluation_date=date(2026, 10, 1), requested_deadline=date(2027, 3, 1),
                material_type="Standard aluminum profiles", region="Inland", wind_exposure="Low",
                technical_complexity="Low", design_repetition="Repeated", installation_model="Client installation",
                element_quantity=20, production_hours_per_unit=4, production_capacity_hours_per_week=160)
    base.update(kw)
    return ProjectInput(**base)


def market(low):
    return MarketRiskResult(probability_low_competition=0.6 if low else 0.1, low_competition=low, threshold=0.4)


def test_matrix_covers_all_cells():
    assert set(DECISION_MATRIX) == {(r, c) for r in ("Low", "Medium", "High") for c in (True, False)}


def test_low_risk_and_low_competition_is_priority():
    assert recommend_bid(evaluate_project(project()), market(True)).label == "Priority tender"


def test_low_risk_and_strong_competition_expects_price_pressure():
    assert recommend_bid(evaluate_project(project()), market(False)).label == "Bid with price pressure"


def test_critical_deadline_overrides_favourable_market():
    result = evaluate_project(project(requested_deadline=date(2026, 10, 10)))
    rec = recommend_bid(result, market(True))
    assert rec.critical_override and rec.internal_risk == "High"
    assert rec.label == "Resolve critical issues first"


def test_critical_margin_and_strong_competition_gives_do_not_bid():
    rec = recommend_bid(evaluate_project(project(estimated_cost=97000)), market(False))
    assert rec.label == "Do not bid"


def test_features_handle_missing_value():
    f = tender_features(TenderInput(title="Roof repair"))
    assert f.loc[0, "val_missing"] == 1 and f.loc[0, "cpv3"] == "NA"


@pytest.mark.skipif(not Path(DEFAULT_MODEL_PATH).exists(), reason="trained model file not present")
def test_model_scores_open_school_tender_as_competitive():
    t = TenderInput(title="Window and door replacement", description="Replacement of windows at a primary school",
                    estimated_value_gbp=450000, procedure="Open procedure", cpv_code="45421100",
                    buyer_name="Example Borough Council")
    m = assess_market_risk(t)
    assert 0 <= m.probability_low_competition <= 1 and not m.low_competition and m.top_factors


@pytest.mark.skipif(not Path(DEFAULT_MODEL_PATH).exists(), reason="trained model file not present")
def test_model_scores_direct_award_as_low_competition():
    t = TenderInput(title="Bridge strengthening works", procedure="Award procedure without prior publication of a call for competition",
                    cpv_code="45221111")
    assert assess_market_risk(t).low_competition
