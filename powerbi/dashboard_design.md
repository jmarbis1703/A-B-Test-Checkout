# Power BI Dashboard — Design & Data Model

## Overview

This document specifies the Power BI dashboard for presenting the checkout-redesign A/B test results to executive stakeholders. The dashboard is designed to tell a three-part story: *What happened? → Is it real? → What should we do?*

---

## Data Model

### Tables

| Table | Source | Grain | Description |
|---|---|---|---|
| `fact_sessions` | `ab_test_data.csv` | One row per user session | Core fact table with all session-level metrics |
| `dim_date` | Generated in Power Query | One row per calendar date | Standard date dimension for time-series filtering |
| `dim_device` | Extracted from fact table | One row per device type | Device dimension (desktop, mobile, tablet) |
| `dim_source` | Extracted from fact table | One row per traffic source | Traffic source dimension |

### Relationships

```
dim_date[date] ──1:M── fact_sessions[date]
dim_device[device] ──1:M── fact_sessions[device]
dim_source[traffic_source] ──1:M── fact_sessions[traffic_source]
```

### Key DAX Measures

```dax
-- Primary KPI
Conversion Rate =
    DIVIDE(
        CALCULATE(COUNTROWS(fact_sessions), fact_sessions[converted] = 1),
        COUNTROWS(fact_sessions),
        0
    )

-- Revenue per session
Revenue Per Session =
    DIVIDE(
        SUM(fact_sessions[revenue]),
        COUNTROWS(fact_sessions),
        0
    )

-- Total conversions
Total Conversions =
    CALCULATE(COUNTROWS(fact_sessions), fact_sessions[converted] = 1)

-- Total revenue
Total Revenue = SUM(fact_sessions[revenue])

-- Control CVR (for comparison callout)
Control CVR =
    CALCULATE([Conversion Rate], fact_sessions[group] = "control")

-- Treatment CVR
Treatment CVR =
    CALCULATE([Conversion Rate], fact_sessions[group] = "treatment")

-- Absolute Lift
CVR Lift (pp) =
    ([Treatment CVR] - [Control CVR]) * 100

-- Relative Lift
CVR Lift (%) =
    DIVIDE([Treatment CVR] - [Control CVR], [Control CVR], 0)

-- Average Order Value
AOV = CALCULATE(
    AVERAGE(fact_sessions[revenue]),
    fact_sessions[converted] = 1
)
```

---

## Dashboard Layout (3 Pages)

### Page 1: Executive Summary

**Purpose:** 10-second answer to "Did it work?"

| Position | Visual | Content |
|---|---|---|
| Top banner | KPI cards (4) | Control CVR, Treatment CVR, Absolute Lift, p-value |
| Center-left | Donut chart | Conversion split by group |
| Center-right | Big number callout | Projected annual revenue uplift ($487K) |
| Bottom | Clustered bar | CVR by group × device |

**Conditional formatting:** Lift card turns green if p < 0.05, amber if p < 0.10, red otherwise.

### Page 2: Deep Dive — Trends & Segments

**Purpose:** Show the effect is real and stable.

| Position | Visual | Content |
|---|---|---|
| Top | Line chart | Daily CVR by group over 21 days |
| Middle-left | Line chart | Cumulative CVR convergence |
| Middle-right | Matrix | CVR by device × group with data bars |
| Bottom-left | Stacked bar | Traffic source mix (balance check) |
| Bottom-right | Scatter | Session duration vs. pages viewed, colored by group |

**Slicer panel (left sidebar):** Date range, device, traffic source.

### Page 3: Business Recommendation

**Purpose:** The "so what" page for decision-makers.

| Position | Visual | Content |
|---|---|---|
| Top | Text box | Decision: SHIP ✅ — one sentence summary |
| Center | Horizontal bar chart | Revenue uplift scenarios (conservative / expected / optimistic) |
| Bottom-left | Bullet list visual | Key supporting evidence (5 bullets) |
| Bottom-right | Bullet list visual | Risks & follow-ups (3 bullets) |

---

## Formatting Standards

- **Color palette:** Control = `#5B8DB8` (steel blue), Treatment = `#E07B54` (warm orange)
- **Font:** Segoe UI, 11pt body, 24pt KPI titles
- **Background:** `#F8F8F8` canvas, white card backgrounds
- **Gridlines:** Minimal, light gray
- **All percentages:** One decimal place
- **Currency:** USD, no cents

---

## Power Query Transformations

1. Import `ab_test_data.csv` with auto-type detection.
2. Parse `timestamp` → extract `date`, `hour`, `day_of_week`.
3. Create `dim_date` using `List.Dates(#date(2024,9,2), 21, #duration(1,0,0,0))`.
4. Extract unique `device` and `traffic_source` into dimension tables.
5. Set data types: `revenue` as Currency, `converted` as Whole Number.

---

## Refresh & Governance

- **Data source:** Static CSV (experiment complete). No refresh needed.
- **Row-level security:** Not applicable (no PII; experiment-level data only).
- **File format:** `.pbix` committed to `powerbi/` directory.
