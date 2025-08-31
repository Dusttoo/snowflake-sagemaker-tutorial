-- Snowflake Setup Script for Animal Insights Pipeline
-- Run these commands in your Snowflake worksheet

-- 1. Create Storage Integration (replace with your actual role ARN)
CREATE STORAGE INTEGRATION s3_integration
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::YOUR_ACCOUNT:role/snowflake-s3-role-YOUR_SUFFIX'
  STORAGE_ALLOWED_LOCATIONS = ('s3://animal-insights-YOUR_SUFFIX/');

-- 2. Get integration details (save these for Terraform configuration)
DESC STORAGE INTEGRATION s3_integration;

-- 3. Create database and schema
CREATE DATABASE IF NOT EXISTS animal_insights;

USE DATABASE animal_insights;

CREATE SCHEMA IF NOT EXISTS raw_data;

CREATE SCHEMA IF NOT EXISTS analytics;

-- 4. Create external stage
CREATE STAGE animal_data_stage
  STORAGE_INTEGRATION = s3_integration
  URL = 's3://animal-insights-YOUR_SUFFIX/'
  FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1 FIELD_OPTIONALLY_ENCLOSED_BY = '"');

-- 5. Create raw data table
CREATE TABLE raw_data.animal_outcomes (
    animal_id STRING,
    date_of_birth DATE,
    name STRING,
    datetime TIMESTAMP,
    month_year STRING,
    outcome_type STRING,
    outcome_subtype STRING,
    animal_type STRING,
    sex_upon_outcome STRING,
    age_upon_outcome STRING,
    breed STRING,
    color STRING,
    load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- 6. Create cleaned data view
CREATE OR REPLACE VIEW analytics.clean_animal_outcomes AS
SELECT 
  animal_id,
  COALESCE(name, 'Unknown') as animal_name,
  datetime::timestamp as outcome_datetime,
  outcome_type,
  outcome_subtype,
  animal_type,
  sex_upon_outcome,
  CASE 
    WHEN age_upon_outcome LIKE '%year%' THEN 
      TRY_CAST(SPLIT_PART(age_upon_outcome, ' ', 1) AS INTEGER) * 365
    WHEN age_upon_outcome LIKE '%month%' THEN 
      TRY_CAST(SPLIT_PART(age_upon_outcome, ' ', 1) AS INTEGER) * 30
    WHEN age_upon_outcome LIKE '%week%' THEN 
      TRY_CAST(SPLIT_PART(age_upon_outcome, ' ', 1) AS INTEGER) * 7
    WHEN age_upon_outcome LIKE '%day%' THEN 
      TRY_CAST(SPLIT_PART(age_upon_outcome, ' ', 1) AS INTEGER)
    ELSE NULL
  END as age_days,
  breed,
  color,
  EXTRACT(HOUR FROM datetime) as outcome_hour,
  EXTRACT(MONTH FROM datetime) as outcome_month,
  EXTRACT(YEAR FROM datetime) as outcome_year,
  load_timestamp
FROM raw_data.animal_outcomes
WHERE outcome_type IS NOT NULL;

-- 7. Load data from S3 (run after uploading data)
-- COPY INTO raw_data.animal_outcomes
-- FROM @animal_data_stage/raw/Austin_Animal_Center_Outcomes__10_01_2013_to_05_05_2025__20250830.csv;

-- 8. Data quality checks
-- SELECT COUNT(*) FROM raw_data.animal_outcomes;
-- SELECT outcome_type, COUNT(*) FROM analytics.clean_animal_outcomes GROUP BY outcome_type ORDER BY 2 DESC;
-- SELECT animal_type, COUNT(*) FROM analytics.clean_animal_outcomes GROUP BY animal_type ORDER BY 2 DESC;