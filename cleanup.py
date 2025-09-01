#!/usr/bin/env python3
"""
Comprehensive cleanup script for Animal Insights Tutorial
Prevents unexpected AWS charges by cleaning up all resources
"""

import json
import subprocess
import sys
import time

import boto3


def cleanup_sagemaker():
    """Clean up all SageMaker resources"""
    print("Cleaning up SageMaker resources...")
    sagemaker = boto3.client("sagemaker")

    cleaned_items = []

    try:
        # Delete endpoints
        endpoints = sagemaker.list_endpoints()
        for endpoint in endpoints["Endpoints"]:
            if "animal" in endpoint["EndpointName"].lower():
                print(f"Deleting endpoint: {endpoint['EndpointName']}")
                sagemaker.delete_endpoint(EndpointName=endpoint["EndpointName"])
                cleaned_items.append(f"Endpoint: {endpoint['EndpointName']}")

        # Delete endpoint configurations
        configs = sagemaker.list_endpoint_configs()
        for config in configs["EndpointConfigs"]:
            if "animal" in config["EndpointConfigName"].lower():
                print(f"Deleting endpoint config: {config['EndpointConfigName']}")
                sagemaker.delete_endpoint_config(
                    EndpointConfigName=config["EndpointConfigName"]
                )
                cleaned_items.append(f"Endpoint config: {config['EndpointConfigName']}")

        # Delete models
        models = sagemaker.list_models()
        for model in models["Models"]:
            if "animal" in model["ModelName"].lower():
                print(f"Deleting model: {model['ModelName']}")
                sagemaker.delete_model(ModelName=model["ModelName"])
                cleaned_items.append(f"Model: {model['ModelName']}")

        if cleaned_items:
            print(f"Cleaned up {len(cleaned_items)} SageMaker resources")
        else:
            print("No SageMaker resources found to clean up")

    except Exception as e:
        print(f"SageMaker cleanup error: {e}")


def cleanup_s3():
    """Empty S3 buckets before Terraform destroy"""
    print("Cleaning up S3 buckets...")
    s3 = boto3.client("s3")

    try:
        # Get bucket name from Terraform
        result = subprocess.run(
            ["terraform", "output", "-raw", "s3_bucket_name"],
            cwd="terraform",
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            bucket_name = result.stdout.strip()
            print(f"Emptying S3 bucket: {bucket_name}")

            # Delete all objects and versions
            paginator = s3.get_paginator("list_object_versions")
            delete_keys = []

            for page in paginator.paginate(Bucket=bucket_name):
                # Delete regular objects
                if "Versions" in page:
                    for version in page["Versions"]:
                        delete_keys.append(
                            {"Key": version["Key"], "VersionId": version["VersionId"]}
                        )

                # Delete delete markers
                if "DeleteMarkers" in page:
                    for marker in page["DeleteMarkers"]:
                        delete_keys.append(
                            {"Key": marker["Key"], "VersionId": marker["VersionId"]}
                        )

            # Delete in batches of 1000 (AWS limit)
            for i in range(0, len(delete_keys), 1000):
                batch = delete_keys[i : i + 1000]
                if batch:
                    s3.delete_objects(Bucket=bucket_name, Delete={"Objects": batch})

            print(f"Deleted {len(delete_keys)} objects from S3")

    except subprocess.CalledProcessError:
        print("Could not get S3 bucket name from Terraform")
    except Exception as e:
        print(f"S3 cleanup error: {e}")


def cleanup_terraform():
    """Destroy Terraform infrastructure"""
    print("Destroying Terraform infrastructure...")
    try:
        result = subprocess.run(
            ["terraform", "destroy", "-auto-approve"], cwd="terraform"
        )
        if result.returncode == 0:
            print("Terraform resources destroyed successfully")
            return True
        else:
            print("Terraform destroy failed - check manually")
            return False
    except Exception as e:
        print(f"Terraform cleanup error: {e}")
        return False


def verify_cleanup():
    """Verify all resources are cleaned up"""
    print("\nVerifying cleanup...")

    issues = []

    try:
        # Check SageMaker endpoints
        sagemaker = boto3.client("sagemaker")
        endpoints = sagemaker.list_endpoints()
        active_endpoints = [
            ep
            for ep in endpoints["Endpoints"]
            if ep["EndpointStatus"] in ["InService", "Creating"]
            and "animal" in ep["EndpointName"].lower()
        ]

        if active_endpoints:
            issues.append(f"{len(active_endpoints)} SageMaker endpoints still active")
            for ep in active_endpoints:
                print(f"   - {ep['EndpointName']}: {ep['EndpointStatus']}")
        else:
            print("✅ No active SageMaker endpoints")

        # Check for S3 buckets
        s3 = boto3.client("s3")
        buckets = s3.list_buckets()
        animal_buckets = [
            b for b in buckets["Buckets"] if "animal-insights" in b["Name"]
        ]

        if animal_buckets:
            issues.append(f"{len(animal_buckets)} S3 buckets still exist")
            for bucket in animal_buckets:
                print(f"   - {bucket['Name']}")
        else:
            print("✅ No animal-insights S3 buckets found")

    except Exception as e:
        print(f"Verification error: {e}")

    if issues:
        print(f"\n⚠️  Found {len(issues)} potential issues:")
        for issue in issues:
            print(f"   - {issue}")
        print("\nYou may want to check the AWS Console manually")
    else:
        print("\n✅ Cleanup verification complete - no issues found")

    return len(issues) == 0


def estimate_monthly_costs():
    """Estimate what monthly costs would be if resources were left running"""
    print("\nCost Information:")
    print("If resources were left running, monthly costs could be:")
    print("• SageMaker ml.t2.medium endpoint: ~$35/month")
    print("• Snowflake X-Small warehouse: ~$23/month")
    print("• S3 storage: ~$1/month for tutorial data")
    print("• Total if left running: ~$60/month")
    print("\nThis cleanup prevents these charges!")


def main():
    """Run comprehensive cleanup"""
    print("🧹 Starting comprehensive cleanup of Animal Insights Pipeline")
    print("=" * 60)

    # Confirm cleanup
    response = input(
        "\nThis will delete ALL resources for this tutorial. Continue? (yes/no): "
    )
    if response.lower() not in ["yes", "y"]:
        print("Cleanup cancelled")
        return

    print("\nStep 1: Cleaning up SageMaker resources...")
    cleanup_sagemaker()

    # Wait for SageMaker deletions to process
    print("\nWaiting 30 seconds for SageMaker deletions to process...")
    time.sleep(30)

    print("\nStep 2: Emptying S3 buckets...")
    cleanup_s3()

    print("\nStep 3: Destroying Terraform infrastructure...")
    terraform_success = cleanup_terraform()

    print("\nStep 4: Verifying cleanup...")
    verification_success = verify_cleanup()

    estimate_monthly_costs()

    print("\n" + "=" * 60)
    if terraform_success and verification_success:
        print("🎉 Cleanup completed successfully!")
        print("\nWhat was cleaned up:")
        print("• All SageMaker endpoints, models, and configurations")
        print("• S3 buckets and all contained data")
        print("• IAM roles and policies")
        print("• All Terraform-managed resources")
    else:
        print("⚠️  Cleanup completed with some issues")
        print("Please check AWS Console manually for any remaining resources")

    print("\nNext time you want to run the tutorial:")
    print("1. Run: terraform apply")
    print("2. Follow the tutorial from the beginning")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCleanup interrupted. Some resources may still exist.")
        print("Run this script again or check AWS Console manually.")
        sys.exit(1)
