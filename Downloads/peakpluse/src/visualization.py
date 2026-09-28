"""
PeakPulse — Food Delivery SLA Insights
Visualization Module

Generates interactive, publication-quality Plotly charts matching the
PeakPulse dark-mode Figma UI design.
"""

from typing import Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Figma Dark Mode Theme Configuration
THEME = {
    "paper_bgcolor": "#0B0F19",
    "plot_bgcolor": "#161F30",
    "font_family": "Inter, Roboto, sans-serif",
    "font_color": "#F8FAFC",
    "muted_color": "#94A3B8",
    "grid_color": "#24324D",
    "crimson": "#FF4B4B",
    "blue": "#38BDF8",
    "amber": "#F59E0B",
    "emerald": "#10B981",
    "purple": "#A855F7",
}


def apply_dark_theme(fig: go.Figure, title: str = "", height: int = 400) -> go.Figure:
    """Apply consistent Figma dark-theme styling to a Plotly figure."""
    fig.update_layout(
        title={
            "text": f"<b>{title}</b>",
            "font": {"size": 16, "color": THEME["font_color"]},
            "x": 0.02,
            "xanchor": "left",
        },
        paper_bgcolor=THEME["paper_bgcolor"],
        plot_bgcolor=THEME["plot_bgcolor"],
        font=dict(family=THEME["font_family"], color=THEME["font_color"]),
        height=height,
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(
            showgrid=True,
            gridcolor=THEME["grid_color"],
            linecolor=THEME["grid_color"],
            tickfont=dict(color=THEME["muted_color"]),
            title_font=dict(color=THEME["muted_color"]),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=THEME["grid_color"],
            linecolor=THEME["grid_color"],
            tickfont=dict(color=THEME["muted_color"]),
            title_font=dict(color=THEME["muted_color"]),
        ),
        legend=dict(
            font=dict(color=THEME["font_color"]),
            bgcolor="rgba(22, 31, 48, 0.7)",
            bordercolor=THEME["grid_color"],
        ),
    )
    return fig


