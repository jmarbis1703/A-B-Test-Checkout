"""Statistical utilities for A/B test analysis."""

import numpy as np
from scipy import stats
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportions_ztest, proportion_confint


def required_sample_size(baseline_rate, mde, alpha=0.05, power=0.80):
    """Calculate per-group sample size for a two-proportion z-test."""
    effect_size = mde / np.sqrt(baseline_rate * (1 - baseline_rate))
    analysis = NormalIndPower()
    n = analysis.solve_power(effect_size=effect_size, alpha=alpha, power=power,
                             ratio=1.0, alternative='two-sided')
    return int(np.ceil(n))


def run_proportion_ztest(successes, nobs):
    """Two-sided z-test for two proportions. Returns z-stat, p-value."""
    z_stat, p_value = proportions_ztest(successes, nobs, alternative='two-sided')
    return z_stat, p_value


def compute_confidence_interval(count, nobs, alpha=0.05, method='wilson'):
    """Wilson confidence interval for a single proportion."""
    lo, hi = proportion_confint(count, nobs, alpha=alpha, method=method)
    return lo, hi


def compute_lift_ci(rate_control, rate_treatment, n_control, n_treatment, alpha=0.05):
    """Confidence interval for the absolute difference (treatment - control)."""
    diff = rate_treatment - rate_control
    se = np.sqrt(
        rate_control * (1 - rate_control) / n_control
        + rate_treatment * (1 - rate_treatment) / n_treatment
    )
    z = stats.norm.ppf(1 - alpha / 2)
    return diff, diff - z * se, diff + z * se


def cohens_h(p1, p2):
    """Cohen's h effect size for two proportions."""
    return 2 * (np.arcsin(np.sqrt(p1)) - np.arcsin(np.sqrt(p2)))


def run_mannwhitney(group_a, group_b):
    """Non-parametric test for continuous metrics (e.g., revenue per user)."""
    stat, p_value = stats.mannwhitneyu(group_a, group_b, alternative='two-sided')
    return stat, p_value


def bootstrap_mean_diff(group_a, group_b, n_boot=10000, ci=0.95, seed=42):
    """Bootstrap confidence interval for difference in means."""
    rng = np.random.default_rng(seed)
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        sample_a = rng.choice(group_a, size=len(group_a), replace=True)
        sample_b = rng.choice(group_b, size=len(group_b), replace=True)
        diffs[i] = sample_b.mean() - sample_a.mean()
    lo = np.percentile(diffs, (1 - ci) / 2 * 100)
    hi = np.percentile(diffs, (1 + ci) / 2 * 100)
    return diffs.mean(), lo, hi
