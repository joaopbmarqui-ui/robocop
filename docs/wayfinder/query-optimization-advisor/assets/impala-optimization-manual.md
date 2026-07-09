***

# Hadoop Usage Guidelines: SQL Query Optimization Manual

## Table of Contents

1.  Introduction
2.  Platform Use Cases & Data Pull Guidelines
3.  Query Structure and Data Organization
4.  JOIN Optimization Strategies
5.  Table Management & Naming Conventions
6.  Tactical Code Guidelines
7.  Resource Management & Environment Hygiene
8.  Practical Examples & Quiz Solutions
9.  Quick Reference Summary

***

## 1. Introduction

This manual compiles best practices for optimizing SQL queries in Impala, ensuring enhanced query efficiency, reduced resource consumption, and improved user experience. Based on Hadoop Usage Guidelines for enhancing query efficiency via structured data pulls, broadcast logic, and naming conventions.

**Key Goals:**
- Faster query execution through structured data pulls
- Efficient resource utilization
- Cleaner, maintainable code
- Better collaboration across teams

***

## 2. Platform Use Cases & Data Pull Guidelines

### Platform Use Cases
- **Data Pull:** Use Impala for extracting data
- **Data Manipulation, Summarization, etc.:** Use Spark/Hive for processing

### Core Principles for Data Pulls

**Guideline #1: Always Use Process Date and Partition Columns in Filters**

During data pull, **process date** and **partition columns** must always be used in filters to minimize data scanned.

```sql
WHERE dw_process_date = '2021-12-31'
AND clr.dw_iss_country_cd IN ('USA')
AND clr.dw_acct_prefix6 IN (558158)
```

**Guideline #2: Create Files in Employee ID Location**

User must create all files in the **employee ID location** and not in the home directory.

```
LOCATION '/das/coe/enc/e105572/e105572_cr_usa_ext_impala'
```

This ensures:
- Proper file organization
- Easy identification of file ownership
- Prevents clutter in shared directories

### Broadcast vs. Shuffle Strategy

**Guideline #3: Tables to be Broadcasted or Shuffled in Join Queries**

Tables should be **broadcasted or shuffled** in join queries (valid only for Impala queries) as per the recommended list.

**When to use BROADCAST:**
- For tables smaller than 1GB
- Reduces shuffle overhead
- Improves join performance

**When to use SHUFFLE:**
- For larger tables
- Distributes data across nodes

**Recommended Impala Join Strategy Table:**

| Database | Table Name | Recommended Join Type |
|----------|------------|----------------------|
| CORE | cut_clear_dtl_hsh/enc | SHUFFLE |
| CORE | mmh_location | SHUFFLE |
| CORE | mmh_industry | BROADCAST |
| CORE/GCO | product_hierarchy | BROADCAST |
| CORE | member_hierarchy | BROADCAST |
| CORE | aggregate_merchant | BROADCAST |
| CORE | Auth_dtl_enc/hsh | SHUFFLE |
| CORE | clear_dtl_hsh/enc | SHUFFLE |
| GCO | clear_dtl_hsh/enc | SHUFFLE |
| MRS | Program | Broadcast |
| MRS | aggregate_merchant | Shuffle |
| MRS | bank_product | Broadcast |
| MRS | member_product_hierarchy | Broadcast |
| MRS | call_statistics | Broadcast |
| MRS | card_input_mode | Broadcast |
| MRS | cardholder_present | Broadcast |
| MRS | cardholder_redtemp_history | Shuffle |
| MRS | customer_account | Broadcast |
| MRS | member_hierarchy | Broadcast |
| MRS | redemption_history | Shuffle |
| MRS | reward_item | Shuffle |
| MRS | reward_matrix_item | Shuffle |
| MRS | trans_detail | Shuffle |

**Guideline #4: Check Table Size Before Using Broadcast**

For any other custom tables, if the **table is below 1 GB** then **use only broadcast**.

Query to check file size:
```sql
SHOW TABLE STATS tablename;
```

***

## 3. Query Structure and Data Organization

### Best Practices for Query Structure

**Always Select Only Required Columns**

Never do a `SELECT * FROM <Core Table>` statement on core tables without any filter. This causes unnecessary data scanning and resource consumption.

```sql
-- Bad Practice
SELECT * FROM core.cut_clear_dtl_enc LIMIT 10;

-- Good Practice
SELECT column1, column2, column3 
FROM core.cut_clear_dtl_enc 
WHERE dw_process_date = '2023-12-31';
```

**Use Partition and Process Date Columns in Filters**

Always filter by partition columns and process dates to access only necessary data, reducing execution time and resource usage.

```sql
WHERE dw_process_date BETWEEN "2023-08-01" AND "2024-07-31"
AND dw_iss_country_cd IN ("IDN")
AND dw_acct_ranuni_grp_num < 30
```

**Filter Data in Subqueries Before JOINs**

Put the required filters in the main query instead of pulling global data. This reduces the volume of data processed.

