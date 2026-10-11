# Construction Project Efficiency Estimator

Python + Streamlit prototype for the master's thesis *Application of AI and Machine Learning for Project
Profitability and Risk Evaluation* (VILNIUS TECH). It supports pre-contract evaluation of façade, window and
door projects with two components:

- **Internal project evaluation (rule-based):** margin, schedule feasibility, technical and environmental
  requirements, PAS 24 / RC2 / RC3 / access control, similarity to reference scenarios, weighted efficiency
  score, alerts, checklist and PDF report. Rules are used because company project outcomes are confidential,
  so no outcome data are available to train or validate a model.
- **Market risk (machine learning):** probability that a construction tender receives at most two bids,
  predicted from the tender notice by Logistic Regression on tabular and text features, trained on
  5,735 UK public construction tenders (Find a Tender Service, 2021–2026; ROC AUC 0.83 in nested
  cross-validation, 0.80 on 2025–2026).
- **Bid recommendation:** both results are combined in a decision matrix (thesis, Table 13). Critical internal
  issues (requested deadline before material readiness, margin below 5 %) always take precedence.

## Project structure

```text
app.py                         Streamlit application
train_market_model.py          retrains the market-risk model from the Find a Tender Excel files
requirements.txt
data/
  historical_projects.csv      eight reference scenarios for the similarity component
  pricing_matrix.csv           indicative pricing and fabrication-time data
src/project_evaluator/
  evaluator.py                 rule-based internal evaluation
  pricing.py                   pricing matrix and cost estimation
  market_risk.py               market-risk prediction and decision matrix
  market_risk_ui.py            Streamlit section for the market risk
  market_risk_model.joblib     trained market-risk model
  models.py                    data classes
tests/                         unit tests (22)
.github/workflows/tests.yml    runs the tests on every push
```

## Run the prototype

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\activate     Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Tests

```bash
python -m pip install pytest
python -m pytest -q
```

## Research experiments

The experiments of the thesis (Chapter 3) are in a separate Jupyter notebook supplied with the thesis
(`01_Thesis_Experiments.ipynb`). They use the public UK Find a Tender Service data in OCDS format
(Open Government Licence v3.0), available from https://data.open-contracting.org.

To retrain the market-risk model, place `united_kingdom_fts_2021.xlsx` … `united_kingdom_fts_2026.xlsx`
next to `train_market_model.py`, run `python train_market_model.py` and copy `market_risk_model.joblib`
into `src/project_evaluator/`.

## Previous version

The previous version of the prototype (with `ml/` and `THESIS_METHOD_NOTE.md`) is kept unchanged in the
`old_version/` folder. Run it with:

```bash
python -m streamlit run old_version/app.py
```
