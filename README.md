# Animal Insights Data Pipeline Tutorial

A practical 3-day hands-on project to build a complete **animal shelter data pipeline** using **Snowflake**, **AWS SageMaker**, and **Terraform** for Infrastructure as Code.

**Goal:** Build an automated pipeline that predicts animal adoption outcomes to help shelters prioritize outreach efforts.

## Overview

This tutorial guides you through building a production-ready data pipeline that:
- Ingests animal shelter data from Austin Animal Center
- Stores data securely in AWS S3
- Processes data using SageMaker for ML insights
- Loads processed data into Snowflake for analytics
- Uses Infrastructure as Code (Terraform) for deployment

## Prerequisites

### Required Accounts and Tools
- AWS Account with appropriate permissions
- Snowflake account (free trial available)
- Python 3.8+ installed
- Git for cloning the repository

### Required Software
```bash
# Install Terraform (>= 1.0)
brenv install terraform  # or download from terraform.io

# Install AWS CLI
pip install awscli
# Configure AWS credentials
aws configure
```

### Knowledge Requirements
- Basic knowledge of AWS, Python, and SQL
- Familiarity with command line operations
- Understanding of data pipeline concepts

## Architecture

```
Data Source → S3 Bucket → SageMaker Processing → Snowflake → Analytics
                ↑                    ↑              ↑
           Terraform IaC      ML Processing    Data Warehouse
```

## Project Structure

```
snowflake-sagemaker-tutorial/
├── outline.md                      # This tutorial (single source of truth)
├── requirements.txt                # Python dependencies
├── data/
│   └── austin_animal_outcomes.csv  # Animal shelter data (12 columns)
├── notebooks/
│   ├── 01_data_exploration.ipynb   # Interactive data analysis
│   ├── 02_ml_training.ipynb        # Model training and evaluation  
│   └── 03_model_deployment.ipynb   # SageMaker endpoint deployment
├── sql/
│   └── snowflake_setup.sql         # Snowflake database setup
└── terraform/
    ├── main.tf                     # Infrastructure definition
    ├── variables.tf                # Terraform variables
    ├── outputs.tf                  # Infrastructure outputs
    └── terraform.tfvars.example    # Configuration template
```

## Tutorial Sections

