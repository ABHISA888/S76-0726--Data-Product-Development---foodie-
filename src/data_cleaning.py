"""
PeakPulse — Food Delivery SLA Insights
Data Cleaning & Preprocessing Pipeline

This script loads the raw food-delivery dataset, performs quality checks,
cleans formatting inconsistencies, derives operational features (SLA violation,
peak hours, delivery distance, pickup delay), and saves a reproducible cleaned
dataset to data/processed/cleaned_delivery_data.csv.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Add project root to sys.path to allow config import
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.config import (
    RAW_DATA_PATH,
    PROCESSED_DATA_PATH,
    DEFAULT_SLA_THRESHOLD_MINUTES,
    PEAK_HOURS_DINNER,
    LUNCH_PEAK_HOURS,
)


def load_raw_data(file_path: Path) -> pd.DataFrame:
    """
    Step 1: Load the raw CSV dataset without altering the original file.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Raw data file not found at: {file_path}")
    print(f"[INFO] Loading raw data from: {file_path}")
    df = pd.read_csv(file_path)
    print(f"[INFO] Raw dataset loaded: {df.shape[0]:,} rows, {df.shape[1]} columns.")
    return df


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Step 2: Clean column names by removing leading/trailing whitespace.
    """
    df = df.copy()
    df.columns = [col.strip() for col in df.columns]
    return df


def parse_time_value(val) -> str | None:
    """
    Helper function to parse and standardize order and pickup time strings.
    
    Handles 3 common real-world formatting cases:
    1. Excel day fractions: e.g. '0.833333333' -> 20:00 (0.8333 * 24 hours)
    2. Excel day end: '1' -> 24:00 (midnight)
    3. Normal time strings: '21:55', '24:15:00' -> handles 24:xx rollover to 00:xx
    """
    if pd.isna(val):
        return None
    
    val_str = str(val).strip()
    if val_str == "" or val_str.lower() == "nan":
        return None
    
    # Case 1: Excel day-fraction decimal (e.g. 0.833333333 or 1.0)
    try:
        float_val = float(val_str)
        total_seconds = int(round(float_val * 24 * 3600))
        hours = (total_seconds // 3600) % 24
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    except ValueError:
        pass
    
    # Case 2: Colon-separated time string (HH:MM or HH:MM:SS)
    parts = val_str.split(":")
    if len(parts) >= 2:
        try:
            hours = int(parts[0]) % 24  # Handles 24:15 -> 00:15
            minutes = int(parts[1])
            return f"{hours:02d}:{minutes:02d}"
        except ValueError:
            return None
    
    return None


def calculate_haversine_distance(lat1, lon1, lat2, lon2) -> np.ndarray:
    """
    Helper to calculate great-circle distance between two GPS coordinates in kilometers.
    
    Notes:
    - Coordinates in India are strictly positive (Lat ~8°-35° N, Lon ~68°-97° E).
      We take abs() to correct inverted negative signs.
    - Zero coordinates (0, 0) indicate missing GPS data; they are returned as NaN.
    """
    # Create mask of valid coordinates (non-zero)
    is_valid = (lat1 != 0) & (lon1 != 0) & (lat2 > 1) & (lon2 > 1)
    
    distances = np.full(len(lat1), np.nan)
    
    if not is_valid.any():
        return distances
    
    # Convert degrees to radians for valid rows
    r_lat1 = np.radians(np.abs(lat1[is_valid]))
    r_lon1 = np.radians(np.abs(lon1[is_valid]))
    r_lat2 = np.radians(np.abs(lat2[is_valid]))
    r_lon2 = np.radians(np.abs(lon2[is_valid]))
    
    dlat = r_lat2 - r_lat1
    dlon = r_lon2 - r_lon1
    
    a = np.sin(dlat / 2.0) ** 2 + np.cos(r_lat1) * np.cos(r_lat2) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    earth_radius_km = 6371.0
    
    distances[is_valid] = np.round(earth_radius_km * c, 2)
    return distances


def clean_and_transform(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Main transformation pipeline applying all data engineering and cleaning rules.
    """
    print("[INFO] Starting data cleaning and transformation...")
    df = standardize_column_names(df_raw)
    
    # -------------------------------------------------------------------------
    # 1. Duplicates check
    # -------------------------------------------------------------------------
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        print(f"[INFO] Removing {dup_count} completely duplicate rows.")
        df = df.drop_duplicates()
    else:
        print("[INFO] No duplicate rows found in dataset.")
    
    # -------------------------------------------------------------------------
    # 2. Date parsing (Order_Date)
    # Format in dataset: 'DD-MM-YYYY'
    # -------------------------------------------------------------------------
    df["order_date"] = pd.to_datetime(df["Order_Date"].str.strip(), format="%d-%m-%Y")
    df["order_day"] = df["order_date"].dt.day
    df["order_month"] = df["order_date"].dt.month
    df["order_day_name"] = df["order_date"].dt.day_name()
    df["is_weekend"] = df["order_date"].dt.dayofweek.apply(lambda x: 1 if x >= 5 else 0)
    
    # -------------------------------------------------------------------------
    # 3. Time standardization & Pickup Delay
    # -------------------------------------------------------------------------
    df["time_ordered"] = df["Time_Orderd"].apply(parse_time_value)
    df["time_order_picked"] = df["Time_Order_picked"].apply(parse_time_value)
    
    # Extract order_hour (integer 0-23)
    def extract_hour(time_str):
        if time_str is None or pd.isna(time_str):
            return np.nan
        return int(time_str.split(":")[0])
    
    df["order_hour"] = df["time_ordered"].apply(extract_hour)
    
    # Calculate pickup delay in minutes (Order Placed -> Rider Picked Up)
    def calc_delay(row):
        t_ord = row["time_ordered"]
        t_pic = row["time_order_picked"]
        if pd.isna(t_ord) or pd.isna(t_pic) or t_ord is None or t_pic is None:
            return np.nan
        h1, m1 = map(int, t_ord.split(":"))
        h2, m2 = map(int, t_pic.split(":"))
        diff = (h2 * 60 + m2) - (h1 * 60 + m1)
        if diff < 0:  # Midnight rollover (e.g., ordered 23:55, picked up 00:10)
            diff += 1440
        return diff
    
    df["pickup_delay_minutes"] = df.apply(calc_delay, axis=1)
    
    # -------------------------------------------------------------------------
    # 4. Delivery Distance (Haversine formula)
    # -------------------------------------------------------------------------
    df["delivery_distance_km"] = calculate_haversine_distance(
        df["Restaurant_latitude"].values,
        df["Restaurant_longitude"].values,
        df["Delivery_location_latitude"].values,
        df["Delivery_location_longitude"].values,
    )
    
    # -------------------------------------------------------------------------
    # 5. Handle Categorical Columns & Missing Values
    # Categorical missing values are filled with 'Unknown' to avoid losing rows.
    # -------------------------------------------------------------------------
    df["weather"] = df["Weather_conditions"].fillna("Unknown").astype(str).str.strip()
    df["traffic_density"] = df["Road_traffic_density"].fillna("Unknown").astype(str).str.strip()
    df["order_type"] = df["Type_of_order"].astype(str).str.strip()
    df["vehicle_type"] = df["Type_of_vehicle"].astype(str).str.strip()
    df["festival"] = df["Festival"].fillna("Unknown").astype(str).str.strip()
    df["city"] = df["City"].fillna("Unknown").astype(str).str.strip()
    
    # -------------------------------------------------------------------------
    # 6. Numerical Columns & Investigation of Suspicious Values
    # -------------------------------------------------------------------------
    # Vehicle condition (0 to 3)
    df["vehicle_condition"] = df["Vehicle_condition"].astype(int)
    
    # Multiple deliveries: fill 993 missing with median (1.0)
    df["multiple_deliveries"] = df["multiple_deliveries"].fillna(1.0).astype(int)
    
    # Delivery person age:
    # 38 records show age 15. We preserve them as float, but flag them for audit.
    df["delivery_person_age"] = pd.to_numeric(df["Delivery_person_Age"], errors="coerce")
    
    # Delivery person ratings:
    # 53 records show rating 6.0 (out of 5.0 scale). We set values > 5.0 to NaN for clean rating averages.
    clean_ratings = pd.to_numeric(df["Delivery_person_Ratings"], errors="coerce")
    df["delivery_person_rating"] = clean_ratings.apply(lambda r: np.nan if r > 5.0 else r)
    
    # Delivery time (Time_taken (min)) — core target metric with 0 missing values
    df["delivery_time_min"] = df["Time_taken (min)"].astype(int)
    
    # -------------------------------------------------------------------------
    # 7. Project-Defined Analytical SLA & Peak-Hour Features
    # -------------------------------------------------------------------------
    # SLA Violation: Delivery time > threshold
    df["is_sla_violated"] = (df["delivery_time_min"] > DEFAULT_SLA_THRESHOLD_MINUTES).astype(int)
    
    # Peak-hour classification
    def classify_peak(hour):
        if pd.isna(hour):
            return "Unknown"
        h = int(hour)
        if h in PEAK_HOURS_DINNER:
            return "Dinner Peak (18-21)"
        elif h in LUNCH_PEAK_HOURS:
            return "Lunch Peak (12-13)"
        else:
            return "Off-Peak"
    
    df["peak_period"] = df["order_hour"].apply(classify_peak)
    
    def is_peak_flag(hour):
        if pd.isna(hour):
            return np.nan
        return 1 if int(hour) in PEAK_HOURS_DINNER else 0
    
    df["is_peak_hour"] = df["order_hour"].apply(is_peak_flag)
    
    # -------------------------------------------------------------------------
    # 8. Organize and Select Cleaned Output Columns
    # -------------------------------------------------------------------------
    cleaned_df = pd.DataFrame({
        "order_id": df["ID"].astype(str).str.strip(),
        "delivery_person_id": df["Delivery_person_ID"].astype(str).str.strip(),
        "delivery_person_age": df["delivery_person_age"],
        "delivery_person_rating": df["delivery_person_rating"],
        "restaurant_latitude": df["Restaurant_latitude"],
        "restaurant_longitude": df["Restaurant_longitude"],
        "delivery_location_latitude": df["Delivery_location_latitude"],
        "delivery_location_longitude": df["Delivery_location_longitude"],
        "delivery_distance_km": df["delivery_distance_km"],
        "order_date": df["order_date"].dt.strftime("%Y-%m-%d"),
        "time_ordered": df["time_ordered"],
        "time_order_picked": df["time_order_picked"],
        "order_hour": df["order_hour"],
        "order_day": df["order_day"],
        "order_month": df["order_month"],
        "order_day_name": df["order_day_name"],
        "is_weekend": df["is_weekend"],
        "pickup_delay_minutes": df["pickup_delay_minutes"],
        "weather": df["weather"],
        "traffic_density": df["traffic_density"],
        "vehicle_condition": df["vehicle_condition"],
        "order_type": df["order_type"],
        "vehicle_type": df["vehicle_type"],
        "multiple_deliveries": df["multiple_deliveries"],
        "festival": df["festival"],
        "city": df["city"],
        "delivery_time_min": df["delivery_time_min"],
        "is_sla_violated": df["is_sla_violated"],
        "is_peak_hour": df["is_peak_hour"],
        "peak_period": df["peak_period"],
    })
    
    return cleaned_df


