# Method alignment note for the diploma

## 1. Final research structure

The final thesis uses two distinct scenario-based datasets:

1. `historical_projects.csv` contains eight reference scenarios used only for Case-Based Reasoning / similarity retrieval.
2. `Combined_Projects_Dataset_100_enriched_v2.xlsx` contains 100 modelled expert-labelled project scenarios used for the supervised ML comparison.

The 100 scenarios are modelled because identifiable real company projects cannot be disclosed. Their structure, parameter ranges, technical characteristics, pricing logic, and business assumptions are based on real organisational data structures and domain practice.

## 2. Rule-based component

The rule-based score uses five weighted criteria:

| Component | Weight |
|---|---:|
| Financial viability | 30% |
| Technical readiness | 25% |
| Schedule feasibility | 25% |
| Environmental conditions | 10% |
| Reference similarity | 10% |

Risk bands:

- score >= 75: Low risk / high efficiency;
- 55 <= score < 75: Medium risk / acceptable with checks;
- score < 55: High risk / revise before tender.

These weights and thresholds are expert-informed research assumptions and are not claimed to be universally optimal.

## 3. Final ML experiment

The final supervised ML experiment uses:

- 100 modelled scenarios;
- 17 selected pre-contract features;
- target: `Expert_Risk_Assessment`;
- stratified 80/20 train/test split;
- `random_state = 42`;
- stratified 5-fold cross-validation inside the 80-record training subset;
- 11 model configurations across Random Forest, Decision Tree, and Logistic Regression.

The 20-record held-out subset is used once for final comparison.

The same preprocessing is fitted only inside the corresponding training fold / training subset:

- numeric: median imputation + StandardScaler;
- categorical: most-frequent imputation + OneHotEncoder(handle_unknown="ignore");
- binary: missing-value imputation.

## 4. Selected model

The selected ML configuration is Logistic Regression with `C = 10`.

It is selected using the combined evidence from held-out classification performance and cross-validation stability.

The final Streamlit prototype uses this Logistic Regression model as a second opinion beside the deterministic rule-based result.

## 5. Hybrid architecture

The operational prototype combines three mechanisms:

1. Rule-based evaluation for transparent mandatory checks, weighted scoring, alerts, schedule, and technical logic.
2. Logistic Regression for a data-driven risk-classification second opinion.
3. Case-Based Reasoning for retrieval of comparable reference scenarios.

If the rule-based and ML classes agree, the interface shows agreement.

If they disagree, the interface displays an assessment-disagreement warning and recommends additional professional review.

The ML classifier does not autonomously override the rule-based result.

## 6. Model confidence

The Logistic Regression classifier produces class probabilities.

The Streamlit UI displays the highest predicted class probability as **model confidence**.

This value is not a calibrated real-world probability of project risk. A value such as 99% means that the trained classifier strongly favours one class within the scenario-based model; it does not mean that the project has a 99% real-world probability of belonging to that class.

## 7. Security variables

PAS 24, RC2, RC3, and access control are included in the final 17-feature ML set where represented in the scenario dataset. They are also handled by deterministic rule-based logic in the prototype.

Scenario status values are modelling assumptions and must not be presented as verified project certification records.

## 8. Reproducibility

The ML experiment is reproducible directly from GitHub without Google Colab:

```bash
python ml/evaluate_ml.py --output-dir ml_results
```

The selected model can be reproduced with:

```bash
python ml/train_ml.py
```

GitHub Actions additionally runs the ML evaluation automatically through:

```text
.github/workflows/ml-evaluation.yml
```

## 9. Limitations

The current study remains a proof of concept because:

- the ML dataset contains 100 modelled scenarios rather than independently observed completed-project outcomes;
- the target is an expert risk assessment rather than a realised final project outcome;
- the held-out test set contains only 20 scenarios;
- the rule-based weights and thresholds are expert-informed;
- model probabilities are not independently calibrated;
- production deployment would require controlled model versioning, monitoring, validation data, and a retraining policy.
