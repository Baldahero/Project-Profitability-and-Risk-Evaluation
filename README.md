# Construction Project Efficiency Estimator

Python and Streamlit prototype for the master thesis topic: pre-contract construction project efficiency evaluation using transparent AI-supported decision logic.

The prototype focuses on facade, door, and window installation projects. It combines:

- rule-based checks for margin, technical complexity, schedule feasibility, wind exposure, environmental conditions, PAS 24, RC2/RC3 and access control;
- weighted scoring for an overall efficiency and risk level;
- similarity-based comparison with historical projects;
- material lead time and production readiness date estimation;
- alerts and a project-specific engineering checklist.

## Project Structure

```text
app.py                         Streamlit interface
data/historical_projects.csv   Example historical similarity cases
data/pricing_matrix.csv        Price matrix extracted from the Excel example
src/project_evaluator/         Evaluation and similarity logic
tests/test_evaluator.py        Existing core logic tests
tests/test_security_rules.py   Security-rule regression tests
THESIS_METHOD_NOTE.md          Exact data roles, assumptions and limitations
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
python3 -m unittest discover -s tests -v
```

Windows:

```powershell
python -m unittest discover -s tests -v
```

## Security Rule Assumptions

PAS 24 and the burglary-resistance class are separate inputs because a project may require both PAS 24 and RC2/RC3.

| Input | Technical-score deduction | Extra preparation time |
|---|---:|---:|
| PAS 24 | 5 points | 0.5 week |
| RC2 | 10 points | 1.0 week |
| RC3 | 20 points | 2.0 weeks |
| Access control / electric locking | 8 points | 1.0 week |

The effects are cumulative. These values are transparent research assumptions, not certification records. Project evidence must be checked before tender approval.

## Data Roles

- `data/pricing_matrix.csv` supplies element prices and fabrication times.
- `data/historical_projects.csv` contains eight illustrative reference cases used only for the historical-similarity component (10% of the rule-based score).
- The separate 100-project research dataset is used for the ML proof-of-concept comparison. It must not replace `historical_projects.csv` because its schema and purpose are different.

## Notes For Thesis Use

The system is intentionally explainable. Each output is derived from visible rules and weights, which matches the thesis focus on managerial decision support rather than black-box prediction.

The pricing matrix was extracted from the provided Excel example. The application uses it to calculate material, glass, labour, coating, margin, and final price in GBP before running the financial risk evaluation.

See `THESIS_METHOD_NOTE.md` for the exact model description, data separation and limitations.
