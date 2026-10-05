# PeakPulse — Food Delivery SLA Insights

An internal operations analytics product and dashboard built to detect delivery turnaround bottlenecks, evaluate SLA violations, and uncover operational patterns across peak hours, weather, traffic, and multi-order batching.

---

## 1. Project Title
**PeakPulse — Food Delivery SLA Insights**  
*Operations Analytics Dashboard for Service-Level Agreement (SLA) Monitoring & Peak-Hour Bottleneck Detection*

---

## 2. Problem Statement
On-demand food delivery platforms operate in time-critical environments where delivery delays degrade customer trust, escalate driver churn, and harm restaurant partnerships. Operations managers need clear, data-driven visibility into:
1. When delivery delays concentrate throughout the day (peak vs. off-peak hours).
2. Which external conditions (traffic congestion, severe weather) are associated with prolonged turnarounds.
3. How dispatch decisions (e.g., stacking multiple orders onto a single courier) impact delivery duration.
4. How operational thresholds (Service Level Agreements) perform across different operational scenarios.

**PeakPulse** provides an end-to-end data pipeline, SQL analytical suite, and interactive Streamlit operations dashboard to answer these critical operational questions.

---

## 3. Target Users
- **Operations Managers & City Leads:** Monitoring daily delivery compliance and identifying city-level delivery bottlenecks.
- **Dispatch & Logistics Engineers:** Evaluating the impact of multi-order stacking and delivery radius constraints.
- **Fleet & Rider Experience Coordinators:** Tracking rider performance distributions, vehicle fitness patterns, and scheduling shifts according to peak demand curves.

---

## 4. Objectives
- **Build a Reproducible Data Pipeline:** Clean and transform 45,584 raw delivery logs without data loss or silent modifications.
- **Establish a Defensible Analytical SLA:** Define an operational SLA baseline grounded in empirical distribution analysis.
- **Empirical Peak-Hour Definition:** Identify peak operating periods based on volume and delay concentration.
- **Execute SQL Operational Analysis:** Provide beginner-friendly, structured SQL queries answering core business questions.
- **Interactive Operations Dashboard:** Build a responsive Streamlit application featuring KPI tracking, dual-axis peak trends, category breakdowns, and dynamic SLA threshold simulations.
- **Transparent Data Limitations:** Explicitly declare dataset boundaries (no customer complaints, no refunds, observational claims only).

---

## 5. Dataset Summary
- **Source:** Food delivery operational dataset (`data/raw/Zomato Dataset.csv`).
- **Total Records:** 45,584 orders across 20 raw attributes.
- **Temporal Coverage:** February 11, 2022 to April 06, 2022.
- **Key Attributes:**
  - `ID`: Unique order identifier.
  - `Delivery_person_ID`: Unique courier identifier (1,320 couriers).
  - `Delivery_person_Age` & `Delivery_person_Ratings`: Rider demographic & performance rating.
  - `Restaurant_latitude/longitude` & `Delivery_location_latitude/longitude`: Geocoordinates.
  - `Order_Date`, `Time_Orderd`, `Time_Order_picked`: Order lifecycle timestamps.
  - `Weather_conditions`: Atmospheric conditions (`Sunny`, `Cloudy`, `Fog`, `Stormy`, `Sandstorms`, `Windy`).
  - `Road_traffic_density`: Traffic conditions (`Low`, `Medium`, `High`, `Jam`).
  - `multiple_deliveries`: Number of stacked orders assigned to the rider (`0`, `1`, `2`, `3`).
  - `Vehicle_condition`: Fleet mechanical rating (`0` to `3`).
  - `Type_of_vehicle`: Mode of transport (`motorcycle`, `scooter`, `electric_scooter`, `bicycle`).
  - `City`: Urban categorization (`Metropolitian`, `Urban`, `Semi-Urban`).
  - `Time_taken (min)`: Total delivery duration from order placement to delivery (target variable).

---

## 6. Dataset Limitations
To preserve academic and analytical honesty, the following constraints are documented:
1. **No Promised Delivery Time:** The source dataset does not log the dynamic ETA shown to customers when ordering.
2. **No Customer Complaints:** No customer service tickets, dispute records, or call logs exist.
3. **No Refund or Cancellation Records:** Financial compensation and order cancellation data are not present.
4. **No Rider Reassignment History:** The data does not record whether an order was declined or reassigned across multiple couriers.
5. **Observational Bounds:** All analyses reflect observational associations (e.g., "condition X is associated with higher delivery durations"), not causal relationships.

---

## 7. Data Pipeline Architecture

