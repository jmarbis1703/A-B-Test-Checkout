"""Data loading and validation utilities."""

import pandas as pd
import numpy as np


def load_ab_data(path='data/ab_test_data.csv'):
    df = pd.read_csv(path, parse_dates=['timestamp'])
    return df


def validate_data(df):
    """Run basic data quality checks; returns a dict of results."""
    checks = {}
    checks['total_rows'] = len(df)
    checks['null_counts'] = df.isnull().sum().to_dict()
    checks['duplicate_user_ids'] = df['user_id'].duplicated().sum()
    checks['group_counts'] = df['group'].value_counts().to_dict()

    # Sample ratio mismatch (SRM) test — chi-squared
    observed = df['group'].value_counts().values
    expected = np.full_like(observed, observed.sum() / len(observed), dtype=float)
    from scipy.stats import chisquare
    chi2, srm_p = chisquare(observed, f_exp=expected)
    checks['srm_chi2'] = round(chi2, 4)
    checks['srm_p_value'] = round(srm_p, 4)
    checks['srm_flag'] = srm_p < 0.01

    return checks


def add_derived_features(df):
    """Add columns useful for analysis."""
    df = df.copy()
    df['date'] = df['timestamp'].dt.date
    df['day_of_week'] = df['timestamp'].dt.day_name()
    df['hour'] = df['timestamp'].dt.hour
    return df
