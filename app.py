"""
Customer Engagement & Product Utilization Analytics for Retention Strategy
----------------------------------------------------------------------------
Live Streamlit analytics dashboard.

Run with:
    streamlit run app.py

Expects European_Bank.csv (or any CSV with the same schema) either bundled
at ./data/European_Bank.csv or uploaded via the sidebar.
"""

import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="Customer Engagement & Retention Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY = "#1B2A4A"
TEAL = "#2E7D82"
GOLD = "#C9A15A"
RED = "#B5474D"
GREY = "#8C97A8"
SEQ = [NAVY, TEAL, GOLD, RED]

st.markdown(
    """
    <style>
    .metric-card {
        background-color: #F7F8FA;
        border-left: 5px solid #1B2A4A;
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 8px;
    }
    .block-container { padding-top: 1.6rem; }
    h1, h2, h3 { color: #1B2A4A; }
    </style>
    """,
    unsafe_allow_html=True,
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "European_Bank.csv")

# =============================================================================
# DATA LOADING & FEATURE ENGINEERING
# =============================================================================
@st.cache_data
def load_data(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    required = {"CustomerId", "CreditScore", "Geography", "Gender", "Age", "Tenure",
                "Balance", "NumOfProducts", "HasCrCard", "IsActiveMember",
                "EstimatedSalary", "Exited"}
    missing = required - set(df.columns)
    if missing:
        st.error(f"Uploaded file is missing required columns: {sorted(missing)}")
        st.stop()
    return df


@st.cache_data
def enrich(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def classify(row):
        if row["IsActiveMember"] == 1 and row["NumOfProducts"] >= 2:
            return "Active Engaged"
        elif row["IsActiveMember"] == 0:
            return "Inactive High-Balance" if row["Balance"] >= 100_000 else "Inactive Disengaged"
        elif row["IsActiveMember"] == 1 and row["NumOfProducts"] == 1:
            return "Active Low-Product"
        return "Other"

    df["EngagementSegment"] = df.apply(classify, axis=1)

    # Relationship Strength Index (0-100): Activity 40%, Product depth (capped at 2) 30%,
    # Tenure 15%, Credit card 15%
    prod_score = df["NumOfProducts"].clip(upper=2) / 2
    tenure_score = df["Tenure"].clip(upper=10) / 10
    df["RSI"] = (
        df["IsActiveMember"] * 0.40
        + prod_score * 0.30
        + tenure_score * 0.15
        + df["HasCrCard"] * 0.15
    ) * 100
    df["RSI"] = df["RSI"].round(1)
    df["RSI_Tier"] = pd.cut(
        df["RSI"], bins=[-1, 25, 50, 75, 100],
        labels=["Low (0-25)", "Moderate (25-50)", "Good (50-75)", "Strong (75-100)"],
    )
    df["AgeBand"] = pd.cut(
        df["Age"], bins=[17, 30, 40, 50, 60, 100],
        labels=["18-30", "31-40", "41-50", "51-60", "61+"],
    )
    return df


def churn_pct(frame: pd.DataFrame) -> float:
    return round(frame["Exited"].mean() * 100, 2) if len(frame) else 0.0


# =============================================================================
# SIDEBAR — DATA SOURCE + FILTERS
# =============================================================================
st.sidebar.title("📊 Retention Analytics")
st.sidebar.caption("Customer Engagement & Product Utilization Analytics for Retention Strategy")

st.sidebar.markdown("### Data Source")
uploaded = st.sidebar.file_uploader("Upload a customer CSV (optional)", type=["csv"])
if uploaded is not None:
    raw = load_data(uploaded)
    st.sidebar.success(f"Loaded {len(raw):,} customers from upload.")
elif os.path.exists(DATA_PATH):
    raw = load_data(DATA_PATH)
    st.sidebar.info(f"Using bundled dataset: {len(raw):,} customers.")
else:
    st.sidebar.warning("No bundled dataset found — please upload a CSV to continue.")
    st.stop()

data = enrich(raw)

st.sidebar.markdown("### Engagement Filters")
geo_opts = sorted(data["Geography"].unique().tolist())
sel_geo = st.sidebar.multiselect("Geography", geo_opts, default=geo_opts)

gender_opts = sorted(data["Gender"].unique().tolist())
sel_gender = st.sidebar.multiselect("Gender", gender_opts, default=gender_opts)

seg_opts = ["Active Engaged", "Active Low-Product", "Inactive Disengaged", "Inactive High-Balance"]
sel_seg = st.sidebar.multiselect("Engagement Segment", seg_opts, default=seg_opts)

activity_opt = st.sidebar.radio("Activity Status", ["All", "Active only", "Inactive only"], index=0)

st.sidebar.markdown("### Product Count")
prod_min, prod_max = int(data["NumOfProducts"].min()), int(data["NumOfProducts"].max())
sel_prod = st.sidebar.slider("Number of Products", prod_min, prod_max, (prod_min, prod_max))

st.sidebar.markdown("### Financial Thresholds")
bal_min, bal_max = float(data["Balance"].min()), float(data["Balance"].max())
sel_bal = st.sidebar.slider("Balance range (€)", bal_min, bal_max, (bal_min, bal_max), format="€%.0f")

sal_min, sal_max = float(data["EstimatedSalary"].min()), float(data["EstimatedSalary"].max())
sel_sal = st.sidebar.slider("Estimated salary range (€)", sal_min, sal_max, (sal_min, sal_max), format="€%.0f")

age_min, age_max = int(data["Age"].min()), int(data["Age"].max())
sel_age = st.sidebar.slider("Age range", age_min, age_max, (age_min, age_max))

# Apply filters
f = data[
    data["Geography"].isin(sel_geo)
    & data["Gender"].isin(sel_gender)
    & data["EngagementSegment"].isin(sel_seg)
    & data["NumOfProducts"].between(sel_prod[0], sel_prod[1])
    & data["Balance"].between(sel_bal[0], sel_bal[1])
    & data["EstimatedSalary"].between(sel_sal[0], sel_sal[1])
    & data["Age"].between(sel_age[0], sel_age[1])
].copy()

if activity_opt == "Active only":
    f = f[f["IsActiveMember"] == 1]
elif activity_opt == "Inactive only":
    f = f[f["IsActiveMember"] == 0]

st.sidebar.markdown("---")
st.sidebar.metric("Customers in current view", f"{len(f):,}", f"of {len(data):,} total")

# =============================================================================
# HEADER + TOP-LEVEL KPI STRIP
# =============================================================================
st.title("Customer Engagement & Product Utilization Analytics")
st.caption("Retention Strategy Dashboard  ·  Live analytics over the filtered customer population")

if f.empty:
    st.warning("No customers match the current filter combination. Adjust the filters in the sidebar.")
    st.stop()

k1, k2, k3, k4, k5 = st.columns(5)
overall_churn = churn_pct(f)
active_churn = churn_pct(f[f["IsActiveMember"] == 1])
inactive_churn = churn_pct(f[f["IsActiveMember"] == 0])
err_ratio = round(inactive_churn / active_churn, 2) if active_churn else np.nan

one_prod_churn = churn_pct(f[f["NumOfProducts"] == 1])
two_prod_churn = churn_pct(f[f["NumOfProducts"] == 2])
pdi = round((1 - (two_prod_churn / one_prod_churn)) * 100, 1) if one_prod_churn else np.nan

bal_q75 = data["Balance"].quantile(0.75)
hb = f[f["Balance"] >= bal_q75]
hb_disengagement = churn_pct(hb[hb["IsActiveMember"] == 0])

rsi_mean = round(f["RSI"].mean(), 1) if len(f) else np.nan

k1.metric("Overall Churn Rate", f"{overall_churn:.1f}%")
k2.metric("Engagement Retention Ratio", f"{err_ratio:.2f}×" if not np.isnan(err_ratio) else "n/a",
          help="Inactive churn rate ÷ active churn rate")
k3.metric("Product Depth Index", f"{pdi:.1f}%" if not np.isnan(pdi) else "n/a",
          help="Relative churn reduction moving from 1 to 2 products")
k4.metric("High-Balance Disengagement Rate", f"{hb_disengagement:.1f}%",
          help="Churn rate of inactive customers in the top balance quartile")
k5.metric("Avg. Relationship Strength Index", f"{rsi_mean:.1f} / 100")

st.markdown("---")

# =============================================================================
# TABS — CORE MODULES
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Engagement vs Churn Overview",
    "🧩 Product Utilization Impact",
    "💰 High-Value Disengaged Detector",
    "🏆 Retention Strength Scoring",
])

