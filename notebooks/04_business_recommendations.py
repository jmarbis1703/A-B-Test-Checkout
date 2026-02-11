"""
04 — Business Recommendations & Impact Sizing
=============================================
Purpose:
  Translates statistical results into a clear business case.
  1. Calculates current performance (Baseline).
  2. Projects annual revenue impact based on test results.
  3. Summarizes risks and gives a final Ship/No-Ship recommendation.
"""

import sys, os
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.data_utils import load_ab_data

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ab_test_data.csv')
ASSETS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets')

# Confidence Interval bounds from Step 03 (could be automated, but hardcoded for clarity here)
LIFT_SCENARIOS = {
    'Conservative (Lower Bound)': 0.0027,  # +0.27%
    'Expected (Point Estimate)':  None,    # Calculated dynamically below
    'Optimistic (Upper Bound)':   0.0079   # +0.79%
}

# ─── 1. LOAD & PREPARE DATA ───────────────────────────────────────────────────
df = load_ab_data(DATA_PATH)
control_group = df[df.group == 'control']
treatment_group = df[df.group == 'treatment']

# ─── 2. CALCULATE BASELINE METRICS ────────────────────────────────────────────
# Conversion Rate (CVR): What % of users buy?
baseline_cvr = control_group.converted.mean()
new_cvr = treatment_group.converted.mean()

# Uplift: The actual difference the new design made
actual_lift = new_cvr - baseline_cvr
LIFT_SCENARIOS['Expected (Point Estimate)'] = actual_lift

# Average Order Value (AOV): How much do buyers spend?
# We use the average of all converters to project revenue
average_order_value = df.loc[df.converted == 1, 'revenue'].mean()

# Traffic Projection: Estimate annual volume based on this sample
daily_sessions = len(df) / df.timestamp.dt.date.nunique()
annual_sessions = daily_sessions * 365

# ─── 3. FINANCIAL MODELING ────────────────────────────────────────────────────
print("=" * 60)
print("BUSINESS IMPACT PROJECTION — Annual Basis")
print("=" * 60)
print(f"\nKey Assumptions:")
print(f"  • Baseline Annual Traffic: {annual_sessions:,.0f} sessions")
print(f"  • Average Order Value:     ${average_order_value:.2f}")
print(f"  • Current Conversion Rate: {baseline_cvr:.2%}")

print(f"\n{'Scenario':<30} {'Extra Orders':>15} {'Revenue Uplift':>18}")
print("-" * 65)

# Calculate revenue impact for each scenario
projections = {}
for label, lift_pp in LIFT_SCENARIOS.items():
    # Formula: Sessions * Increase in CVR * Value per Order
    extra_orders = annual_sessions * lift_pp
    revenue_impact = extra_orders * average_order_value
    
    projections[label] = revenue_impact  # Store for plotting later
    
    print(f"{label:<30} {extra_orders:>15,.0f} {revenue_impact:>17,.0f}$")

print("-" * 65)
print(f"EXPECTED ANNUAL UPLIFT: ${projections['Expected (Point Estimate)']:,.0f}")
print("-" * 65)


# ─── 4. RISK ASSESSMENT ───────────────────────────────────────────────────────
print("\n=== Risk Assessment ===")
risks = [
    ("✓", "Statistical Significance", "p < 0.001 (High confidence)"),
    ("✓", "Temporal Stability",       "Lift was consistent across all 3 weeks"),
    ("✓", "Average Order Value",      "No negative impact on basket size"),
    ("⚠", "Tablet Segment",           "Showed negative lift (small sample size)"),
    ("⚠", "Novelty Effect",           "Initial spike faded, but lift remained positive")
]

for icon, area, note in risks:
    print(f"  {icon} {area:<25} : {note}")


# ─── 5. FINAL RECOMMENDATION ──────────────────────────────────────────────────
print("\n=== RECOMMENDATION ===")
print("DECISION: 🟢 SHIP the new single-page checkout\n")

rationale = [
    "Primary Goal Met: +0.53% lift in conversion rate (16.7% relative improvement).",
    "Financial Impact: Direct revenue gain of ~$0.32 per session.",
    "User Consistency: Positive effect on Desktop and Mobile (>87% of traffic).",
    "Safe Change: Increased orders without lowering average order value."
]

print("Rationale:")
for i, point in enumerate(rationale, 1):
    print(f"  {i}. {point}")

print("\nNext Steps:")
print("  1. Roll out to 100% traffic immediately.")
print("  2. Keep a 5% holdback group for 2 weeks to validate long-term lift.")
print("  3. Investigate Tablet specific UX issues.")


# ─── 6. VISUALIZATION ─────────────────────────────────────────────────────────
# Create a horizontal bar chart to show the range of outcomes
fig, ax = plt.subplots(figsize=(8, 4.5))

labels = list(projections.keys())
values = list(projections.values())
colors = ['#5B8DB8', '#E07B54', '#5B8DB8'] # Highlight the expected value in orange

bars = ax.barh(labels, values, color=colors, edgecolor='white', height=0.6)

# Format the chart to look professional
ax.bar_label(bars, fmt='${:,.0f}', padding=5, fontsize=10)
ax.set_xlabel('Projected Annual Revenue Uplift (USD)')
ax.set_title('Checkout Redesign — Projected Annual Impact')
ax.xaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))

# Remove clutter
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig(os.path.join(ASSETS_DIR, 'revenue_impact.png'), dpi=150, bbox_inches='tight')
plt.close()

print("\n✓ Saved chart to assets/revenue_impact.png")
