-- ==============================================================================
-- PeakPulse — Food Delivery SLA Insights
-- Analytical SQL Queries (SQLite Compatible)
--
-- Table: deliveries
-- Description: Contains cleaned operational food delivery records.
-- Project Analytical SLA Threshold: > 30 minutes is marked as SLA Violated (is_sla_violated = 1)
-- ==============================================================================


-- ------------------------------------------------------------------------------
-- 1. OVERALL OPERATIONAL KPIS
-- Answers: What is our total delivery volume, average delivery time,
-- total SLA violations, and overall SLA violation percentage?
-- ------------------------------------------------------------------------------
SELECT 
    COUNT(*) AS total_deliveries,
    ROUND(AVG(delivery_time_min), 2) AS avg_delivery_time_min,
    SUM(is_sla_violated) AS total_sla_violations,
    ROUND(AVG(is_sla_violated) * 100.0, 2) AS sla_violation_rate_pct,
    ROUND(AVG(delivery_distance_km), 2) AS avg_distance_km
FROM deliveries;


-- ------------------------------------------------------------------------------
-- 2. PEAK VS NON-PEAK DELIVERIES
-- Answers: How do dinner peak hours (18:00 to 21:00) compare against non-peak
-- hours in terms of volume, average duration, and SLA violations?
-- ------------------------------------------------------------------------------
SELECT 
    CASE 
        WHEN is_peak_hour = 1 THEN 'Dinner Peak (18-21)'
        WHEN is_peak_hour = 0 THEN 'Non-Peak'
        ELSE 'Unknown Hour'
    END AS operational_period,
    COUNT(*) AS total_deliveries,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM deliveries), 2) AS pct_of_total_orders,
    ROUND(AVG(delivery_time_min), 2) AS avg_delivery_time_min,
    SUM(is_sla_violated) AS total_sla_violations,
    ROUND(AVG(is_sla_violated) * 100.0, 2) AS sla_violation_rate_pct
FROM deliveries
GROUP BY is_peak_hour
ORDER BY is_peak_hour DESC;


-- ------------------------------------------------------------------------------
-- 3. HOURLY PERFORMANCE BREAKDOWN
-- Answers: At which specific hours do delivery times and SLA breaches spike?
-- ------------------------------------------------------------------------------
SELECT 
    CAST(order_hour AS INT) AS hour_of_day,
    COUNT(*) AS order_volume,
    ROUND(AVG(delivery_time_min), 2) AS avg_delivery_time_min,
    SUM(is_sla_violated) AS sla_violations,
    ROUND(AVG(is_sla_violated) * 100.0, 2) AS sla_violation_rate_pct
FROM deliveries
WHERE order_hour IS NOT NULL
GROUP BY CAST(order_hour AS INT)
ORDER BY hour_of_day ASC;


-- ------------------------------------------------------------------------------
-- 4. CITY-LEVEL PERFORMANCE & SLA VIOLATIONS
-- Answers: How does delivery performance vary across city tiers?
-- ------------------------------------------------------------------------------
SELECT 
    city,
    COUNT(*) AS total_deliveries,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM deliveries), 2) AS order_share_pct,
    ROUND(AVG(delivery_time_min), 2) AS avg_delivery_time_min,
    SUM(is_sla_violated) AS sla_violations,
    ROUND(AVG(is_sla_violated) * 100.0, 2) AS sla_violation_rate_pct
FROM deliveries
GROUP BY city
ORDER BY total_deliveries DESC;


-- ------------------------------------------------------------------------------
-- 5. TRAFFIC DENSITY IMPACT
-- Answers: How strongly is road traffic density associated with delivery delays?
-- ------------------------------------------------------------------------------
SELECT 
    traffic_density,
    COUNT(*) AS total_deliveries,
    ROUND(AVG(delivery_time_min), 2) AS avg_delivery_time_min,
    SUM(is_sla_violated) AS sla_violations,
    ROUND(AVG(is_sla_violated) * 100.0, 2) AS sla_violation_rate_pct
FROM deliveries
GROUP BY traffic_density
ORDER BY avg_delivery_time_min DESC;


-- ------------------------------------------------------------------------------
-- 6. MULTIPLE DELIVERIES (BATCHING) IMPACT
-- Answers: Does stacking multi-drop orders increase SLA violation risk?
-- ------------------------------------------------------------------------------
SELECT 
    multiple_deliveries AS multi_orders_stacked,
    COUNT(*) AS total_deliveries,
    ROUND(AVG(delivery_time_min), 2) AS avg_delivery_time_min,
    SUM(is_sla_violated) AS sla_violations,
    ROUND(AVG(is_sla_violated) * 100.0, 2) AS sla_violation_rate_pct
FROM deliveries
GROUP BY multiple_deliveries
ORDER BY multiple_deliveries ASC;


-- ------------------------------------------------------------------------------
-- 7. VEHICLE TYPE & VEHICLE CONDITION
-- Answers: Which vehicle modes and mechanical conditions achieve best turnaround?
-- ------------------------------------------------------------------------------
SELECT 
    vehicle_type,
    vehicle_condition,
    COUNT(*) AS total_deliveries,
    ROUND(AVG(delivery_time_min), 2) AS avg_delivery_time_min,
    ROUND(AVG(is_sla_violated) * 100.0, 2) AS sla_violation_rate_pct
FROM deliveries
GROUP BY vehicle_type, vehicle_condition
ORDER BY vehicle_type ASC, vehicle_condition ASC;


-- ------------------------------------------------------------------------------
-- 8. WEATHER CONDITIONS PERFORMANCE
-- Answers: How do adverse weather patterns correlate with delivery delay times?
-- ------------------------------------------------------------------------------
SELECT 
    weather,
    COUNT(*) AS total_deliveries,
    ROUND(AVG(delivery_time_min), 2) AS avg_delivery_time_min,
    SUM(is_sla_violated) AS sla_violations,
    ROUND(AVG(is_sla_violated) * 100.0, 2) AS sla_violation_rate_pct
FROM deliveries
GROUP BY weather
ORDER BY avg_delivery_time_min DESC;


-- ------------------------------------------------------------------------------
-- 9. FESTIVAL PERIOD IMPACT
-- Answers: How severe is the delivery delay surge during festival events?
-- ------------------------------------------------------------------------------
SELECT 
    festival,
    COUNT(*) AS total_deliveries,
    ROUND(AVG(delivery_time_min), 2) AS avg_delivery_time_min,
    SUM(is_sla_violated) AS sla_violations,
    ROUND(AVG(is_sla_violated) * 100.0, 2) AS sla_violation_rate_pct
FROM deliveries
GROUP BY festival
ORDER BY avg_delivery_time_min DESC;


-- ------------------------------------------------------------------------------
-- 10. HIGH-VOLUME RIDER PERFORMANCE SUMMARY
-- Answers: What is the SLA compliance among the top active riders (>= 50 deliveries)?
-- ------------------------------------------------------------------------------
SELECT 
    delivery_person_id,
    COUNT(*) AS total_orders_delivered,
    ROUND(AVG(delivery_person_rating), 2) AS avg_rider_rating,
    ROUND(AVG(delivery_time_min), 2) AS avg_delivery_time_min,
    SUM(is_sla_violated) AS sla_violations,
    ROUND(AVG(is_sla_violated) * 100.0, 2) AS sla_violation_rate_pct
FROM deliveries
GROUP BY delivery_person_id
HAVING COUNT(*) >= 50
ORDER BY total_orders_delivered DESC, sla_violation_rate_pct ASC
LIMIT 15;