```
Raw CSV (data/raw/Zomato Dataset.csv)
       │
       ▼
Data Cleaning & Feature Engineering (src/data_cleaning.py)
  ├── Column whitespace trimming
  ├── Excel decimal time & 24:xx rollover parsing
  ├── Haversine distance calculation (km)
  ├── Missing value imputation ('Unknown' categorical / median)
  └── Derived metrics (order_hour, pickup_delay, is_peak_hour, is_sla_violated)
       │
       ├──► Cleaned CSV (data/processed/cleaned_delivery_data.csv)
       │
       ▼
SQLite Database (data/peakpulse.db) ──► SQL Queries (sql/queries.sql)
       │
       ├──► Analytics Engine (src/analysis.py)
       ├──► Visualization Engine (src/visualization.py)
       │
       ▼
Streamlit Interactive Dashboard (dashboard/app.py)
```

---

## 8. Data Cleaning Methodology

| Issue in Raw Data | Discovery / Audit Findings | Cleaning Decision & Rationale |
|:---|:---|:---|
| **Whitespace in Column Headers** | Leading/trailing spaces found in raw CSV column names. | Cleaned using `df.columns.str.strip()`. |
| **Excel Day-Fraction Floats in Time** | `Time_Orderd` contained strings like `'0.833333333'` (20:00) and `'1'` (24:00). | Converted float fractions (`float_val * 24 * 3600`) into standard 24-hr `HH:MM` format. |
| **Rollover Times (24:xx)** | 880 entries in `Time_Order_picked` started with `24:xx` (e.g. `24:15` = 00:15). | Handled midnight rollover by converting `24:xx` to `00:xx`, preventing drop into `NaT`. |
| **Missing Order Times** | 1,731 rows missing `Time_Orderd`. | Kept rows; assigned `order_hour` as `NaN` / `Unknown` to avoid distorting hourly analysis. |
| **Inverted & Zero Geocoordinates** | 3,640 records had restaurant coordinates of 0; some negative latitude signs. | Took absolute values (India lat/lon are strictly positive). Zero coordinates set to `NaN` distance. |
| **Missing Categorical Values** | `City` (1,200), `Weather` (616), `Traffic` (601), `Festival` (228). | Imputed as `'Unknown'` category to retain valid delivery time and operational data. |
| **Outlier Rider Ratings (6.0)** | 53 records had rating `6.0` on a 5-point scale (coinciding with missing weather/traffic). | Set values `> 5.0` to `NaN` for rating averages; records retained for volume counts. |
| **Rider Age 15** | 38 records recorded age 15 (legal working age is 18). | Documented as logging anomalies; retained with original values to prevent data tampering. |

---

## 9. SLA Methodology (Project-Defined Analytical SLA)

### Why an Analytical Baseline?
Because the raw dataset lacks an explicit customer promise timestamp, we established a **project-defined analytical SLA threshold**.

### Empirical Distribution of `delivery_time_min`:
- **Minimum:** 10 minutes
- **25th Percentile (Q1):** 19 minutes
- **Median (50th Percentile):** 26 minutes
- **Mean:** 26.29 minutes
- **75th Percentile (Q3):** 32 minutes
- **Maximum:** 54 minutes

### Evaluation of Candidate Thresholds:
- **> 25 minutes:** 50.10% violation rate (too sensitive; flags half of normal operations).
- **> 30 minutes:** **29.84% violation rate (Recommended Baseline)**.
  - Represents a standard operational benchmark in metropolitan food delivery (Zomato, Swiggy, Uber Eats).
  - Captures the upper ~30% of turnaround delays, providing clean operational variance across traffic and batching conditions.
- **> 32 minutes:** 24.71% violation rate (corresponds to upper quartile Q3).
- **> 35 minutes:** 17.56% violation rate (conservative severe delay threshold).

*The threshold is stored in `config/config.py` as `DEFAULT_SLA_THRESHOLD_MINUTES = 30` and is dynamically adjustable via the dashboard sidebar slider (20–45 min).*

---

## 10. Peak-Hour Methodology

Rather than assuming peak hours arbitrarily, the operational windows were derived empirically:
1. **Dinner Peak Window (18:00 – 21:00):**
   - Accounts for **>40%** of total daily orders (18,295 deliveries).
   - Average delivery turnaround rises from ~22 min (off-peak) to **>31 minutes**.
   - SLA violation rate reaches **49.4% – 50.6%** during this window.
2. **Lunch Peak Window (12:00 – 13:00):**
   - Accounts for secondary volume surge with average turnaround of ~26.8 minutes.
3. **Off-Peak Window:**
   - Morning hours (08:00 – 10:00) average ~19.5 minutes turnaround with <1% SLA violations.

---

