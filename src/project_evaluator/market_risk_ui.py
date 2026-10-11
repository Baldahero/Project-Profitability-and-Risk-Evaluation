"""Streamlit section for the market-risk component and the bid recommendation (thesis, Section 4.2, Table 13).

Usage in app.py:
    market = get_market_assessment(result)     # before the header/PDF, returns (MarketRiskResult, BidRecommendation) or None
    ...
    render_market_risk_section(result, market) # form + results
"""
from __future__ import annotations

import streamlit as st

from .market_risk import DEFAULT_THRESHOLD, assess_market_risk, load_market_model, recommend_bid
from .models import BidRecommendation, EvaluationResult, MarketRiskResult, TenderInput

TENDER_KEY = "market_risk_tender"
THRESHOLD_KEY = "market_risk_threshold"

PROCEDURES = [
    "Open procedure",
    "Restricted procedure",
    "Below threshold - open competition",
    "Competitive flexible procedure",
    "Competitive procedure with negotiation",
    "Negotiated procedure with prior call for competition",
    "Competitive dialogue",
    "Award procedure without prior publication of a call for competition",
]


@st.cache_resource
def _model():
    return load_market_model()


def get_market_assessment(
    evaluation: EvaluationResult,
) -> tuple[MarketRiskResult, BidRecommendation] | None:
    """Score the tender stored in the session (if any) and combine it with the internal evaluation."""
    tender = st.session_state.get(TENDER_KEY)
    if tender is None:
        return None
    try:
        model = _model()
    except FileNotFoundError:
        return None
    market = assess_market_risk(tender, model=model,
                                threshold=st.session_state.get(THRESHOLD_KEY, DEFAULT_THRESHOLD))
    return market, recommend_bid(evaluation, market)


def render_market_risk_section(
    evaluation: EvaluationResult,
    assessment: tuple[MarketRiskResult, BidRecommendation] | None = None,
) -> None:
    st.markdown("#### Market risk of the tender and bid recommendation")
    st.caption("Probability that the tender receives at most two bids, predicted from the tender notice by a "
               "Logistic Regression model trained on 5,735 UK public construction tenders (2021–2026). "
               "The result is combined with the internal evaluation in the decision matrix.")

    stored: TenderInput | None = st.session_state.get(TENDER_KEY)
    with st.form("market_risk_form"):
        title = st.text_input("Tender title", value=stored.title if stored else "",
                              placeholder="e.g. Window and door replacement programme")
        description = st.text_area("Tender description", value=stored.description if stored else "", height=110)
        col1, col2 = st.columns(2)
        with col1:
            value = st.number_input("Estimated value (GBP, 0 = not published)", min_value=0.0, step=10000.0,
                                    value=float(stored.estimated_value_gbp or 0) if stored else 0.0)
            procedure = st.selectbox("Procedure", PROCEDURES,
                                     index=PROCEDURES.index(stored.procedure) if stored and stored.procedure in PROCEDURES else 0)
            cpv = st.text_input("CPV code", value=stored.cpv_code if stored else "45421100")
        with col2:
            buyer = st.text_input("Buyer name", value=stored.buyer_name if stored else "",
                                  placeholder="e.g. Leeds City Council")
            lots = st.number_input("Number of lots", min_value=1, max_value=50, value=stored.lots if stored else 1)
            framework = st.checkbox("Framework agreement", value=stored.framework_agreement if stored else False)
        threshold = st.slider("Decision threshold", 0.20, 0.70,
                              float(st.session_state.get(THRESHOLD_KEY, DEFAULT_THRESHOLD)), 0.05,
                              help="0.40 is recommended for screening tenders (thesis, Section 3.6).")
        submitted = st.form_submit_button("Assess market risk", use_container_width=True)

    if submitted:
        if not title.strip():
            st.warning("Enter at least the tender title.")
            return
        st.session_state[TENDER_KEY] = TenderInput(
            title=title, description=description, estimated_value_gbp=value or None, procedure=procedure,
            cpv_code=cpv, buyer_name=buyer, lots=int(lots), framework_agreement=framework)
        st.session_state[THRESHOLD_KEY] = threshold
        st.rerun()

    if assessment is None:
        if stored is not None:
            st.error("Market-risk model file not found (market_risk_model.joblib). "
                     "Train it with train_market_model.py and copy it into src/project_evaluator/.")
        else:
            st.info("Enter the tender information to obtain the market-risk prediction and the bid recommendation.")
        return

    market, rec = assessment
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Probability of at most two bids", f"{market.probability_low_competition:.0%}",
                  "likely low competition" if market.low_competition else "likely strong competition",
                  delta_color="normal" if market.low_competition else "inverse")
    with col2:
        st.metric("Internal evaluation", rec.internal_risk + " risk",
                  "critical issue" if rec.critical_override else None, delta_color="inverse")

    box = {"Priority tender": st.success, "Do not bid": st.error}.get(rec.label, st.warning)
    box(f"**Bid recommendation: {rec.label}.** {rec.recommendation}")
    for reason in rec.reasons:
        st.write("• " + reason)

    st.markdown("**Main factors of the market-risk prediction** (positive = fewer bidders expected)")
    st.dataframe([{"Factor": f, "Contribution": c} for f, c in market.top_factors],
                 use_container_width=True, hide_index=True)
    if st.button("Clear tender"):
        st.session_state.pop(TENDER_KEY, None)
        st.rerun()
