"""
01 — Generate Synthetic A/B Test Data
======================================
Simulates a 21-day checkout-page redesign experiment for a mid-size
e-commerce retailer (~3,500 sessions/day).

Treatment: A simplified, single-page checkout replacing the legacy
multi-step flow. We embed realistic patterns: day-of-week seasonality,
device-mix effects, a small novelty bump that fades, and a genuine
(but modest) treatment lift in conversion rate.

All random seeds are fixed for reproducibility.
"""

import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
RNG = np.random.default_rng(SEED)

# ── Experiment parameters ──────────────────────────────────────────
N_DAYS = 21
SESSIONS_PER_DAY_MEAN = 3500
START_DATE = pd.Timestamp('2024-09-02')  # Monday

BASELINE_CVR = 0.032          # 3.2% control conversion rate
TRUE_TREATMENT_LIFT = 0.004   # +0.4 pp → 3.6% treatment CVR (~12.5% relative lift)
BASELINE_AOV_MEAN = 68.0      # average order value, USD
BASELINE_AOV_STD = 32.0

# Device mix probabilities and their conversion multipliers
DEVICE_PROBS = {'desktop': 0.42, 'mobile': 0.45, 'tablet': 0.13}
DEVICE_CVR_MULT = {'desktop': 1.15, 'mobile': 0.82, 'tablet': 1.05}
DEVICE_AOV_MULT = {'desktop': 1.10, 'mobile': 0.88, 'tablet': 1.02}

# Traffic source mix
SOURCE_PROBS = {'organic': 0.35, 'paid_search': 0.28, 'social': 0.18,
                'email': 0.12, 'direct': 0.07}

# Day-of-week seasonality (Mon=0 … Sun=6)
DOW_TRAFFIC_MULT = [1.0, 0.97, 0.95, 1.02, 1.08, 1.15, 1.05]
DOW_CVR_MULT     = [1.0, 1.01, 1.00, 0.99, 1.03, 0.96, 0.94]

# Novelty effect: small bump in treatment CVR that decays exponentially
NOVELTY_PEAK = 0.003   # extra 0.3 pp on day 1
NOVELTY_HALFLIFE = 4    # days


def _novelty_effect(day_index):
    return NOVELTY_PEAK * np.exp(-np.log(2) * day_index / NOVELTY_HALFLIFE)


def generate_dataset():
    records = []
    user_counter = 0

    for day_idx in range(N_DAYS):
        date = START_DATE + pd.Timedelta(days=day_idx)
        dow = date.dayofweek

        n_sessions = int(RNG.poisson(SESSIONS_PER_DAY_MEAN * DOW_TRAFFIC_MULT[dow]))

        # assign groups (50/50 randomisation at the user level)
        groups = RNG.choice(['control', 'treatment'], size=n_sessions)
        devices = RNG.choice(list(DEVICE_PROBS.keys()), size=n_sessions,
                             p=list(DEVICE_PROBS.values()))
        sources = RNG.choice(list(SOURCE_PROBS.keys()), size=n_sessions,
                             p=list(SOURCE_PROBS.values()))

        # timestamps spread across the day with realistic hourly distribution
        hour_weights = np.array([
            1, 0.5, 0.3, 0.2, 0.2, 0.3,   # 00-05
            0.8, 1.5, 2.5, 3.5, 4.0, 4.5,  # 06-11
            4.0, 3.8, 3.5, 3.2, 3.5, 4.0,  # 12-17
            4.5, 4.8, 5.0, 4.5, 3.0, 2.0,  # 18-23
        ])
        hour_weights /= hour_weights.sum()
        hours = RNG.choice(24, size=n_sessions, p=hour_weights)
        minutes = RNG.integers(0, 60, size=n_sessions)
        seconds = RNG.integers(0, 60, size=n_sessions)

        timestamps = [
            date + pd.Timedelta(hours=int(h), minutes=int(m), seconds=int(s))
            for h, m, s in zip(hours, minutes, seconds)
        ]

        for i in range(n_sessions):
            user_counter += 1
            group = groups[i]
            device = devices[i]
            source = sources[i]

            # build conversion probability
            cvr = BASELINE_CVR * DOW_CVR_MULT[dow] * DEVICE_CVR_MULT[device]
            if group == 'treatment':
                cvr += TRUE_TREATMENT_LIFT
                cvr += _novelty_effect(day_idx)

            converted = int(RNG.random() < cvr)

            # revenue: log-normal-ish with device adjustment
            revenue = 0.0
            if converted:
                aov = RNG.normal(BASELINE_AOV_MEAN * DEVICE_AOV_MULT[device],
                                 BASELINE_AOV_STD)
                revenue = round(max(aov, 5.0), 2)  # floor at $5

            # pages viewed (higher for non-converters who bounce)
            if converted:
                pages = int(RNG.poisson(5.5)) + 1
            else:
                pages = int(RNG.poisson(2.8)) + 1

            # session duration in seconds
            if converted:
                duration = int(RNG.exponential(320)) + 30
            else:
                duration = int(RNG.exponential(90)) + 5

            records.append({
                'user_id': f'U{user_counter:07d}',
                'timestamp': timestamps[i],
                'group': group,
                'device': device,
                'traffic_source': source,
                'pages_viewed': pages,
                'session_duration_sec': duration,
                'converted': converted,
                'revenue': revenue,
            })

    df = pd.DataFrame(records)
    df = df.sort_values('timestamp').reset_index(drop=True)
    return df


if __name__ == '__main__':
    out_dir = Path('data')
    out_dir.mkdir(exist_ok=True)

    df = generate_dataset()
    df.to_csv(out_dir / 'ab_test_data.csv', index=False)
    print(f"Generated {len(df):,} rows → data/ab_test_data.csv")
    print(f"  Control: {(df.group=='control').sum():,}")
    print(f"  Treatment: {(df.group=='treatment').sum():,}")
    print(f"  Overall CVR: {df.converted.mean():.4f}")
    print(f"  Control CVR: {df.loc[df.group=='control','converted'].mean():.4f}")
    print(f"  Treatment CVR: {df.loc[df.group=='treatment','converted'].mean():.4f}")
