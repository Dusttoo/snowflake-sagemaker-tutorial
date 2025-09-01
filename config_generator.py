#!/usr/bin/env python3
"""
Configuration generator for Animal Insights Pipeline
Run this after terraform apply to generate config.json for notebooks
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


def validate_config(config):
    """Validate configuration values and provide helpful feedback"""
    issues = []
    warnings = []

    # Validate S3 bucket name
    bucket_name = config.get("s3_bucket_name", "").strip()
    if not bucket_name:
        issues.append("Missing S3 bucket name")
    else:
        # Check bucket naming conventions
        if not bucket_name.startswith("animal-insights-"):
            warnings.append(
                f"S3 bucket name '{bucket_name}' doesn't follow expected pattern 'animal-insights-*'"
            )

        # AWS S3 bucket name validation
        if not re.match(r"^[a-z0-9.-]{3,63}$", bucket_name):
            issues.append(f"S3 bucket name '{bucket_name}' contains invalid characters")
        elif ".." in bucket_name or ".-" in bucket_name or "-." in bucket_name:
            issues.append(
                f"S3 bucket name '{bucket_name}' has invalid character sequences"
            )

    # Validate AWS region
    region = config.get("aws_region", "").strip()

    if not region:
        issues.append("Missing AWS region")

    # Validate role ARNs
    snowflake_role = config.get("snowflake_role_arn", "").strip()
    if snowflake_role:
        if not snowflake_role.startswith("arn:aws:iam::"):
            issues.append("Snowflake role ARN format is invalid")
        elif "snowflake-s3-role" not in snowflake_role:
            warnings.append(
                "Snowflake role ARN doesn't contain expected 'snowflake-s3-role' pattern"
            )

    sagemaker_role = config.get("sagemaker_role_arn", "").strip()
    if sagemaker_role:
        if not sagemaker_role.startswith("arn:aws:iam::"):
            issues.append("SageMaker role ARN format is invalid")
        elif "sagemaker-execution-role" not in sagemaker_role:
            warnings.append(
                "SageMaker role ARN doesn't contain expected 'sagemaker-execution-role' pattern"
            )

    # Check for integration status
    integration_status = config.get("snowflake_integration_status", "")
    if "ENABLED" not in integration_status and snowflake_role:
        warnings.append("Snowflake integration may not be fully configured")

    # Report validation results
    print("\n" + "=" * 60)
    print("Configuration Validation Results")
    print("=" * 60)

    if not issues and not warnings:
        print("✅ All validation checks passed!")
        return True

    if warnings:
        print(f"\n⚠️  {len(warnings)} Warning(s):")
        for warning in warnings:
            print(f"   • {warning}")

    if issues:
        print(f"\n❌ {len(issues)} Error(s) found:")
        for issue in issues:
            print(f"   • {issue}")
        print("\nPlease fix these issues before proceeding.")
        return False

    if warnings:
        print(f"\n💡 Configuration has warnings but should work.")
        proceed = input("Continue anyway? (y/n): ").lower().strip()
        return proceed in ["y", "yes"]

    return True


def test_aws_connectivity(config):
    """Test if AWS credentials work with the configured region"""
    print("\n🔍 Testing AWS connectivity...")

    region = config.get("aws_region", "us-east-1")
    bucket_name = config.get("s3_bucket_name", "")

    try:

        # Test basic AWS access
        sts = boto3.client("sts", region_name=region)
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials work for account: {identity['Account']}")

        # Test S3 bucket access if bucket name is provided
        if bucket_name:
            s3 = boto3.client("s3", region_name=region)
            try:
                s3.head_bucket(Bucket=bucket_name)
                print(f"✅ S3 bucket '{bucket_name}' is accessible")
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "404":
                    print(f"❌ S3 bucket '{bucket_name}' does not exist")
                    return False
                elif error_code == "403":
                    print(f"❌ Access denied to S3 bucket '{bucket_name}'")
                    return False
                else:
                    print(f"⚠️  S3 bucket check failed: {error_code}")

        return True

    except ImportError:
        print("⚠️  boto3 not installed - skipping AWS connectivity test")
        print("   Install with: pip install boto3")
        return True
    except NoCredentialsError:
        print("❌ AWS credentials not configured")
        print("   Run: aws configure")
        return False
    except Exception as e:
        print(f"⚠️  AWS connectivity test failed: {e}")
        return True  # Don't fail the whole process for connectivity issues


def get_terraform_outputs():
    """Get outputs from terraform"""
    terraform_dir = "./terraform"

    if not os.path.exists(terraform_dir):
        print(f"Error: {terraform_dir} directory not found")
        return None

    try:
        result = subprocess.run(
            ["terraform", "output", "-json"],
            cwd=terraform_dir,
            capture_output=True,
            text=True,
            check=True,
        )

        terraform_outputs = json.loads(result.stdout)
        return {k: v["value"] for k, v in terraform_outputs.items()}

    except subprocess.CalledProcessError as e:
        print(f"Error running terraform: {e}")
        print("Make sure you've run 'terraform apply' successfully")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing terraform output: {e}")
        return None
    except FileNotFoundError:
        print("Terraform not found. Make sure terraform is installed and in PATH")
        return None


def interactive_config_input():
    """Get configuration values interactively with validation"""
    print("\n📝 Manual Configuration Input")
    print("Please provide the following values:")

    config = {}

    # S3 bucket with validation
    while True:
        bucket = input("\nS3 bucket name: ").strip()
        if bucket:
            temp_config = {"s3_bucket_name": bucket, "aws_region": "us-east-1"}
            if validate_s3_bucket_name(bucket):
                config["s3_bucket_name"] = bucket
                break
            print("Please enter a valid S3 bucket name.")
        else:
            print("S3 bucket name is required.")

    # AWS region with validation
    region = input("\nAWS region [us-east-1]: ").strip() or "us-east-1"
    config["aws_region"] = region

    # Optional role ARNs
    snowflake_role = input(
        "\nSnowflake role ARN (optional, press Enter to skip): "
    ).strip()
    if snowflake_role:
        config["snowflake_role_arn"] = snowflake_role

    sagemaker_role = input(
        "\nSageMaker role ARN (optional, press Enter to skip): "
    ).strip()
    if sagemaker_role:
        config["sagemaker_role_arn"] = sagemaker_role

    return config


def validate_s3_bucket_name(bucket_name):
    """Validate S3 bucket name format"""
    if not bucket_name or len(bucket_name) < 3 or len(bucket_name) > 63:
        return False
    if not re.match(r"^[a-z0-9.-]+$", bucket_name):
        return False
    if ".." in bucket_name or ".-" in bucket_name or "-." in bucket_name:
        return False
    return True


def generate_config():
    """Generate config.json from terraform outputs"""

    print("🔧 Animal Insights Pipeline Configuration Generator")
    print("=" * 55)

    # Get terraform outputs
    terraform_config = get_terraform_outputs()

    if not terraform_config:
        print("\n⚠️  Could not get Terraform outputs.")
        print("This usually means:")
        print("1. Terraform hasn't been applied yet (run: terraform apply)")
        print("2. Terraform is not installed")
        print("3. You're not in the project root directory")

        use_manual = input("\nUse manual configuration input? (y/n): ").lower().strip()
        if use_manual not in ["y", "yes"]:
            print("Configuration cancelled.")
            return False

        config = interactive_config_input()
    else:
        config = terraform_config
        print("✅ Terraform outputs loaded successfully")

    # Add metadata
    config["created_at"] = datetime.now().isoformat()
    config["version"] = "1.0"
    config["generator"] = "config_generator.py"

    # Validate configuration
    print("\n🔍 Validating configuration...")
    if not validate_config(config):
        print("\n❌ Configuration validation failed!")
        retry = (
            input("Would you like to enter values manually? (y/n): ").lower().strip()
        )
        if retry in ["y", "yes"]:
            config.update(interactive_config_input())
            if not validate_config(config):
                print("❌ Manual configuration also failed validation.")
                return False
        else:
            return False

    # Test AWS connectivity
    if not test_aws_connectivity(config):
        print("\n⚠️  AWS connectivity issues detected.")
        print("You may encounter problems running the notebooks.")
        continue_anyway = (
            input("Continue with configuration anyway? (y/n): ").lower().strip()
        )
        if continue_anyway not in ["y", "yes"]:
            return False

    # Write config file
    config_path = "./config.json"
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"\n✅ Configuration saved to {config_path}")
    except Exception as e:
        print(f"\n❌ Failed to save configuration: {e}")
        return False

    # Display summary
    print("\n📋 Configuration Summary:")
    print("-" * 30)
    print(f"S3 Bucket: {config['s3_bucket_name']}")
    print(f"AWS Region: {config['aws_region']}")

    if config.get("snowflake_role_arn"):
        print(f"Snowflake Role: {config['snowflake_role_arn'][:50]}...")
    else:
        print("Snowflake Role: Not configured")

    if config.get("sagemaker_role_arn"):
        print(f"SageMaker Role: {config['sagemaker_role_arn'][:50]}...")
    else:
        print("SageMaker Role: Not configured")

    if config.get("snowflake_integration_status"):
        print(f"Integration Status: {config['snowflake_integration_status']}")

    print(f"\n🎯 Next Steps:")
    print("1. Upload data to S3 (austin_animal_outcomes.csv is already included):")
    print(
        f"   aws s3 cp data/austin_animal_outcomes.csv s3://{config['s3_bucket_name']}/raw/"
    )
    print("\n2. Start the tutorial:")
    print("   jupyter lab")
    print("   Open: notebooks/01_data_exploration.ipynb")

    return True


if __name__ == "__main__":
    try:
        success = generate_config()
        if not success:
            print("\n❌ Configuration generation failed.")
            sys.exit(1)
        print("\n🎉 Configuration generation completed successfully!")
    except KeyboardInterrupt:
        print("\n\n⚠️  Configuration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