## 11. SQL Analysis Summary
The project contains 10 structured SQLite queries saved in `sql/queries.sql` and executable via `src/run_sql.py`:
1. **Overall KPIs:** Total deliveries, avg time, SLA breach count, breach rate %, avg distance.
2. **Peak vs Non-Peak:** Performance comparison between 18:00–21:00 and off-peak hours.
3. **Hourly Breakdown:** Hour-by-hour order volumes, avg delivery durations, and breach percentages.
4. **City-Level SLA Analysis:** Delivery performance across Metropolitian, Urban, and Semi-Urban.
5. **Traffic Density Impact:** Low vs Medium vs High vs Jam.
6. **Multi-Delivery Batching:** Evaluating turnaround across 0, 1, 2, and 3 stacked deliveries.
7. **Vehicle Type & Condition:** Assessing vehicle mechanics (condition 0 to 3) and vehicle categories.
8. **Weather Conditions:** Sunny vs Fog vs Cloudy vs Stormy.
9. **Festival Period Impact:** Regular days vs festive rush turnaround.
10. **High-Volume Rider Performance:** Riders with ≥ 50 deliveries and their SLA compliance.

---

## 12. Dashboard Features (`dashboard/app.py`)
Built with Streamlit and Plotly, styled to match the dark Figma prototype (`#0B0F19` canvas, `#161F30` cards, `#FF4B4B` pulse accent):
- **Global Sidebar Filters:**
  - Dynamic Analytical SLA Threshold slider (20 to 45 min).
  - Multi-select filters for City, Traffic, Weather, Vehicle Type, and Order Type.
  - Operational period filter (Dinner Peak, Lunch Peak, Off-Peak).
  - Festival toggle (All / Yes / No).
- **Tab 1: Overview:** 5 KPI cards (Total Deliveries, SLA Violations, SLA Rate %, Avg Time, Peak Share), delivery time distribution histogram, and traffic performance chart.
- **Tab 2: Peak-Hour Analysis:** Full-width dual-axis combo chart (Hourly Volume Bar + SLA Violation Rate Line) with peak window highlighted, plus peak vs non-peak comparison table.
- **Tab 3: Location Analysis:** City tier comparison and weather condition breakdown.
- **Tab 4: Rider & Delivery Patterns:** Multi-delivery stacking chart, vehicle condition matrix, and top rider volume leaderboard.
- **Tab 5: Customer Impact & Data Limitations:** Transparent documentation of missing complaint/refund fields, and explanation of delay as an operational proxy.
- **Tab 6: Key Insights:** Evidence-based insights formatted with Pattern, Evidence, Operational Meaning, and Limitation.

---

## 13. Key Evidence-Based Insights

### 1. Multi-Order Stacking Delays
- **Pattern:** Stacking multiple drops onto a single rider is associated with severe turnaround escalation.
- **Evidence:** Orders with 0 multiple deliveries averaged 22.88 minutes (18.1% SLA breach rate), whereas orders with 2 stacked drops averaged 40.45 minutes (100% SLA breach rate).
- **Operational Meaning:** Dispatch systems should enforce strict geographical clustering constraints before allowing 2+ order batching.

### 2. Traffic Congestion Surge
- **Pattern:** Severe traffic conditions are strongly associated with SLA violations.
- **Evidence:** Under 'Low' traffic, orders averaged 21.27 minutes (7.87% violation rate). Under 'Jam' traffic, orders averaged 31.18 minutes (50.63% violation rate).
- **Operational Meaning:** Operations teams should dynamically widen customer delivery estimates during traffic spikes.

### 3. Dinner Peak Strain (18:00 – 21:00)
- **Pattern:** Peak dinner hours handle the highest volume and suffer the highest delay rates.
- **Evidence:** Orders between 18:00 and 21:00 averaged >31 minutes turnaround with ~50% SLA violation rates, compared to 23.2 minutes and 14.6% in the subsequent 22:00 window.
- **Operational Meaning:** Fleet staffing shifts must be heavily scheduled around 17:30–21:30.

### 4. Vehicle Condition & Turnaround
- **Pattern:** Poor vehicle condition (condition 0) is associated with higher delivery durations.
- **Evidence:** Condition 0 vehicles averaged 30.07 minutes (41.69% violation rate), while condition 1 and 2 vehicles averaged ~24.4 minutes (~23.6% violation rate).
- **Operational Meaning:** Fleet onboarding should mandate basic mechanical fitness inspections.

---

## 14. Tech Stack
- **Language:** Python 3.10+
- **Data Engineering:** Pandas, NumPy
- **Database & Querying:** SQLite3, SQL
- **Visualization:** Plotly Graph Objects
- **Dashboard Framework:** Streamlit
- **Version Control:** Git & GitHub

