#!/usr/bin/env python3
"""
Validation script for Animal Insights Pipeline setup
Run this to check if your environment is ready
"""

import importlib
import os
import subprocess
import sys


def check_command(command, name):
    """Check if a command is available"""
    try:
        subprocess.run([command, "--version"], capture_output=True, check=True)
        print(f"✅ {name} is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"❌ {name} is not installed or not working")
        return False


def check_python_package(package, name=None):
    """Check if a Python package is available"""
    if name is None:
        name = package
    try:
        importlib.import_module(package)
        print(f"✅ {name} package is available")
        return True
    except ImportError:
        print(f"❌ {name} package is missing")
        return False


def check_aws_credentials():
    """Check if AWS credentials are configured"""
    try:
        result = subprocess.run(
            ["aws", "sts", "get-caller-identity"],
            capture_output=True,
            check=True,
            text=True,
        )
        import json

        identity = json.loads(result.stdout)
        print(
            f"✅ AWS credentials configured for account {identity.get('Account', 'Unknown')}"
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        print("❌ AWS credentials not configured or AWS CLI not working")
        return False


def check_file_exists(filepath, description):
    """Check if a required file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description} exists")
        return True
    else:
        print(f"❌ {description} missing at {filepath}")
        return False


def check_terraform_state():
    """Check if Terraform has been applied"""
    try:
        result = subprocess.run(
            ["terraform", "output", "-json"],
            cwd="./terraform",
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            import json

            outputs = json.loads(result.stdout)
            if outputs:
                print("✅ Terraform infrastructure deployed")
                if "s3_bucket_name" in outputs:
                    print(f"   S3 bucket: {outputs['s3_bucket_name']['value']}")
                return True
            else:
                print("⚠️  Terraform state exists but no outputs found")
                return False
        else:
            print("❌ Terraform not applied or no state found")
            return False
    except Exception as e:
        print(f"❌ Error checking Terraform state: {e}")
        return False


def main():
    """Run all validation checks"""
    print("Validating Animal Insights Pipeline Setup")
    print("=" * 50)

    checks = []

    # Check command line tools
    print("\n🔧 Command Line Tools:")
    checks.append(check_command("python", "Python"))
    checks.append(check_command("pip", "pip"))
    checks.append(check_command("terraform", "Terraform"))
    checks.append(check_command("aws", "AWS CLI"))

    # Check Python packages
    print("\n🐍 Python Packages:")
    packages = [
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("boto3", "boto3"),
        ("sklearn", "scikit-learn"),
        ("matplotlib", "matplotlib"),
        ("jupyter", "Jupyter"),
    ]

    for package, name in packages:
        checks.append(check_python_package(package, name))

    # Check AWS configuration
    print("\n☁️  AWS Configuration:")
    checks.append(check_aws_credentials())

    # Check Terraform state
    print("\n🏗️  Infrastructure:")
    checks.append(check_terraform_state())

    # Check required files
    print("\n📁 Required Files:")
    files = [
        ("./terraform/main.tf", "Terraform configuration"),
        ("./requirements.txt", "Python requirements"),
        ("./data/austin_animal_outcomes.csv", "Dataset"),
    ]

    for filepath, description in files:
        checks.append(check_file_exists(filepath, description))

    # Summary
    passed = sum(checks)
    total = len(checks)

    print("\n" + "=" * 50)
    print(f"📊 Validation Results: {passed}/{total} checks passed")

    if passed == total:
        print("🎉 All checks passed! You're ready to start the tutorial.")
        print("\nNext steps:")
        print("1. Run: python config_generator.py")
        print("2. Run: jupyter lab")
        print("3. Open notebooks/01_data_exploration.ipynb")
    else:
        print("⚠️  Some checks failed. Please fix the issues above before continuing.")
        print("\nCommon fixes:")
        print("- Install Terraform: https://terraform.io/downloads")
        print("- Install AWS CLI: pip install awscli && aws configure")
        print("- Dataset should already be included in data/ directory")
        print("- Run: pip install -r requirements.txt")
        if not check_terraform_state():
            print("- Run: cd terraform && terraform init && terraform apply")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
