# Customer Engagement & Retention Analytics — Streamlit Dashboard

Live analytics dashboard for the *Customer Engagement & Product Utilization
Analytics for Retention Strategy* project (Unified Mentor / European Central
Bank retention analytics engagement).

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Data

The dashboard loads `data/European_Bank.csv` by default. You can also upload
any CSV with the same schema from the sidebar (**Data Source → Upload a
customer CSV**):

```
CustomerId, CreditScore, Geography, Gender, Age, Tenure, Balance,
NumOfProducts, HasCrCard, IsActiveMember, EstimatedSalary, Exited
```

## Modules

1. **Engagement vs Churn Overview** — churn by engagement segment, activity
   status, geography, and age band.
2. **Product Utilization Impact** — churn by product count, single- vs.
   multi-product retention, and a product-count × engagement cross-tab.
3. **High-Value Disengaged Customer Detector** — configurable balance/salary
   percentile thresholds to flag at-risk premium customers, with a
   downloadable CSV of the flagged list.
4. **Retention Strength Scoring** — the Relationship Strength Index (RSI):
   distribution, churn by tier, and a per-customer score lookup.

## Filters (sidebar)

Geography, Gender, Engagement Segment, Activity Status, Number of Products,
Balance range, Estimated Salary range, and Age range — all filters apply
across every tab and KPI simultaneously.
