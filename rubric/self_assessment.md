# Self-Assessment Rubric

## Grading Scale

| Score | Meaning |
|---|---|
| 5 | Hiring-level excellence |
| 4 | Strong, minor gaps |
| 3 | Adequate but not impressive |
| 2 | Significant weaknesses |
| 1 | Unacceptable for hiring |

---

## Scores

| Category | Score | Justification |
|---|---|---|
| **Business Framing & Problem Clarity** | 5 | Clear, realistic business problem (checkout redesign). Hypotheses are explicit. Primary and secondary KPIs are defined with rationale. The "why this matters" is woven throughout. |
| **Experimental Design Rigor** | 4 | Power analysis, pre-committed duration, randomisation strategy, and risk inventory (SRM, novelty, peeking, multiple comparisons) are all addressed. Deducted 1 point: no formal pre-registration document or sequential testing boundary discussed. |
| **Statistical Correctness** | 5 | Appropriate test selection (z-test for proportions, Mann-Whitney and bootstrap for revenue). Assumptions validated. Bonferroni correction, permutation test, and segment-level consistency checks all included. Effect sizes reported alongside p-values. |
| **Analytical Depth** | 4 | EDA covers traffic balance, device/source mix, temporal trends, and novelty decay. Robustness checks are thorough. Deducted 1 point: could have included a logistic regression controlling for device and source as a covariate-adjusted estimate. |
| **Code Quality & Engineering Practices** | 4 | Modular structure with reusable `src/` utilities. Functions are well-scoped. Code is readable and avoids over-abstraction. Deducted 1 point: no unit tests for `stats_utils.py`; scripts could benefit from argparse for flexibility. |
| **Data Visualisation & Power BI Quality** | 4 | Analysis plots are clean and purposeful. Power BI spec includes data model, DAX measures, and a page-by-page layout. Deducted 1 point: no actual `.pbix` file committed (design doc only). |
| **Business Interpretation & Recommendations** | 5 | Clear ship/no-ship recommendation with quantified upside, downside, and uncertainty. Risk assessment is balanced. Follow-up actions are specific and actionable. |
| **Documentation & GitHub Readiness** | 5 | README covers context, methodology, results, impact, repo structure, and reproducibility. Executive summary is stakeholder-ready. All scripts run deterministically from a clean clone. |
| **Overall Hireability Signal** | 4 | This project demonstrates the analytical rigour, business acumen, and communication skills expected of a senior analyst or applied DS at a top consulting firm. The gap to a 5 is the absence of a working Power BI file and a few engineering refinements. |

---

## Hiring-Manager Verdict

> **Strong hire.** The candidate demonstrates end-to-end ownership of an experiment lifecycle: from framing a business question, through rigorous statistical analysis, to a clear and quantified recommendation. The code is clean and team-ready. The documentation reads like it was written for real stakeholders, not for a classroom. The candidate understands that the point of A/B testing is a *business decision*, not a p-value — and that comes through in every deliverable.

---

## Improvements Required to Reach a Perfect Score

1. **Commit a working `.pbix` file** with the data model and all three dashboard pages implemented. The design spec is solid; the deliverable needs to exist.

2. **Add covariate-adjusted analysis.** A logistic regression with device and traffic source as covariates would strengthen the causal claim and demonstrate deeper statistical fluency.

3. **Write unit tests for `stats_utils.py`.** Even a small `tests/test_stats_utils.py` with 5–6 assertions on known inputs would signal engineering discipline.

4. **Add CLI arguments** (`argparse`) to the analysis scripts so paths and parameters aren't hardcoded.

5. **Include a pre-analysis plan (PAP)** or experiment protocol document that would have been written *before* the experiment ran. This is standard practice at top experimentation teams and demonstrates process maturity.

6. **Add a sequential testing / always-valid confidence interval** discussion, even if not implemented. Acknowledging the peeking problem with a concrete alternative method would push experimental design rigour to a 5.

7. **Add a `.gitignore`** and a lightweight CI config (e.g., GitHub Actions to run the scripts on push) to show DevOps awareness.