```sql
-- Fetch only the required columns in subquery
SELECT latest_parent_de93_issuer_id, de22_cardholder_present_cd, dw_net_pd_amt, dw_net_pd_cnt
FROM (
  SELECT *
  FROM core.cut_clear_dtl_enc clearing
  WHERE clearing.dw_process_date BETWEEN "2023-08-01" AND "2024-07-31"
  AND clearing.dw_iss_country_cd IN ("IDN")
  AND clearing.dw_acct_ranuni_grp_num < 30
) clearing
```

***

## 4. JOIN Optimization Strategies

### Broadcast vs. Shuffle Joins

**Use Broadcast for Small Tables (<1GB)**

For tables smaller than 1GB, use BROADCAST joins to reduce shuffle overhead and improve performance.

```sql
INNER JOIN [BROADCAST] core.product_hierarchy AS prod 
  ON (clearing.dw_product_cd = prod.product_code)
```

**Use Shuffle for Large Tables**

For larger tables, use SHUFFLE to distribute data across nodes.

```sql
INNER JOIN [SHUFFLE] core.cut_clear_dtl_enc AS clearing
  ON (...)
```

**Filter Large Tables During Joins**

Always apply filters to larger tables before performing joins to reduce cardinality.

```sql
-- Apply filters before join
FROM (
  SELECT * FROM core.cut_clear_dtl_enc
  WHERE dw_process_date BETWEEN "2023-08-01" AND "2024-07-31"
  AND dw_iss_country_cd IN ("IDN")
) clearing
INNER JOIN [BROADCAST] core.product_hierarchy prod
  ON (clearing.dw_product_cd = prod.product_code)
WHERE prod.credit_debit_ind IN ("CR")
```

### Runtime Filters and Dynamic Optimization

**Impala automatically applies runtime filters to optimize joins**

Runtime filters are a powerful Impala feature that automatically reduces data scanned during joins by pushing filter conditions from one side of the join to the other.

```sql
-- Runtime filters work best with this pattern:
-- Small/filtered table generates filters that are applied to large table scan

WITH filtered_base AS (
  SELECT
      card,
      tx_date,
      amount
  FROM my_transaction_table
  WHERE approve_flag = 'APPROVED'
),
auth_data AS (
  SELECT
      CAST(de2_card_nbr AS VARCHAR(19)) AS card,
      CAST(hdr_banknet_date AS DATE) AS tx_date,
      account_type
  FROM CORE.auth_dtl_enc a
  INNER JOIN filtered_base b
    ON CAST(a.de2_card_nbr AS VARCHAR(19)) = b.card
   AND CAST(a.hdr_banknet_date AS DATE) = b.tx_date
  WHERE a.dw_process_date BETWEEN '2024-08-01' AND '2024-12-31'
  GROUP BY card, tx_date, account_type
)
SELECT * FROM auth_data;

-- Impala creates runtime bloom filters from filtered_base
-- These filters are pushed to auth_dtl_enc scan to reduce rows read
-- EXPLAIN shows: "runtime filters: RF000[bloom] <- b.card"
```

**Key Benefits of Runtime Filters:**
- Automatically reduce large table scans by 90-99%
- No explicit hints needed - optimizer handles it
- Work across shuffle boundaries
- Especially effective for star schema joins

**Best Practices for Runtime Filter Optimization:**
1. **Filter the smaller table first** - Creates more selective filters
2. **Use consistent data types** - Avoid unnecessary CASTs in join conditions
3. **Join on indexed/partition columns** when possible
4. **Avoid excessive CASTs** - They can prevent filter pushdown

```sql
-- Good - Consistent types, filters applied early
WITH base AS (
  SELECT CAST(card AS VARCHAR(19)) AS card_str, tx_date
  FROM transactions
  WHERE status = 'APPROVED'
)
SELECT *
FROM large_table l
INNER JOIN base b ON l.card_number = b.card_str

-- Less optimal - CAST in join condition
SELECT *
FROM large_table l
INNER JOIN transactions t 
  ON CAST(l.card_number AS VARCHAR(19)) = CAST(t.card AS VARCHAR(19))
WHERE t.status = 'APPROVED'
```

### Understanding EXPLAIN Cardinality vs Actual Rows

**Initial cardinality estimates may appear high but get reduced by runtime filters**

When analyzing EXPLAIN output, understand that row counts shown are **estimates before runtime filters apply**.

```
Example EXPLAIN output interpretation:

01:SCAN HDFS [core.auth_dtl_enc]
   partitions=469/5105 files=524071 size=43.82TB
   runtime filters: RF004[bloom] -> card, RF005[bloom] -> tx_date
   cardinality=25.14G  <-- Initial estimate BEFORE filters

After execution (from PROFILE):
   Rows read: 25.14G
   Rows returned: 74.60M  <-- 97% filtered out by runtime filters!
```

**What to look for in EXPLAIN:**
✅ **Good signs:**
- `runtime filters: RF00X[bloom] -> column_name`
- Partition pruning: `partitions=469/5105` (not all partitions)
- Join strategy matches table size (BROADCAST for small, SHUFFLE for large)
- Predicates pushed to scan nodes

