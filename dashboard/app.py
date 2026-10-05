"""
PeakPulse — Food Delivery SLA Insights
Interactive Streamlit Operations Dashboard

Author: Data Analytics & Operations Team
Framework: Streamlit + Plotly + Pandas
"""

import sys
from pathlib import Path
import pandas as pd
import streamlit as st

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.config import (
    PROCESSED_DATA_PATH,
    DEFAULT_SLA_THRESHOLD_MINUTES,
    PEAK_HOURS_DINNER,
    COLORS,
)
from src.analysis import (
    compute_kpis,
    analyze_hourly_patterns,
    compare_peak_vs_nonpeak,
    analyze_category_impact,
    generate_key_insights,
)
from src.visualization import (
    plot_hourly_trend,
    plot_traffic_performance,
    plot_multi_delivery_impact,
    plot_city_comparison,
    plot_delivery_time_distribution,
    plot_weather_performance,
)

# ------------------------------------------------------------------------------
# 1. PAGE SETUP & FIGMA DARK THEME STYLING
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="PeakPulse — Food Delivery SLA Insights",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS matching Figma Prototype Theme
st.markdown(
    """
    <style>
    /* Dark background */
    .stApp {
        background-color: #0B0F19;
        color: #F8FAFC;
        font-family: 'Inter', sans-serif;
    }
    
    /* Top Header */
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: -0.5px;
        margin-bottom: 2px;
    }
    .sub-header {
        font-size: 14px;
        color: #94A3B8;
        margin-bottom: 16px;
    }
    
    /* KPI Card Container */
    .kpi-container {
        background: linear-gradient(135deg, #161F30 0%, #111827 100%);
        border: 1px solid #24324D;
        border-radius: 10px;
        padding: 16px;
        text-align: left;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .kpi-container:hover {
        border-color: #38BDF8;
        transform: translateY(-2px);
    }
    .kpi-title {
        font-size: 12px;
        text-transform: uppercase;
        color: #94A3B8;
        letter-spacing: 0.8px;
        margin-bottom: 4px;
        font-weight: 600;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 2px;
    }
    .kpi-subtitle {
        font-size: 12px;
        color: #38BDF8;
        font-weight: 500;
    }
    .kpi-alert {
        color: #FF4B4B !important;
    }
    
    /* Alert Banner */
    .sla-banner {
        background-color: rgba(255, 75, 75, 0.1);
        border-left: 4px solid #FF4B4B;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 18px;
        font-size: 13px;
        color: #CBD5E1;
    }
    
    /* Insight Cards */
    .insight-card {
        background-color: #161F30;
        border: 1px solid #24324D;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 14px;
    }
    .insight-title {
        color: #38BDF8;
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0E1422;
        border-right: 1px solid #1E293B;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #24324D;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        padding: 8px 16px;
        background-color: #161F30;
        border-radius: 6px 6px 0 0;
        color: #94A3B8;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #24324D !important;
        color: #FFFFFF !important;
        border-bottom: 2px solid #FF4B4B !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------------------
# 2. DATA LOADING & CACHING
# ------------------------------------------------------------------------------
@st.cache_data
def load_delivery_data():
    """Load cleaned delivery dataset with caching for fast UI interactions."""
    if not PROCESSED_DATA_PATH.exists():
        # Fallback: trigger cleaning if processed file doesn't exist
        from src.data_cleaning import main as run_cleaning
        run_cleaning()
    df = pd.read_csv(PROCESSED_DATA_PATH)
    return df

df_full = load_delivery_data()


# ------------------------------------------------------------------------------
# 3. SIDEBAR CONTROLS & FILTERS
# ------------------------------------------------------------------------------
st.sidebar.markdown("## ⚡ **PeakPulse**")
st.sidebar.markdown("<p style='font-size: 12px; color: #94A3B8;'>Food Delivery SLA Insights & Ops Monitor</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# SLA Threshold Slider
st.sidebar.markdown("### 🎯 **Analytical SLA Setting**")
sla_threshold = st.sidebar.slider(
    "Target Max Delivery Time (min)",
    min_value=20,
    max_value=45,
    value=DEFAULT_SLA_THRESHOLD_MINUTES,
    step=1,
    help=(
        "Project-defined analytical SLA threshold. The source dataset lacks official SLA timestamps; "
        "30 minutes represents a defensible operational benchmark based on distribution analysis."
    ),
)
st.sidebar.caption(f"Currently defining SLA breach as **> {sla_threshold} min**.")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 **Operational Filters**")

# City Filter
cities = sorted(df_full["city"].dropna().unique().tolist())
selected_cities = st.sidebar.multiselect("City Classification", options=cities, default=cities)

# Traffic Filter
traffics = ["Low", "Medium", "High", "Jam", "Unknown"]
existing_traffics = [t for t in traffics if t in df_full["traffic_density"].unique()]
selected_traffic = st.sidebar.multiselect("Traffic Density", options=existing_traffics, default=existing_traffics)

# Weather Filter
weathers = sorted(df_full["weather"].dropna().unique().tolist())
selected_weather = st.sidebar.multiselect("Weather Conditions", options=weathers, default=weathers)

# Vehicle Type Filter
vehicles = sorted(df_full["vehicle_type"].dropna().unique().tolist())
selected_vehicles = st.sidebar.multiselect("Vehicle Type", options=vehicles, default=vehicles)

# Operational Period (Peak/Non-Peak)
period_options = ["All Periods", "Dinner Peak (18-21)", "Lunch Peak (12-13)", "Off-Peak"]
selected_period = st.sidebar.selectbox("Operational Period", options=period_options, index=0)

# Festival Filter
festivals = ["All", "Yes", "No"]
selected_festival = st.sidebar.radio("Festival Orders", options=festivals, index=0, horizontal=True)

# Apply Filters
filtered_df = df_full.copy()
if selected_cities:
    filtered_df = filtered_df[filtered_df["city"].isin(selected_cities)]
if selected_traffic:
    filtered_df = filtered_df[filtered_df["traffic_density"].isin(selected_traffic)]
if selected_weather:
    filtered_df = filtered_df[filtered_df["weather"].isin(selected_weather)]
if selected_vehicles:
    filtered_df = filtered_df[filtered_df["vehicle_type"].isin(selected_vehicles)]
if selected_festival != "All":
    filtered_df = filtered_df[filtered_df["festival"] == selected_festival]
if selected_period == "Dinner Peak (18-21)":
    filtered_df = filtered_df[filtered_df["peak_period"] == "Dinner Peak (18-21)"]
elif selected_period == "Lunch Peak (12-13)":
    filtered_df = filtered_df[filtered_df["peak_period"] == "Lunch Peak (12-13)"]
elif selected_period == "Off-Peak":
    filtered_df = filtered_df[filtered_df["peak_period"] == "Off-Peak"]

st.sidebar.markdown("---")
st.sidebar.caption(f"Showing **{len(filtered_df):,}** of **{len(df_full):,}** orders ({len(filtered_df)/len(df_full)*100:.1f}%)")


# ------------------------------------------------------------------------------
# 4. MAIN HEADER & SLA BANNER
# ------------------------------------------------------------------------------
st.markdown("<div class='main-header'>PeakPulse — Food Delivery SLA Insights</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='sub-header'>Operations Analytics Dashboard for Delivery Delays, SLA Violations & Peak-Hour Bottlenecks</div>",
    unsafe_allow_html=True,
)

# SLA Notice Alert Banner
st.markdown(
    f"""
    <div class='sla-banner'>
        <strong>⚠️ Analytical Notice:</strong> The source dataset does not contain an explicit customer-promised delivery time or official SLA. 
        All SLA metrics on this dashboard are calculated using a <strong>project-defined analytical baseline of {sla_threshold} minutes</strong> 
        derived from turnaround distributions (Median: {df_full['delivery_time_min'].median():.0f}m, Q3: {df_full['delivery_time_min'].quantile(0.75):.0f}m).
    </div>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------------------
# 5. DASHBOARD TABS
# ------------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Overview",
    "⏰ Peak-Hour Analysis",
    "📍 Location Analysis",
    "🛵 Rider & Delivery Patterns",
    "🛡️ Customer Impact & Limitations",
    "💡 Key Insights",
])


