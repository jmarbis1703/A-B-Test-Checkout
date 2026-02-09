"""
04 — Business Recommendations & Impact Sizing
===============================================
Translates statistical results into executive-ready business insights
and quantifies expected financial impact.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from src.data_utils import load_ab_data

df = load_ab_data(os.path.join(os.path.dirname(__file__), '..', 'data', 'ab_test_data.csv'))
FIGDIR = os.path.join(os.path.dirname(__file__), '..', 'assets')

# ── Core experiment results ───────────────────────────────────────
ctrl = df[df.group == 'control']
treat = df[df.group == 'treatment']

cvr_ctrl = ctrl.converted.mean()
cvr_treat = treat.converted.mean()
abs_lift = cvr_treat - cvr_ctrl
rel_lift = abs_lift / cvr_ctrl

avg_daily_sessions = len(df) / df.timestamp.dt.date.nunique()
annual_sessions = avg_daily_sessions * 365

aov = df.loc[df.converted == 1, 'revenue'].mean()

# ── Impact projections ────────────────────────────────────────────
# Using the CI bounds from the analysis: [0.27 pp, 0.79 pp]
scenarios = {
    'Conservative (CI lower bound)': 0.0027,
    'Point estimate':                abs_lift,
    'Optimistic (CI upper bound)':   0.0079,
}

print("=" * 60)
print("BUSINESS IMPACT PROJECTION — Annual Basis")
print("=" * 60)
print(f"\nBaseline annual sessions: {annual_sessions:,.0f}")
print(f"Baseline CVR: {cvr_ctrl:.2%}")
print(f"Average order value: ${aov:.2f}")

print(f"\n{'Scenario':<35s} {'Extra Conv':>12s} {'Revenue Uplift':>15s}")
print("-" * 62)
for label, lift in scenarios.items():
    extra_conversions = annual_sessions * lift
    revenue_uplift = extra_conversions * aov
    print(f"{label:<35s} {extra_conversions:>12,.0f} {revenue_uplift:>14,.0f}$")

# the point estimate
extra_conv_annual = annual_sessions * abs_lift
rev_uplift_annual = extra_conv_annual * aov

print(f"\n{'─' * 60}")
print(f"EXPECTED ANNUAL REVENUE UPLIFT: ${rev_uplift_annual:,.0f}")
print(f"{'─' * 60}")

# ── Risk assessment ───────────────────────────────────────────────
print("\n=== Risk Assessment ===")
print("""
  ✓ Statistical significance:   p < 0.001 (well below α=0.05)
  ✓ Bonferroni-corrected:       Still significant
  ✓ Permutation test:           Confirms parametric result
  ✓ Temporal stability:         Lift consistent across weeks
  ⚠ Tablet segment:             Negative lift (n=~5K each, noisy)
  ⚠ Novelty effect:             Small fade observed but lift persists
  ✓ AOV unchanged:              Revenue gain comes from volume, not price
""")

# ── Decision framework ────────────────────────────────────────────
print("=== RECOMMENDATION ===")
print("""
  DECISION:  🟢  SHIP the new single-page checkout

  Rationale:
  1. Primary KPI (CVR) shows a statistically significant and
     practically meaningful +0.53 pp lift (16.7% relative).
  2. Revenue per session improves by ~$0.32 — a direct bottom-line gain.
  3. The effect is consistent across desktop and mobile (>87% of traffic).
  4. After accounting for a fading novelty bump, the treatment effect
     remains positive and stable in the final week of the experiment.
  5. No degradation in average order value — the checkout change
     increases conversion volume without cannibalising basket size.

  Caveats & Follow-up:
  - Monitor tablet conversion post-launch; the negative signal there
    may warrant a device-specific layout adjustment.
  - Plan a 2-week post-launch holdback (5% of traffic) to validate
    the lift persists without experimental observation effects.
  - Track the funnel-step drop-off in the new flow to identify
    further micro-optimisation opportunities.
""")

# ── Summary visual ────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 4.5))
labels = list(scenarios.keys())
rev_vals = [annual_sessions * lift * aov for lift in scenarios.values()]

colors = ['#5B8DB8', '#E07B54', '#5B8DB8']
bars = ax.barh(labels, rev_vals, color=colors, edgecolor='white', height=0.5)
ax.bar_label(bars, fmt='${:,.0f}', padding=5, fontsize=10)
ax.set_xlabel('Projected Annual Revenue Uplift (USD)')
ax.set_title('Checkout Redesign — Projected Annual Impact')
ax.xaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
plt.tight_layout()
plt.savefig(os.path.join(FIGDIR, 'revenue_impact.png'), dpi=150, bbox_inches='tight')
plt.close()
print("✓ Saved revenue_impact.png")