⚠️ **Warning signs:**
- `partitions=5105/5105` (no partition pruning)
- No runtime filters on large table scans
- Very high memory estimates without corresponding filtering
- Cartesian products in join graph

**How to verify actual performance:**
1. Run EXPLAIN to check plan structure
2. Execute the query
3. Run PROFILE to see actual rows processed vs returned
4. Look for high filter effectiveness (e.g., 25B rows read → 100M returned = 99.6% filtered)

### Choosing Between JOIN Strategies for Auth_dtl_enc

**Auth_dtl_enc requires special consideration due to its massive size**

The auth_dtl_enc table is one of the largest tables in CORE, requiring careful join strategy selection.

**Scenario 1: Small base table joining to auth_dtl_enc**
```sql
-- When base table is < 500M rows
-- Use INNER JOIN and let runtime filters do the work
WITH small_base AS (
  SELECT card, tx_date
  FROM my_transactions
  WHERE country = 'BRA'
    AND tx_date BETWEEN DATE '2024-01-01' AND DATE '2024-12-31'
  -- Results in ~10M rows
)
SELECT *
FROM CORE.auth_dtl_enc a
INNER JOIN small_base b
  ON CAST(a.de2_card_nbr AS VARCHAR(19)) = b.card
 AND CAST(a.hdr_banknet_date AS DATE) = b.tx_date
WHERE a.dw_process_date BETWEEN '2024-01-01' AND '2024-12-31'
-- Runtime filters from small_base will reduce auth scan dramatically
```

**Scenario 2: Large base table joining to auth_dtl_enc**
```sql
-- When base table is > 500M rows
-- Consider breaking into smaller time periods
WITH base_q1 AS (
  SELECT * FROM my_large_table
  WHERE tx_date BETWEEN '2024-01-01' AND '2024-03-31'
),
base_q2 AS (
  SELECT * FROM my_large_table
  WHERE tx_date BETWEEN '2024-04-01' AND '2024-06-30'
)
-- Process each quarter separately, then UNION ALL
```

**Scenario 3: When you need auth data for subset of transactions**
```sql
-- Filter aggressively on BOTH sides before joining
WITH filtered_base AS (
  SELECT card, tx_date, amount
  FROM transactions
  WHERE source <> 'Debit'  -- Exclude types that don't need auth lookup
    AND tx_date BETWEEN DATE '2024-01-01' AND DATE '2024-12-31'
),
auth_aggregated AS (
  SELECT
      CAST(de2_card_nbr AS VARCHAR(19)) AS card,
      CAST(hdr_banknet_date AS DATE) AS tx_date,
      MAX(CASE WHEN acct_type_ind = 'D' THEN 1 ELSE 0 END) AS is_debit
  FROM CORE.auth_dtl_enc
  INNER JOIN filtered_base fb
    ON CAST(de2_card_nbr AS VARCHAR(19)) = fb.card
   AND CAST(hdr_banknet_date AS DATE) = fb.tx_date
  WHERE dw_process_date BETWEEN '2024-01-01' AND '2024-12-31'
  GROUP BY card, tx_date
)
-- Now join aggregated result (much smaller) to base
SELECT *
FROM filtered_base b
LEFT JOIN [BROADCAST] auth_aggregated a  -- Can broadcast after aggregation
  ON b.card = a.card AND b.tx_date = a.tx_date
```

### Splitting Query Paths for Different Data Types

**Sometimes it's more efficient to split query into separate paths then UNION**

When different subsets of data require different processing, consider split-process-union pattern.

**Anti-pattern: One-size-fits-all with complex CASE logic**
```sql
-- Not optimal - processes ALL data through auth join even when not needed
SELECT
    issuer,
    CASE
      WHEN source = 'Debit' THEN 'Debit'
      WHEN auth_flag = 'D' THEN 'Debit'
      ELSE 'Credit'
    END AS card_type,
    SUM(amount) AS total
FROM all_transactions t
LEFT JOIN auth_data a ON t.card = a.card  -- Joins ALL records
GROUP BY 1, 2
```

**Optimal: Split paths based on processing needs**
```sql
-- Better - separate paths for data that needs different processing
WITH credit_path AS (
  SELECT
      issuer,
      CASE WHEN a.auth_flag = 'D' THEN 'Debit' ELSE 'Credit' END AS card_type,
      amount
  FROM all_transactions t
  INNER JOIN auth_data a ON t.card = a.card
  WHERE t.source = 'Credit'  -- Only process records that need auth lookup
),
debit_path AS (
  SELECT
      issuer,
      'Debit' AS card_type,  -- No auth lookup needed
      amount
  FROM all_transactions
  WHERE source = 'Debit'
),
combined AS (
  SELECT * FROM credit_path
  UNION ALL
  SELECT * FROM debit_path
)
SELECT issuer, card_type, SUM(amount) AS total
FROM combined
GROUP BY issuer, card_type
```

**When to use split-path approach:**
- Different data subsets require different joins
- Some records can skip expensive operations (like auth table lookups)
- Clear logical separation (e.g., Debit vs Credit, Domestic vs International)
- Each path can be optimized independently

