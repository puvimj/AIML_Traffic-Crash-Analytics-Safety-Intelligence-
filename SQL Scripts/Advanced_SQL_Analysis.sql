-- Q1
SELECT 
	"WEATHER_CONDITION", "FIRST_CRASH_TYPE",COUNT(*) "Total Crashes"
FROM "CrashTable"
GROUP BY "WEATHER_CONDITION", "FIRST_CRASH_TYPE"
ORDER BY "Total Crashes" DESC;

-- Q2
SELECT 
    "STREET_NAME" AS "Street Name",
    COUNT(*) AS "Injury Crashes Count",          
    SUM("INJURIES_TOTAL"::int) AS "Total Victims Hurt" 
FROM "CrashTable"
WHERE "INJURIES_TOTAL" IS NOT NULL 
  	AND "INJURIES_TOTAL"::int > 0  
GROUP BY "STREET_NAME"
ORDER BY "Injury Crashes Count" DESC             
LIMIT 10;

-- Q3
SELECT "FIRST_CRASH_TYPE" AS "Crash Type", 
	COUNT(CASE WHEN "INJURIES_TOTAL"::int > 0 THEN 1 END),
	COUNT(*) AS "Total Incidents",
	    ROUND(100.0 * COUNT(CASE WHEN "INJURIES_TOTAL"::int > 0 THEN 1 END) / COUNT(*), 2) AS "Injury Probability (%%)"
FROM "CrashTable"
GROUP BY "FIRST_CRASH_TYPE"
ORDER BY "Injury Probability (%%)" DESC;

-- Q4
SELECT a."Month Number", a."Crash Hour" AS "Peak Crash Hour",
a."Incident Count" AS "Crashes Recorded"
from (
SELECT "CRASH_MONTH" AS "Month Number", "CRASH_HOUR"::int AS "Crash Hour", 
	COUNT(*) AS "Incident Count",
	ROW_NUMBER() OVER(PARTITION BY "CRASH_MONTH" ORDER BY COUNT(*) DESC) AS rank
FROM "CrashTable"
GROUP BY "CRASH_MONTH", "CRASH_HOUR"
) a
WHERE rank = 1 ORDER BY a."Month Number"::int ASC;

-- Q5
SELECT 
	"PRIM_CONTRIBUTORY_CAUSE" AS "Primary Cause", 
	COUNT(*) AS "Total Crashes"
FROM "CrashTable" WHERE "CRASH_HOUR"::int >= 18 
GROUP BY "PRIM_CONTRIBUTORY_CAUSE" 
ORDER BY "Total Crashes" DESC LIMIT 5;

-- Q6
SELECT 
	CASE WHEN "LIGHTING_CONDITION" ILIKE '%%DAYLIGHT%%' THEN 
		'Daylight' 
	ELSE 'Darkness' 
	END AS "Light Condition",
	ROUND(AVG("INJURIES_TOTAL"::int), 4) AS "Average Injuries"
FROM "CrashTable" 
WHERE "LIGHTING_CONDITION" IS NOT NULL
GROUP BY 
	CASE WHEN "LIGHTING_CONDITION" ILIKE '%%DAYLIGHT%%' THEN 
		'Daylight' 
	ELSE 'Darkness' 
	END

-- Q7
SELECT 
	"TRAFFIC_CONTROL_DEVICE" AS "Control Device", 
	COUNT(*) AS "Total Crashes",
	ROUND(AVG("INJURIES_TOTAL"::int), 4) AS "Average Injuries"
	FROM "CrashTable" 
	GROUP BY "TRAFFIC_CONTROL_DEVICE" HAVING COUNT(*) > 100 
	ORDER BY "Average Injuries" DESC;

-- Q8
SELECT 
	"LATITUDE" AS "Latitude", 
	"LONGITUDE" AS "Longitude", 
	COUNT(*) AS "Total Crashes"
FROM "CrashTable" 
WHERE "LATITUDE" IS NOT NULL 
	AND "LONGITUDE" IS NOT NULL
GROUP BY "LATITUDE", "LONGITUDE" 
ORDER BY "Total Crashes" DESC LIMIT 5

-- Q9
SELECT 
	"STREET_NAME" AS "Street Name", 
	--COUNT(*) AS "Total Crashes",
	--COUNT(CASE WHEN "INJURIES_TOTAL"::int > 0 THEN 1 END) AS "Injury Crashes",
	ROUND(100.0 * COUNT(
		CASE WHEN "INJURIES_TOTAL"::int > 0 THEN 1 END) / COUNT(*), 2) 
		AS "Injury Rate (%%)"
