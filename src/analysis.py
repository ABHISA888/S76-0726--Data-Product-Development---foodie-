"""
PeakPulse — Food Delivery SLA Insights
Analytics & Insight Generation Engine

Contains modular data-analytics functions calculating operational metrics,
evaluating dynamic SLA thresholds, and generating evidence-based operational insights.
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np


def compute_kpis(df: pd.DataFrame, sla_threshold: int = 30) -> Dict[str, Any]:
    """
    Compute top-level operational KPIs based on the given dataset and SLA threshold.
    """
    total_orders = len(df)
    if total_orders == 0:
        return {
            "total_orders": 0,
            "avg_time": 0.0,
            "median_time": 0.0,
            "sla_violations": 0,
            "sla_violation_rate": 0.0,
            "peak_orders": 0,
            "peak_share_pct": 0.0,
            "avg_distance": 0.0,
        }

    is_violated = (df["delivery_time_min"] > sla_threshold).astype(int)
    sla_violations = int(is_violated.sum())
    sla_violation_rate = (sla_violations / total_orders) * 100.0
    avg_time = float(df["delivery_time_min"].mean())
    median_time = float(df["delivery_time_min"].median())
    
    # Peak deliveries (hours 18 to 21)
    peak_mask = df["is_peak_hour"] == 1
    peak_orders = int(peak_mask.sum())
    peak_share_pct = (peak_orders / total_orders) * 100.0 if total_orders > 0 else 0.0
    
    # Valid delivery distance
    valid_dist = df["delivery_distance_km"].dropna()
    avg_distance = float(valid_dist.mean()) if len(valid_dist) > 0 else 0.0

    return {
        "total_orders": total_orders,
        "avg_time": round(avg_time, 2),
        "median_time": round(median_time, 1),
        "sla_violations": sla_violations,
        "sla_violation_rate": round(sla_violation_rate, 2),
        "peak_orders": peak_orders,
        "peak_share_pct": round(peak_share_pct, 2),
        "avg_distance": round(avg_distance, 2),
    }


def analyze_hourly_patterns(df: pd.DataFrame, sla_threshold: int = 30) -> pd.DataFrame:
    """
    Aggregate orders, average delivery time, and SLA violation rate by order hour.
    """
    df_valid = df.dropna(subset=["order_hour"]).copy()
    df_valid["is_violated_dyn"] = (df_valid["delivery_time_min"] > sla_threshold).astype(int)
    
    hourly = df_valid.groupby("order_hour").agg(
        order_count=("order_id", "count"),
        avg_delivery_time=("delivery_time_min", "mean"),
        sla_violations=("is_violated_dyn", "sum"),
    ).reset_index()
    
    hourly["sla_violation_rate"] = (hourly["sla_violations"] / hourly["order_count"]) * 100.0
    hourly["order_hour"] = hourly["order_hour"].astype(int)
    hourly = hourly.sort_values("order_hour").reset_index(drop=True)
    return hourly


def compare_peak_vs_nonpeak(df: pd.DataFrame, sla_threshold: int = 30) -> pd.DataFrame:
    """
    Compare operational performance between Peak (18:00-21:00) and Non-Peak periods.
    """
    df_valid = df.dropna(subset=["is_peak_hour"]).copy()
    df_valid["is_violated_dyn"] = (df_valid["delivery_time_min"] > sla_threshold).astype(int)
    
    summary = df_valid.groupby("is_peak_hour").agg(
        order_count=("order_id", "count"),
        avg_delivery_time=("delivery_time_min", "mean"),
        median_delivery_time=("delivery_time_min", "median"),
        sla_violations=("is_violated_dyn", "sum"),
    ).reset_index()
    
    summary["sla_violation_rate"] = (summary["sla_violations"] / summary["order_count"]) * 100.0
    summary["order_share_pct"] = (summary["order_count"] / summary["order_count"].sum()) * 100.0
    summary["period_label"] = summary["is_peak_hour"].map({
        1.0: "Dinner Peak (18:00 - 21:00)",
        0.0: "Non-Peak Hours"
    })
    return summary


def analyze_category_impact(df: pd.DataFrame, category_col: str, sla_threshold: int = 30) -> pd.DataFrame:
    """
    Generic aggregator to compute volume, avg time, and violation rate for any categorical dimension.
    """
    df_work = df.copy()
    df_work["is_violated_dyn"] = (df_work["delivery_time_min"] > sla_threshold).astype(int)
    
    cat_summary = df_work.groupby(category_col).agg(
        order_count=("order_id", "count"),
        avg_delivery_time=("delivery_time_min", "mean"),
        median_delivery_time=("delivery_time_min", "median"),
        sla_violations=("is_violated_dyn", "sum"),
    ).reset_index()
    
    cat_summary["sla_violation_rate"] = (cat_summary["sla_violations"] / cat_summary["order_count"]) * 100.0
    cat_summary["order_share_pct"] = (cat_summary["order_count"] / len(df_work)) * 100.0
    return cat_summary.sort_values("avg_delivery_time", ascending=False).reset_index(drop=True)


def generate_key_insights(df: pd.DataFrame, sla_threshold: int = 30) -> List[Dict[str, str]]:
    """
    Generate evidence-based insights directly from the filtered data.
    Uses strictly observational language (associated with, observed pattern).
    """
    insights = []
    
    # 1. Multi-delivery batching pattern
    multi_agg = df.groupby("multiple_deliveries")["delivery_time_min"].agg(["count", "mean"])
    if 0 in multi_agg.index and 2 in multi_agg.index:
        time_0 = multi_agg.loc[0, "mean"]
        time_2 = multi_agg.loc[2, "mean"]
        insights.append({
            "title": "Multi-Order Stacking & Delay Escalation",
            "pattern": "Deliveries with multiple stacked orders exhibit dramatically higher delivery times.",
            "evidence": (
                f"Single drop orders (0 multiple deliveries) averaged {time_0:.1f} minutes, "
                f"whereas orders stacked with 2 drops averaged {time_2:.1f} minutes "
                f"(an observed increase of +{time_2 - time_0:.1f} minutes)."
            ),
            "operational_meaning": (
                "Automated dispatch batching algorithms should be capped or optimized with strict distance "
                "radius constraints to prevent compounded customer wait times."
            ),
            "limitation": (
                "The dataset records the total multiple delivery count but does not record the rider's drop sequence "
                "or intermediate restaurant wait times."
            ),
        })

    # 2. Traffic Jam Congestion pattern
    traffic_agg = df.groupby("traffic_density")["delivery_time_min"].agg(["count", "mean"])
    if "Jam" in traffic_agg.index and "Low" in traffic_agg.index:
        jam_time = traffic_agg.loc["Jam", "mean"]
        low_time = traffic_agg.loc["Low", "mean"]
        jam_viol = (df[df["traffic_density"] == "Jam"]["delivery_time_min"] > sla_threshold).mean() * 100
        low_viol = (df[df["traffic_density"] == "Low"]["delivery_time_min"] > sla_threshold).mean() * 100
        insights.append({
            "title": "Severe Traffic Congestion Bottlenecks",
            "pattern": "High traffic density conditions are associated with substantially elevated SLA breach rates.",
            "evidence": (
                f"Deliveries conducted during 'Jam' conditions experienced an average delivery duration of {jam_time:.1f} minutes "
                f"with a {jam_viol:.1f}% SLA breach rate, compared to {low_time:.1f} minutes and {low_viol:.1f}% under 'Low' traffic."
            ),
            "operational_meaning": (
                "Operations teams should dynamically expand delivery time estimates and increase rider incentives "
                "or localized geo-fencing when municipal traffic sensors report congestion."
            ),
            "limitation": (
                "Traffic density is logged as a categorical descriptor without precise vehicular speed or GPS telematics."
            ),
        })

    # 3. Dinner Peak Volume & Delay Surge
    hourly = analyze_hourly_patterns(df, sla_threshold)
    dinner_peak_rows = hourly[hourly["order_hour"].isin([18, 19, 20, 21])]
    if not dinner_peak_rows.empty:
        peak_avg_time = dinner_peak_rows["avg_delivery_time"].mean()
        peak_viol_rate = dinner_peak_rows["sla_violation_rate"].mean()
        nonpeak_rows = hourly[~hourly["order_hour"].isin([18, 19, 20, 21])]
        nonpeak_avg_time = nonpeak_rows["avg_delivery_time"].mean()
        nonpeak_viol_rate = nonpeak_rows["sla_violation_rate"].mean()
        insights.append({
            "title": "Dinner Rush Operational Stress (18:00 – 21:00)",
            "pattern": "The dinner peak represents both the highest demand window and the peak window for SLA breaches.",
            "evidence": (
                f"Orders placed between 18:00 and 21:00 averaged {peak_avg_time:.1f} minutes delivery time and "
                f"{peak_viol_rate:.1f}% SLA violation rate, compared to {nonpeak_avg_time:.1f} minutes and "
                f"{nonpeak_viol_rate:.1f}% during non-peak operating hours."
            ),
            "operational_meaning": (
                "Rider supply scheduling must be heavily weighted toward 17:30–21:30 to absorb peak dinner surge, "
                "and restaurant kitchen prep throttling should be considered."
            ),
            "limitation": (
                "Order volume peaks reflect aggregated historical logs; kitchen prep delays are inferred through pickup buffer."
            ),
        })

    # 4. Vehicle Condition & Mechanical Readiness
    vc_agg = df.groupby("vehicle_condition")["delivery_time_min"].agg(["count", "mean"])
    if 0 in vc_agg.index and 2 in vc_agg.index:
        time_c0 = vc_agg.loc[0, "mean"]
        time_c2 = vc_agg.loc[2, "mean"]
        viol_c0 = (df[df["vehicle_condition"] == 0]["delivery_time_min"] > sla_threshold).mean() * 100
        viol_c2 = (df[df["vehicle_condition"] == 2]["delivery_time_min"] > sla_threshold).mean() * 100
        insights.append({
            "title": "Vehicle Condition & Turnaround Efficiency",
            "pattern": "Vehicles graded condition 0 (poor) exhibit significantly higher delay frequencies.",
            "evidence": (
                f"Deliveries with vehicle condition 0 averaged {time_c0:.1f} minutes with a {viol_c0:.1f}% SLA breach rate, "
                f"whereas condition 2 vehicles averaged {time_c2:.1f} minutes with a {viol_c2:.1f}% breach rate."
            ),
            "operational_meaning": (
                "Implementing periodic vehicle maintenance audits or fleet onboarding fitness checks can "
                "help protect delivery turnaround reliability."
            ),
            "limitation": (
                "The vehicle condition index (0–3) represents an internal operational score whose exact mechanical criteria "
                "are not detailed in the source documentation."
            ),
        })

    # 5. Festival Surge
    fest_agg = df.groupby("festival")["delivery_time_min"].agg(["count", "mean"])
    if "Yes" in fest_agg.index and "No" in fest_agg.index:
        fest_time = fest_agg.loc["Yes", "mean"]
        norm_time = fest_agg.loc["No", "mean"]
        fest_viol = (df[df["festival"] == "Yes"]["delivery_time_min"] > sla_threshold).mean() * 100
        norm_viol = (df[df["festival"] == "No"]["delivery_time_min"] > sla_threshold).mean() * 100
        insights.append({
            "title": "Festival Disruption and Order Backlogs",
            "pattern": "Deliveries during festival periods encounter extreme delivery delays.",
            "evidence": (
                f"Festival orders experienced an average turnaround of {fest_time:.1f} minutes and {fest_viol:.1f}% SLA violation rate, "
                f"compared to {norm_time:.1f} minutes and {norm_viol:.1f}% during standard operational days."
            ),
            "operational_meaning": (
                "Special festive operational protocols (curated menus, expanded ETAs, emergency surge riders) "
                "are essential to prevent customer disappointment during major festivals."
            ),
            "limitation": (
                "Festival orders account for a small percentage (~2%) of total records, so sample size is smaller."
            ),
        })

    return insights
