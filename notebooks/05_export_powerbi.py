"""
Export data in Power BI-ready format (xlsx with dimension tables).
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from src.data_utils import load_ab_data, add_derived_features

df = load_ab_data(os.path.join(os.path.dirname(__file__), '..', 'data', 'ab_test_data.csv'))
df = add_derived_features(df)

out_path = os.path.join(os.path.dirname(__file__), '..', 'powerbi', 'ab_test_powerbi.xlsx')

with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
    # Fact table
    df.to_excel(writer, sheet_name='fact_sessions', index=False)

    # Date dimension
    dates = pd.DataFrame({'date': pd.date_range(df.timestamp.min().date(),
                                                  df.timestamp.max().date())})
    dates['day_of_week'] = dates.date.dt.day_name()
    dates['week_number'] = dates.date.dt.isocalendar().week.astype(int)
    dates['is_weekend'] = dates.date.dt.dayofweek >= 5
    dates.to_excel(writer, sheet_name='dim_date', index=False)

    # Device dimension
    devices = pd.DataFrame({'device': sorted(df.device.unique())})
    devices.to_excel(writer, sheet_name='dim_device', index=False)

    # Source dimension
    sources = pd.DataFrame({'traffic_source': sorted(df.traffic_source.unique())})
    sources.to_excel(writer, sheet_name='dim_source', index=False)

print(f"✓ Exported Power BI data → {out_path}")