**When NOT to split:**
- Both paths require similar processing
- Split adds more complexity than benefit
- Runtime filters already handle the optimization

***

## 5. Table Management & Naming Conventions

**Guideline #5: Table Names Must Have Employee ID Attached**

Table names should always have the **employee ID attached** at the beginning.

**Example:** `coe_hsh.eXXXXXX_Filename`

This ensures:
- Easy identification of table ownership
- Prevents naming conflicts
- Simplifies table management and cleanup

```sql
CREATE TABLE coe_enc.e105572_cr_usa_ext_impala
STORED AS PARQUET
LOCATION '/das/coe/enc/e105572/e105572_cr_usa_ext_impala'
AS
SELECT ...
```

***

## 6. Tactical Code Guidelines

**Guideline #6: Always Use DROP TABLE IF EXISTS**

Drop table if exists command shall always be used with the table. Table name shall always be checked to ensure proper table is dropped, not impacting any other user's database.

```sql
DROP TABLE IF EXISTS coe_enc.e105572_cr_usa_ext_impala;
CREATE TABLE coe_enc.e105572_cr_usa_ext_impala
STORED AS PARQUET
LOCATION '/das/coe/enc/e105572/e105572_cr_usa_ext_impala'
AS
SELECT *
FROM core.cut_clear_dtl_enc AS clr
WHERE ...
```

**Guideline #7: Drop All Project Files After 1 Quarter of Completion**

Dropping all project-related files post 1 quarter completion of the project:

```bash
hadoop fs -rm <source-directory-with-filename>
```

This helps:
- Free up storage space
- Maintain a clean environment
- Reduce clutter in shared directories

**Guideline #8: Data Pull Time Limits in Impala**

In Impala, data can be pulled for **13 months in one go**. For larger time period requirements, break the query into sub parts.

**Guideline #9: Filter Bigger Tables During Join**

New custom queries being developed should have **bigger tables** like cut_clear_dtl_enc/hsh filtered during the join statement.

```sql
INNER JOIN [SHUFFLE]
(SELECT impurity, cleansed_merchant_name, ceid_loc_id FROM core.mmh_location_hsh
 WHERE dw_merch_location_id = main_old_loc_id
 GROUP BY 1,2,3
) a
```

***

## 7. Resource Management & Environment Hygiene

**Guideline #10: Never Do SELECT * Without Filters**

Never do a `"SELECT * FROM <Core Table> limit 10;"` statement on core tables without any filter.

**Guideline #11: Do Not Acquire More Than 3 PySpark Ports**

Do not acquire **more than 3 pyspark ports** at a time to ensure fair resource distribution across users.

**Guideline #12: Always Create Folder for Metadata Storage**

Always create **folder inside** your user directory for **storing metadata.**

Example: `/das/coe/enc/eXXXXX/Table_name`

**Guideline #13: Shut Down Kernels Daily**

**At least once per day** (or at the end of your working session), **shut down kernels** you no longer need to free up resources.

**Guideline #14: Stop Unused Processes**

In some cases, you may need to **stop processes** that aren't tied directly to a notebook or are not shut down properly **through the JupyterHub interface**.

**Guideline #15: Clean Environment Before Resource-Intensive Tasks**

Ensure your **environment is as clean as possible before** initiating **resource-intensive tasks** to maximize performance and avoid conflicts.

***

## 8. Advanced Impala Query Optimization Techniques

### Partition Pruning Optimization

**Always leverage partition columns for maximum efficiency**

Impala uses partition pruning to skip reading unnecessary data. Always include partition columns in WHERE clauses.

```sql
-- Excellent - Partition pruning enabled
WHERE dw_process_date = '2023-12-31'

-- Good - Range with partition column
WHERE dw_process_date BETWEEN '2023-01-01' AND '2023-12-31'

-- Bad - No partition filtering
WHERE transaction_amount > 1000  -- Scans all partitions
```

### Predicate Pushdown Strategies

**Push filters as close to the data source as possible**

Impala performs better when filters are applied early in the query execution.

```sql
-- Optimized - Filters in subquery
SELECT customer_id, SUM(amount) 
FROM (
  SELECT customer_id, amount
  FROM core.cut_clear_dtl_enc
  WHERE dw_process_date = '2023-12-31'
    AND dw_iss_country_cd = 'USA'
    AND dw_acct_prefix6 IN (558158)
) filtered_data
GROUP BY customer_id

-- Not optimized - Filters after aggregation
SELECT customer_id, SUM(amount)
FROM core.cut_clear_dtl_enc
GROUP BY customer_id
HAVING dw_process_date = '2023-12-31'
```

### Data Type Optimization

**Use appropriate data types to reduce memory footprint**

Smaller data types mean less memory usage and faster processing.

```sql
-- Use CAST for more efficient data types
CAST(product_code AS SMALLINT) instead of INT
CAST(flag AS TINYINT) instead of INT
CAST(date_string AS TIMESTAMP) for date operations

-- Example
SELECT 
  CAST(product_type_code AS SMALLINT) AS product_type,
  CAST(is_active AS TINYINT) AS active_flag
FROM core.product_hierarchy
```

