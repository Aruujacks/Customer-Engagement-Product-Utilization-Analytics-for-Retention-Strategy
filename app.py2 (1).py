"""
Customer Engagement & Product Utilization Analytics for Retention Strategy
---------------------------------------------------------------------------
A Streamlit dashboard exploring how engagement and product usage relate to
customer churn at a European bank.

HOW TO RUN THIS FILE:
    1. Open a terminal in this folder (the one containing app.py and
       European_Bank.csv)
    2. Run:  streamlit run app.py
    3. Your browser will open automatically at http://localhost:8501

Everything below is organized into clearly labeled sections that match the
four "Core Modules" from the project brief:
    1. Engagement vs Churn Overview
    2. Product Utilization Impact Analysis
    3. High-Value Disengaged Customer Detector
    4. Retention Strength Scoring Panels
"""

import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------------------------
# PAGE CONFIG  (must be the first Streamlit command in the script)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Retention Analytics | European Bank",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# DATA LOADING
# @st.cache_data means the CSV is only read from disk once, not on every
# click -- this is what keeps the dashboard feeling instant.
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("European_Bank.csv")

    # Human-readable labels for the two binary columns, used in charts
    df["ActivityStatus"] = df["IsActiveMember"].map({1: "Active", 0: "Inactive"})
    df["CardStatus"] = df["HasCrCard"].map({1: "Has Card", 0: "No Card"})
    df["ChurnStatus"] = df["Exited"].map({1: "Churned", 0: "Retained"})

    return df


df_full = load_data()

# ---------------------------------------------------------------------------
# SIDEBAR — USER FILTERS
# These control everything below. df_full stays untouched; df is the
# filtered copy every chart/table reads from.
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")

geo_options = sorted(df_full["Geography"].unique())
selected_geo = st.sidebar.multiselect(
    "Geography", geo_options, default=geo_options
)

activity_options = ["Active", "Inactive"]
selected_activity = st.sidebar.multiselect(
    "Engagement (Activity Status)", activity_options, default=activity_options
)

product_range = st.sidebar.slider(
    "Number of Products",
    min_value=int(df_full["NumOfProducts"].min()),
    max_value=int(df_full["NumOfProducts"].max()),
    value=(int(df_full["NumOfProducts"].min()), int(df_full["NumOfProducts"].max())),
)

balance_range = st.sidebar.slider(
    "Balance range",
    min_value=float(df_full["Balance"].min()),
    max_value=float(df_full["Balance"].max()),
    value=(float(df_full["Balance"].min()), float(df_full["Balance"].max())),
    format="%.0f",
)

salary_range = st.sidebar.slider(
    "Estimated Salary range",
    min_value=float(df_full["EstimatedSalary"].min()),
    max_value=float(df_full["EstimatedSalary"].max()),
    value=(float(df_full["EstimatedSalary"].min()), float(df_full["EstimatedSalary"].max())),
    format="%.0f",
)

df = df_full[
    (df_full["Geography"].isin(selected_geo))
    & (df_full["ActivityStatus"].isin(selected_activity))
    & (df_full["NumOfProducts"].between(*product_range))
    & (df_full["Balance"].between(*balance_range))
    & (df_full["EstimatedSalary"].between(*salary_range))
]

st.sidebar.markdown(f"**{len(df):,} customers** match current filters (of {len(df_full):,} total)")

# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
st.title("Customer Engagement & Product Utilization Analytics")
st.caption("Retention strategy insights for a European bank — behavior over demographics")

if df.empty:
    st.warning("No customers match the current filters. Widen a filter in the sidebar.")
    st.stop()

# ---------------------------------------------------------------------------
# KPI CALCULATIONS
# Each KPI is computed on the currently FILTERED data (df), so the numbers
# at the top of the page move as the user changes filters in the sidebar.
# ---------------------------------------------------------------------------

def safe_rate(sub):
    """Churn rate of a subset, or None if the subset is empty."""
    return sub["Exited"].mean() if len(sub) else None


overall_churn = safe_rate(df)

active_churn = safe_rate(df[df.IsActiveMember == 1])
inactive_churn = safe_rate(df[df.IsActiveMember == 0])
# Engagement Retention Ratio: how many times more likely an inactive
# customer is to churn compared to an active one. >1 means engagement
# genuinely protects against churn.
engagement_retention_ratio = (
    inactive_churn / active_churn if active_churn not in (None, 0) else None
)

single_churn = safe_rate(df[df.NumOfProducts == 1])
multi_churn = safe_rate(df[df.NumOfProducts >= 2])
# Product Depth Index: churn-rate difference between single- and
# multi-product holders. Positive = holding more products is associated
# with lower churn (loyalty); negative = the opposite.
product_depth_index = (
    (single_churn - multi_churn) if None not in (single_churn, multi_churn) else None
)