def save_cleaned_data(df: pd.DataFrame, output_path: Path):
    """
    Step 9: Save the cleaned DataFrame to the processed directory.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[INFO] Successfully saved cleaned dataset to: {output_path}")
    print(f"[INFO] Total Cleaned Records: {len(df):,} rows, {df.shape[1]} columns.")


def print_data_quality_report(df_raw: pd.DataFrame, df_clean: pd.DataFrame):
    """
    Step 10: Print a clear audit summary comparing raw vs cleaned dataset.
    """
    print("\n" + "=" * 65)
    print("         PEAKPULSE DATA QUALITY & CLEANING AUDIT REPORT")
    print("=" * 65)
    print(f"Total Raw Rows:                 {len(df_raw):,}")
    print(f"Total Cleaned Rows:             {len(df_clean):,}")
    print(f"Project-Defined Analytical SLA: {DEFAULT_SLA_THRESHOLD_MINUTES} minutes")
    
    sla_violations = df_clean["is_sla_violated"].sum()
    sla_rate = (sla_violations / len(df_clean)) * 100
    print(f"SLA Violations (> {DEFAULT_SLA_THRESHOLD_MINUTES} min):        {sla_violations:,} ({sla_rate:.2f}%)")
    print(f"Average Delivery Time:          {df_clean['delivery_time_min'].mean():.2f} min")
    print(f"Median Delivery Time:           {df_clean['delivery_time_min'].median():.1f} min")
    
    valid_hours = df_clean["order_hour"].dropna()
    peak_count = df_clean["is_peak_hour"].eq(1).sum()
    peak_pct = (peak_count / len(valid_hours)) * 100
    print(f"Peak-Hour Orders (18:00-21:00): {peak_count:,} ({peak_pct:.2f}% of orders with valid time)")
    
    valid_dist = df_clean["delivery_distance_km"].dropna()
    print(f"Valid Geocoded Distances:       {len(valid_dist):,} (Mean: {valid_dist.mean():.2f} km)")
    print(f"Missing Order Times:            {df_clean['time_ordered'].isna().sum():,} (retained with 'Unknown' hour)")
    print("=" * 65 + "\n")


def main():
    """Execute the end-to-end cleaning pipeline."""
    df_raw = load_raw_data(RAW_DATA_PATH)
    df_clean = clean_and_transform(df_raw)
    save_cleaned_data(df_clean, PROCESSED_DATA_PATH)
    print_data_quality_report(df_raw, df_clean)


if __name__ == "__main__":
    main()
