# Method alignment note for the diploma

## 1. What the prototype evaluates

The prototype calculates a weighted efficiency score from five components:

| Component | Weight |
|---|---:|
| Financial | 30% |
| Technical | 25% |
| Schedule | 25% |
| Environment | 10% |
| Historical similarity | 10% |

The final rule-based risk band is:

- 75–100: Low risk / high efficiency;
- 55–74.9: Medium risk / acceptable with checks;
- below 55: High risk / revise before tender.

## 2. Security requirements

PAS 24, RC2/RC3 and access control are now inputs of the same rule-based system,
not variables added only to the ML dataset. PAS 24 is independent from RC2/RC3,
so a project can require both PAS 24 and RC3. The assumptions are:

| Requirement | Technical deduction | Preparation addition | Generated control |
|---|---:|---:|---|
| PAS 24 | 5 | 0.5 week | Check that the full configuration is covered by evidence |
| RC2 | 10 | 1.0 week | Verify tested-system classification |
| RC3 | 20 | 2.0 weeks | Specialist review and classification evidence |
| Access control | 8 | 1.0 week | Check interfaces, power, fire strategy and commissioning |

The deductions are cumulative and enter the weighted result through the
technical component. The additions enter the calculated readiness date.
Security does not automatically set the final risk class; it changes the score
and creates alerts/checklist actions. This avoids claiming that every RC3
project is automatically commercially unviable.

## 3. Which data source is used where

The two datasets must be described separately:

1. `historical_projects.csv` has eight historical reference cases. It is used
   only to calculate the 10% similarity component in the interactive prototype.
2. `Combined_Projects_Dataset_100...` has 100 research observations (90
   synthetic development cases and 10 real external cases in the current
   experiment). It is used only for the proof-of-concept ML comparison.

The 100-row dataset must not be renamed to `historical_projects.csv` or loaded
directly by the prototype because it does not have the same schema. Conversely,
the eight similarity cases must not be presented as the ML training sample.

## 4. Required wording about PAS 24 and RC3 values

Where project certificates were not available, status values must be described
as **research-scenario assumptions used for modelling, not verified
certification records**. The application likewise tells the user that evidence
has to be checked against the project specification.

## 5. Reproducibility statement

The source code, pricing matrix, historical reference cases and automated tests
are packaged together. The security-rule test verifies the exact deductions,
timeline additions, combined `PAS 24 + RC3 + Access control` case, generated
actions and rejection of unsupported resistance classes.

## 6. Limitation that should remain in the thesis

The rule coefficients are expert/research assumptions and require calibration
on a larger set of verified completed projects. The current ML results are a
proof of concept and should not be described as evidence of production-level
generalisation because the external test contains only ten real projects.
