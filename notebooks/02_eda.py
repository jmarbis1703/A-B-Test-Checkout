"""Exploratory Data Analysis"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from src.data_utils import load_ab_data, validate_data, add_derived_features

sns.set_theme(style='whitegrid', palette='muted', font_scale=1.1)
FIGDIR = os.path.join(os.path.dirname(__file__), '..', 'assets')
os.makedirs(FIGDIR, exist_ok=True)

# Load
df = load_ab_data(os.path.join(os.path.dirname(__file__), '..', 'data', 'ab_test_data.csv'))
checks = validate_data(df)
for k, v in checks.items():
    print(f"  {k}: {v}")

df = add_derived_features(df)

# Group Balance
print("\n Group Sizes")
print(df['group'].value_counts())
print(f"\nSRM p-value: {checks['srm_p_value']}",
      "⚠ FLAGGED" if checks['srm_flag'] else "No issue")

# traffic and  conversion by day
daily = (df.groupby(['date', 'group'])
         .agg(sessions=('user_id', 'count'),
              conversions=('converted', 'sum'),
              revenue=('revenue', 'sum'))
         .reset_index())
daily['cvr'] = daily['conversions'] / daily['sessions']

fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

for grp, color in [('control', '#5B8DB8'), ('treatment', '#E07B54')]:
    subset = daily[daily.group == grp]
    axes[0].plot(subset.date, subset.sessions, marker='o', ms=4, label=grp, color=color)
    axes[1].plot(subset.date, subset.cvr * 100, marker='o', ms=4, label=grp, color=color)

axes[0].set_ylabel('Daily Sessions')
axes[0].set_title('Daily Traffic by Group')
axes[0].legend()
axes[1].set_ylabel('Conversion Rate (%)')
axes[1].set_title('Daily Conversion Rate by Group')
axes[1].legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(FIGDIR, 'daily_traffic_cvr.png'), dpi=150, bbox_inches='tight')
plt.close()
print("Saved daily_traffic_cvr.png")

# By device
device_stats = (df.groupby(['group', 'device'])
                .agg(n=('user_id', 'count'), conversions=('converted', 'sum'))
                .reset_index())
device_stats['cvr'] = device_stats['conversions'] / device_stats['n']

fig, ax = plt.subplots(figsize=(8, 5))
width = 0.35
devices = sorted(df.device.unique())
x = np.arange(len(devices))
for i, grp in enumerate(['control', 'treatment']):
    vals = device_stats[device_stats.group == grp].set_index('device').reindex(devices)['cvr'] * 100
    ax.bar(x + i * width, vals, width, label=grp,
           color=['#5B8DB8', '#E07B54'][i])
ax.set_xticks(x + width / 2)
ax.set_xticklabels(devices)
ax.set_ylabel('Conversion Rate (%)')
ax.set_title('Conversion Rate by Device & Group')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(FIGDIR, 'cvr_by_device.png'), dpi=150, bbox_inches='tight')
plt.close()
print("Saved cvr_by_device.png")

# Revenue distribution only converters
converters = df[df.converted == 1]

fig, ax = plt.subplots(figsize=(8, 5))
for grp, color in [('control', '#5B8DB8'), ('treatment', '#E07B54')]:
    subset = converters[converters.group == grp]['revenue']
    ax.hist(subset, bins=40, alpha=0.55, label=f'{grp} (n={len(subset)})', color=color)
ax.set_xlabel('Revenue (USD)')
ax.set_ylabel('Count')
ax.set_title('Revenue Distribution — Converters Only')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(FIGDIR, 'revenue_distribution.png'), dpi=150, bbox_inches='tight')
plt.close()
print("Saved revenue_distribution.png")

#Traffic source mix─
source_mix = (df.groupby(['group', 'traffic_source'])
              .size().unstack(fill_value=0))
source_pct = source_mix.div(source_mix.sum(axis=1), axis=0) * 100
print("\nTraffic Source Mix (%)")
print(source_pct.round(2))

# Sessions by group
print("\nSession Metrics by Group")
summary = (df.groupby('group')
           .agg(
               sessions=('user_id', 'count'),
               cvr=('converted', 'mean'),
               avg_pages=('pages_viewed', 'mean'),
               avg_duration=('session_duration_sec', 'mean'),
               total_revenue=('revenue', 'sum'),
           ))
summary['rev_per_session'] = summary['total_revenue'] / summary['sessions']
print(summary.round(4))

# CVR check first vs last 
df['week'] = pd.to_datetime(df['date']).dt.isocalendar().week.astype(int)
weeks = sorted(df['week'].unique())
first_week, last_week = weeks[0], weeks[-1]

novelty = (df[df.week.isin([first_week, last_week])]
           .groupby(['group', 'week'])
           .agg(n=('user_id', 'count'), conv=('converted', 'sum'))
           .reset_index())
novelty['cvr'] = novelty['conv'] / novelty['n']
print("\ Novelty Check: Week 1 vs Week 3 CVR")
print(novelty[['group', 'week', 'n', 'cvr']].to_string(index=False))

print("\nEDA complete.  See assets/ for plots.")
