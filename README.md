# Construction Project Efficiency Estimator

Python and Streamlit prototype for the master thesis topic: pre-contract construction project efficiency evaluation using transparent AI-supported decision logic.

The prototype focuses on facade, door, and window installation projects. It combines:

- rule-based checks for margin, technical complexity, schedule feasibility, wind exposure, and environmental conditions;
- weighted scoring for an overall efficiency and risk level;
- similarity-based comparison with historical projects;
- material lead time and production readiness date estimation;
- alerts and a project-specific engineering checklist.

## Project Structure

```text
app.py                         Streamlit interface
data/historical_projects.csv   Example historical project cases
data/pricing_matrix.csv        Price matrix extracted from the Excel example
src/project_evaluator/         Evaluation and similarity logic
tests/test_evaluator.py        Core logic tests
requirements.txt               Runtime dependency list
```

## Run

Install Python 3.10 or newer first.

Kali Linux / Debian:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Test

Kali Linux / Debian:

```bash
source .venv/bin/activate
python3 -m unittest discover -s tests
```

Windows:

```powershell
python -m unittest discover -s tests
```

## Notes For Thesis Use

The system is intentionally explainable. Each output is derived from visible rules and weights, which matches the thesis focus on managerial decision support rather than black-box prediction.

The historical project CSV contains illustrative data only. It can be replaced with anonymized company project history using the same columns.

The pricing matrix was extracted from the provided Excel example. The application uses it to calculate material, glass, labour, coating, margin, and final price in GBP before running the financial risk evaluation.