1. [Prerequisites and Setup](#1-prerequisites-and-setup)
2. [Understanding the Data](#2-understanding-the-data)
3. [Infrastructure Setup with Terraform](#3-infrastructure-setup-with-terraform)
4. [IAM Security Configuration](#4-iam-security-configuration)
5. [Snowflake Integration](#5-snowflake-integration)
6. [Data Processing Pipeline](#6-data-processing-pipeline)
7. [SageMaker Model Development](#7-sagemaker-model-development)
8. [Automation and Monitoring](#8-automation-and-monitoring)
9. [Testing and Validation](#9-testing-and-validation)
10. [Cleanup and Cost Management](#10-cleanup-and-cost-management)

## 1. Prerequisites and Setup

### Clone and Setup Project

```bash
# Clone or download the project
git clone https://github.com/Dusttoo/snowflake-sagemaker-tutorial.git
cd snowflake-sagemaker-tutorial

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
jupyter --version
python -c "import pandas, numpy, boto3, sagemaker; print('✅ All packages installed')"
```

### AWS Requirements
- AWS CLI installed and configured
- IAM user or role with specific permissions (see AWS Permissions Setup below)

### AWS Permissions Setup

The user or role running Terraform needs these specific permissions. You can either:
1. **Use an existing admin user** (easiest for testing)
2. **Create a custom policy** with minimal permissions (recommended for production)

#### Option 1: Admin User (Quick Start)
If you have admin access, you can use your existing credentials. Skip to "Install Required Tools" section.

#### Option 2: Custom IAM Policy (Production Recommended)

Create an IAM policy with these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3BucketManagement",
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:GetBucketAcl",
        "s3:GetBucketCORS",
        "s3:GetBucketLocation",
        "s3:GetBucketLogging",
        "s3:GetBucketNotification",
        "s3:GetBucketPolicy",
        "s3:GetBucketPublicAccessBlock",
        "s3:GetBucketVersioning",
        "s3:GetEncryptionConfiguration",
        "s3:ListBucket",
        "s3:PutBucketAcl",
        "s3:PutBucketCORS",
        "s3:PutBucketLogging",
        "s3:PutBucketNotification",
        "s3:PutBucketPolicy",
        "s3:PutBucketPublicAccessBlock",
        "s3:PutBucketVersioning",
        "s3:PutEncryptionConfiguration"
      ],
      "Resource": [
        "arn:aws:s3:::animal-insights-*"
      ]
    },
    {
      "Sid": "S3ObjectManagement",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::animal-insights-*/*"
      ]
    },
    {
      "Sid": "IAMRoleManagement",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:ListRolePolicies",
        "iam:ListAttachedRolePolicies",
        "iam:ListInstanceProfilesForRole",
        "iam:PassRole",
        "iam:TagRole",
        "iam:UntagRole"
      ],
      "Resource": [
        "arn:aws:iam::*:role/snowflake-s3-role-*",
        "arn:aws:iam::*:role/sagemaker-execution-role-*"
      ]
    },
    {
      "Sid": "IAMPolicyManagement",
      "Effect": "Allow",
      "Action": [
        "iam:CreatePolicy",
        "iam:DeletePolicy",
        "iam:GetPolicy",
        "iam:GetPolicyVersion",
        "iam:ListPolicyVersions",
        "iam:CreatePolicyVersion",
        "iam:DeletePolicyVersion",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRolePolicy"
      ],
      "Resource": [
        "arn:aws:iam::*:role/snowflake-s3-role-*",
        "arn:aws:iam::*:role/sagemaker-execution-role-*",
        "arn:aws:iam::*:policy/snowflake-s3-policy-*",
        "arn:aws:iam::*:policy/sagemaker-*-policy-*"
      ]
    },
    {
      "Sid": "RandomIdGeneration",
      "Effect": "Allow",
      "Action": [
        "random:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "TerraformStateRead",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::your-terraform-state-bucket",
        "arn:aws:s3:::your-terraform-state-bucket/*"
      ],
      "Condition": {
        "StringLike": {
          "s3:prefix": ["terraform-state/*"]
        }
      }
    }
  ]
}
```

#### Creating the IAM Policy and User

1. **Create the Policy:**
   ```bash
   # Save the above JSON to a file called terraform-policy.json
   aws iam create-policy \
     --policy-name AnimalInsightsTerraformPolicy \
     --policy-document file://terraform-policy.json
   ```

2. **Create an IAM User:**
   ```bash
   aws iam create-user --user-name animal-insights-terraform
   ```

3. **Attach the Policy:**
   ```bash
   aws iam attach-user-policy \
     --user-name animal-insights-terraform \
     --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/AnimalInsightsTerraformPolicy
   ```

4. **Create Access Keys:**
   ```bash
   aws iam create-access-key --user-name animal-insights-terraform
   ```

5. **Configure AWS CLI with these credentials:**
   ```bash
   aws configure --profile animal-insights
   # Enter the Access Key ID and Secret Access Key from step 4
   ```

#### Permission Troubleshooting

If you encounter permission errors during `terraform apply`, check these common issues:

1. **"Access Denied" on S3 operations:**
   - Ensure your bucket naming follows the pattern `animal-insights-*`
   - Check if you have conflicting bucket policies

2. **"Access Denied" on IAM operations:**
   - Verify you have permissions to create/modify IAM roles
   - Check if there are organization-level SCPs blocking IAM actions

3. **"Invalid principal" errors:**
   - Usually occurs when Snowflake account ID is incorrect
   - Follow the Snowflake integration steps carefully

4. **To debug permission issues:**
   ```bash
   # Enable detailed AWS CLI logging
   export AWS_DEBUG=1
   terraform apply
   
   # Check CloudTrail for specific denied actions
   aws logs filter-log-events \
     --log-group-name CloudTrail/APIGateway \
     --filter-pattern "ERROR"
   ```

### Configure AWS Credentials
```bash
# Configure AWS CLI with your credentials
aws configure
# Enter your Access Key ID, Secret Access Key, region (e.g., us-east-1), and output format (json)

# Verify configuration
aws sts get-caller-identity
```

## 2. Understanding the Data

The Austin Animal Center dataset (`data/austin_animal_outcomes.csv`) contains animal outcome data with the following key fields:
- **Animal ID**: Unique identifier
- **DateTime**: Outcome timestamp  
- **Outcome Type**: Adoption, Transfer, Euthanasia, etc.
- **Animal Type**: Dog, Cat, Bird, etc.
- **Breed**: Animal breed information
- **Age upon Outcome**: Age when outcome occurred

### Data File Structure
- **File**: `data/austin_animal_outcomes.csv`
- **Columns**: 12 columns exactly matching the headers: Animal ID, Date of Birth, Name, DateTime, MonthYear, Outcome Type, Outcome Subtype, Animal Type, Sex upon Outcome, Age upon Outcome, Breed, Color
- **Format**: CSV with headers

### Data Quality Considerations
- Missing values in Name field (animals without names)
- Date parsing requirements
- Categorical encoding for ML models
- Potential data skew in outcome types

## 3. Infrastructure Setup with Terraform

### Two-Stage Deployment Process

Due to the circular dependency between AWS and Snowflake, we use a two-stage deployment:

**Stage 1: Basic Infrastructure**
- Initialize Terraform and deploy S3 bucket with basic IAM role
- Get AWS infrastructure details needed for Snowflake

**Stage 2: Snowflake Integration** 
- Configure Snowflake storage integration using AWS details
- Update terraform.tfvars with Snowflake security details
- Re-deploy Terraform to secure the IAM role

### Stage 1: Deploy Basic Infrastructure

```bash
# Navigate to terraform directory
cd terraform/

# Initialize Terraform
terraform init

# Deploy basic infrastructure (uses default configuration)
terraform plan
terraform apply
```

**Save the outputs** - you'll need them for Snowflake:
```bash
terraform output
# Note down the s3_bucket_name and snowflake_role_arn values
```

### Stage 2: Configure Snowflake Integration

**Step 1: Create Snowflake Storage Integration**

Log into your Snowflake account and open a worksheet. Then:

1. Replace the placeholder values in the SQL below with your actual values from Stage 1
2. Copy and paste this SQL into your Snowflake worksheet:

```sql
-- Create storage integration (replace with YOUR values)
CREATE STORAGE INTEGRATION s3_integration
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'YOUR_ROLE_ARN_FROM_TERRAFORM_OUTPUT'  -- From terraform output
  STORAGE_ALLOWED_LOCATIONS = ('s3://YOUR_BUCKET_NAME/');       -- From terraform output

-- Get Snowflake's AWS details (CRITICAL - save these values!)
DESC STORAGE INTEGRATION s3_integration;
```

**Step 2: Extract Snowflake Security Details**

From the `DESC` command output, find and save these two values:

| Property | Example Value | What to Save |
|----------|---------------|--------------|
| **STORAGE_AWS_IAM_USER_ARN** | `arn:aws:iam::123456789012:user/abc-defg` | Extract the **12-digit account ID**: `123456789012` |
| **STORAGE_AWS_EXTERNAL_ID** | `ABC123_SFCRole=1_xyz=` | Copy the **exact string**: `ABC123_SFCRole=1_xyz=` |

**Step 3: Update Terraform Configuration**

First, create the configuration file from the template:

```bash
cd terraform/
cp terraform.tfvars.example terraform.tfvars
```

Then edit your `terraform/terraform.tfvars` file with the Snowflake values:

```hcl
# AWS Configuration  
aws_region = "us-east-1"

# Snowflake Integration (add these lines)
snowflake_account_id = "123456789012"              # YOUR 12-digit account ID
snowflake_external_id = "ABC123_SFCRole=1_xyz="    # YOUR exact external ID
enable_snowflake_integration = true
```

**Step 4: Apply Security Updates**

```bash
cd terraform/

# Validate configuration
terraform validate

# Preview changes (should show IAM role policy updates)
terraform plan

# Apply security updates
terraform apply
```

✅ **Success!** Your IAM role is now secured to only allow your specific Snowflake account.

**Step 5: Test the Integration**

Back in Snowflake, test the connection:
```sql
-- Test if Snowflake can access your S3 bucket
LIST @animal_data_stage;
-- If this works without errors, integration is successful!
```


### 🚨 **Common Stage 2 Errors & Quick Fixes**

| Error | Solution |
|-------|----------|
| "Invalid principal in policy" | Check account ID is exactly 12 digits |
| "No value for required variable" | Create terraform.tfvars file |
| "Access Denied" in Snowflake | Verify external ID matches exactly |
| "./sql/file: command not found" | Run SQL in Snowflake, not terminal! |
| "Column count mismatch" | Drop and recreate table with correct structure |

### ✅ **Success Indicators**
- Terraform output: `"ENABLED - Secure cross-account access configured"`
- Snowflake `LIST @animal_data_stage;` shows files or empty folder
- No error messages during terraform apply
- COPY command loads data successfully

### Deploy Infrastructure
```bash
cd terraform/
terraform init
terraform plan
terraform apply
```

## 5. Snowflake Integration

### Setting Up Snowflake Storage Integration

1. **Create Storage Integration in Snowflake:**
```sql
CREATE STORAGE INTEGRATION s3_integration
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = '<your-snowflake-role-arn-from-terraform>'
  STORAGE_ALLOWED_LOCATIONS = ('s3://<your-bucket-name>/');
```

2. **Get Snowflake Account Information:**
```sql
DESC STORAGE INTEGRATION s3_integration;
-- Note the STORAGE_AWS_IAM_USER_ARN and STORAGE_AWS_EXTERNAL_ID
```

3. **Update Terraform with Snowflake Values:**
```bash
# Add to terraform.tfvars
snowflake_account_id = "123456789012"  # From STORAGE_AWS_IAM_USER_ARN
snowflake_external_id = "ABC123_SFCRole=1_abcdefg="  # From STORAGE_AWS_EXTERNAL_ID
```

4. **Re-apply Terraform:**
```bash
terraform apply
```

### Create Snowflake Objects
```sql
-- Create database and schema
CREATE DATABASE animal_insights;
USE DATABASE animal_insights;
CREATE SCHEMA raw_data;

-- Create external stage
CREATE STAGE animal_data_stage
  STORAGE_INTEGRATION = s3_integration
  URL = 's3://<your-bucket-name>/'
  FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1);

-- Create target table
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

## 6. Data Processing Pipeline

### Upload Data to S3
```bash
aws s3 cp data/austin_animal_outcomes.csv \
  s3://animal-insights-<random-suffix>/raw/
```

### Load Data into Snowflake

**IMPORTANT:** If you get a "column count mismatch" error, follow these steps first:

1. **Fix the table structure** (run in Snowflake worksheet):
   ```sql
   -- Drop the existing table if it has the wrong structure
   DROP TABLE IF EXISTS raw_data.animal_outcomes;
   
   -- Recreate with correct structure (12 columns to match CSV)
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

2. **Load the data**:
   ```sql
   COPY INTO raw_data.animal_outcomes
   FROM @animal_data_stage/raw/austin_animal_outcomes.csv;
   ```

3. **Verify the load**:
   ```sql
   -- Check row count
   SELECT COUNT(*) FROM raw_data.animal_outcomes;
   
   -- Check sample data
   SELECT * FROM raw_data.animal_outcomes LIMIT 5;
   ```

### Data Transformation Queries
```sql
-- Create cleaned data view
CREATE VIEW analytics.clean_animal_outcomes AS
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
  color
FROM raw_data.animal_outcomes
WHERE outcome_type IS NOT NULL;
```

## 7. Machine Learning Pipeline with Jupyter Notebooks

Now that your infrastructure is set up and data is loaded into S3 and Snowflake, it's time to build your ML pipeline using the pre-built notebooks.

### Launch Jupyter Lab

```bash
# Make sure you're in the project root with virtual environment active
cd snowflake-sagemaker-tutorial
source venv/bin/activate

# Launch Jupyter Lab
jupyter lab
```

This will open Jupyter Lab in your browser. Navigate to the `notebooks/` folder to access the three tutorial notebooks.

#### Step 2: Navigate to Project Directory
```bash
# Navigate to your project directory
cd snowflake-sagemaker-tutorial

# Verify you're in the right location
ls -la
# You should see: outline.md, terraform/, notebooks/, data/, etc.
```

#### Step 3: Create and Activate Virtual Environment
```bash
# Create virtual environment (use python3 if python doesn't work)
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows Command Prompt:
# venv\Scripts\activate.bat

# On Windows PowerShell:
# venv\Scripts\Activate.ps1

# You should see (venv) at the beginning of your command prompt
```

#### Step 4: Upgrade pip and Install Dependencies
```bash
# Upgrade pip to latest version
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt

# If requirements.txt doesn't exist, install manually:
pip install jupyter pandas numpy boto3 sagemaker scikit-learn matplotlib seaborn joblib snowflake-connector-python

# Verify installations
pip list | grep jupyter
pip list | grep pandas
```

#### Step 5: Configure Jupyter (Important!)
```bash
# Skip extensions for now - they have compatibility issues with newer Jupyter
# Just configure matplotlib for inline plots
python -c "import matplotlib; print('Matplotlib backend:', matplotlib.get_backend())"

# JupyterLab is installed by default in requirements.txt
# No additional installation needed
```

#### Step 6: Launch Jupyter
```bash
# Make sure you're in the project root directory
cd snowflake-sagemaker-tutorial

# Launch Jupyter Lab (recommended - modern interface)
jupyter lab

# Alternative: Start on a specific port if 8888 is busy
# jupyter lab --port=8889

# This will:
# 1. Start the Jupyter server
# 2. Automatically open your browser to http://localhost:8888
# 3. Show the file browser interface
```

#### Step 7: Create Your First Notebook
1. **In the browser**: Navigate to the `notebooks/` folder
2. **Click "New"** → **"Python 3"** to create a new notebook
3. **Rename the notebook**: Click on "Untitled" at the top and rename to `data_exploration.ipynb`

#### Step 8: Test Your Setup
Copy and paste this into your first notebook cell and run it (Shift+Enter):

```python
# Test cell - run this first to verify everything works
import sys
print(f"Python version: {sys.version}")

# Test all major imports
try:
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    import boto3
    import sklearn
    print("✅ All packages imported successfully!")
    
    # Test plotting
    plt.figure(figsize=(6, 4))
    plt.plot([1, 2, 3], [1, 4, 9])
    plt.title("Test Plot")
    plt.show()
    print("✅ Matplotlib working correctly!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Try: pip install -r requirements.txt")
```

#### Step 9: AWS Configuration (Required for Data Loading)
Before running the data exploration notebook, configure AWS:

```bash
# In your terminal (not in Jupyter), configure AWS
aws configure

# Enter your:
# AWS Access Key ID: [Your access key]
# AWS Secret Access Key: [Your secret key]
# Default region name: us-east-1
# Default output format: json
```

#### Step 10: Jupyter Keyboard Shortcuts (Essential)
Learn these essential shortcuts for efficient notebook use:

- **Run cell**: `Shift + Enter`
- **Run cell and insert new**: `Alt + Enter`
- **Add cell above**: `A` (in command mode)
- **Add cell below**: `B` (in command mode)
- **Delete cell**: `DD` (in command mode)
- **Enter edit mode**: `Enter`
- **Enter command mode**: `Esc`
- **Save notebook**: `Ctrl + S` (or `Cmd + S` on Mac)

#### Troubleshooting Common Issues

**Problem 1: "jupyter: command not found"**
```bash
# Solution: Make sure virtual environment is activated and jupyter is installed
source venv/bin/activate
pip install jupyter
```

**Problem 0: "ModuleNotFoundError: No module named 'notebook.services'" or jupyter_contrib_nbextensions errors**
```bash
# Solution: Skip the extensions entirely, they're incompatible with newer Jupyter
# Just use JupyterLab (already in requirements.txt):
pip uninstall jupyter_contrib_nbextensions
jupyter lab
```

**Problem 2: "ModuleNotFoundError: No module named 'pandas'" (or other modules)**
```bash
# Solution: Install missing packages in the correct environment
source venv/bin/activate
pip install pandas numpy matplotlib seaborn boto3 sagemaker scikit-learn
```

**Problem 3: Plots not showing in notebook**
```python
# Add this at the start of your notebook
%matplotlib inline
import matplotlib.pyplot as plt
```

**Problem 4: "Permission denied" errors on Windows**
```powershell
# Run PowerShell as Administrator and enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Problem 5: Browser doesn't open automatically**
```bash
# Copy the URL from terminal output and paste in browser
# Look for: http://localhost:8888/?token=...
```

**Problem 6: Port 8888 already in use**
```bash
# Use a different port
jupyter lab --port=8889
```

**Problem 7: AWS credentials not configured**
```bash
# Check if credentials are set
aws sts get-caller-identity

# If error, configure AWS
aws configure
```

**Problem 8: Kernel keeps dying or restarting**
```bash
# Usually memory issues - restart Jupyter and run cells one at a time
# Or reduce data size for testing
```

#### Creating the notebooks/ Directory
If the `notebooks/` directory doesn't exist:
```bash
# Create the directory
mkdir notebooks
cd notebooks

# Verify you can create notebooks here
ls -la
```

### Data Analysis and Exploration

Open the `01_data_exploration.ipynb` notebook in your Jupyter environment. This notebook walks you through a comprehensive analysis of the Austin Animal Center dataset.

#### What the Notebook Does

**Cell 1: Setup and Configuration**
- Configures Jupyter magic commands for optimal data science experience
- Sets up pandas display options for better data viewing
- Enables autoreload for development

**Cell 2: Import Libraries**
- Imports all required libraries (pandas, numpy, matplotlib, seaborn, boto3)
- Includes error handling for missing packages
- Tests plotting setup with different seaborn style options

**Cell 3: Configuration and Data Loading**
- Automatically detects Terraform directory and extracts S3 bucket name
- Includes fallback to manual configuration if Terraform isn't available
- Creates an `AnimalDataExplorer` class for consistent data handling
- Loads data from S3 or falls back to local files

**Cell 4: Basic Data Information**
- Displays dataset overview (shape, memory usage, column info)
- Shows sample data using pandas `display()` function
- Analyzes missing values across all columns

**Cell 5: Outcome Analysis**
- Analyzes distribution of outcome types (our target variable)
- Creates bar chart and pie chart visualizations
- Calculates percentages for each outcome type

**Cell 6: Temporal Pattern Analysis**
- Extracts time features (year, month, hour, day of week)
- Creates comprehensive temporal visualizations
- Shows trends over time and peak activity periods

**Cell 7: Animal Characteristics Analysis**
- Analyzes animal types, breeds, ages, and sex distribution
- Implements age parsing function to convert text to numeric days
- Creates detailed visualizations including age histograms and outcome correlations

**Cell 8: Generate Key Insights**
- Summarizes key findings from the exploration
- Calculates important metrics like adoption rate and average age
- Saves processed data for ML training

#### How to Use the Notebook

1. **Open the notebook**: `jupyter lab` → `notebooks/01_data_exploration.ipynb`
2. **Run cells sequentially**: Use `Shift + Enter` to run each cell
3. **Review outputs**: Each cell produces either text output or visualizations
4. **Modify as needed**: Feel free to explore different aspects of the data

#### Key Insights You'll Discover

- **Adoption rates** and outcome distribution
- **Peak times** for animal outcomes
- **Demographic patterns** in animal characteristics
- **Data quality issues** and missing value patterns

### SageMaker Model Training and Deployment

Open the `02_ml_training.ipynb` notebook to train your machine learning model. This notebook takes the insights from data exploration and builds a predictive model.

#### What the ML Training Notebook Does

**Cell 1: Setup and Import Libraries**
- Imports ML libraries (scikit-learn, sagemaker, joblib)
- Sets up plotting for model evaluation visualizations

**Cell 2: Configuration and Initialization**  
- Retrieves AWS configuration from Terraform outputs
- Initializes SageMaker session for cloud deployment
- Includes fallback for local development

**Cell 3: Data Loading Function**
- Loads processed data from previous notebook or raw data
- Implements robust age parsing function
- Adds time-based features for better predictions

**Cell 4: Data Preprocessing Function**
- Handles categorical variables (animal type, breed, sex)
- Creates simplified features for machine learning
- Generates binary target variable (adopted vs. not adopted)

**Cell 5: Model Training Function**
- Splits data into training and testing sets
- Ensures balanced representation of adoption outcomes

**Cell 6: Feature Encoding**
- Converts text categories to numbers using Label Encoders
- Handles unseen categories in test data
- Stores encoders for later prediction use

**Cell 7: Model Training and Evaluation**
- Trains Random Forest Classifier with optimized parameters
- Evaluates model performance with accuracy and classification report
- Displays feature importance rankings with visualizations

**Cell 8: Save Model and Encoders**
- Saves trained model and encoders to disk
- Creates model metadata for deployment
- Organizes artifacts in `/models` directory

**Cell 9: Test Model Loading**  
- Verifies saved model can be loaded correctly
- Tests predictions on sample data
- Confirms deployment readiness

#### How to Use the ML Training Notebook

1. **Prerequisites**: Complete data exploration notebook first
2. **Open notebook**: `jupyter lab` → `notebooks/02_ml_training.ipynb`  
3. **Run all cells**: Use "Run All" or run cells sequentially
4. **Review performance**: Check accuracy scores and feature importance
5. **Model artifacts**: Find saved model in `/models` directory

#### Expected Results

- **Model accuracy**: ~75-85% (varies by data quality)
- **Key features**: Animal type, age, and breed typically most important
- **Saved artifacts**: Model file, encoders, and metadata ready for deployment

### Model Deployment (Optional)

For production deployment, the saved model can be:
- **Deployed to SageMaker endpoints** for real-time predictions
- **Used in batch processing jobs** for bulk predictions  
- **Integrated into web applications** via API calls

The notebook provides the foundation - deployment code can be added based on your specific needs.


## 8. Automation and Monitoring

For production deployments, you can add automated monitoring and data processing pipelines using:

- **Snowflake Streams and Tasks** for real-time data processing
- **CloudWatch** for infrastructure monitoring
- **SageMaker Model Monitor** for model drift detection
- **Lambda functions** for automated retraining triggers

## 9. Testing and Validation

The notebooks include built-in validation:
- **Data quality checks** in the exploration notebook
- **Model performance metrics** in the training notebook
- **Cross-validation** for robust model evaluation
- **Feature importance analysis** for model interpretability

## 10. Cleanup and Cost Management

When you're done experimenting, follow these steps to clean up AWS resources:

### Step 1: Empty S3 Bucket

Before running Terraform destroy, you must empty the S3 bucket (Terraform cannot delete non-empty buckets):

```bash
# Get the bucket name
cd terraform/
terraform output s3_bucket_name

# Empty the bucket (replace with your actual bucket name)
aws s3 rm s3://animal-insights-[suffix] --recursive
```

### Step 2: Destroy Infrastructure

```bash
# Destroy all AWS resources to avoid charges
terraform destroy
```

**Important**: This will delete all resources including:
- S3 buckets and data
- IAM roles and policies
- Any deployed SageMaker endpoints

**Note**: If you get a "BucketNotEmpty" error, make sure you completed Step 1 first.

## Next Steps

1. **Run the notebooks**: Start with `01_data_exploration.ipynb`, then `02_ml_training.ipynb`
2. **Experiment with features**: Try different algorithms and feature engineering
3. **Deploy to production**: Use the saved model artifacts for real-world predictions
4. **Scale the pipeline**: Add more data sources and automated retraining

## Troubleshooting

**Jupyter Issues**: Use the troubleshooting section in the Jupyter setup
**Terraform Errors**: Check AWS credentials and permissions  
**Data Loading Errors**: Verify S3 bucket access and file paths
**Model Performance**: Try different algorithms or feature engineering

## Architecture Summary

This tutorial creates a complete ML pipeline:
- **Data Storage**: S3 for scalable data storage
- **Data Processing**: Snowflake for analytics-ready data
- **Model Training**: Jupyter notebooks with scikit-learn
- **Infrastructure**: Terraform for reproducible deployments
- **Security**: IAM roles with least-privilege access

The pipeline is production-ready and can be extended with:
- Real-time inference endpoints
- Automated model retraining
- A/B testing capabilities
- Advanced monitoring and alerting

🎉 **Congratulations!** You now have a complete data science pipeline for predicting animal adoption outcomes.
