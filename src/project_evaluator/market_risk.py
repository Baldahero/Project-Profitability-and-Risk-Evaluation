"""Market-risk component: probability that a construction tender receives at most two bids.

The model (Logistic Regression on tabular and text features) is trained offline on UK Find a Tender
data with ``train_market_model.py`` and stored as ``market_risk_model.joblib`` (thesis, Sections 3.10 and 4.2).
This module loads the model, scores a tender notice and combines the result with the rule-based
internal evaluation in the decision matrix (thesis, Table 13).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .models import BidRecommendation, EvaluationResult, MarketRiskResult, TenderInput

DEFAULT_THRESHOLD = 0.40          # thesis, Section 3.6
DEFAULT_MODEL_PATH = Path(__file__).with_name("market_risk_model.joblib")

# Decision matrix (thesis, Table 13): (internal risk row, low competition?) -> (label, recommendation)
DECISION_MATRIX: dict[tuple[str, bool], tuple[str, str]] = {
    ("Low", True): ("Priority tender", "Bid at the standard margin."),
    ("Low", False): ("Bid with price pressure", "Bid, but expect price pressure; review the pricing strategy."),
    ("Medium", True): ("Bid after clarification", "Bid after resolving the clarification items."),
    ("Medium", False): ("Check if worth preparing", "Assess whether the preparation effort is justified."),
    ("High", True): ("Resolve critical issues first", "Bid only after the critical issues have been resolved."),
    ("High", False): ("Do not bid", "Do not bid."),
}

_BUYER_TYPES = [("nhs", "health"), ("hospital", "health"), ("council", "council"), ("borough", "council"),
                ("county", "council"), ("university", "education"), ("college", "education"),
                ("school", "education"), ("academy", "education"), ("housing", "housing"), ("homes", "housing"),
                ("police", "police"), ("ministry", "central"), ("department", "central"), ("agency", "central")]

_NUMERIC_LABELS = {"logval": "Estimated value", "val_missing": "Value not published", "lots": "Number of lots",
                   "buyer_n": "Buyer activity", "gpa": "GPA coverage", "dps": "Dynamic purchasing system",
                   "framework": "Framework agreement", "eauction": "Electronic auction"}


def buyer_type(name: str) -> str:
    name = str(name).lower()
    for key, value in _BUYER_TYPES:
        if key in name:
            return value
    return "other"


def tender_features(tender: TenderInput) -> pd.DataFrame:
    """Build the one-row feature table expected by the trained model (same features as in training)."""
    value = tender.estimated_value_gbp
    logval = float(np.log10(value)) if value and value > 0 else np.nan
    row = {
        "logval": logval,
        "val_missing": int(np.isnan(logval)),
        "lots": min(max(tender.lots, 1), 20),
        "buyer_n": min(max(tender.buyer_activity, 1), 50),
        "gpa": int(tender.gpa_covered),
        "dps": int(tender.dynamic_purchasing_system),
        "framework": int(tender.framework_agreement),
        "eauction": int(tender.electronic_auction),
        "procedure": tender.procedure,
        "legal": tender.legal_basis,
        "above": {True: "True", False: "False", None: "nan"}[tender.above_threshold],
        "cpv3": (tender.cpv_code or "NA")[:3],
        "buyer_type": buyer_type(tender.buyer_name),
        "text": f"{tender.title} {tender.description[:1500]}",
    }
    return pd.DataFrame([row])


@lru_cache(maxsize=4)
def load_market_model(path: str | Path = DEFAULT_MODEL_PATH) -> Any:
    import joblib
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Market-risk model not found: {path}. Train it with train_market_model.py and copy it here."
        )
    return joblib.load(path)


def _readable(name: str) -> str:
    prefix, _, rest = name.partition("__")
    if prefix == "t":
        return f'Tender text: "{rest}"'
    if prefix == "n":
        return _NUMERIC_LABELS.get(rest, rest)
    for key, label in [("procedure_", "Procedure"), ("legal_", "Legal basis"), ("above_", "Above threshold"),
                       ("cpv3_", "Work type (CPV)"), ("buyer_type_", "Buyer type")]:
        if rest.startswith(key):
            return f"{label}: {rest[len(key):]}"
    return rest


def assess_market_risk(tender: TenderInput, model: Any | None = None,
                       threshold: float = DEFAULT_THRESHOLD, top: int = 5) -> MarketRiskResult:
    """Return the probability of low competition (at most two bids) and the main contributing factors."""
    model = model if model is not None else load_market_model()
    features = tender_features(tender)
    probability = float(model.predict_proba(features)[0, 1])

    pre, clf = model.named_steps["p"], model.named_steps["m"]
    z = pre.transform(features)
    coef = clf.coef_[0]
    contrib = np.asarray(z.multiply(coef).todense()).ravel() if hasattr(z, "multiply") else np.ravel(z) * coef
    names = pre.get_feature_names_out()
    order = [i for i in np.argsort(-np.abs(contrib)) if contrib[i] != 0][:top]
    factors = tuple((_readable(names[i]), round(float(contrib[i]), 3)) for i in order)

    return MarketRiskResult(
        probability_low_competition=round(probability, 3),
        low_competition=probability >= threshold,
        threshold=threshold,
        top_factors=factors,
    )


def _internal_row(evaluation: EvaluationResult) -> tuple[str, bool]:
    """Map the internal evaluation to Low/Medium/High; critical issues always give High."""
    critical = evaluation.score_breakdown.get("schedule", 100) == 0 or evaluation.margin_percent < 5
    if critical:
        return "High", True
    level = evaluation.risk_level.split()[0]
    return (level if level in {"Low", "Medium", "High"} else "Medium"), False


def recommend_bid(evaluation: EvaluationResult, market: MarketRiskResult) -> BidRecommendation:
    """Combine the internal evaluation and the market-risk prediction (thesis, Table 13)."""
    row, critical = _internal_row(evaluation)
    label, text = DECISION_MATRIX[(row, market.low_competition)]
    reasons = [
        f"Internal evaluation: {evaluation.risk_level} (score {evaluation.efficiency_score}).",
        f"Market risk: probability of at most two bids {market.probability_low_competition:.0%} "
        f"({'likely low' if market.low_competition else 'likely strong'} competition, "
        f"threshold {market.threshold:.2f}).",
    ]
    if critical:
        reasons.append("A critical internal issue (deadline before material readiness or margin below 5%) "
                       "takes precedence over the market-risk prediction.")
    return BidRecommendation(label=label, recommendation=text, internal_risk=row,
                             low_competition=market.low_competition, critical_override=critical,
                             reasons=tuple(reasons))
