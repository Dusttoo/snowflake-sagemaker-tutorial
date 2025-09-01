# Animal Adoption Prediction Pipeline

A practical hands-on project to build a complete **animal shelter data pipeline** using **Snowflake**, **AWS SageMaker**, and **Terraform**.

**Goal:** Build an automated pipeline that predicts animal adoption outcomes to help shelters prioritize outreach efforts.

## What You'll Build

```
Austin Animal Data → AWS S3 → Snowflake → ML Model → Predictions
                       ↑         ↑          ↑         ↑
                   Data Lake   Analytics   Training   API
```

**End Result**: A working ML model that predicts adoption likelihood with ~80% accuracy, plus the infrastructure to deploy it in production.

## Learning Path Overview

This hands-on tutorial takes you through building a complete data science pipeline from raw data to deployed machine learning model. You'll work with real Austin Animal Center data (170K+ records) to predict animal adoption outcomes.

**Part 1: Data Exploration & Insights** (Notebook 1)
- Load and explore animal shelter records
- Discover patterns in adoption rates and timing
- Generate data visualizations and insights
- Prepare clean data for machine learning

**Part 2: Machine Learning Training** (Notebook 2)  
- Engineer features from raw animal data
- Train Random Forest classifier
- Evaluate model performance and feature importance
- Save trained model for deployment

**Part 3: Model Deployment** (Notebook 3)
- Deploy model to AWS SageMaker for real-time predictions
- Create batch prediction workflows
- Set up production monitoring and scaling

### What You'll Learn

**Data Engineering Skills:**
- Cloud data lake and warehouse architecture
- ETL/ELT pipeline patterns with S3 and Snowflake
- Data quality assessment and validation techniques
- Secure cross-account access configuration

**Machine Learning Skills:**
- End-to-end ML workflow from data to deployment
- Feature engineering for tabular data
- Model evaluation and interpretation
- Production deployment with SageMaker

**Infrastructure Skills:**
- Infrastructure as Code with Terraform
- AWS services integration (S3, IAM, SageMaker)
- Security best practices and cost optimization

## Prerequisites