### Column Order in GROUP BY and ORDER BY

**Order columns by cardinality (lowest to highest)**

This helps Impala optimize grouping operations.

```sql
-- Optimized - Low cardinality first
GROUP BY country_cd, product_type, merchant_id

-- Less optimized - High cardinality first
GROUP BY merchant_id, product_type, country_cd
```

### Avoiding Expensive Operations

**Minimize use of DISTINCT, UNION, and complex functions**

```sql
-- Instead of DISTINCT, use GROUP BY when possible
-- Bad
SELECT DISTINCT country_cd, product_type
FROM core.cut_clear_dtl_enc

-- Better
SELECT country_cd, product_type
FROM core.cut_clear_dtl_enc
GROUP BY country_cd, product_type

-- Use UNION ALL instead of UNION when duplicates are acceptable
-- Bad - Adds deduplication overhead
SELECT * FROM table1
UNION
SELECT * FROM table2

-- Better - No deduplication
SELECT * FROM table1
UNION ALL
SELECT * FROM table2
```

### Optimizing String Operations

**String operations are expensive - minimize their use**

```sql
-- Avoid LIKE with leading wildcards
-- Bad - Full table scan
WHERE merchant_name LIKE '%store%'

-- Better - Use leading characters when possible
WHERE merchant_name LIKE 'store%'

-- Even better - Use exact match or IN clause
WHERE merchant_name IN ('store1', 'store2', 'store3')

-- Avoid REGEXP when simple comparison works
-- Bad
WHERE merchant_name REGEXP '^ABC.*'

-- Better
WHERE merchant_name LIKE 'ABC%'
```

### NULL Handling Optimization

**Be explicit about NULL handling**

```sql
-- Use IS NULL/IS NOT NULL instead of functions
-- Bad
WHERE COALESCE(column_name, '') != ''

-- Better
WHERE column_name IS NOT NULL AND column_name != ''

-- For joins, filter NULLs before joining
SELECT *
FROM (
  SELECT * FROM table1 
  WHERE join_key IS NOT NULL
) t1
JOIN table2 t2 ON t1.join_key = t2.join_key
```

### Subquery Optimization with CTEs

**Use Common Table Expressions (CTEs) for better readability and performance**

```sql
-- Good practice - Using CTEs
WITH filtered_clearing AS (
  SELECT 
    dw_product_cd,
    dw_net_pd_amt,
    dw_process_date
  FROM core.cut_clear_dtl_enc
  WHERE dw_process_date BETWEEN '2023-01-01' AND '2023-12-31'
    AND dw_iss_country_cd = 'USA'
),
product_filtered AS (
  SELECT 
    product_code,
    product_name
  FROM core.product_hierarchy
  WHERE level_number = 5
)
SELECT 
  p.product_name,
  SUM(c.dw_net_pd_amt) AS total_amount
FROM filtered_clearing c
INNER JOIN [BROADCAST] product_filtered p 
  ON c.dw_product_cd = p.product_code
GROUP BY p.product_name
```

### Aggregate Function Optimization

**Use appropriate aggregate functions and avoid nested aggregations**

```sql
-- Avoid COUNT(DISTINCT) on large datasets - use GROUP BY instead
-- Bad
SELECT COUNT(DISTINCT customer_id) FROM large_table

-- Better - Two-step aggregation
SELECT COUNT(*) FROM (
  SELECT customer_id FROM large_table GROUP BY customer_id
) subquery

-- Use SUM(1) instead of COUNT(*) when appropriate
-- Both work, but SUM(1) can be clearer
SELECT merchant_id, SUM(1) AS transaction_count
FROM core.cut_clear_dtl_enc
GROUP BY merchant_id
```

### CASE Statement Optimization

**Simplify CASE statements and use them efficiently**

```sql
-- Order CASE conditions by frequency (most common first)
-- Optimized
CASE 
  WHEN product_type = 'CREDIT' THEN 1  -- Most common
  WHEN product_type = 'DEBIT' THEN 2   -- Second most common
  WHEN product_type = 'PREPAID' THEN 3 -- Least common
  ELSE 0
END

-- Avoid repeated CASE statements - calculate once
-- Bad
SELECT 
  CASE WHEN amount > 1000 THEN 'HIGH' ELSE 'LOW' END AS category,
  CASE WHEN amount > 1000 THEN amount * 0.1 ELSE amount * 0.05 END AS fee
FROM transactions

-- Better
SELECT 
  category,
  CASE WHEN category = 'HIGH' THEN amount * 0.1 ELSE amount * 0.05 END AS fee
FROM (
  SELECT 
    amount,
    CASE WHEN amount > 1000 THEN 'HIGH' ELSE 'LOW' END AS category
  FROM transactions
) t
```

### Date and Time Optimization

**Use efficient date filtering techniques**