bal_threshold = df_full["Balance"].median()  # fixed reference point, not affected by slider
high_balance_inactive = df[(df.Balance > bal_threshold) & (df.IsActiveMember == 0)]
# High-Balance Disengagement Rate: churn rate among customers who are
# financially valuable (above median balance) but not engaged.
high_balance_disengagement_rate = safe_rate(high_balance_inactive)

card_churn = safe_rate(df[df.HasCrCard == 1])
no_card_churn = safe_rate(df[df.HasCrCard == 0])
# Credit Card Stickiness Score: churn-rate difference between non-card and
# card holders. Positive = owning a card is associated with lower churn.
credit_card_stickiness_score = (
    (no_card_churn - card_churn) if None not in (card_churn, no_card_churn) else None
)

# Relationship Strength Index: a simple 0-3 composite per customer built
# from three loyalty signals (active membership, holding 2+ products,
# owning a credit card). We report the AVERAGE score for the filtered
# group, and separately show how average score varies with churn.
df = df.copy()
df["RelationshipScore"] = (
    df["IsActiveMember"] + (df["NumOfProducts"] >= 2).astype(int) + df["HasCrCard"]
)
relationship_strength_index = df["RelationshipScore"].mean()

# ---------------------------------------------------------------------------
# KPI ROW
# ---------------------------------------------------------------------------
st.subheader("Key Performance Indicators")
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Overall Churn Rate", f"{overall_churn:.1%}")
k2.metric(
    "Engagement Retention Ratio",
    f"{engagement_retention_ratio:.2f}x" if engagement_retention_ratio else "N/A",
    help="Inactive churn rate ÷ Active churn rate. >1 means engagement protects against churn.",
)
k3.metric(
    "Product Depth Index",
    f"{product_depth_index:+.1%}" if product_depth_index is not None else "N/A",
    help="Single-product churn minus multi-product churn. Positive = more products, less churn.",
)
k4.metric(
    "High-Balance Disengagement Rate",
    f"{high_balance_disengagement_rate:.1%}" if high_balance_disengagement_rate is not None else "N/A",
    help="Churn rate among above-median-balance customers who are inactive.",
)
k5.metric(
    "Credit Card Stickiness Score",
    f"{credit_card_stickiness_score:+.1%}" if credit_card_stickiness_score is not None else "N/A",
    help="No-card churn minus card-holder churn. Positive = cards associated with retention.",
)
k6.metric(
    "Relationship Strength Index",
    f"{relationship_strength_index:.2f} / 3",
    help="Average of (Active member + Holds 2+ products + Has credit card) across filtered customers.",
)

st.divider()

# ---------------------------------------------------------------------------
# TABS FOR THE FOUR CORE MODULES
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "1. Engagement vs Churn",
        "2. Product Utilization",
        "3. High-Value Disengaged Detector",
        "4. Retention Strength Scoring",
    ]
)

# ---- MODULE 1: ENGAGEMENT VS CHURN OVERVIEW -------------------------------
with tab1:
    st.markdown("#### Does being an active member actually reduce churn?")

    col1, col2 = st.columns(2)
    with col1:
        activity_churn_df = (
            df.groupby("ActivityStatus")["Exited"].mean().reset_index()
        )
        fig = px.bar(
            activity_churn_df,
            x="ActivityStatus",
            y="Exited",
            color="ActivityStatus",
            text_auto=".1%",
            labels={"Exited": "Churn Rate"},
            title="Churn Rate: Active vs Inactive Members",
        )
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Build the four engagement profiles named in the project brief
        bal_median_full = df_full["Balance"].median()

        def classify_segment(row):
            if row.IsActiveMember == 1 and row.NumOfProducts >= 2:
                return "Active & Engaged"
            if row.IsActiveMember == 0 and row.NumOfProducts == 1:
                return "Inactive & Disengaged"
            if row.IsActiveMember == 1 and row.NumOfProducts == 1:
                return "Active, Low-Product"
            if row.IsActiveMember == 0 and row.Balance > bal_median_full:
                return "Inactive, High-Balance"
            return "Other"

        df["EngagementSegment"] = df.apply(classify_segment, axis=1)
        seg_df = (
            df.groupby("EngagementSegment")["Exited"]
            .agg(["mean", "count"])
            .reset_index()
            .rename(columns={"mean": "ChurnRate", "count": "Customers"})
            .sort_values("ChurnRate", ascending=False)
        )
        fig2 = px.bar(
            seg_df,
            x="EngagementSegment",
            y="ChurnRate",
            text_auto=".1%",
            hover_data=["Customers"],
            title="Churn Rate by Engagement Profile",
            labels={"ChurnRate": "Churn Rate", "EngagementSegment": "Segment"},
        )
        fig2.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown(
        "**Reading this:** if 'Inactive & Disengaged' churns much more than "
        "'Active & Engaged', engagement is doing real protective work — not "
        "just correlating with wealthier or older customers."
    )

