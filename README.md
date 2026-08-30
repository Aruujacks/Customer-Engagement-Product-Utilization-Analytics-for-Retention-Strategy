# Customer Engagement & Product Utilization Analytics for Retention Strategy

An interactive Streamlit dashboard analyzing customer churn at a European bank through the lens of **engagement and product usage** rather than demographics alone.

🔗 **Live app:** _add your Streamlit Cloud link here after deploying_

## Overview

This dashboard supports a retention-strategy analysis with four modules:

1. **Engagement vs Churn Overview** — compares churn between active/inactive members and across four engagement profiles (Active & Engaged, Inactive & Disengaged, Active/Low-Product, Inactive/High-Balance).
2. **Product Utilization Impact Analysis** — churn rate by number of products held, and single- vs multi-product retention.
3. **High-Value Disengaged Customer Detector** — an adjustable-threshold tool to surface "at-risk premium customers" (high balance/salary but inactive).
4. **Retention Strength Scoring** — a simple 0–3 composite "Relationship Strength" score (active membership + 2+ products + credit card) plotted against churn.

## Key Performance Indicators

| KPI | Definition |
|---|---|
| Engagement Retention Ratio | Inactive churn rate ÷ Active churn rate |
| Product Depth Index | Single-product churn rate − Multi-product churn rate |
| High-Balance Disengagement Rate | Churn rate among above-median-balance, inactive customers |
| Credit Card Stickiness Score | No-card churn rate − Card-holder churn rate |
| Relationship Strength Index | Average of (Active + Holds 2+ Products + Has Card) across customers, on a 0–3 scale |

## Dataset

`European_Bank.csv` — 10,000 customer records with credit score, geography, demographics, account balance, product holdings, activity status, and churn outcome (`Exited`).

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tech stack

Python, pandas, Plotly, Streamlit.