```sql
-- Use date partition columns directly
-- Good
WHERE dw_process_date = '2023-12-31'

-- Avoid functions on partition columns - prevents partition pruning
-- Bad
WHERE YEAR(dw_process_date) = 2023 AND MONTH(dw_process_date) = 12

-- Better
WHERE dw_process_date >= '2023-12-01' AND dw_process_date < '2024-01-01'

-- Use date literals in correct format
WHERE dw_process_date = '2023-12-31'  -- YYYY-MM-DD format
```

### JOIN Order Optimization

**Order joins from smallest to largest table**

```sql
-- Optimal join order - small tables first
SELECT *
FROM small_table1 s1
INNER JOIN [BROADCAST] small_table2 s2 ON s1.id = s2.id
INNER JOIN [BROADCAST] small_table3 s3 ON s2.id = s3.id
INNER JOIN [SHUFFLE] large_table l ON s3.id = l.id
WHERE l.dw_process_date = '2023-12-31'
```

### Avoiding Cartesian Products

**Always include proper join conditions**

```sql
-- Bad - Cartesian product
SELECT * FROM table1, table2
WHERE table1.date = '2023-12-31'

-- Good - Explicit join condition
SELECT * FROM table1
INNER JOIN table2 ON table1.id = table2.id
WHERE table1.date = '2023-12-31'
```

### Window Function Optimization

**Use window functions efficiently for analytical queries**

```sql
-- Partition window functions appropriately
SELECT 
  merchant_id,
  transaction_date,
  amount,
  SUM(amount) OVER (
    PARTITION BY merchant_id 
    ORDER BY transaction_date 
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) AS rolling_7day_sum
FROM core.cut_clear_dtl_enc
WHERE dw_process_date BETWEEN '2023-01-01' AND '2023-12-31'

-- Avoid multiple window functions with same partitioning
-- Bad
SELECT 
  ROW_NUMBER() OVER (PARTITION BY merchant_id ORDER BY date) AS rn,
  RANK() OVER (PARTITION BY merchant_id ORDER BY date) AS rnk
FROM transactions

-- Better - Use single window function when possible
SELECT 
  ROW_NUMBER() OVER (PARTITION BY merchant_id ORDER BY date) AS rn
FROM transactions
```

### Statistics and Compute Stats

**Keep table statistics updated for optimal query planning**

```sql
-- Run COMPUTE STATS after creating/updating tables
COMPUTE STATS coe_enc.e105572_my_custom_table;

-- Check statistics
SHOW TABLE STATS coe_enc.e105572_my_custom_table;
SHOW COLUMN STATS coe_enc.e105572_my_custom_table;
```

### Query Hints and Directives

**Use Impala query hints to guide the optimizer**

```sql
-- Straight join - forces join order as written
SELECT STRAIGHT_JOIN *
FROM small_table
JOIN large_table ON small_table.id = large_table.id

-- Shuffle hint - forces shuffle join
SELECT * FROM table1
JOIN [SHUFFLE] table2 ON table1.id = table2.id

-- Broadcast hint - forces broadcast join
SELECT * FROM large_table
JOIN [BROADCAST] small_table ON large_table.id = small_table.id

-- Noshuffle hint - prevents shuffle
SELECT /*+ NOSHUFFLE */ * FROM table1, table2
WHERE table1.id = table2.id
```

### Memory Management in Queries

**Design queries to minimize memory usage**

```sql
-- Break large queries into smaller steps using temporary tables
-- Instead of one massive query, use intermediate tables

-- Step 1: Create intermediate result
DROP TABLE IF EXISTS coe_enc.e105572_temp_step1;
CREATE TABLE coe_enc.e105572_temp_step1 AS
SELECT * FROM core.cut_clear_dtl_enc
WHERE dw_process_date = '2023-12-31'
  AND dw_iss_country_cd = 'USA';

-- Step 2: Use intermediate result
DROP TABLE IF EXISTS coe_enc.e105572_final_result;
CREATE TABLE coe_enc.e105572_final_result AS
SELECT * FROM coe_enc.e105572_temp_step1
JOIN [BROADCAST] core.product_hierarchy 
  ON temp_step1.product_cd = product_hierarchy.product_code;

-- Step 3: Clean up
DROP TABLE IF EXISTS coe_enc.e105572_temp_step1;
```

### Analyzing Query Performance

**Use EXPLAIN and PROFILE to understand query execution**

```sql
-- Get query execution plan
EXPLAIN SELECT * FROM core.cut_clear_dtl_enc 
WHERE dw_process_date = '2023-12-31';

-- Get detailed execution profile after running query
PROFILE;

-- Look for:
-- - Partition pruning effectiveness
-- - Join strategy (broadcast vs shuffle)
-- - Rows processed vs rows returned
-- - Memory spills
-- - Long-running operators
```

***

## 9. Practical Examples & Quiz Solutions

### Real-World Query Optimization Example

**Context:** User is trying to pull 30% sample data of consumer credit portfolio of Indonesia

#### Original Query (Not Optimized)