# ---- MODULE 2: PRODUCT UTILIZATION IMPACT ANALYSIS ------------------------
with tab2:
    st.markdown("#### How does the number of products relate to churn?")

    col1, col2 = st.columns(2)
    with col1:
        prod_df = (
            df.groupby("NumOfProducts")["Exited"]
            .agg(["mean", "count"])
            .reset_index()
            .rename(columns={"mean": "ChurnRate", "count": "Customers"})
        )
        fig3 = px.bar(
            prod_df,
            x="NumOfProducts",
            y="ChurnRate",
            text_auto=".1%",
            hover_data=["Customers"],
            title="Churn Rate by Number of Products",
        )
        fig3.update_yaxes(tickformat=".0%")
        fig3.update_xaxes(type="category")
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        single_multi_df = pd.DataFrame(
            {
                "Group": ["Single Product", "Multi-Product (2+)"],
                "ChurnRate": [single_churn, multi_churn],
            }
        )
        fig4 = px.bar(
            single_multi_df,
            x="Group",
            y="ChurnRate",
            text_auto=".1%",
            title="Single-Product vs Multi-Product Retention",
            color="Group",
        )
        fig4.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown(
        "**Watch for this:** in the full dataset, 3- and 4-product customers "
        "churn *far more* than 2-product customers — the opposite of what "
        "you'd expect if 'more products = more loyalty' were universally "
        "true. That's a genuine, non-obvious finding worth writing up: "
        "product depth only helps retention up to a point, after which it "
        "may signal over-selling or customer frustration rather than "
        "loyalty."
    )

# ---- MODULE 3: HIGH-VALUE DISENGAGED CUSTOMER DETECTOR --------------------
with tab3:
    st.markdown("#### Find customers who look valuable on paper but are checked out")
    st.write(
        "Adjust the thresholds below to define 'high value' and 'disengaged', "
        "then inspect the customers who fall into that risky combination."
    )

    c1, c2 = st.columns(2)
    with c1:
        detector_balance_min = st.slider(
            "Minimum Balance to count as 'high value'",
            min_value=float(df_full["Balance"].min()),
            max_value=float(df_full["Balance"].max()),
            value=float(df_full["Balance"].quantile(0.75)),
            format="%.0f",
        )
    with c2:
        detector_salary_min = st.slider(
            "Minimum Estimated Salary to count as 'high value'",
            min_value=float(df_full["EstimatedSalary"].min()),
            max_value=float(df_full["EstimatedSalary"].max()),
            value=float(df_full["EstimatedSalary"].quantile(0.75)),
            format="%.0f",
        )

    at_risk = df[
        (df.Balance >= detector_balance_min)
        & (df.EstimatedSalary >= detector_salary_min)
        & (df.IsActiveMember == 0)
    ].sort_values("Balance", ascending=False)

    st.markdown(f"**{len(at_risk):,} high-value, disengaged customers found** under current thresholds")
    st.dataframe(
        at_risk[
            [
                "CustomerId",
                "Surname",
                "Geography",
                "Balance",
                "EstimatedSalary",
                "NumOfProducts",
                "HasCrCard",
                "ChurnStatus",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    if len(at_risk):
        churned_share = at_risk["Exited"].mean()
        st.error(
            f"Of these at-risk customers, {churned_share:.1%} have already churned — "
            "the rest are a live retention target list."
        )

# ---- MODULE 4: RETENTION STRENGTH SCORING PANEL ---------------------------
with tab4:
    st.markdown("#### Relationship Strength Index vs churn")
    st.write(
        "Each customer gets a score from 0-3, one point each for: being an "
        "active member, holding 2+ products, and owning a credit card. "
        "Higher should mean 'stickier'."
    )

    score_df = (
        df.groupby("RelationshipScore")["Exited"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "ChurnRate", "count": "Customers"})
    )
    fig5 = px.bar(
        score_df,
        x="RelationshipScore",
        y="ChurnRate",
        text_auto=".1%",
        hover_data=["Customers"],
        title="Churn Rate by Relationship Strength Score (0 = weakest, 3 = strongest)",
    )
    fig5.update_yaxes(tickformat=".0%")
    fig5.update_xaxes(type="category")
    st.plotly_chart(fig5, use_container_width=True)

    st.markdown(
        "**Reading this:** a steadily declining bar from left (score 0) to "
        "right (score 3) supports using this composite score as a simple, "
        "explainable retention-risk flag — no machine learning required."
    )

    with st.expander("See underlying customer-level data"):
        st.dataframe(
            df[
                [
                    "CustomerId",
                    "Surname",
                    "Geography",
                    "RelationshipScore",
                    "IsActiveMember",
                    "NumOfProducts",
                    "HasCrCard",
                    "ChurnStatus",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

st.divider()
st.caption(
    "Customer Engagement & Product Utilization Analytics for Retention Strategy "
    "— built with Streamlit, pandas, and Plotly."
)
