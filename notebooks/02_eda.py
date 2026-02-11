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
df = add_derived_features(df)
checks = validate_data(df)

# Group Balance
print(f"Group Split: {df['group'].value_counts().to_dict()}")
if checks['srm_p_value'] < 0.01:
    print(f"Potential SRM detected (p={checks['srm_p_value']:.4f})")
else:
    print(f"Groups are balanced (SRM p={checks['srm_p_value']:.3f})")

# traffic and  conversion by day
daily = (df.groupby(['date', 'group'])
         .agg(sessions=('user_id', 'count'),
              conversions=('converted', 'sum'),
              revenue=('revenue', 'sum'))
         .reset_index())
daily['cvr'] = daily['conversions'] / daily['sessions']

#Plotting
fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

# Plot 1
custom_palette = {'control': '#5B8DB8', 'treatment': '#E07B54'}
sns.lineplot(data=daily,  x='date',  y='sessions', hue='group', 
    palette=custom_palette, marker='o', ax=axes[0])
axes[0].set_title('Daily Traffic by Group')
axes[0].set_ylabel('Daily Sessions')
axes[0].legend(loc='upper right')

#Plot 2
sns.lineplot(data=daily, x='date', y=daily['cvr'] * 100, hue='group', 
    palette=custom_palette, marker='o', ax=axes[1])
axes[1].set_title('Daily Conversion Rate by Group')
axes[1].set_ylabel('Conversion Rate (%)')
axes[1].set_xlabel('Date')
axes[1].legend(loc='upper right')

plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(FIGDIR, 'daily_traffic_cvr.png'), dpi=150, bbox_inches='tight')
plt.close()

print("Saved daily_traffic_cvr.png")



# By device
device_metrics = (df.groupby(['device', 'group'])['converted']
                    .mean()
                    .reset_index())
device_metrics['cvr_percent'] = device_metrics['converted'] * 100

plt.figure(figsize=(8, 5))
sns.barplot(data=device_metrics, x='device', y='cvr_percent', hue='group')
plt.title('Conversion Rate by Device')
plt.ylabel('Conversion Rate (%)')
plt.xlabel('') 
plt.tight_layout()
plt.savefig(os.path.join(FIGDIR, 'cvr_by_device.png'))
plt.close()
print("Saved cvr_by_device.png")

# Revenue distribution only converters
converters = df[df.converted == 1]

plt.figure(figsize=(8, 5))

sns.histplot(data=converters, x='revenue', hue='group', element='step', bins=40, alpha=0.3)
plt.title('Revenue Distribution (Converters Only)')
plt.xlabel('Revenue (USD)')
plt.tight_layout()
plt.savefig(os.path.join(FIGDIR, 'revenue_distribution.png'))
plt.close()

print("Saved revenue_distribution.png")

#Traffic source mix─
source_mix = pd.crosstab(df['traffic_source'], df['group'], normalize='columns') * 100
print(source_mix.round(1))
print("\n Key Metrics Summary")
summary = df.groupby('group').agg({
    'user_id': 'count',
    'converted': 'mean',
    'revenue': 'mean',  
    'session_duration_sec': 'mean'
}).rename(columns={
    'user_id': 'Sessions',
    'converted': 'CVR',
    'revenue': 'Rev/Session',
    'session_duration_sec': 'Avg Duration (s)'
})

print(summary.style.format({
    'CVR': '{:.2%}',
    'Rev/Session': '${:.2f}',
    'Avg Duration (s)': '{:.0f}'
}).to_string())

# CVR check first vs last 
df['week'] = pd.to_datetime(df['date']).dt.isocalendar().week
start_week, end_week = df['week'].min(), df['week'].max()

print(f"\n Novelty Analysis (Week {start_week} vs. Week {end_week})")

novelty_stats = (
    df[df['week'].isin([start_week, end_week])]
    .groupby(['week', 'group'])['converted']
    .mean()
    .unstack()
)

novelty_stats['lift'] = novelty_stats['treatment'] - novelty_stats['control']

print(novelty_stats.apply(lambda x: x.map("{:.2%}".format)))
print("\n EDA Complete. Plots saved to 'assets/' folder.")
