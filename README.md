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
- Batch predictions (local) — or use **SageMaker Batch Transform** for large offline jobs (see “Batch Transform (offline) at a glance”)
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
- AWS account with the following minimum IAM permissions:
  - `IAMFullAccess` (to create roles and policies)
  - `AmazonS3FullAccess` (to create and manage S3 buckets)
  - `AmazonSageMakerFullAccess` (for ML model deployment)
  - Alternatively, use an admin user for the tutorial (recommended for learning)
- Snowflake account ([free trial](https://signup.snowflake.com/))
  - Note your account identifier (format: `ORGNAME-ACCOUNTNAME` or legacy format)
  - Choose a region that matches your AWS region for optimal performance
  - Free trial includes $400 in credits, sufficient for this tutorial

**Required Software:**
- Python 3.8–3.11
- Git for cloning the repository
- **AWS CLI v2** (recommended). Install from the official installer for your OS.  
  *Note:* `pip install awscli` installs **AWS CLI v1**; use only if you specifically need v1.


**Knowledge Level:** Beginner-friendly
- Basic knowledge of Python and SQL helpful
- Familiarity with command line operations
- No prior AWS/ML experience required

**Version Pinning (training ↔ serving compatibility)**
- We deploy with a SageMaker **scikit-learn** container (e.g., `framework_version='1.2-1'`).
- **Training and serving must use compatible scikit-learn versions.**
- Recommended training pins (also reflected in `requirements.txt`):
  - `scikit-learn==1.2.1`
  - `joblib>=1.1.0`

## Quick Start

Before you run `setup_env.py`, make sure you have the following prerequisites ready:

✅ **Checklist:**
- [ ] AWS CLI v2 installed and configured (`aws --version`, `aws configure`)
- [ ] Python 3.8–3.11 (these versions are tested)
- [ ] An AWS region you'll use throughout (e.g., `us-east-1`)
- [ ] Terraform installed (`terraform --version`)
- [ ] S3 bucket name following the `animal-insights-*` convention is **not already taken**

The automated setup script handles most of the configuration for you:

```bash
git clone https://github.com/Dusttoo/snowflake-sagemaker-tutorial
cd snowflake-sagemaker-tutorial
python setup_env.py
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

- **`setup_env.py`** - Complete automated setup (infrastructure + configuration)
- **`validate_setup.py`** - Diagnose environment and setup issues  
- **`config_generator.py`** - Generate configuration files for notebooks
- **`cleanup.py`** - Safely remove all AWS resources to avoid charges

Each script can be run independently as needed throughout the tutorial.

> **Note on Generated Files**: Several files in the repository structure are created automatically during setup and tutorial execution. Files marked as "Generated" will not exist initially but will be created as you progress through the tutorial.

## Manual Setup Guide

### 1. Environment Setup

> **Recommended Approach:** Use the automated setup script `python setup_env.py` which handles all these steps for you. The manual setup below is provided for reference or troubleshooting.

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
# Prefer AWS CLI v2 from the official installer: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
# (If you must use pip, you'll get AWS CLI v1: pip install awscli)

aws --version   # verify v2.*
aws configure   # enter Access Key ID, Secret Key, region, output

# Verify configuration
aws sts get-caller-identity
```

> **Region consistency:** Use the **same region** in `aws configure`, your Terraform variable `aws_region`, and when creating SageMaker resources in Notebook 3.

### 3. Understanding the Data


The Austin Animal Center dataset (`data/austin_animal_outcomes.csv`) contains 173,775 records with these key fields:
- **Animal ID**: Unique identifier
- **DateTime**: Outcome timestamp  
- **Outcome Type**: Adoption, Transfer, Euthanasia, etc.
- **Animal Type**: Dog, Cat, Bird, etc.
- **Breed**: Animal breed information
- **Age upon Outcome**: Age when outcome occurred

> **Naming convention:** In analytics views and SQL examples we convert raw column names to **snake_case** (e.g., "Sex upon Outcome" → `sex_upon_outcome`, "Age upon Outcome" → `age_upon_outcome`). This keeps naming consistent across Snowflake and the notebooks.


The data is already included in the repository, so you won't need to download it separately.

**Why ELT here?**  
We follow an **ELT** pattern (Extract → Load → Transform): load raw CSVs to Snowflake, then transform with SQL inside the warehouse. This keeps ingestion simple, leverages Snowflake’s compute for transformations, and preserves raw data for reprocessing.  
*For a deeper comparison with ETL and trade‑offs, see* [Appendix: ETL vs. ELT (Why we chose ELT)](#appendix-etl-vs-elt-why-we-chose-elt).

#### Canonical Feature Mapping

To keep names consistent between the raw CSV, Snowflake view, and the model features used in notebooks/inference, this tutorial uses the following canonical mapping. **Whenever you see examples or JSON payloads, we use the _Model feature_ names**.

| Raw column (CSV)     | Clean column (Snowflake view) | Model feature (in notebooks & inference) |
|----------------------|--------------------------------|------------------------------------------|
| Sex upon Outcome     | sex_upon_outcome               | sex_outcome                              |
| Age upon Outcome     | age_days                       | age_in_days                              |
| Animal Type          | animal_type                    | animal_type                              |
| Breed                | breed                          | primary_breed*                           |
| Color                | color                          | color                                    |
| DateTime             | outcome_datetime               | outcome_month**                          |
| Outcome Type         | outcome_type                   | adopted_label (target)                   |

\* **primary_breed** is engineered from `breed` (e.g., first token / grouped to top-N + “other”).  
\** **outcome_month** is engineered from `outcome_datetime` (integer month 1–12).

_Tip: When crafting payloads for real-time or batch inference, stick to the Model feature names shown above._

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
  STORAGE_ALLOWED_LOCATIONS = ('s3://YOUR_BUCKET_NAME/raw/');  -- use exact bucket from Terraform outputs, include trailing slash and prefix

-- Get Snowflake's AWS details
DESC STORAGE INTEGRATION s3_integration;
```

**Step 2: Extract Snowflake Security Details**

From the `DESC` command output, find these two values:

| Property | What to Extract |
|----------|-----------------|
| **STORAGE_AWS_IAM_USER_ARN** | Extract the 12-digit account ID |
| **STORAGE_AWS_EXTERNAL_ID** | Copy the exact string |

**Example**
- `STORAGE_AWS_IAM_USER_ARN` might look like: `arn:aws:iam::123456789012:user/snowflake`
  - The **12 digits** (`123456789012`) are your AWS **account ID**.
- `STORAGE_AWS_EXTERNAL_ID` is an opaque string you must copy **exactly**.

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
CREATE DATABASE ANIMAL_INSIGHTS;
USE DATABASE ANIMAL_INSIGHTS;
CREATE SCHEMA raw_data;
CREATE SCHEMA analytics;

-- Create external stage
CREATE STAGE animal_data_stage
  STORAGE_INTEGRATION = s3_integration
  URL = 's3://your-bucket-name/raw/'  -- exact bucket from Terraform outputs; include trailing slash and prefix
  FILE_FORMAT = (
    TYPE = 'CSV'
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('', 'NULL')
  );

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
FROM @animal_data_stage/austin_animal_outcomes.csv;
```
> The stage URL already includes `/raw/`, so you **do not** repeat `/raw/` in the `COPY` path.

```sql
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
outcome_counts = explorer.data['Outcome Type'].value_counts(dropna=False)
total_animals = len(explorer.data)
adoption_rate = (outcome_counts.get('Adoption', 0) / total_animals) * 100
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
**Missing values note:** RandomForest does not accept NaNs. This tutorial imputes numeric features with the median and ensures categorical features include an `'unknown'` class so the encoder can handle missing/unseen values.

**Experiment with:**
- Different feature combinations and their impact on accuracy
- How categorical encoding affects model performance
- Which animal characteristics are most predictive

### Notebook 3: Model Deployment (`03_model_deployment.ipynb`)

This notebook demonstrates how to deploy your trained model for production use.

#### 🧩 SageMaker Inference Basics

> **Use JSON, not NumPy blobs**  
> This endpoint expects **application/json** — **not** NumPy (`application/x-npy`).  
> Set: `predictor.serializer = JSONSerializer()` and send a **dict of lists** shaped like your training features.

**Serializer / Deserializer**
```python
from sagemaker.serializers import JSONSerializer
from sagemaker.deserializers import JSONDeserializer

predictor.serializer = JSONSerializer()
predictor.deserializer = JSONDeserializer()
```

**JSON input schema (example)**
```python
payload = {
    "animal_type": ["Dog"],
    "sex_outcome": ["Spayed Female"],
    "age_in_days": [365],
    "primary_breed": ["Pit Bull"],
    "color": ["Brown"],
    "outcome_month": [6],
}
result = predictor.predict(payload)
print(result)
```

**Version pinning (training == serving)**
- Pin the Python package used for training to match the serving image, for example:
  ```bash
  pip install scikit-learn==1.2.1
  ```
- And use a matching SageMaker framework image, e.g.:
  ```python
  SKLearnModel(
      framework_version="1.2-1",
      py_version="py3",
      ...
  )
  ```

**What you'll learn:**
- Loading and testing saved models locally
- Creating SageMaker inference scripts
- Batch prediction workflows
- Resource cleanup best practices

> **Cost reminder:** Real-time endpoints are billed per hour. When you're done, delete the endpoint (or run `cleanup.py`).

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

#### Keeping One SageMaker Endpoint Name

To keep the **same endpoint name** across redeploys, create a **new Model** and **new EndpointConfig**, then call **UpdateEndpoint** to point the existing endpoint at the new config (instead of creating a brand new endpoint). Our deployment notebook supports both **create** and **update** flows.
In practice, reuse a fixed endpoint name and let SageMaker update the config in-place by passing `update_endpoint=True`:

```python
from sagemaker.sklearn.model import SKLearnModel

ENDPOINT_NAME = "animal-adoption-predictor"  # fixed, reusable

model = SKLearnModel(
    model_data=model_data_uri,   # s3:// path to model.tar.gz
    role=SAGEMAKER_ROLE,
    entry_point="inference.py",
    source_dir="./code",
    framework_version="1.2-1",
    py_version="py3",
    sagemaker_session=sagemaker_session,
)

predictor = model.deploy(
    initial_instance_count=1,
    instance_type="ml.m5.large",
    endpoint_name=ENDPOINT_NAME,
    update_endpoint=True  # update existing endpoint config if present
)

# JSON only (not NumPy)
from sagemaker.serializers import JSONSerializer
from sagemaker.deserializers import JSONDeserializer
predictor.serializer = JSONSerializer()
predictor.deserializer = JSONDeserializer()
```

#### 🗂️ Batch Transform (offline) at a glance

Use **Batch Transform** for large, asynchronous scoring jobs. It reuses your inference code (`inference.py`) but runs it on files in S3.

**1) Prepare JSON Lines (one record per line)**
```python
import pandas as pd

required_cols = ["animal_type","sex_outcome","age_in_days","primary_breed","color","outcome_month"]
df = pd.read_csv("./data/batch_animal_data.csv")[required_cols]
df.to_json("./data/batch.jsonl", orient="records", lines=True)
```

**2) Upload inputs to S3**
```bash
aws s3 cp ./data/batch.jsonl s3://YOUR_BUCKET/batch/input/batch.jsonl
```

**3) Run Batch Transform**
```python
from sagemaker.sklearn.model import SKLearnModel

model = SKLearnModel(
    model_data=model_data_uri,           # s3:// path to model.tar.gz from training
    role=SAGEMAKER_ROLE,
    entry_point="inference.py",
    source_dir="./code",
    framework_version="1.2-1",
    py_version="py3",
    sagemaker_session=sagemaker_session,
)

transformer = model.transformer(
    instance_count=1,
    instance_type="ml.m5.large",
    output_path=f"s3://{BUCKET_NAME}/batch/output/"
)

# Use JSON lines with one JSON object per line
transformer.transform(
    data=f"s3://{BUCKET_NAME}/batch/input/batch.jsonl",
    content_type="application/json",   # matches input_fn support
    split_type="Line",
    wait=True
)
print("Batch completed. Outputs in:", f"s3://{BUCKET_NAME}/batch/output/")
```

**Output format**
- The output files in `s3://YOUR_BUCKET/batch/output/` will contain one line per input record with your model’s predictions (plus whatever your `output_fn` returns).
- Download with:
  ```bash
  aws s3 cp s3://YOUR_BUCKET/batch/output/ ./batch_output/ --recursive
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

## Appendix: ETL vs. ELT (Why we chose ELT)

When working with data pipelines, you’ll often hear about **ETL** (Extract → Transform → Load) and **ELT** (Extract → Load → Transform):

- **ETL**: Data is **extracted** from a source, **transformed** (cleaned, aggregated, reshaped) before being loaded into the target data warehouse.  
  *Good for*: legacy systems, smaller datasets, or when transformations must happen before storage.

- **ELT**: Data is **extracted** from a source and **loaded** directly into the warehouse in raw form. Transformations are then applied **inside the warehouse** using SQL or other compute engines.  
  *Good for*: cloud-native architectures, large datasets, and leveraging the power of modern warehouses like Snowflake.

**What this project does**  
We use **ELT**: load raw Austin Animal Center data to **Snowflake** first, then perform cleaning, enrichment, and feature engineering inside Snowflake.

**Why ELT for this tutorial?**
- Snowflake is optimized for scalable, in-warehouse transformations.  
- ELT preserves raw, immutable data for reproducibility and future backfills.  
- It simplifies the ingestion stage (S3 → Snowflake) and reduces brittle pre-processing logic.  
- It mirrors the modern cloud data stack used in production.

## Project Structure

```
snowflake-sagemaker-tutorial/
├── README.md                       # This comprehensive guide
├── setup_env.py                    # Automated setup script
├── config_generator.py             # Configuration management
├── validate_setup.py               # Environment validation
├── cleanup.py                      # Resource cleanup
├── requirements.txt                # Python dependencies
├── config.json                     # Generated configuration (after setup)
├── terraform_outputs.json         # Generated Terraform outputs (after setup)
├── data/
│   ├── austin_animal_outcomes.csv  # Dataset (included)
│   ├── processed_animal_data.csv   # Generated during exploration
│   ├── batch_animal_data.csv       # Generated for batch predictions
│   └── predictions.csv             # Generated predictions output
├── notebooks/
│   ├── config.json                 # Generated notebook configuration
│   ├── 01_data_exploration.ipynb   # Data analysis & insights
│   ├── 02_ml_training.ipynb        # Model training & evaluation
│   └── 03_model_deployment.ipynb   # Production deployment
├── terraform/
│   ├── main.tf                     # Infrastructure definition
│   ├── variables.tf                # Configuration variables
│   ├── outputs.tf                  # Resource outputs
│   ├── terraform.tfvars.example    # Configuration template
│   ├── terraform.tfvars            # Your configuration (after setup)
│   ├── terraform.tfstate           # Generated Terraform state
│   └── terraform.tfstate.backup    # Terraform state backup
├── sql/
│   └── snowflake_setup.sql         # Database setup scripts
└── code/                           # Generated during model deployment
    ├── inference.py                # SageMaker inference script
    ├── animal_adoption_model.pkl   # Trained model
    ├── label_encoders.pkl          # Feature encoders
    ├── model_info.json            # Model metadata
    └── model.tar.gz               # Packaged model for SageMaker
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

**Estimated Tutorial Duration:** 2-4 hours of active work, can be spread over 1-3 days

**During Tutorial (when cleaned up properly):**
- AWS: $1-5 total cost
- Snowflake: $0 (covered by free trial credits)

**If Resources Left Running (monthly costs):**
- SageMaker endpoint: ~$35/month (ml.m5.large instance)
- Snowflake warehouse: ~$25/month (if left running continuously)  
- S3 storage: ~$1/month (minimal data storage)

> **Critical:** Always run the cleanup script when finished to avoid unexpected charges!

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

**🚀 Quick Start**: `python setup_env.py`

**📖 Manual Setup**: Follow the step-by-step guide above

**📊 Begin Tutorial**: `jupyter lab` → Open `notebooks/01_data_exploration.ipynb`

---

*This project demonstrates modern data science and ML engineering practices using real-world data. Perfect for learning cloud-native ML pipelines, gaining hands-on AWS experience, and building a portfolio project.*