```sql
create table coe_enc.e105572_idn_cons_credit_sample_30_pct
stored as parquet
location '/das/coe/enc/e105572/e105572_idn_cons_credit_sample_30_pct' as
select latest_parent_de93_issuer_id, de22_cardholder_present_cd, dw_net_pd_amt, dw_net_pd_cnt,
cast(prod.product_type_code as smallint) as latest_product_type_cd
FROM
(       select *
        FROM
        core.cut_clear_dtl_enc clearing
        where clearing.dw_process_date between "2023-08-01" and "2024-07-31") clearing
INNER JOIN [BROADCAST] core.product_hierarchy as prod on (clearing.dw_product_cd=prod.product_code)
where clearing.dw_iss_country_cd in ("IDN")
and clearing.dw_acct_ranuni_grp_num<30
and prod.credit_debit_ind in ("CR")
and prod.product_type_code != 2
and prod.level_number=5
```

#### Optimized Query

```sql
create table coe_enc.e105572_idn_cons_credit_sample_30_pct
stored as parquet
location '/das/coe/enc/e105572/e105572_idn_cons_credit_sample_30_pct' as
select latest_parent_de93_issuer_id, de22_cardholder_present_cd, dw_net_pd_amt, dw_net_pd_cnt,
cast(prod.product_type_code as smallint) as latest_product_type_cd
FROM
(       select latest_parent_de93_issuer_id, de22_cardholder_present_cd, dw_net_pd_amt, dw_net_pd_cnt
        FROM
        core.cut_clear_dtl_enc clearing
        where clearing.dw_process_date between "2023-08-01" and "2024-07-31"
        and clearing.dw_iss_country_cd in ("IDN")
        and clearing.dw_acct_ranuni_grp_num<30
) clearing
INNER JOIN [BROADCAST] core.product_hierarchy as prod on (clearing.dw_product_cd=prod.product_code)
where prod.credit_debit_ind in ("CR")
and prod.product_type_code != 2
and prod.level_number=5
```

#### Key Improvements:

1. **Fetching only the required columns** in the subquery instead of SELECT *
2. **Putting the required filters in the main query** instead of pulling the global data
   - Moved `dw_iss_country_cd` and `dw_acct_ranuni_grp_num` filters to the subquery
3. Used **BROADCAST** for small table (product_hierarchy)
4. Avoided unnecessary data scanning

***

## 9. Quick Reference Summary

### Essential Guidelines Checklist

✅ **Data Pull Best Practices:**
- Always use process date and partition columns in filters
- Create files in employee ID location, not home directory
- Use broadcast/shuffle joins as per recommended table list
- Check table size before using broadcast (< 1GB)

✅ **Query Structure:**
- Never do SELECT * without filters on core tables
- Select only required columns
- Filter data in subqueries before JOINs
- Apply filters to larger tables before performing joins

✅ **Table Management:**
- Table names must have employee ID attached (e.g., `coe_hsh.eXXXXXX_Filename`)
- Always use DROP TABLE IF EXISTS before creating tables
- Drop project files 1 quarter after completion
- Store metadata in user-specific folders

✅ **Code Guidelines:**
- Data can be pulled for 13 months maximum in Impala
- Filter bigger tables (cut_clear_dtl_enc/hsh) during join statements
- Use partition columns in WHERE clauses

✅ **Resource Management:**
- Do not acquire more than 3 PySpark ports at a time
- Shut down kernels at least once per day
- Stop unused processes not tied to notebooks
- Clean environment before resource-intensive tasks

✅ **Performance Tips:**
- Use BROADCAST for tables < 1GB
- Use SHUFFLE for larger tables
- Apply filters early in query execution
- Avoid unnecessary columns and data scanning

### Query Optimization Process

1. **Identify bottlenecks** - Use EXPLAIN to analyze query plan
2. **Apply filters early** - Use partition and process date columns
3. **Optimize JOINs** - Choose appropriate broadcast/shuffle strategy
4. **Select only needed columns** - Avoid SELECT *
5. **Test and validate** - Check performance improvements
6. **Monitor resources** - Ensure fair usage

### Common Anti-Patterns to Avoid

❌ SELECT * from core tables without filters
❌ Not using partition columns in WHERE clause
❌ Acquiring more than 3 PySpark ports
❌ Creating files in home directory instead of employee ID location
❌ Not shutting down kernels after work
❌ Using BROADCAST on tables > 1GB
❌ Not checking table names before DROP operations
❌ Pulling more than 13 months of data in single Impala query
❌ Using functions on partition columns (breaks partition pruning)
❌ Leading wildcards in LIKE operations (%pattern%)
❌ Cartesian products from missing join conditions
❌ Using DISTINCT instead of GROUP BY
❌ Using UNION instead of UNION ALL when duplicates don't matter
❌ Nested aggregations (COUNT(DISTINCT) on large tables)
❌ Not running COMPUTE STATS after table creation
❌ Multiple window functions with identical partitioning
❌ Using REGEXP when simple LIKE works
❌ Not filtering NULL values before joins
❌ Repeating CASE statements instead of calculating once

### Impala-Specific Performance Checklist

✅ **Query Planning:**
- Run EXPLAIN before executing complex queries
- Check partition pruning is working
- Verify join strategy (broadcast/shuffle) is appropriate
- Review estimated rows and memory requirements

