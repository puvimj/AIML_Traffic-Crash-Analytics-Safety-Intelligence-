SELECT 
        "WEATHER_CONDITION" AS "Weather",
        COUNT(*) AS "Total Crashes"
    FROM "CrashTable"
    GROUP BY "WEATHER_CONDITION"
    ORDER BY "Total Crashes" DESC;

SELECT 
	"PRIM_CONTRIBUTORY_CAUSE" AS "Primary Cause",
    COUNT(*) AS "Incident Count",
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM "CrashTable"), 2) AS "Percentage of Total (%)"
FROM "CrashTable"
GROUP BY "PRIM_CONTRIBUTORY_CAUSE"
ORDER BY "Incident Count" DESC;

SELECT 
        EXTRACT(YEAR FROM TO_TIMESTAMP("CRASH_DATE", 'MM/DD/YYYY HH12:MI:SS AM')) AS "Year",
        EXTRACT(MONTH FROM TO_TIMESTAMP("CRASH_DATE", 'MM/DD/YYYY HH12:MI:SS AM'))  AS "Month Number",
        TO_CHAR(TO_TIMESTAMP("CRASH_DATE", 'MM/DD/YYYY HH12:MI:SS AM'), 'Month') AS "Month Name",
        COUNT(*) AS "Crashes Recorded"
    FROM "CrashTable"
    GROUP BY 
        EXTRACT(YEAR FROM TO_TIMESTAMP("CRASH_DATE", 'MM/DD/YYYY HH12:MI:SS AM')) , 
        EXTRACT(MONTH FROM TO_TIMESTAMP("CRASH_DATE", 'MM/DD/YYYY HH12:MI:SS AM')) , 
        TO_CHAR(TO_TIMESTAMP("CRASH_DATE", 'MM/DD/YYYY HH12:MI:SS AM'), 'Month')
    ORDER BY 
        "Year" DESC, 
        "Month Number" ASC;



	