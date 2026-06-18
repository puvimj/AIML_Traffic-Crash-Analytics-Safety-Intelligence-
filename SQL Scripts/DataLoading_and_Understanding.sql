-- Phase 1: Data Loading & Understanding
-- 1. Row count verification
SELECT COUNT(*) FROM "CrashTable";

-- 2. Schema verification
SELECT table_schema AS "Schema", table_name AS "Table Name"
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- 3. Data type verification
SELECT 
    column_name AS "Column",
    data_type AS "Data Type",
    is_nullable AS "Allows Nulls"
FROM 
    information_schema.columns
WHERE 
    table_schema = 'public' 
    AND table_name = 'CrashTable';  

-- 4. Select Query
SELECT * FROM "CrashTable" LIMIT 100;