def plot_hourly_trend(hourly_df: pd.DataFrame) -> go.Figure:
    """
    Dual-axis combo chart:
    - Primary Y-axis: Order Volume (Bar Chart, Neon Blue)
    - Secondary Y-axis: SLA Violation Rate % (Line Chart, Crimson Pulse)
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # 1. Bar: Order Volume
    fig.add_trace(
        go.Bar(
            x=hourly_df["order_hour"],
            y=hourly_df["order_count"],
            name="Order Volume",
            marker_color=THEME["blue"],
            opacity=0.85,
            hovertemplate="Hour %{x}:00<br>Orders: %{y:,}<extra></extra>",
        ),
        secondary_y=False,
    )
    
    # 2. Line: SLA Violation Rate
    fig.add_trace(
        go.Scatter(
            x=hourly_df["order_hour"],
            y=hourly_df["sla_violation_rate"],
            name="SLA Violation Rate (%)",
            mode="lines+markers",
            line=dict(color=THEME["crimson"], width=3),
            marker=dict(size=7, color=THEME["crimson"]),
            hovertemplate="Hour %{x}:00<br>SLA Violation: %{y:.1f}%<extra></extra>",
        ),
        secondary_y=True,
    )
    
    # Add peak window highlight band (18:00 - 21:00)
    fig.add_vrect(
        x0=17.5,
        x1=21.5,
        fillcolor="rgba(255, 75, 75, 0.12)",
        layer="below",
        line_width=1,
        line_dash="dot",
        line_color=THEME["crimson"],
        annotation_text="Dinner Peak (18-21)",
        annotation_position="top left",
        annotation_font=dict(color=THEME["crimson"], size=11),
    )

    fig = apply_dark_theme(fig, "Hourly Order Volume & SLA Violation Rate Trend", height=420)
    fig.update_xaxes(title_text="Hour of Day (24-Hour Clock)", dtick=1)
    fig.update_yaxes(title_text="Order Volume", secondary_y=False, showgrid=True)
    fig.update_yaxes(title_text="SLA Violation Rate (%)", secondary_y=True, showgrid=False, range=[0, 100])
    return fig


def plot_traffic_performance(traffic_df: pd.DataFrame) -> go.Figure:
    """
    Bar chart showing Average Delivery Time and SLA Violation Rate across Traffic Conditions.
    """
    traffic_order = ["Low", "Medium", "High", "Jam", "Unknown"]
    df_sorted = traffic_df.set_index("traffic_density").reindex([c for c in traffic_order if c in traffic_df["traffic_density"].values]).reset_index()
    
    # Map colors from emerald (low) to crimson (jam)
    color_map = {
        "Low": THEME["emerald"],
        "Medium": THEME["blue"],
        "High": THEME["amber"],
        "Jam": THEME["crimson"],
        "Unknown": THEME["muted_color"],
    }
    bar_colors = [color_map.get(t, THEME["blue"]) for t in df_sorted["traffic_density"]]

    fig = go.Figure(
        data=[
            go.Bar(
                x=df_sorted["traffic_density"],
                y=df_sorted["avg_delivery_time"],
                text=[f"{v:.1f} min<br>({r:.1f}% viol.)" for v, r in zip(df_sorted["avg_delivery_time"], df_sorted["sla_violation_rate"])],
                textposition="auto",
                marker_color=bar_colors,
                hovertemplate="Traffic: %{x}<br>Avg Time: %{y:.1f} min<extra></extra>",
            )
        ]
    )
    fig = apply_dark_theme(fig, "Average Delivery Time by Traffic Density", height=380)
    fig.update_xaxes(title_text="Traffic Density Level")
    fig.update_yaxes(title_text="Average Delivery Time (minutes)", range=[0, 40])
    return fig


def plot_multi_delivery_impact(multi_df: pd.DataFrame) -> go.Figure:
    """
    Bar chart demonstrating multi-order batching impact on SLA violation and turnaround.
    """
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(
            x=[f"{int(x)} Drops" for x in multi_df["multiple_deliveries"]],
            y=multi_df["avg_delivery_time"],
            name="Avg Delivery Time (min)",
            marker_color=THEME["purple"],
            text=[f"{v:.1f} min" for v in multi_df["avg_delivery_time"]],
            textposition="outside",
            hovertemplate="Batched Orders: %{x}<br>Avg Time: %{y:.1f} min<extra></extra>",
        )
    )
    
    fig = apply_dark_theme(fig, "Delivery Time vs Number of Batched Deliveries", height=380)
    fig.update_xaxes(title_text="Stacked Delivery Count")
    fig.update_yaxes(title_text="Average Delivery Time (minutes)", range=[0, 60])
    return fig


def plot_city_comparison(city_df: pd.DataFrame) -> go.Figure:
    """
    Bar chart comparing delivery times across city tiers.
    """
    fig = go.Figure(
        data=[
            go.Bar(
                x=city_df["city"],
                y=city_df["avg_delivery_time"],
                marker_color=[THEME["blue"], THEME["emerald"], THEME["crimson"], THEME["muted_color"]],
                text=[f"{t:.1f} min" for t in city_df["avg_delivery_time"]],
                textposition="outside",
                hovertemplate="City: %{x}<br>Avg Time: %{y:.1f} min<extra></extra>",
            )
        ]
    )
    fig = apply_dark_theme(fig, "Average Delivery Turnaround by City Tier", height=380)
    fig.update_xaxes(title_text="City Classification")
    fig.update_yaxes(title_text="Average Delivery Time (minutes)", range=[0, 60])
    return fig


def plot_delivery_time_distribution(df: pd.DataFrame, sla_threshold: int = 30) -> go.Figure:
    """
    Histogram showing distribution of Delivery Time (min) with median and SLA threshold cutoffs.
    """
    fig = go.Figure()
    
    # Histogram of times
    fig.add_trace(
        go.Histogram(
            x=df["delivery_time_min"],
            nbinsx=45,
            marker_color=THEME["blue"],
            opacity=0.75,
            name="Delivery Orders",
            hovertemplate="Delivery Time: %{x} min<br>Count: %{y:,}<extra></extra>",
        )
    )
    
    median_val = df["delivery_time_min"].median()
    
    # SLA threshold line
    fig.add_vline(
        x=sla_threshold,
        line_width=3,
        line_dash="dash",
        line_color=THEME["crimson"],
        annotation_text=f"SLA Threshold ({sla_threshold}m)",
        annotation_position="top right",
        annotation_font=dict(color=THEME["crimson"], size=12),
    )
    
    # Median line
    fig.add_vline(
        x=median_val,
        line_width=2,
        line_dash="dot",
        line_color=THEME["emerald"],
        annotation_text=f"Median ({median_val:.0f}m)",
        annotation_position="top left",
        annotation_font=dict(color=THEME["emerald"], size=12),
    )

    fig = apply_dark_theme(fig, "Delivery Time Distribution & SLA Threshold Boundary", height=380)
    fig.update_xaxes(title_text="Delivery Time (minutes)")
    fig.update_yaxes(title_text="Order Frequency")
    return fig


def plot_weather_performance(weather_df: pd.DataFrame) -> go.Figure:
    """
    Bar chart showing SLA performance across weather conditions.
    """
    fig = go.Figure(
        data=[
            go.Bar(
                x=weather_df["weather"],
                y=weather_df["avg_delivery_time"],
                marker_color=THEME["blue"],
                text=[f"{v:.1f} m" for v in weather_df["avg_delivery_time"]],
                textposition="auto",
                hovertemplate="Weather: %{x}<br>Avg Time: %{y:.1f} min<extra></extra>",
            )
        ]
    )
    fig = apply_dark_theme(fig, "Average Delivery Time by Weather Condition", height=380)
    fig.update_xaxes(title_text="Weather Condition")
    fig.update_yaxes(title_text="Average Delivery Time (minutes)", range=[0, 35])
    return fig
