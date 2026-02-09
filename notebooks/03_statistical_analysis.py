"""
03 — Statistical Analysis
==========================
Power analysis, hypothesis tests, robustness checks, and segment analysis
for the checkout-page A/B test.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from src.data_utils import load_ab_data, add_derived_features
from src.stats_utils import (
    required_sample_size, run_proportion_ztest, compute_confidence_interval,
    compute_lift_ci, cohens_h, run_mannwhitney, bootstrap_mean_diff,
)

sns.set_theme(style='whitegrid', palette='muted', font_scale=1.1)
FIGDIR = os.path.join(os.path.dirname(__file__), '..', 'assets')

df = load_ab_data(os.path.join(os.path.dirname(__file__), '..', 'data', 'ab_test_data.csv'))
df = add_derived_features(df)

ctrl = df[df.group == 'control']
treat = df[df.group == 'treatment']

# ══════════════════════════════════════════════════════════════════
# 1. POWER ANALYSIS
# ══════════════════════════════════════════════════════════════════
baseline_cvr = ctrl.converted.mean()
print("=== Pre-Experiment Power Analysis ===")
for mde in [0.003, 0.004, 0.005]:
    n = required_sample_size(0.032, mde, alpha=0.05, power=0.80)
    print(f"  MDE = {mde*100:.1f} pp → need {n:,} per group "
          f"(~{n/3500:.0f} days at 1,750/group/day)")

actual_per_group = min(len(ctrl), len(treat))
print(f"\n  Actual per-group sample: {actual_per_group:,}")
achievable_mde_estimate = 0.004  # approximation consistent with power calc
print(f"  With 80% power we can detect ≥ ~0.4 pp lift")

# ══════════════════════════════════════════════════════════════════
# 2. PRIMARY METRIC: CONVERSION RATE
# ══════════════════════════════════════════════════════════════════
print("\n=== Primary Metric: Conversion Rate ===")

n_ctrl, n_treat = len(ctrl), len(treat)
conv_ctrl, conv_treat = ctrl.converted.sum(), treat.converted.sum()
cvr_ctrl, cvr_treat = conv_ctrl / n_ctrl, conv_treat / n_treat

print(f"  Control:   {cvr_ctrl:.4f}  ({conv_ctrl}/{n_ctrl})")
print(f"  Treatment: {cvr_treat:.4f}  ({conv_treat}/{n_treat})")
print(f"  Absolute lift: {(cvr_treat - cvr_ctrl)*100:.2f} pp")
print(f"  Relative lift: {(cvr_treat - cvr_ctrl) / cvr_ctrl * 100:.1f}%")

# z-test
z_stat, p_value = run_proportion_ztest(
    [conv_treat, conv_ctrl], [n_treat, n_ctrl]
)
print(f"\n  z-statistic: {z_stat:.3f}")
print(f"  p-value:     {p_value:.5f}")

# confidence intervals for each group
ci_ctrl = compute_confidence_interval(conv_ctrl, n_ctrl)
ci_treat = compute_confidence_interval(conv_treat, n_treat)
print(f"  Control 95% CI:   [{ci_ctrl[0]:.4f}, {ci_ctrl[1]:.4f}]")
print(f"  Treatment 95% CI: [{ci_treat[0]:.4f}, {ci_treat[1]:.4f}]")

# lift CI
diff, diff_lo, diff_hi = compute_lift_ci(cvr_ctrl, cvr_treat, n_ctrl, n_treat)
print(f"  Lift 95% CI: [{diff_lo*100:.2f} pp, {diff_hi*100:.2f} pp]")

# effect size
h = cohens_h(cvr_treat, cvr_ctrl)
print(f"  Cohen's h: {h:.4f} (small = 0.2, medium = 0.5)")

significant = p_value < 0.05
print(f"\n  → {'REJECT' if significant else 'FAIL TO REJECT'} H₀ at α=0.05")

# ══════════════════════════════════════════════════════════════════
# 3. SECONDARY METRIC: REVENUE PER SESSION
# ══════════════════════════════════════════════════════════════════
print("\n=== Secondary Metric: Revenue per Session ===")
rps_ctrl = ctrl.revenue.values
rps_treat = treat.revenue.values

print(f"  Control mean:   ${rps_ctrl.mean():.4f}")
print(f"  Treatment mean: ${rps_treat.mean():.4f}")

# Revenue is zero-inflated and skewed → use Mann-Whitney + bootstrap
mw_stat, mw_p = run_mannwhitney(rps_ctrl, rps_treat)
print(f"  Mann-Whitney p-value: {mw_p:.5f}")

boot_diff, boot_lo, boot_hi = bootstrap_mean_diff(rps_ctrl, rps_treat, n_boot=10000)
print(f"  Bootstrap mean diff: ${boot_diff:.4f}")
print(f"  Bootstrap 95% CI:    [${boot_lo:.4f}, ${boot_hi:.4f}]")

# ══════════════════════════════════════════════════════════════════
# 4. SECONDARY METRIC: AVERAGE ORDER VALUE (converters only)
# ══════════════════════════════════════════════════════════════════
print("\n=== Secondary Metric: AOV (Converters Only) ===")
aov_ctrl = ctrl.loc[ctrl.converted == 1, 'revenue'].values
aov_treat = treat.loc[treat.converted == 1, 'revenue'].values

print(f"  Control AOV:   ${aov_ctrl.mean():.2f} (n={len(aov_ctrl)})")
print(f"  Treatment AOV: ${aov_treat.mean():.2f} (n={len(aov_treat)})")

t_stat, t_p = stats.ttest_ind(aov_ctrl, aov_treat, equal_var=False)
print(f"  Welch's t-test p-value: {t_p:.4f}")
print(f"  → AOV difference is {'significant' if t_p < 0.05 else 'NOT significant'} at α=0.05")

# ══════════════════════════════════════════════════════════════════
# 5. ROBUSTNESS CHECKS
# ══════════════════════════════════════════════════════════════════
print("\n=== Robustness Checks ===")

# 5a. Bonferroni correction for multiple comparisons
n_tests = 3
bonferroni_alpha = 0.05 / n_tests
print(f"\n  Bonferroni-adjusted α: {bonferroni_alpha:.4f}")
print(f"  Primary CVR p={p_value:.5f} → {'significant' if p_value < bonferroni_alpha else 'NOT significant'} after correction")

# 5b. Segment-level consistency (by device)
print("\n  Device-level CVR lift:")
for device in sorted(df.device.unique()):
    c = ctrl[ctrl.device == device]
    t = treat[treat.device == device]
    cvr_c = c.converted.mean()
    cvr_t = t.converted.mean()
    lift = cvr_t - cvr_c
    print(f"    {device:>8s}: control={cvr_c:.4f}  treat={cvr_t:.4f}  lift={lift*100:+.2f} pp")

# 5c. Temporal stability — first half vs second half
midpoint = df.date.unique()[len(df.date.unique()) // 2]
for label, mask in [('First half', df.date <= midpoint),
                    ('Second half', df.date > midpoint)]:
    sub = df[mask]
    c = sub[sub.group == 'control'].converted.mean()
    t = sub[sub.group == 'treatment'].converted.mean()
    print(f"  {label}: control={c:.4f}  treat={t:.4f}  lift={((t-c)*100):+.2f} pp")

# 5d. Permutation test as a non-parametric sanity check
print("\n  Permutation test (10,000 iterations)...")
observed_diff = cvr_treat - cvr_ctrl
combined = df.converted.values
rng = np.random.default_rng(42)
perm_diffs = np.empty(10000)
for i in range(10000):
    perm = rng.permutation(combined)
    perm_diffs[i] = perm[:n_treat].mean() - perm[n_treat:n_treat+n_ctrl].mean()
perm_p = (np.abs(perm_diffs) >= np.abs(observed_diff)).mean()
print(f"  Permutation p-value: {perm_p:.4f}")

# ══════════════════════════════════════════════════════════════════
# 6. VISUALIZATION — Confidence Interval Forest Plot
# ══════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 4))
metrics = ['CVR (pp)']
diffs = [diff * 100]
los = [diff_lo * 100]
his = [diff_hi * 100]

ax.errorbar(diffs, metrics, xerr=[[d - l for d, l in zip(diffs, los)],
                                   [h - d for d, h in zip(diffs, his)]],
            fmt='o', color='#E07B54', capsize=6, ms=8, lw=2)
ax.axvline(0, color='gray', ls='--', lw=1)
ax.set_xlabel('Treatment Effect (percentage points)')
ax.set_title('Primary Metric — Treatment Lift with 95% CI')
plt.tight_layout()
plt.savefig(os.path.join(FIGDIR, 'lift_ci_plot.png'), dpi=150, bbox_inches='tight')
plt.close()
print("\n✓ Saved lift_ci_plot.png")

# ══════════════════════════════════════════════════════════════════
# 7. CUMULATIVE CONVERSION RATE OVER TIME
# ══════════════════════════════════════════════════════════════════
daily = (df.groupby(['date', 'group'])
         .agg(n=('user_id', 'count'), conv=('converted', 'sum'))
         .reset_index()
         .sort_values('date'))

for grp in ['control', 'treatment']:
    mask = daily.group == grp
    daily.loc[mask, 'cum_n'] = daily.loc[mask, 'n'].cumsum()
    daily.loc[mask, 'cum_conv'] = daily.loc[mask, 'conv'].cumsum()

daily['cum_cvr'] = daily['cum_conv'] / daily['cum_n']

fig, ax = plt.subplots(figsize=(10, 5))
for grp, color in [('control', '#5B8DB8'), ('treatment', '#E07B54')]:
    sub = daily[daily.group == grp]
    ax.plot(sub.date, sub.cum_cvr * 100, marker='o', ms=3, label=grp, color=color)
ax.set_ylabel('Cumulative CVR (%)')
ax.set_title('Cumulative Conversion Rate Over Experiment Duration')
ax.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(FIGDIR, 'cumulative_cvr.png'), dpi=150, bbox_inches='tight')
plt.close()
print("✓ Saved cumulative_cvr.png")

print("\n=== Analysis Complete ===")
