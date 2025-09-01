-- Snowflake Setup Script for Animal Insights Pipeline
-- IMPORTANT: Replace placeholders with your actual values from terraform output

-- Step 1: Create warehouse (cost-optimized)
CREATE WAREHOUSE IF NOT EXISTS DEMO_WH WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE COMMENT = 'Demo warehouse for animal insights tutorial';

-- Step 2: Create database and schemas
CREATE DATABASE IF NOT EXISTS ANIMAL_INSIGHTS COMMENT = 'Database for animal adoption prediction pipeline';

USE DATABASE ANIMAL_INSIGHTS;

CREATE SCHEMA IF NOT EXISTS RAW_DATA COMMENT = 'Schema for raw data from S3';

CREATE SCHEMA IF NOT EXISTS ANALYTICS COMMENT = 'Schema for cleaned and transformed data';

USE WAREHOUSE DEMO_WH;

-- Step 3: Create storage integration
-- REPLACE with your actual values from terraform output
CREATE OR REPLACE STORAGE INTEGRATION s3_integration
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::YOUR_ACCOUNT:role/snowflake-s3-role-YOUR_SUFFIX'
  STORAGE_ALLOWED_LOCATIONS = ('s3://animal-insights-YOUR_SUFFIX/')
  COMMENT = 'Integration for accessing S3 data bucket';

-- Step 4: Get integration details (SAVE THESE VALUES!)
DESC STORAGE INTEGRATION s3_integration;

-- Step 5: Create file format for CSV files
CREATE OR REPLACE FILE FORMAT csv_format
  TYPE = 'CSV'
  FIELD_DELIMITER = ','
  RECORD_DELIMITER = '\n'
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  TRIM_SPACE = TRUE
  ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
  REPLACE_INVALID_CHARACTERS = TRUE
  DATE_FORMAT = 'MM/DD/YYYY'
  TIMESTAMP_FORMAT = 'MM/DD/YYYY HH12:MI:SS AM'
  COMMENT = 'File format for Austin Animal Center CSV files';

-- Step 6: Create external stage
CREATE
OR
REPLACE
    STAGE animal_data_stage STORAGE_INTEGRATION = s3_integration URL = 's3://animal-insights-YOUR_SUFFIX/' FILE_FORMAT = csv_format COMMENT = 'External stage for animal data files';

-- Step 7: Test the stage (should return empty or show files)
LIST @animal_data_stage;

-- Step 8: Create raw data table (matching actual CSV columns)
USE SCHEMA RAW_DATA;

CREATE
OR
REPLACE
TABLE animal_outcomes (
    animal_id STRING,
    date_of_birth STRING,
    name STRING,
    datetime STRING,
    monthyear STRING,
    outcome_type STRING,
    outcome_subtype STRING,
    animal_type STRING,
    sex_upon_outcome STRING,
    age_upon_outcome STRING,
    breed STRING,
    color STRING,
    load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) COMMENT = 'Raw animal outcome data from Austin Animal Center';

-- Step 9: Load data (run AFTER uploading CSV to S3)
COPY INTO RAW_DATA.animal_outcomes (
    animal_id,
    date_of_birth,
    name,
    datetime,
    monthyear,
    outcome_type,
    outcome_subtype,
    animal_type,
    sex_upon_outcome,
    age_upon_outcome,
    breed,
    color
)
FROM
    @animal_data_stage / raw / austin_animal_outcomes.csv FILE_FORMAT = csv_format ON_ERROR = 'CONTINUE';

-- Step 10: Verify the load
SELECT COUNT(*) as total_records FROM RAW_DATA.animal_outcomes;

SELECT outcome_type, COUNT(*) as count
FROM RAW_DATA.animal_outcomes
GROUP BY
    outcome_type;

-- Step 11: Create cleaned view for analytics
USE SCHEMA ANALYTICS;

CREATE OR REPLACE VIEW clean_animal_outcomes AS
SELECT
    -- IDs and basic info
    animal_id, COALESCE(
        NULLIF(TRIM(name), ''), 'Unknown'
    ) as animal_name,

-- Date conversions with error handling
TRY_TO_DATE (date_of_birth, 'MM/DD/YYYY') as birth_date,
TRY_TO_TIMESTAMP (
    datetime,
    'MM/DD/YYYY HH12:MI:SS AM'
) as outcome_datetime,

-- Categorical fields (cleaned and standardized)
TRIM(UPPER(outcome_type)) as outcome_type,
TRIM(outcome_subtype) as outcome_subtype,
TRIM(UPPER(animal_type)) as animal_type,
TRIM(UPPER(sex_upon_outcome)) as sex_upon_outcome,
TRIM(breed) as breed,
TRIM(color) as color,

-- Age parsing (convert text to days)
CASE
    WHEN age_upon_outcome ILIKE '%year%' THEN TRY_CAST (
        REGEXP_SUBSTR(age_upon_outcome, '\\d+') AS INTEGER
    ) * 365
    WHEN age_upon_outcome ILIKE '%month%' THEN TRY_CAST (
        REGEXP_SUBSTR(age_upon_outcome, '\\d+') AS INTEGER
    ) * 30
    WHEN age_upon_outcome ILIKE '%week%' THEN TRY_CAST (
        REGEXP_SUBSTR(age_upon_outcome, '\\d+') AS INTEGER
    ) * 7
    WHEN age_upon_outcome ILIKE '%day%' THEN TRY_CAST (
        REGEXP_SUBSTR(age_upon_outcome, '\\d+') AS INTEGER
    )
    ELSE NULL
END as age_in_days,

-- Time features for ML
EXTRACT(
    HOUR
    FROM TRY_TO_TIMESTAMP (
            datetime, 'MM/DD/YYYY HH12:MI:SS AM'
        )
) as outcome_hour,
EXTRACT(
    MONTH
    FROM TRY_TO_TIMESTAMP (
            datetime, 'MM/DD/YYYY HH12:MI:SS AM'
        )
) as outcome_month,
EXTRACT(
    YEAR
    FROM TRY_TO_TIMESTAMP (
            datetime, 'MM/DD/YYYY HH12:MI:SS AM'
        )
) as outcome_year,

-- Primary breed (first part before mix indicator)
TRIM(SPLIT_PART (breed, ' Mix', 1)) as primary_breed,

-- Binary target for ML (1 = adopted, 0 = not adopted)
CASE
    WHEN UPPER(outcome_type) = 'ADOPTION' THEN 1
    ELSE 0
END as adopted_label,

-- Metadata
load_timestamp
FROM RAW_DATA.animal_outcomes
WHERE
    animal_id IS NOT NULL
    AND outcome_type IS NOT NULL COMMENT = 'Cleaned and feature-engineered animal outcomes for ML training';

-- Step 12: Test the cleaned view
SELECT COUNT(*) as cleaned_records
FROM ANALYTICS.clean_animal_outcomes;

SELECT adopted_label, COUNT(*)
FROM ANALYTICS.clean_animal_outcomes
GROUP BY
    adopted_label;