"""03 — Statistical Analysis"""
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

# laod and setup
sns.set_theme(style='whitegrid', palette='muted', font_scale=1.1)
FIGDIR = os.path.join(os.path.dirname(__file__), '..', 'assets')

df = load_ab_data(os.path.join(os.path.dirname(__file__), '..', 'data', 'ab_test_data.csv'))
df = add_derived_features(df)

ctrl = df[df.group == 'control']
treat = df[df.group == 'treatment']

# Power analysis
baseline_cvr = ctrl.converted.mean()
print("Pre Experiment Power Analysis")
for mde in [0.003, 0.004, 0.005]:
    n = required_sample_size(0.032, mde, alpha=0.05, power=0.80)
    print(f"To detect +{mde:.1%} lift:\n Need {n:,} per group (~{n/1750:.0f} days at 1,750/group/day)\n")

print(f"\n Actual per-group sample: {min(len(ctrl), len(treat)):,}\nWith 80% power we can detect ≥ 0.4 pp lift")


#Conversion Rate Analysis
stats_df = df.groupby('group')['converted'].agg(['count', 'sum', 'mean'])
n_ctrl, n_treat = stats_df.loc['control', 'count'], stats_df.loc['treatment', 'count']
conv_ctrl, conv_treat = stats_df.loc['control', 'sum'], stats_df.loc['treatment', 'sum']
cvr_ctrl, cvr_treat = stats_df.loc['control', 'mean'], stats_df.loc['treatment', 'mean']

print(f"  Control:   {cvr_ctrl:.4f}  ({conv_ctrl}/{n_ctrl})")
print(f"  Treatment: {cvr_treat:.4f}  ({conv_treat}/{n_treat})")
print(f"  Absolute lift: {(cvr_treat - cvr_ctrl)*100:.2f} pp")
print(f"  Relative lift: {(cvr_treat - cvr_ctrl) / cvr_ctrl * 100:.1f}%")

# z-test and p val
z_stat, p_value = run_proportion_ztest([conv_treat, conv_ctrl], [n_treat, n_ctrl])
print(f"\n  z-statistic: {z_stat:.3f}\n  p-value:{p_value:.5f}")

# confidence int per gorup
ci_ctrl = compute_confidence_interval(conv_ctrl, n_ctrl)
ci_treat = compute_confidence_interval(conv_treat, n_treat)
print(f"  Control 95% CI:   [{ci_ctrl[0]:.4f}, {ci_ctrl[1]:.4f}]")
print(f"  Treatment 95% CI: [{ci_treat[0]:.4f}, {ci_treat[1]:.4f}]")

diff, diff_lo, diff_hi = compute_lift_ci(cvr_ctrl, cvr_treat, n_ctrl, n_treat)
print(f"  Lift 95% CI: [{diff_lo*100:.2f} pp, {diff_hi*100:.2f} pp]")

h = cohens_h(cvr_treat, cvr_ctrl)
print(f"  Cohen's h: {h:.4f} (small = 0.2, medium = 0.5)")

print(f"\n  → {'REJECT' if p_value < 0.05 else 'FAIL TO REJECT'} H₀ at α=0.05")


# Revenue per Session analysis
print("\n=== Secondary Metric: Revenue per Session ===")
print(f"  Control mean:    ${ctrl.revenue.mean():.4f}")
print(f"  Treatment mean: ${treat.revenue.mean():.4f}")

# Mann-Whitney + bootstrap
mw_stat, mw_p = run_mannwhitney(ctrl.revenue, treat.revenue)
print(f"  Mann-Whitney p-value: {mw_p:.5f}")

boot_diff, boot_lo, boot_hi = bootstrap_mean_diff(ctrl.revenue.values, treat.revenue.values, n_boot=10000)
print(f"  Bootstrap mean diff: ${boot_diff:.4f}\n  Bootstrap 95% CI:    [${boot_lo:.4f}, ${boot_hi:.4f}]")


#AOV analysis
aov_ctrl = ctrl.loc[ctrl.converted == 1, 'revenue']
aov_treat = treat.loc[treat.converted == 1, 'revenue']

print(f"  Control AOV:   ${aov_ctrl.mean():.2f} (n={len(aov_ctrl)})")
print(f"  Treatment AOV: ${aov_treat.mean():.2f} (n={len(aov_treat)})")

t_stat, t_p = stats.ttest_ind(aov_ctrl, aov_treat, equal_var=False)
print(f" Welch's t-test p-value: {t_p:.4f}")
print(f" AOV difference is {'significant' if t_p < 0.05 else 'NOT significant'} at α=0.05")



#Robustness

#Bonferroni correction 
bonferroni_alpha = 0.05 / 3
print(f"\n  Bonferroni adjusted α: {bonferroni_alpha:.4f}")
print(f"  Primary CVR p={p_value:.5f} → {'significant' if p_value < bonferroni_alpha else 'NOT significant'} after correction")

# consistancy by device
dev_stats = df.groupby(['device', 'group'])['converted'].mean().unstack()
for dev, row in dev_stats.iterrows():
    lift = row['treatment'] - row['control']
    print(f" {dev:>8}: control={row['control']:.4f}  treat={row['treatment']:.4f}  lift={lift*100:+.2f} pp")

# time check
midpoint = df.date.unique()[len(df.date.unique()) // 2]
for label, sub in [('First half', df[df.date <= midpoint]), ('Second half', df[df.date > midpoint])]:
    c, t = sub.groupby('group')['converted'].mean()[['control', 'treatment']]
    print(f"  {label}: control={c:.4f}  treat={t:.4f}  lift={((t-c)*100):+.2f} pp")

# sanity check
observed_diff = cvr_treat - cvr_ctrl
pool = df.converted.values
perm_diffs = [np.random.permutation(pool)[:n_treat].mean() - np.random.permutation(pool)[n_treat:].mean() for _ in range(10000)]
perm_p = np.mean(np.abs(perm_diffs) >= np.abs(observed_diff))
print(f"  Permutation p-value: {perm_p:.4f}")


#Vizualisations
fig, ax = plt.subplots(figsize=(8, 4))
ax.errorbar([diff * 100], ['CVR (pp)'], xerr=[[diff * 100 - diff_lo * 100], [diff_hi * 100 - diff * 100]], 
            fmt='o', color='#E07B54', capsize=6, ms=8, lw=2)
ax.axvline(0, color='gray', ls='--', lw=1)
ax.set(xlabel='Treatment Effect (percentage points)', title='Primary Metric — Treatment Lift with 95% CI')
plt.tight_layout()
plt.savefig(os.path.join(FIGDIR, 'lift_ci_plot.png'), dpi=150, bbox_inches='tight')
plt.close()
print("\n Saved lift_ci_plot.png")


# Cumulative CR 
daily = df.groupby(['date', 'group']).agg(n=('user_id', 'count'), conv=('converted', 'sum')).reset_index().sort_values('date')
daily[['cum_n', 'cum_conv']] = daily.groupby('group')[['n', 'conv']].cumsum()
daily['cum_cvr'] = daily['cum_conv'] / daily['cum_n']

fig, ax = plt.subplots(figsize=(10, 5))
sns.lineplot(data=daily, x='date', y=daily['cum_cvr'] * 100, hue='group', palette={'control': '#5B8DB8', 'treatment': '#E07B54'}, marker='o', ax=ax)
ax.set(ylabel='Cumulative CVR (%)', title='Cumulative Conversion Rate Over Experiment Duration')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(FIGDIR, 'cumulative_cvr.png'), dpi=150, bbox_inches='tight')
plt.close()
print("Saved cumulative_cvr.png")

print("\n  Analysis Complete ")