# ---------------------------------------------------------------------------
# TAB 1 — ENGAGEMENT VS CHURN OVERVIEW
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Engagement vs Churn Overview")
    c1, c2 = st.columns([1.1, 1])

    with c1:
        seg_summary = (
            f.groupby("EngagementSegment", observed=True)
            .agg(Customers=("CustomerId", "count"), ChurnRate=("Exited", "mean"))
            .reindex(seg_opts)
            .dropna()
            .reset_index()
        )
        seg_summary["ChurnRate"] = (seg_summary["ChurnRate"] * 100).round(2)
        fig = px.bar(
            seg_summary, x="ChurnRate", y="EngagementSegment", orientation="h",
            color="EngagementSegment", color_discrete_sequence=SEQ, text="ChurnRate",
            labels={"ChurnRate": "Churn Rate (%)", "EngagementSegment": ""},
            title="Churn Rate by Engagement Segment",
        )
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        act_summary = (
            f.groupby("IsActiveMember").agg(Customers=("CustomerId", "count"), ChurnRate=("Exited", "mean")).reset_index()
        )
        act_summary["IsActiveMember"] = act_summary["IsActiveMember"].map({0: "Inactive", 1: "Active"})
        act_summary["ChurnRate"] = (act_summary["ChurnRate"] * 100).round(2)
        fig2 = px.bar(
            act_summary, x="IsActiveMember", y="ChurnRate", color="IsActiveMember",
            color_discrete_map={"Active": TEAL, "Inactive": RED}, text="ChurnRate",
            labels={"ChurnRate": "Churn Rate (%)", "IsActiveMember": ""},
            title="Active vs Inactive Churn",
        )
        fig2.update_traces(texttemplate="%{text}%", textposition="outside")
        fig2.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        geo_summary = f.groupby("Geography").agg(Customers=("CustomerId", "count"), ChurnRate=("Exited", "mean")).reset_index()
        geo_summary["ChurnRate"] = (geo_summary["ChurnRate"] * 100).round(2)
        fig3 = px.bar(geo_summary, x="Geography", y="ChurnRate", color="Geography",
                       color_discrete_sequence=SEQ, text="ChurnRate", title="Churn Rate by Geography")
        fig3.update_traces(texttemplate="%{text}%", textposition="outside")
        fig3.update_layout(showlegend=False, height=340)
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        age_summary = f.groupby("AgeBand", observed=True).agg(Customers=("CustomerId", "count"), ChurnRate=("Exited", "mean")).reset_index()
        age_summary["ChurnRate"] = (age_summary["ChurnRate"] * 100).round(2)
        fig4 = px.bar(age_summary, x="AgeBand", y="ChurnRate", text="ChurnRate",
                       title="Churn Rate by Age Band", color_discrete_sequence=[NAVY])
        fig4.update_traces(texttemplate="%{text}%", textposition="outside")
        fig4.update_layout(height=340)
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("##### Segment Detail")
    st.dataframe(
        seg_summary.rename(columns={"ChurnRate": "Churn Rate (%)"}),
        use_container_width=True, hide_index=True,
    )