✅ **Data Access:**
- Always filter on partition columns first
- Use exact date matches when possible (not date functions)
- Select only needed columns
- Apply filters in subqueries before joins

✅ **Join Optimization:**
- Use broadcast for tables < 1GB
- Place smallest table first in join order
- Filter both sides before joining
- Remove NULL values before joins when possible

✅ **Aggregations:**
- Use GROUP BY instead of DISTINCT
- Avoid nested aggregations
- Order GROUP BY by cardinality (low to high)
- Use two-step aggregation for COUNT(DISTINCT) on large tables

✅ **Data Types:**
- Use smallest appropriate data types (TINYINT, SMALLINT)
- Cast to efficient types early in query
- Be consistent with data types across joins

✅ **String Operations:**
- Avoid leading wildcards in LIKE
- Use exact match or IN when possible
- Minimize REGEXP usage
- Use LIKE instead of REGEXP when sufficient

✅ **Performance Monitoring:**
- Use PROFILE after query execution
- Monitor memory usage and spills
- Check for long-running operators
- Identify bottlenecks in execution plan

✅ **Maintenance:**
- Run COMPUTE STATS after table creation/updates
- Drop temporary tables after use
- Clean up old project files quarterly
- Keep statistics current for optimizer

***

## Additional Resources

### Impala Query Analysis Commands

```sql
-- Check table size and statistics
SHOW TABLE STATS tablename;
SHOW COLUMN STATS tablename;

-- Update statistics (critical for optimization)
COMPUTE STATS tablename;

-- Analyze query execution plan
EXPLAIN query_here;

-- Get detailed performance profile
-- Run your query first, then:
PROFILE;

-- Check available tables in database
SHOW TABLES IN database_name;

-- View table schema
DESCRIBE tablename;
DESCRIBE FORMATTED tablename;  -- More detailed

-- Check partitions
SHOW PARTITIONS tablename;

-- Refresh metadata after external changes
REFRESH tablename;
INVALIDATE METADATA tablename;  -- Full refresh
```

### Performance Tuning Quick Tips

1. **Partition Pruning Check**: In EXPLAIN output, look for "partitions=X/Y" where X < Y indicates successful pruning
2. **Memory Estimation**: Check EXPLAIN for estimated memory - if too high, break query into steps
3. **Cardinality Estimates**: Compare estimated vs actual rows in PROFILE - large differences indicate stale statistics
4. **Broadcast vs Shuffle**: EXPLAIN shows join strategy - verify it matches recommendations
5. **Spills to Disk**: In PROFILE, look for memory spills which indicate need for optimization

### Common EXPLAIN Output Indicators

```
Good Signs:
- "partitions=1/365" (good partition pruning)
- "BROADCAST JOIN" for small tables
- Low estimated memory requirements
- Filter predicates pushed to scan nodes

Warning Signs:
- "partitions=365/365" (no partition pruning)
- "SHUFFLE JOIN" for small tables
- Very high estimated memory
- Cartesian products
- Many unpartitioned data reads
```

### Optimization Priority Matrix

**High Impact, Easy to Implement:**
1. Add partition column filters
2. Select only required columns (avoid SELECT *)
3. Use appropriate broadcast/shuffle hints
4. Filter before joins

**High Impact, Moderate Effort:**
5. Break complex queries into steps with temp tables
6. Run COMPUTE STATS regularly
7. Optimize join order
8. Use CTEs for complex subqueries

**Moderate Impact, Easy to Implement:**
9. Use efficient data types (CAST to smaller types)
10. Replace DISTINCT with GROUP BY
11. Use UNION ALL instead of UNION
12. Avoid leading wildcards in LIKE

**Fine-Tuning (After basics are done):**
13. Optimize CASE statement order
14. Optimize window function partitioning
15. Use query hints (STRAIGHT_JOIN, etc.)
16. Two-step aggregation for COUNT(DISTINCT)

### Troubleshooting Slow Queries

**Step-by-step diagnostic approach:**

1. **Check EXPLAIN plan**
   ```sql
   EXPLAIN your_query_here;
   ```
   Look for: partition pruning, join strategy, estimated rows

2. **Verify partition filtering**
   - Ensure partition columns in WHERE clause
   - No functions on partition columns

3. **Check table statistics**
   ```sql
   SHOW TABLE STATS tablename;
   ```
   Run COMPUTE STATS if outdated

4. **Review join strategy**
   - Small tables should use BROADCAST
   - Large tables should use SHUFFLE
   - Add explicit hints if needed

5. **Run PROFILE after execution**
   ```sql
   PROFILE;
   ```
   Look for: memory spills, long operators, row count mismatches

6. **Break into smaller queries**
   - Use temp tables for intermediate results
   - Isolate the slow part of the query

7. **Contact support if needed**
   - Provide EXPLAIN output
   - Share PROFILE results
   - Document what optimizations you've tried

***

**Document Version:** 2.0  
**Last Updated:** Based on Hadoop Usage Guidelines slides + Advanced Impala Optimization Techniques  
**Maintained by:** Code Optimization Team