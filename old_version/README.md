# Construction Project Efficiency Estimator

Python + Streamlit prototype for a master's thesis on pre-contract construction project efficiency and risk evaluation using AI-supported decision support.

The project combines:

- a transparent rule-based evaluation engine;
- weighted efficiency scoring;
- Case-Based Reasoning using eight reference scenarios;
- a supervised machine-learning comparison;
- the selected Logistic Regression model as an ML second opinion in Streamlit;
- agreement/disagreement handling between rule-based and ML outputs;
- pricing, schedule, alerts, checklists, and PDF reporting.

## Project structure

```text
app.py
requirements.txt
README.md
THESIS_METHOD_NOTE.md

data/
  Combined_Projects_Dataset_100_enriched_v2.xlsx
  historical_projects.csv
  pricing_matrix.csv

ml/
  model_config.py
  train_ml.py
  evaluate_ml.py

src/
  project_evaluator/

tests/

.github/workflows/
  ml-evaluation.yml
```

## Run the Streamlit prototype

```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Run the ML experiment without Google Colab

Google Colab is no longer required to reproduce the thesis ML experiment.

Run the full 11-configuration comparison:

```bash
python ml/evaluate_ml.py --output-dir ml_results
```

This reproduces:

- 100 modelled project scenarios;
- 17 selected ML features;
- stratified 80/20 train/test split;
- random_state = 42;
- stratified 5-fold cross-validation on the 80-record training subset;
- 11 model configurations;
- held-out comparison of Rule-based, Random Forest, Decision Tree, and Logistic Regression;
- class-level recall;
- descriptive full-dataset rule-based result.

Run only the thesis-selected Logistic Regression model:

```bash
python ml/train_ml.py
```

The selected configuration is:

```text
Logistic Regression
C = 10
max_iter = 5000
random_state = 42
```

The final held-out thesis results are expected to reproduce the same experiment reported in the thesis when the same dataset and dependency versions are used.

## GitHub Actions

The repository includes:

```text
.github/workflows/ml-evaluation.yml
```

The workflow runs the ML evaluation automatically when files under `ml/`, the research dataset, or `requirements.txt` change. It also supports manual execution from the GitHub Actions tab.

The workflow uploads the generated CSV result tables as the artifact:

```text
ml-thesis-results
```

## ML features

The supervised ML component uses 17 pre-contract features.

Numeric:
- Num_Construction_Types
- Total_Value_GBP
- Fabrication_Hours

Categorical:
- Technical_Complexity
- Profile_Type
- Wind_Exposure
- Region
- RC2_Status
- RC3_Status
- PAS24_Status

Binary:
- Has_Windows
- Has_External_Doors
- Has_Sliding_Doors
- Has_Folding_Doors
- Has_Curtain_Wall
- Has_High_Insulation
- Has_Access_Control

Target:

```text
Expert_Risk_Assessment
```

## Data roles

- `data/Combined_Projects_Dataset_100_enriched_v2.xlsx`: 100 modelled expert-labelled scenarios for the ML comparison.
- `data/historical_projects.csv`: eight reference scenarios used by the Case-Based Reasoning / similarity component.
- `data/pricing_matrix.csv`: indicative pricing and fabrication-time data used by the prototype.

The 100-row ML dataset and the eight-case reference set have different purposes and must not be treated as the same dataset.

## Final prototype logic

The operational Streamlit prototype combines:

```text
Project input
   |
   +--> Rule-based evaluation
   |
   +--> Logistic Regression prediction
   |
   +--> Reference-scenario similarity
            |
            v
Agreement / disagreement check
            |
            v
Decision-support output
```

The ML result is a second opinion and does not automatically override mandatory rule-based checks.

Displayed ML confidence is a model probability within the scenario-based classifier. It must not be interpreted as a calibrated real-world probability of project success or failure.

## Tests

```bash
python -m unittest discover -s tests -v
```

See `THESIS_METHOD_NOTE.md` for the research-method alignment and limitations.
