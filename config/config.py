"""
PeakPulse — Food Delivery SLA Insights
Central Configuration Module

This module stores project-wide configurations, analytical parameters,
file paths, and visual theme tokens.
"""

from pathlib import Path

# ==============================================================================
# 1. DIRECTORY & FILE PATHS
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "Zomato Dataset.csv"
PROCESSED_DATA_PATH = BASE_DIR / "data" / "processed" / "cleaned_delivery_data.csv"
DB_PATH = BASE_DIR / "data" / "peakpulse.db"
SQL_QUERIES_PATH = BASE_DIR / "sql" / "queries.sql"

# Ensure required directories exist
(BASE_DIR / "data" / "raw").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "data" / "processed").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "sql").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "notebooks").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "src").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "dashboard").mkdir(parents=True, exist_ok=True)

# ==============================================================================
# 2. PROJECT-DEFINED ANALYTICAL SLA THRESHOLD
# ==============================================================================
# IMPORTANT NOTE:
# The source dataset does NOT contain a customer-promised delivery time or official SLA.
# Therefore, this SLA is an ANALYTICAL PROJECT BASELINE defined for operational evaluation.
#
# Empirical Distribution of Time_taken (min):
# - Minimum: 10 minutes
# - 25th Percentile (Q1): 19 minutes
# - Median (50th Percentile): 26 minutes
# - Mean: 26.29 minutes
# - 75th Percentile (Q3): 32 minutes
# - Maximum: 54 minutes
#
# Defensible Rationale for 30 minutes:
# 1. 30 minutes represents a standard operational food-delivery turnaround promise
#    in major metropolitan aggregators (e.g., Zomato, Swiggy, Uber Eats).
# 2. At 30 minutes, 29.84% (13,602 / 45,584) of orders exceed the threshold,
#    providing a meaningful operational variance to analyze delays across traffic,
#    weather, multi-orders, and peak hours.
# 3. Alternative operational baselines can also be evaluated:
#    - 32 minutes (exact 75th percentile / upper quartile: 24.71% violations)
#    - 35 minutes (conservative upper threshold: 17.56% violations)
DEFAULT_SLA_THRESHOLD_MINUTES = 30

# ==============================================================================
# 3. PEAK-HOUR DEFINITIONS
# ==============================================================================
# Empirical findings from order distribution:
# - Evening Dinner hours (17:00 to 23:00) contain >72% of all daily order volume.
# - Peak congestion & delay severity occurs between 18:00 and 21:00, where average
#   delivery time exceeds 31 minutes (compared to ~19-23 minutes during morning/afternoon).
# - A secondary lunch peak occurs between 12:00 and 14:00 (mean ~27 minutes).
PEAK_HOURS_DINNER = [18, 19, 20, 21]       # Primary Dinner Peak (highest volume + delay)
PEAK_HOURS_BROAD = [17, 18, 19, 20, 21, 22, 23] # Broad Evening Window
LUNCH_PEAK_HOURS = [12, 13]                 # Lunch Micro-Peak

# Default operational peak hours considered in analytical comparisons:
DEFAULT_PEAK_HOURS = PEAK_HOURS_DINNER

# ==============================================================================
# 4. DASHBOARD THEME & COLOR PALETTE (Matched with Figma UI)
# ==============================================================================
# Dark mode theme tokens
COLORS = {
    "bg_dark": "#0B0F19",          # Deep midnight canvas
    "card_bg": "#161F30",          # Elevated card surface
    "card_border": "#24324D",      # Subtle border
    "text_primary": "#F8FAFC",    # High contrast heading
    "text_secondary": "#94A3B8",  # Muted descriptive text
    "accent_crimson": "#FF4B4B",   # PeakPulse Primary Pulse (Violations/Alerts)
    "accent_blue": "#38BDF8",      # Volume / Informational
    "accent_amber": "#F59E0B",     # Warning / Medium traffic
    "accent_emerald": "#10B981",   # Healthy SLA / Low traffic
    "accent_purple": "#A855F7",    # Vehicle / Multi-delivery
}