---

## 15. How to Run Locally

### 1. Clone the repository and navigate to project folder:
```bash
git clone <repo-url>
cd peakpluse
```

### 2. Set up virtual environment and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Data Cleaning Pipeline:
```bash
python src/data_cleaning.py
```
*Outputs cleaned dataset to `data/processed/cleaned_delivery_data.csv`.*

### 4. Execute SQL Queries:
```bash
python src/run_sql.py
```
*Creates `data/peakpulse.db` and prints all 10 SQL query results in formatted tables.*

### 5. Launch the Streamlit Dashboard:
```bash
streamlit run dashboard/app.py
```
*Opens the interactive dashboard in your browser at `http://localhost:8501`.*

---

## 16. Project Structure

```
peakpluse/
├── config/
│   └── config.py                   # Central paths, SLA threshold (30m), theme tokens
├── data/
│   ├── raw/
│   │   └── Zomato Dataset.csv      # Original raw dataset (45,584 rows)
│   ├── processed/
│   │   └── cleaned_delivery_data.csv # Processed dataset (30 columns)
│   └── peakpulse.db                # SQLite database with deliveries table
├── notebooks/
│   └── exploratory_analysis.ipynb  # Interactive Jupyter EDA & SLA validation
├── src/
│   ├── data_cleaning.py            # Reproducible data cleaning pipeline
│   ├── run_sql.py                  # SQLite query executor
│   ├── analysis.py                 # Analytics & insight generation logic
│   └── visualization.py            # Plotly dark theme chart generators
├── sql/
│   └── queries.sql                 # 10 beginner-friendly analytical SQL queries
├── dashboard/
│   └── app.py                      # Interactive Streamlit operations dashboard
├── requirements.txt                # Python package dependencies
├── profile_data.py                 # Initial data profiling script
└── README.md                       # Comprehensive documentation & viva guide
```

---

## 17. Viva Preparation Guide (Questions & Model Answers)

### Q1: Why did you choose 30 minutes as your SLA threshold when the dataset didn't have one?
> **Answer:** In data analytics, when an explicit contractual SLA is unavailable, defining an analytical baseline grounded in the empirical distribution is best practice. The median delivery time in our dataset is 26 minutes, and the 75th percentile (Q3) is 32 minutes. A 30-minute threshold represents standard industry turnaround expectations (e.g., Zomato 30-minute delivery guarantees) and cleanly separates the upper 29.8% of delivery times for bottleneck investigation. We also made this threshold a configurable parameter in `config.py` and an interactive slider in our dashboard.

### Q2: How did you define peak hours without guessing?
> **Answer:** We grouped orders by `order_hour` and analyzed both order volume and average delivery duration. We discovered that hours 18:00 to 21:00 (Dinner Peak) account for over 40% of all orders, and average delivery times jump from ~22 minutes off-peak to over 31 minutes, with violation rates reaching ~50%. Thus, peak hours are empirically defined by volume surge coupled with turnaround degradation.

### Q3: How did you handle missing values during data cleaning?
> **Answer:** We avoided blindly dropping rows (`dropna()`), which would have discarded thousands of valuable records. For missing categorical features (`City`, `Weather_conditions`, `Road_traffic_density`, `Festival`), we imputed with `'Unknown'` to retain them in analysis. For missing order times (1,731 rows), we left `order_hour` as null so as not to distort hourly trend curves. For geocoordinates, zero coordinates were identified as missing GPS and resulted in null distance rather than false 0-km deliveries.

### Q4: Why did standard datetime parsing fail on the raw timestamps?
> **Answer:** The raw CSV contained Excel day-fraction decimals (such as `0.833333333` representing 20:00) and rollover timestamps like `24:15:00` (meaning 00:15 next day). Standard datetime libraries treat `24:xx` as invalid hours and produce `NaT`. We engineered a dedicated parser that converts Excel day fractions to hours/minutes and translates `24:xx` into next-day `00:xx`, achieving 100% clean parsing without data loss.

### Q5: Can you say that traffic jams cause delivery delays?
> **Answer:** No. As ethical data analysts, we make observational claims rather than causal claims. We observed that orders under 'Jam' traffic had an average delivery time of 31.2 minutes compared to 21.3 minutes in 'Low' traffic. While traffic is strongly associated with delay, we cannot assert pure causality because confounding factors—such as kitchen backlog during rainy rush hours—also occur simultaneously.

---

## 18. Team Contribution & Credits
- **Project Concept & Dashboard Architecture:** Data Engineering & Analytics Team
- **Pipeline Implementation:** Antigravity AI Assistant & Developer
- **Design Inspiration:** PeakPulse UI Figma Prototype