# ---------------------------------------------------------------------------
# TAB 2 — PRODUCT UTILIZATION IMPACT
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("Product Utilization Impact Analysis")
    c1, c2 = st.columns([1.2, 1])

    with c1:
        prod_summary = f.groupby("NumOfProducts").agg(Customers=("CustomerId", "count"), ChurnRate=("Exited", "mean")).reset_index()
        prod_summary["ChurnRate"] = (prod_summary["ChurnRate"] * 100).round(2)
        colors = [RED if p >= 3 else (TEAL if p == 2 else NAVY) for p in prod_summary["NumOfProducts"]]
        fig = go.Figure(go.Bar(
            x=prod_summary["NumOfProducts"].astype(str), y=prod_summary["ChurnRate"],
            marker_color=colors, text=prod_summary["ChurnRate"].astype(str) + "%",
            textposition="outside",
            customdata=prod_summary["Customers"],
            hovertemplate="Products: %{x}<br>Churn: %{y}%<br>Customers: %{customdata}<extra></extra>",
        ))
        fig.update_layout(title="Churn Rate by Product Count", xaxis_title="Number of Products",
                           yaxis_title="Churn Rate (%)", height=420)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("⚠️ Churn spikes sharply at 3–4 products — a signal of over-bundling or forced cross-sell, not loyalty.")

    with c2:
        st.markdown("##### Single vs Multi-Product Retention")
        single = churn_pct(f[f["NumOfProducts"] == 1])
        multi = churn_pct(f[f["NumOfProducts"] >= 2])
        comp = pd.DataFrame({"Group": ["Single Product", "2+ Products"], "ChurnRate": [single, multi]})
        fig2 = px.pie(comp, names="Group", values=[100 - single, 100 - multi],
                       color_discrete_sequence=[NAVY, TEAL],
                       title="Retention Rate: Single vs Multi-Product")
        fig2.update_traces(textinfo="label+percent")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("##### Product Depth Table")
    st.dataframe(prod_summary.rename(columns={"ChurnRate": "Churn Rate (%)"}), use_container_width=True, hide_index=True)

    st.markdown("##### Explore: Product Count × Engagement")
    cross = f.pivot_table(index="NumOfProducts", columns="EngagementSegment", values="Exited", aggfunc="mean", observed=True) * 100
    st.dataframe(cross.round(1).style.background_gradient(cmap="RdYlGn_r", axis=None), use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 3 — HIGH-VALUE DISENGAGED CUSTOMER DETECTOR
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("High-Value Disengaged Customer Detector")
    st.caption("Identify customers who are financially valuable but behaviorally at risk of silent churn.")

    d1, d2, d3 = st.columns(3)
    with d1:
        bal_pctile = st.slider("Balance percentile threshold", 50, 99, 75, help="Flag customers above this balance percentile")
    with d2:
        sal_pctile = st.slider("Salary percentile threshold", 50, 99, 75, help="Flag customers above this salary percentile")
    with d3:
        require_inactive = st.checkbox("Require inactive status", value=True)

    bal_thresh = data["Balance"].quantile(bal_pctile / 100)
    sal_thresh = data["EstimatedSalary"].quantile(sal_pctile / 100)

    at_risk = f[(f["Balance"] >= bal_thresh) & (f["EstimatedSalary"] >= sal_thresh)]
    if require_inactive:
        at_risk = at_risk[at_risk["IsActiveMember"] == 0]

    m1, m2, m3 = st.columns(3)
    m1.metric("At-Risk Premium Customers", f"{len(at_risk):,}")
    m2.metric("Share of Filtered Base", f"{(len(at_risk) / len(f) * 100 if len(f) else 0):.1f}%")
    m3.metric("Churn Rate in This Group", f"{churn_pct(at_risk):.1f}%")

    st.markdown(f"**Thresholds applied:** Balance ≥ €{bal_thresh:,.0f}  ·  Salary ≥ €{sal_thresh:,.0f}"
                + ("  ·  Inactive members only" if require_inactive else ""))

    c1, c2 = st.columns(2)
    with c1:
        fig = px.scatter(
            f, x="Balance", y="EstimatedSalary", color="EngagementSegment",
            color_discrete_sequence=SEQ, opacity=0.55,
            symbol=f["Exited"].map({0: "Retained", 1: "Churned"}),
            title="Balance vs Salary — colored by engagement segment",
            labels={"symbol": "Outcome"},
        )
        fig.add_vline(x=bal_thresh, line_dash="dash", line_color=GREY)
        fig.add_hline(y=sal_thresh, line_dash="dash", line_color=GREY)
        fig.update_layout(height=440)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        hb_activity = f[f["Balance"] >= bal_thresh].groupby("IsActiveMember").agg(
            Customers=("CustomerId", "count"), ChurnRate=("Exited", "mean")
        ).reset_index()
        hb_activity["IsActiveMember"] = hb_activity["IsActiveMember"].map({0: "Inactive", 1: "Active"})
        hb_activity["ChurnRate"] = (hb_activity["ChurnRate"] * 100).round(2)
        fig2 = px.bar(hb_activity, x="IsActiveMember", y="ChurnRate", color="IsActiveMember",
                       color_discrete_map={"Active": TEAL, "Inactive": RED}, text="ChurnRate",
                       title=f"Top {100 - bal_pctile}% Balance Customers: Churn by Activity")
        fig2.update_traces(texttemplate="%{text}%", textposition="outside")
        fig2.update_layout(showlegend=False, height=440)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("##### At-Risk Customer List")
    show_cols = ["CustomerId", "Surname", "Geography", "Age", "Balance", "EstimatedSalary",
                 "NumOfProducts", "IsActiveMember", "RSI", "EngagementSegment", "Exited"]
    st.dataframe(at_risk[show_cols].sort_values("Balance", ascending=False), use_container_width=True, hide_index=True, height=320)
    st.download_button(
        "⬇️ Download at-risk customer list (CSV)",
        data=at_risk[show_cols].to_csv(index=False).encode("utf-8"),
        file_name="at_risk_premium_customers.csv",
        mime="text/csv",
    )

# ---------------------------------------------------------------------------
# TAB 4 — RETENTION STRENGTH SCORING PANEL
# ---------------------------------------------------------------------------
with tab4:
    st.subheader("Retention Strength Scoring Panel")
    st.caption("Relationship Strength Index (RSI): a 0–100 composite of activity (40%), product depth capped at 2 (30%), tenure (15%), and credit card ownership (15%).")

    c1, c2 = st.columns([1.2, 1])
    with c1:
        tier_summary = f.groupby("RSI_Tier", observed=True).agg(
            Customers=("CustomerId", "count"), ChurnRate=("Exited", "mean")
        ).reset_index()
        tier_summary["ChurnRate"] = (tier_summary["ChurnRate"] * 100).round(2)
        fig = px.bar(tier_summary, x="RSI_Tier", y="ChurnRate", color="RSI_Tier",
                      color_discrete_sequence=[RED, GOLD, TEAL, NAVY], text="ChurnRate",
                      title="Churn Rate by Relationship Strength Tier",
                      labels={"RSI_Tier": "RSI Tier", "ChurnRate": "Churn Rate (%)"})
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(showlegend=False, height=420)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig2 = px.histogram(f, x="RSI", nbins=25, color_discrete_sequence=[TEAL],
                              title="RSI Score Distribution")
        fig2.update_layout(height=420, xaxis_title="Relationship Strength Index", yaxis_title="Customers")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("##### Tier Detail")
    st.dataframe(tier_summary.rename(columns={"ChurnRate": "Churn Rate (%)"}), use_container_width=True, hide_index=True)

    st.markdown("##### Score an Individual Customer")
    st.caption("Look up a customer by ID to see their Relationship Strength Index breakdown.")
    cust_id = st.selectbox("Select Customer ID", options=f["CustomerId"].sort_values().tolist())
    row = f[f["CustomerId"] == cust_id].iloc[0]
    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    sc1.metric("RSI Score", f"{row['RSI']:.1f} / 100")
    sc2.metric("Tier", str(row["RSI_Tier"]))
    sc3.metric("Active Member", "Yes" if row["IsActiveMember"] == 1 else "No")
    sc4.metric("Products Held", int(row["NumOfProducts"]))
    sc5.metric("Tenure (yrs)", int(row["Tenure"]))
    st.write(f"**Segment:** {row['EngagementSegment']}  ·  **Geography:** {row['Geography']}  ·  **Balance:** €{row['Balance']:,.0f}  ·  **Churn status:** {'Churned' if row['Exited']==1 else 'Retained'}")

st.markdown("---")
st.caption(
    "Customer Engagement & Product Utilization Analytics for Retention Strategy · "
    "Unified Mentor / European Central Bank retention analytics engagement · "
    "All figures computed live from the filtered dataset above."
)