**Required Accounts** (all have free tiers):
- AWS account with appropriate permissions
- Snowflake account ([free trial](https://signup.snowflake.com/))

**Required Software:**
- Python 3.8+ installed
- Git for cloning the repository

**Knowledge Level:** Beginner-friendly
- Basic knowledge of Python and SQL helpful
- Familiarity with command line operations
- No prior AWS/ML experience required

## Quick Start

The automated setup script handles most of the configuration for you:

```bash
git clone https://github.com/Dusttoo/snowflake-sagemaker-tutorial
cd snowflake-sagemaker-tutorial
python setup.py
```

This script will guide you through:
1. Checking prerequisites (Python, AWS CLI, Terraform)
2. Setting up Python virtual environment
3. Configuring AWS credentials
4. Deploying infrastructure with Terraform
5. Setting up Snowflake integration
6. Preparing data and configuration

**If you encounter issues**, refer to the detailed manual setup below.

### Automated Helper Scripts

This tutorial includes several automated scripts to streamline your experience:

- **`setup.py`** - Complete automated setup (infrastructure + configuration)
- **`validate_setup.py`** - Diagnose environment and setup issues  
- **`config_generator.py`** - Generate configuration files for notebooks
- **`cleanup.py`** - Safely remove all AWS resources to avoid charges

Each script can be run independently as needed throughout the tutorial.

## Manual Setup Guide

### 1. Environment Setup

```bash
# Clone the project
git clone https://github.com/Dusttoo/snowflake-sagemaker-tutorial
cd snowflake-sagemaker-tutorial

# Create and activate Python virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Validate your setup (optional but recommended)
python validate_setup.py
```

### 2. AWS Configuration

```bash
# Install and configure AWS CLI
pip install awscli
aws configure
# Enter your Access Key ID, Secret Access Key, region, and output format

# Verify configuration
aws sts get-caller-identity
```

### 3. Understanding the Data

The Austin Animal Center dataset (`data/austin_animal_outcomes.csv`) contains 173,775 records with these key fields:
- **Animal ID**: Unique identifier
- **DateTime**: Outcome timestamp  
- **Outcome Type**: Adoption, Transfer, Euthanasia, etc.
- **Animal Type**: Dog, Cat, Bird, etc.
- **Breed**: Animal breed information
- **Age upon Outcome**: Age when outcome occurred

The data is already included in the repository, so you won't need to download it separately.

### ETL vs. ELT: Which Approach Do We Use?

When working with data pipelines, you’ll often hear about **ETL** (Extract → Transform → Load) and **ELT** (Extract → Load → Transform):

- **ETL**: Data is **extracted** from a source, **transformed** (cleaned, aggregated, reshaped) before being loaded into the target data warehouse.  
  *Good for*: legacy systems, smaller datasets, or when transformations must happen before storage.

- **ELT**: Data is **extracted** from a source and **loaded** directly into the warehouse in raw form. Transformations are then applied **inside the warehouse** using SQL or other compute engines.  
  *Good for*: cloud-native architectures, large datasets, and leveraging the power of modern warehouses like Snowflake.

**In this tutorial, we use ELT.**  
We load the raw Austin Animal Center data into **Snowflake first**, and then perform cleaning, enrichment, and feature engineering inside Snowflake.  

✅ **Why ELT?**  
- Snowflake is designed for fast, scalable in-warehouse transformations.  
- ELT simplifies the pipeline by keeping raw data available for reprocessing later.  
- It avoids overcomplicating the AWS ingestion stage (S3 → Snowflake).  
- It’s the industry-standard pattern for modern cloud data platforms.

### 4. Infrastructure Deployment with Terraform

Due to the circular dependency between AWS and Snowflake, we use a two-stage deployment approach:

#### Stage 1: Deploy Basic Infrastructure

```bash
# Navigate to terraform directory
cd terraform/

# Initialize and deploy basic infrastructure
terraform init
terraform plan
terraform apply
```

**Save the outputs** - you'll need them for Snowflake:
```bash
terraform output
# Note the s3_bucket_name and snowflake_role_arn values
```

#### Stage 2: Configure Snowflake Integration

**Step 1: Create Snowflake Storage Integration**

Log into your Snowflake account and create a worksheet. Replace the placeholder values with your actual values from Stage 1:

```sql
-- Create storage integration (replace with YOUR values)
CREATE STORAGE INTEGRATION s3_integration
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'YOUR_ROLE_ARN_FROM_TERRAFORM_OUTPUT'
  STORAGE_ALLOWED_LOCATIONS = ('s3://YOUR_BUCKET_NAME/');

-- Get Snowflake's AWS details
DESC STORAGE INTEGRATION s3_integration;
```

**Step 2: Extract Snowflake Security Details**

From the `DESC` command output, find these two values:

| Property | What to Extract |
|----------|-----------------|
| **STORAGE_AWS_IAM_USER_ARN** | Extract the 12-digit account ID |
| **STORAGE_AWS_EXTERNAL_ID** | Copy the exact string |

**Step 3: Update Terraform Configuration**

Create your configuration file:
```bash
cd terraform/
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform/terraform.tfvars` with the Snowflake values:
```hcl
aws_region = "us-east-1"
snowflake_account_id = "123456789012"              # Your 12-digit account ID
snowflake_external_id = "ABC123_SFCRole=1_xyz="    # Your exact external ID
enable_snowflake_integration = true
```

**Step 4: Apply Security Updates**
```bash
terraform validate
terraform plan
terraform apply
```

**Step 5: Test the Integration**
```sql
-- Test if Snowflake can access your S3 bucket
LIST @animal_data_stage;
```

### 5. Set Up Snowflake Database Objects

Run these commands in your Snowflake worksheet:

```sql
-- Create database and schema
CREATE DATABASE animal_insights;
USE DATABASE animal_insights;
CREATE SCHEMA raw_data;
CREATE SCHEMA analytics;

-- Create external stage
CREATE STAGE animal_data_stage
  STORAGE_INTEGRATION = s3_integration
  URL = 's3://your-bucket-name/'
  FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1);

-- Create target table with correct structure
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
    color STRING
);
```

### 6. Load Data

```bash
# Upload data to S3 (the CSV file is already included)
aws s3 cp data/austin_animal_outcomes.csv s3://your-bucket-name/raw/
```

Then load into Snowflake:
```sql
COPY INTO raw_data.animal_outcomes
FROM @animal_data_stage/raw/austin_animal_outcomes.csv;

-- Verify the load
SELECT COUNT(*) FROM raw_data.animal_outcomes;
SELECT * FROM raw_data.animal_outcomes LIMIT 5;
```

## Machine Learning Tutorial with Jupyter Notebooks

Now that your infrastructure is ready, it's time to build your ML pipeline using the interactive notebooks.

### Launch Jupyter Lab

```bash
# Make sure you're in the project root with virtual environment active
cd snowflake-sagemaker-tutorial
source venv/bin/activate

# Generate configuration for notebooks (optional - can also be done within notebooks)
python config_generator.py

# Launch Jupyter Lab
jupyter lab
```

This opens Jupyter Lab in your browser. Navigate to the `notebooks/` folder to access the three tutorial notebooks.

### Notebook 1: Data Exploration (`01_data_exploration.ipynb`)

This notebook provides a comprehensive analysis of the Austin Animal Center dataset.

**What you'll discover:**
- Dataset structure and data quality issues
- Outcome distributions and adoption patterns  
- Temporal trends (seasonal patterns, peak times)
- Animal characteristics (breeds, ages, types)

**Key code patterns you'll use:**
```python
# Data loading with error handling
explorer = AnimalDataExplorer(s3_bucket=BUCKET_NAME)
explorer.load_data()

# Outcome analysis
outcome_counts = explorer.data['Outcome Type'].value_counts()
adoption_rate = (outcomes.get('Adoption', 0) / total_animals) * 100
```

**Run the notebook** and observe:
- How missing data is handled across different columns
- Which visualization techniques reveal patterns most clearly
- How to convert age strings into numeric values for analysis

### Notebook 2: ML Training (`02_ml_training.ipynb`)

This notebook builds a predictive model using the insights from data exploration.

**What you'll build:**
- Feature preprocessing pipeline for categorical data
- Random Forest classifier with hyperparameter tuning
- Model evaluation with accuracy metrics and feature importance
- Model persistence for deployment

**Key concepts you'll apply:**
```python
# Feature preprocessing
def preprocess_features(df):
    # Create binary target: 1 for Adoption, 0 for others
    df['adopted_label'] = (df['Outcome Type'] == 'Adoption').astype(int)
    return df

# Model training
model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
model.fit(X_train_encoded, y_train)
```

**Experiment with:**
- Different feature combinations and their impact on accuracy
- How categorical encoding affects model performance
- Which animal characteristics are most predictive

### Notebook 3: Model Deployment (`03_model_deployment.ipynb`)

This notebook demonstrates how to deploy your trained model for production use.

**What you'll learn:**
- Loading and testing saved models locally
- Creating SageMaker inference scripts
- Batch prediction workflows
- Resource cleanup best practices

**Key deployment patterns:**
```python
# Local prediction testing
def test_local_predictions():
    predictions = model.predict(processed_sample)
    probabilities = model.predict_proba(processed_sample)[:, 1]
    return predictions, probabilities

# Batch predictions
def make_batch_predictions(input_file_path):
    data = pd.read_csv(input_file_path)
    predictions = model.predict(processed_data)
    return predictions
```

**Try exploring:**
- How prediction confidence varies across different animal types
- What happens when you introduce new categories not seen in training
- Different deployment strategies for your specific use case

## Data Transformation and Analysis

Create analytical views in Snowflake for deeper insights:

```sql
-- Create cleaned data view
CREATE VIEW analytics.clean_animal_outcomes AS
SELECT 
  animal_id,
  COALESCE(name, 'Unknown') as animal_name,
  datetime::timestamp as outcome_datetime,
  outcome_type,
  animal_type,
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
  color
FROM raw_data.animal_outcomes
WHERE outcome_type IS NOT NULL;
```

Use this view to answer questions like:
- Which breeds have the highest adoption rates?
- How does adoption likelihood vary by age?
- Are there seasonal patterns in different outcome types?

## Project Structure

```
snowflake-sagemaker-tutorial/
├── README.md                          # This comprehensive guide
├── setup.py                          # Automated setup script
├── config_generator.py               # Configuration management
├── validate_setup.py                 # Environment validation
├── cleanup.py                        # Resource cleanup
├── requirements.txt                  # Python dependencies
├── data/
│   └── austin_animal_outcomes.csv    # Dataset (included)
├── notebooks/
│   ├── 01_data_exploration.ipynb     # Data analysis & insights
│   ├── 02_ml_training.ipynb          # Model training & evaluation
│   └── 03_model_deployment.ipynb     # Production deployment
├── terraform/
│   ├── main.tf                       # Infrastructure definition
│   ├── variables.tf                  # Configuration variables
│   ├── outputs.tf                    # Resource outputs
│   └── terraform.tfvars.example      # Configuration template
├── sql/
│   └── snowflake_setup.sql          # Database setup scripts
├── models/                           # Saved ML models (generated)
└── code/                            # Deployment scripts (generated)
```

## Common Troubleshooting

### Quick Diagnosis

Before diving into specific issues, run the validation script to check your environment:

```bash
python validate_setup.py
```

This script checks:
- Python packages and dependencies
- AWS CLI configuration and credentials  
- Terraform installation and state
- Required files and data
- Infrastructure deployment status

### Setup Issues

**Terraform Permission Errors:**
- Ensure your AWS user has IAM permissions to create roles
- Check that bucket naming follows the pattern `animal-insights-*`

**Snowflake Integration Issues:**
- Verify the 12-digit account ID is extracted correctly
- Ensure external ID is copied exactly as shown
- Run `LIST @animal_data_stage;` to test connection

**Jupyter Issues:**
- Make sure virtual environment is activated
- Try `pip install --upgrade jupyter` if notebooks won't start
- Use `jupyter lab --port=8889` if default port is busy

### Data Loading Issues

**Column Count Mismatch:**
```sql
-- Drop and recreate table with correct structure
DROP TABLE IF EXISTS raw_data.animal_outcomes;
CREATE TABLE raw_data.animal_outcomes (/* 12 columns as shown above */);
```

**S3 Access Denied:**
- Verify AWS credentials are configured: `aws sts get-caller-identity`
- Check S3 bucket name matches terraform output
- Ensure data file was uploaded to the correct path

### Model Training Issues

**Poor Model Performance:**
- Check data quality and missing values
- Experiment with different feature combinations
- Try different algorithms or hyperparameters

**Memory Issues:**
- Reduce dataset size for initial testing
- Restart Jupyter kernel between runs
- Close unused notebook tabs

## Cost Management

**During Tutorial (1-3 days):**
- AWS: $1-5 (if cleaned up properly)
- Snowflake: $0 (free trial credits)

**If Resources Left Running:**
- SageMaker endpoint: ~$35/month
- Snowflake warehouse: ~$25/month  
- S3 storage: ~$1/month

## Cleanup

**Critical: Always clean up when finished to avoid charges!**

### Option 1: Automated Cleanup (Recommended)

```bash
# Run the automated cleanup script
python cleanup.py
```

This script will:
- Stop any running SageMaker endpoints
- Empty S3 buckets automatically
- Run `terraform destroy` to remove all AWS resources
- Verify cleanup completion and provide cost verification steps

### Option 2: Manual Cleanup

```bash
# Empty S3 bucket first (required before terraform destroy)
cd terraform/
terraform output s3_bucket_name
aws s3 rm s3://animal-insights-[suffix] --recursive

# Destroy all infrastructure
terraform destroy
```

**Important:** The automated cleanup script (`cleanup.py`) is safer as it handles the proper cleanup sequence and provides verification steps.

## Next Steps and Extensions

Once you complete the basic tutorial, consider these enhancements:

**Advanced ML Features:**
- Deep learning models with neural networks
- Real-time model retraining pipelines
- A/B testing for model improvements
- Multi-model ensemble approaches

**Production Scaling:**
- Apache Airflow for workflow orchestration
- Multi-region deployments
- Stream processing with Kinesis
- Advanced monitoring and alerting

**Integration Options:**
- Web application with Flask/Django
- Mobile app for shelter staff
- API Gateway for third-party integrations
- Slack bot for interactive predictions

## Architecture Summary

This tutorial creates a production-ready ML pipeline with:
- **Scalable Data Storage**: S3 for petabyte-scale data lakes
- **Analytics Platform**: Snowflake for SQL-based data processing
- **ML Infrastructure**: SageMaker for training and deployment
- **Infrastructure as Code**: Terraform for reproducible deployments
- **Security**: IAM roles with least-privilege access
- **Monitoring**: Built-in data quality checks and model validation

The pipeline demonstrates modern data engineering and ML practices that can be extended for enterprise use cases.

## Support

- **Issues**: Open a GitHub issue for bugs or questions
- **Discussions**: Use GitHub Discussions for general questions  
- **Contributions**: Pull requests welcome!

---

## Ready to Start?

**🚀 Quick Start**: `python setup.py`

**📖 Manual Setup**: Follow the step-by-step guide above

**📊 Begin Tutorial**: `jupyter lab` → Open `notebooks/01_data_exploration.ipynb`

---

*This project demonstrates modern data science and ML engineering practices using real-world data. Perfect for learning cloud-native ML pipelines, gaining hands-on AWS experience, and building a portfolio project.*