FROM "CrashTable" 
GROUP BY "STREET_NAME" HAVING COUNT(*) > 100 
ORDER BY "Injury Rate (%%)" DESC LIMIT 5;

-- Q10
WITH YearTable AS 
(SELECT 
	"year"::int AS "Year", 
	"FIRST_CRASH_TYPE" AS "Crash Type", 
	COUNT(*) AS "Count",
	ROW_NUMBER() OVER(PARTITION BY "year" ORDER BY COUNT(*) DESC) AS rank
FROM "CrashTable" 
WHERE "year" IS NOT NULL 
GROUP BY "year", "FIRST_CRASH_TYPE")
SELECT "Year", "Crash Type", "Count" AS "Incident Count" 
FROM YearTable WHERE rank = 1 ORDER BY "Year" DESC;

-- Q11
SELECT 
	CASE "CRASH_DAY_OF_WEEK"::int
		WHEN 1 THEN 'Sunday' 
		WHEN 2 THEN 'Monday' WHEN 3 THEN 'Tuesday' 
		WHEN 4 THEN 'Wednesday'
		WHEN 5 THEN 'Thursday' 
		WHEN 6 THEN 'Friday' 
		WHEN 7 THEN 'Saturday' 
	END AS "Day of Week",
	ROUND(COUNT(*)::numeric / 24.0, 2) AS "Average Crashes Per Hour"
FROM "CrashTable" 
WHERE "CRASH_DAY_OF_WEEK" IS NOT NULL 
GROUP BY "CRASH_DAY_OF_WEEK" 
ORDER BY "Average Crashes Per Hour" DESC LIMIT 1;

-- Q12
SELECT 
	CASE WHEN "CRASH_HOUR"::int BETWEEN 5 AND 11 THEN 'Morning (05-11)'
		WHEN "CRASH_HOUR"::int BETWEEN 12 AND 16 THEN 'Afternoon (12-16)'
		WHEN "CRASH_HOUR"::int BETWEEN 17 AND 21 THEN 'Evening (17-21)' 
	ELSE 'Night (22-04)' 
	END AS "Time Slot Bucket",
	COUNT(CASE WHEN "INJURIES_TOTAL"::int > 0 THEN 1 END) AS "Total Count", 
	SUM("INJURIES_TOTAL"::int) AS "Total Injuries Logged"
FROM "CrashTable" 
WHERE "CRASH_HOUR" IS NOT NULL
GROUP BY 1 
ORDER BY "Total Count" DESC;

-- Q13
WITH CauseMetricsRanked AS 
	(SELECT "FIRST_CRASH_TYPE" AS "Crash Type", 
	"PRIM_CONTRIBUTORY_CAUSE" AS "Contributing Cause", 
	COUNT(*) AS "Count",
	ROW_NUMBER() OVER(PARTITION BY "FIRST_CRASH_TYPE" ORDER BY COUNT(*) DESC) AS rank
FROM "CrashTable" 
GROUP BY "FIRST_CRASH_TYPE", "PRIM_CONTRIBUTORY_CAUSE")
SELECT "Crash Type", "Contributing Cause", "Count" AS "Incident Count"
FROM CauseMetricsRanked 
WHERE rank <= 3 
ORDER BY "Crash Type" ASC, "Incident Count" DESC;

-- Q14
WITH AnnualTotals AS 
(SELECT 
	"year"::int AS "Year", 
	COUNT(*) AS "Current Year Crashes"
FROM "CrashTable" 
WHERE "year" IS NOT NULL 
GROUP BY "year"),HistoricalTrends AS 
(SELECT 
	"Year", 
	"Current Year Crashes", 
	LAG("Current Year Crashes", 1) OVER (ORDER BY "Year" ASC) 
		AS "Previous Year Crashes"
FROM AnnualTotals)
SELECT 
	"Year", 
	"Current Year Crashes", 
	"Previous Year Crashes",
	ROUND(100.0 * ("Current Year Crashes" - "Previous Year Crashes") / "Previous Year Crashes", 2) AS "YoY Growth Rate (%%)"
FROM HistoricalTrends ORDER BY "Year" DESC;

-- Q15
SELECT 
	ROUND("LATITUDE"::numeric, 2) AS "Zone Latitude", 
	ROUND("LONGITUDE"::numeric, 2) AS "Zone Longitude",
	COUNT(*) AS "Total Crashes in Zone"
FROM "CrashTable" 
WHERE "LATITUDE" IS NOT NULL AND 
	"LONGITUDE" IS NOT NULL
GROUP BY "Zone Latitude","Zone Longitude"
ORDER BY "Total Crashes in Zone" DESC LIMIT 10;