# ==============================================================================
# TAB 1: OVERVIEW
# ==============================================================================
with tab1:
    kpis = compute_kpis(filtered_df, sla_threshold)
    
    # 5 Metric Cards
    c1, c2, c3, c4, c5 = st.columns(5)
    
    with c1:
        st.markdown(
            f"""
            <div class='kpi-container'>
                <div class='kpi-title'>Total Deliveries</div>
                <div class='kpi-value'>{kpis['total_orders']:,}</div>
                <div class='kpi-subtitle'>Active in Scope</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class='kpi-container'>
                <div class='kpi-title'>SLA Violations</div>
                <div class='kpi-value kpi-alert'>{kpis['sla_violations']:,}</div>
                <div class='kpi-subtitle kpi-alert'>Orders > {sla_threshold} min</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class='kpi-container'>
                <div class='kpi-title'>SLA Violation Rate</div>
                <div class='kpi-value kpi-alert'>{kpis['sla_violation_rate']:.1f}%</div>
                <div class='kpi-subtitle'>Breach Frequency</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class='kpi-container'>
                <div class='kpi-title'>Avg Delivery Time</div>
                <div class='kpi-value'>{kpis['avg_time']:.1f} <span style='font-size:16px;'>min</span></div>
                <div class='kpi-subtitle'>Median: {kpis['median_time']:.0f} min</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c5:
        st.markdown(
            f"""
            <div class='kpi-container'>
                <div class='kpi-title'>Dinner Peak Orders</div>
                <div class='kpi-value'>{kpis['peak_orders']:,}</div>
                <div class='kpi-subtitle'>{kpis['peak_share_pct']:.1f}% of Volume</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Overview Charts Row
    row1_c1, row1_c2 = st.columns([1.1, 0.9])
    
    with row1_c1:
        st.plotly_chart(plot_delivery_time_distribution(filtered_df, sla_threshold), use_container_width=True)
        st.caption("Distribution of delivery durations. Dashed red line marks analytical SLA cutoff; dotted green line shows median.")

    with row1_c2:
        traffic_summary = analyze_category_impact(filtered_df, "traffic_density", sla_threshold)
        st.plotly_chart(plot_traffic_performance(traffic_summary), use_container_width=True)
        st.caption("Observed delivery turnaround and SLA breach frequency under various road traffic conditions.")

    # High-level operational summary table
    st.markdown("### 📋 **Operational Snapshot by Traffic Level**")
    display_traffic = traffic_summary.rename(columns={
        "traffic_density": "Traffic Level",
        "order_count": "Orders",
        "order_share_pct": "Share (%)",
        "avg_delivery_time": "Avg Time (min)",
        "median_delivery_time": "Median Time (min)",
        "sla_violations": "SLA Breaches",
        "sla_violation_rate": "SLA Breach Rate (%)"
    })
    st.dataframe(
        display_traffic.style.format({
            "Orders": "{:,}",
            "Share (%)": "{:.1f}%",
            "Avg Time (min)": "{:.2f}",
            "Median Time (min)": "{:.1f}",
            "SLA Breaches": "{:,}",
            "SLA Breach Rate (%)": "{:.2f}%",
        }),
        use_container_width=True,
    )


# ==============================================================================
# TAB 2: PEAK-HOUR ANALYSIS
# ==============================================================================
with tab2:
    st.markdown("### ⏰ **Peak-Hour Demand & Delay Dynamics**")
    st.markdown(
        """
        **Empirical Methodology**: Rather than assuming peak hours arbitrarily, analysis of the order logs reveals that 
        hours **18:00 to 21:00 (Dinner Peak)** handle **>40%** of daily delivery volume and exhibit average delivery times exceeding 
        **31 minutes** (with SLA violation rates reaching ~50%). A secondary micro-peak occurs around lunch (12:00–14:00).
        """
    )
    
    hourly_df = analyze_hourly_patterns(filtered_df, sla_threshold)
    st.plotly_chart(plot_hourly_trend(hourly_df), use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_peak1, col_peak2 = st.columns(2)
    
    with col_peak1:
        st.markdown("#### **Peak vs Non-Peak Comparison**")
        peak_comp = compare_peak_vs_nonpeak(filtered_df, sla_threshold)
        st.dataframe(
            peak_comp[["period_label", "order_count", "order_share_pct", "avg_delivery_time", "sla_violation_rate"]].rename(columns={
                "period_label": "Operating Window",
                "order_count": "Orders",
                "order_share_pct": "Volume Share (%)",
                "avg_delivery_time": "Avg Time (min)",
                "sla_violation_rate": "SLA Breach Rate (%)",
            }).style.format({
                "Orders": "{:,}",
                "Volume Share (%)": "{:.1f}%",
                "Avg Time (min)": "{:.2f}",
                "SLA Breach Rate (%)": "{:.2f}%",
            }),
            use_container_width=True,
        )
        
    with col_peak2:
        st.markdown("#### **Peak Window Operational Findings**")
        st.info(
            """
            - **Volume Concentration**: Dinner hours (18:00–21:00) concentrate massive volume into a narrow window.
            - **Turnaround Degradation**: Average turnaround rises by **~8–11 minutes** compared to morning/off-peak windows.
            - **Breach Rate Spike**: Roughly **1 out of every 2 orders** placed during dinner peak exceeds the 30-minute analytical baseline.
            """
        )


# ==============================================================================
# TAB 3: LOCATION ANALYSIS
# ==============================================================================
with tab3:
    st.markdown("### 📍 **Geographic & Location-Based Performance**")
    
    loc_c1, loc_c2 = st.columns(2)
    with loc_c1:
        city_summary = analyze_category_impact(filtered_df, "city", sla_threshold)
        st.plotly_chart(plot_city_comparison(city_summary), use_container_width=True)
    
    with loc_c2:
        st.markdown("#### **City Performance Summary**")
        st.dataframe(
            city_summary[["city", "order_count", "order_share_pct", "avg_delivery_time", "sla_violation_rate"]].rename(columns={
                "city": "City Tier",
                "order_count": "Total Orders",
                "order_share_pct": "Share (%)",
                "avg_delivery_time": "Avg Time (min)",
                "sla_violation_rate": "SLA Breach Rate (%)",
            }).style.format({
                "Total Orders": "{:,}",
                "Share (%)": "{:.1f}%",
                "Avg Time (min)": "{:.2f}",
                "SLA Breach Rate (%)": "{:.2f}%",
            }),
            use_container_width=True,
        )
        st.caption("Semi-Urban orders represent <1% volume but exhibit severe delivery durations (~49.7 min average).")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### **Weather Impact on Turnaround**")
    weather_summary = analyze_category_impact(filtered_df, "weather", sla_threshold)
    st.plotly_chart(plot_weather_performance(weather_summary), use_container_width=True)


# ==============================================================================
# TAB 4: RIDER & DELIVERY PATTERNS
# ==============================================================================
with tab4:
    st.markdown("### 🛵 **Rider, Batching & Vehicle Insights**")
    
    rc1, rc2 = st.columns(2)
    with rc1:
        multi_summary = analyze_category_impact(filtered_df, "multiple_deliveries", sla_threshold)
        st.plotly_chart(plot_multi_delivery_impact(multi_summary), use_container_width=True)
        st.caption("Demonstrates the steep increase in turnaround time when stacking multi-drop orders.")
        
    with rc2:
        st.markdown("#### **Vehicle Condition Performance**")
        vc_summary = analyze_category_impact(filtered_df, "vehicle_condition", sla_threshold)
        st.dataframe(
            vc_summary[["vehicle_condition", "order_count", "avg_delivery_time", "sla_violation_rate"]].rename(columns={
                "vehicle_condition": "Vehicle Condition (0=Poor, 3=Optimal)",
                "order_count": "Deliveries",
                "avg_delivery_time": "Avg Time (min)",
                "sla_violation_rate": "SLA Breach Rate (%)",
            }).style.format({
                "Deliveries": "{:,}",
                "Avg Time (min)": "{:.2f}",
                "SLA Breach Rate (%)": "{:.2f}%",
            }),
            use_container_width=True,
        )
        st.info("Orders assigned to Condition 0 vehicles experience an average delivery duration of ~30.1 minutes, compared to ~24.4 minutes for Condition 1 & 2.")

    st.markdown("---")
    st.markdown("#### **High-Volume Rider Performance Snapshot (>= 50 Deliveries)**")
    rider_agg = filtered_df.groupby("delivery_person_id").agg(
        total_orders=("order_id", "count"),
        avg_rating=("delivery_person_rating", "mean"),
        avg_time=("delivery_time_min", "mean"),
        sla_violations=("is_sla_violated", "sum"),
    ).reset_index()
    rider_agg["sla_violation_rate"] = (rider_agg["sla_violations"] / rider_agg["total_orders"]) * 100.0
    top_riders = rider_agg[rider_agg["total_orders"] >= 50].sort_values("total_orders", ascending=False).head(15)
    
    st.dataframe(
        top_riders.rename(columns={
            "delivery_person_id": "Rider ID",
            "total_orders": "Total Orders",
            "avg_rating": "Avg Rating",
            "avg_time": "Avg Delivery Time (min)",
            "sla_violations": "SLA Breaches",
            "sla_violation_rate": "SLA Breach Rate (%)",
        }).style.format({
            "Total Orders": "{:,}",
            "Avg Rating": "{:.2f}",
            "Avg Delivery Time (min)": "{:.2f}",
            "SLA Breaches": "{:,}",
            "SLA Breach Rate (%)": "{:.2f}%",
        }),
        use_container_width=True,
    )


# ==============================================================================
# TAB 5: CUSTOMER IMPACT & DATA LIMITATIONS
# ==============================================================================
with tab5:
    st.markdown("### 🛡️ **Dataset Scope & Transparent Analytical Limitations**")
    
    st.error(
        """
        #### 🚫 **Data Not Available in Source Dataset**
        To maintain strict academic and analytical integrity, the following data fields are explicitly declared as **NOT present** in the source dataset:
        1. **Customer Complaint Records**: No customer support tickets, call logs, or negative feedback entries exist.
        2. **Customer Refund Records**: No financial claims, compensation payouts, or cancellation fees are logged.
        3. **Promised Delivery Time / Official SLA**: No contractual SLA target was provided by the original food aggregator.
        4. **Rider Reassignment History**: No logs of re-dispatched riders or rejected delivery assignments exist.
        
        *These fields have NOT been fabricated or simulated.*
        """
    )
    
    st.markdown("#### **Operational Proxy Methodology**")
    st.write(
        """
        In food delivery operations management, excessive order duration is widely recognized as the primary upstream operational driver 
        of customer friction. Therefore, in this dashboard:
        - **Delivery delay exceeding the analytical SLA threshold (> 30 minutes)** is monitored strictly as an **operational proxy** for potential customer service risk.
        - This proxy should be interpreted as an operational stress indicator, not as actual verified customer dissatisfaction.
        """
    )
    
    st.markdown("#### **Summary of Methodological Assumptions**")
    methodology_table = pd.DataFrame([
        {
            "Analytical Dimension": "Analytical SLA Threshold",
            "Project Decision": f"{sla_threshold} Minutes",
            "Defensible Justification": "Aligned with industry 30m baseline and distribution 75th percentile (32m).",
            "Limitation": "Does not reflect actual restaurant-specific or distance-specific customer promises."
        },
        {
            "Analytical Dimension": "Peak Hour Definition",
            "Project Decision": "18:00 – 21:00 (Dinner)",
            "Defensible Justification": "Empirically accounts for >40% of volume and highest delay concentration.",
            "Limitation": "Excludes potential city-specific localized micro-peaks."
        },
        {
            "Analytical Dimension": "Distance Metric",
            "Project Decision": "Haversine Distance (km)",
            "Defensible Justification": "Calculated from non-zero latitude/longitude coordinates.",
            "Limitation": "Represents straight-line displacement rather than actual road routing distance."
        },
        {
            "Analytical Dimension": "Causal Claims",
            "Project Decision": "Strictly Observational",
            "Defensible Justification": "Phrased as 'associated with' or 'observed pattern'.",
            "Limitation": "Confounding factors (kitchen rush, weather, traffic) interact simultaneously."
        },
    ])
    st.table(methodology_table)


# ==============================================================================
# TAB 6: KEY INSIGHTS
# ==============================================================================
with tab6:
    st.markdown("### 💡 **Evidence-Based Operational Insights**")
    st.markdown("All findings below are derived directly from empirical statistics on the active dataset filter.")
    
    insights = generate_key_insights(filtered_df, sla_threshold)
    
    for i, ins in enumerate(insights, 1):
        st.markdown(
            f"""
            <div class='insight-card'>
                <div class='insight-title'>Insight {i}: {ins['title']}</div>
                <p><strong>Pattern:</strong> {ins['pattern']}</p>
                <p><strong>Evidence:</strong> <span style='color: #F8FAFC;'>{ins['evidence']}</span></p>
                <p><strong>Operational Meaning:</strong> {ins['operational_meaning']}</p>
                <p style='color: #94A3B8; font-size: 13px;'><em>⚠️ Limitation:</em> {ins['limitation']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
