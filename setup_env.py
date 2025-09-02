#!/usr/bin/env python3
"""
Complete setup script for Animal Insights Pipeline
Guides users through the entire setup process step by step
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def _get_venv_paths():
    """Return (python_path, pip_path, activate_script, venv_bin_path) for the local venv."""
    if os.name == "nt":
        python_path = os.path.abspath("venv\\Scripts\\python.exe")
        pip_path = os.path.abspath("venv\\Scripts\\pip.exe")
        activate_script = "venv\\Scripts\\activate.bat"
        venv_bin_path = os.path.abspath("venv\\Scripts")
    else:
        python_path = os.path.abspath("venv/bin/python")
        pip_path = os.path.abspath("venv/bin/pip")
        activate_script = "venv/bin/activate"
        venv_bin_path = os.path.abspath("venv/bin")
    return python_path, pip_path, activate_script, venv_bin_path


def print_step(step_num, title):
    """Print a formatted step header"""
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {title}")
    print(f"{'='*60}")


def check_prerequisites():
    """Check if basic prerequisites are installed"""
    print_step(1, "Checking Prerequisites")

    missing_tools = []

    # Check Python
    try:
        result = subprocess.run(
            [sys.executable, "--version"], capture_output=True, text=True
        )
        print(f"Python version: {result.stdout.strip()}")
    except:
        missing_tools.append("Python 3.8+")

    # Check pip
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"], capture_output=True, check=True
        )
        print("pip: Available")
    except:
        missing_tools.append("pip")

    # Check terraform
    try:
        result = subprocess.run(
            ["terraform", "version"], capture_output=True, text=True, check=True
        )
        print(f"Terraform: {result.stdout.split()[1]}")
    except:
        missing_tools.append("terraform")

    # Check AWS CLI
    try:
        result = subprocess.run(
            ["aws", "--version"], capture_output=True, text=True, check=True
        )
        print(f"AWS CLI: {result.stdout.strip()}")
    except:
        missing_tools.append("aws-cli")

    if missing_tools:
        print(f"\nMissing tools: {', '.join(missing_tools)}")
        print("\nPlease install missing tools and run this script again.")
        print("Installation guides:")
        print("- Terraform: https://terraform.io/downloads")
        print(
            "- AWS CLI (v2): https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        )
        return False

    print("\nAll prerequisites found!")
    return True


def setup_python_environment():
    """Set up Python virtual environment"""
    print_step(2, "Setting Up Python Environment")

    if os.path.exists("venv"):
        print("Virtual environment already exists")
        return True

    try:
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)

        python_path, pip_path, activate_script, venv_bin_path = _get_venv_paths()

        print("Installing Python packages...")
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)

        # Ensure boto3 is available for config_generator.py
        subprocess.run([pip_path, "install", "boto3"], check=True)

        # Update environment to activate venv for subsequent steps
        current_path = os.environ.get("PATH", "")
        os.environ["PATH"] = venv_bin_path + os.pathsep + current_path
        os.environ["VIRTUAL_ENV"] = os.path.abspath("venv")

        print(f"\nVirtual environment created successfully!")
        print(f"To activate it manually, run: source {activate_script}")

        return True

    except subprocess.CalledProcessError as e:
        print(f"Failed to set up Python environment: {e}")
        return False


def configure_aws():
    """Guide user through AWS configuration"""
    print_step(3, "Configuring AWS")

    try:
        # Check if AWS is already configured
        result = subprocess.run(
            ["aws", "sts", "get-caller-identity"], capture_output=True, text=True
        )
        if result.returncode == 0:
            identity = json.loads(result.stdout)
            print(f"AWS already configured for account: {identity.get('Account')}")
            return True
    except:
        pass

    print("AWS credentials not configured. Let's set them up.")
    print("\nYou'll need:")
    print("1. AWS Access Key ID")
    print("2. AWS Secret Access Key")
    print("3. Default region (recommend: us-east-1)")

    proceed = input("\nDo you have your AWS credentials ready? (y/n): ")
    if proceed.lower() != "y":
        print("Please get your AWS credentials and run this script again.")
        print("You can get them from: https://console.aws.amazon.com/iam/")
        return False

    try:
        subprocess.run(["aws", "configure"], check=True)

        # Verify configuration worked
        result = subprocess.run(
            ["aws", "sts", "get-caller-identity"],
            capture_output=True,
            text=True,
            check=True,
        )
        identity = json.loads(result.stdout)
        print(f"\nAWS configured successfully for account: {identity.get('Account')}")
        return True

    except Exception as e:
        print(f"AWS configuration failed: {e}")
        return False


def deploy_infrastructure():
    """Deploy Terraform infrastructure"""
    print_step(4, "Deploying Infrastructure")

    try:
        os.chdir("terraform")

        print("Initializing Terraform...")
        subprocess.run(["terraform", "init"], check=True)

        print("Planning infrastructure deployment...")
        subprocess.run(["terraform", "plan"], check=True)

        deploy = input(
            "\nDeploy infrastructure? This will create AWS resources. (y/n): "
        )
        if deploy.lower() != "y":
            print("Infrastructure deployment skipped.")
            return False

        print("Deploying infrastructure...")
        subprocess.run(["terraform", "apply", "-auto-approve"], check=True)

        # Get outputs
        result = subprocess.run(
            ["terraform", "output", "-json"], capture_output=True, text=True, check=True
        )
        outputs = json.loads(result.stdout)

        os.chdir("..")  # Go back to root directory

        # Save outputs for easy access
        config = {k: v["value"] for k, v in outputs.items()}
        with open("terraform_outputs.json", "w") as f:
            json.dump(config, f, indent=2)

        print("\nInfrastructure deployed successfully!")
        print(f"S3 Bucket: {config.get('s3_bucket_name', 'Unknown')}")
        print(f"Snowflake Role: {config.get('snowflake_role_arn', 'Unknown')}")

        return True

    except subprocess.CalledProcessError as e:
        print(f"Infrastructure deployment failed: {e}")
        return False
    except Exception as e:
        print(f"Error during deployment: {e}")
        return False


def setup_snowflake():
    """Guide user through Snowflake setup"""
    print_step(5, "Setting Up Snowflake Integration")

    print("Now we need to set up Snowflake integration.")
    print("\n1. Create a free Snowflake account at: https://signup.snowflake.com/")
    print("2. Once logged in, open a new worksheet")

    # Read the role ARN
    try:
        with open("terraform_outputs.json", "r") as f:
            outputs = json.load(f)
            role_arn = outputs.get("snowflake_role_arn", "UNKNOWN")
            bucket_name = outputs.get("s3_bucket_name", "UNKNOWN")
    except:
        print("Could not read terraform outputs. Please check terraform deployment.")
        return False

    print(f"\n3. Run this SQL in Snowflake (copy/paste the entire block):")
    print("-" * 60)

    sql_template = f"""CREATE STORAGE INTEGRATION s3_integration
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = '{role_arn}'
  STORAGE_ALLOWED_LOCATIONS = ('s3://{bucket_name}/');

DESC STORAGE INTEGRATION s3_integration;"""

    print(sql_template)
    print("-" * 60)

    print("\n4. From the DESC output, you need TWO values:")
    print(
        "   - STORAGE_AWS_IAM_USER_ARN: Complete ARN like 'arn:aws:iam::123456789012:user/k7m2-s-v2st001'"
    )
    print("   - STORAGE_AWS_EXTERNAL_ID: Complete string like 'ABC123_SFCRole=1_xyz='")

    input("\nPress Enter when you've completed the Snowflake setup...")

    # Get Snowflake details from user with better validation
    print("\nEnter the COMPLETE values from Snowflake DESC INTEGRATION output:")

    while True:
        snowflake_account_id = input(
            "Snowflake Account ID (12-digit number inside STORAGE_AWS_IAM_USER_ARN, e.g., for arn:aws:iam::123456789012:user/la761000-s the account ID is 123456789012): "
        ).strip()
        if not snowflake_account_id:
            print("This value is required for secure integration.")
            continue
        if not (snowflake_account_id.isdigit() and len(snowflake_account_id) == 12):
            print(
                "Snowflake account ID must be a 12-digit number. Please copy it from the STORAGE_AWS_IAM_USER_ARN value."
            )
            continue
        break

    while True:
        external_id = input("STORAGE_AWS_EXTERNAL_ID (complete string): ").strip()
        if not external_id:
            print("This value is required for secure integration.")
            continue
        if len(external_id) < 10:
            print("External ID seems too short - please copy the complete value")
            continue
        break

    # Update terraform.tfvars with the account ID and external ID
    tfvars_content = f"""aws_region = "us-east-1"
snowflake_account_id = "{snowflake_account_id}"
snowflake_external_id = "{external_id}"
enable_snowflake_integration = true
"""

    try:
        with open("terraform/terraform.tfvars", "w") as f:
            f.write(tfvars_content)
        print("Terraform configuration updated with Snowflake values...")
    except Exception as e:
        print(f"Failed to write terraform.tfvars: {e}")
        return False

    print("Updating Terraform with Snowflake integration...")
    try:
        os.chdir("terraform")

        # Run terraform plan first to show what will change
        print("Planning Terraform updates...")
        plan_result = subprocess.run(
            ["terraform", "plan"], capture_output=True, text=True
        )

        if plan_result.returncode != 0:
            print("Terraform plan failed:")
            print(plan_result.stderr)
            return False

        # Apply the changes
        subprocess.run(
            ["terraform", "apply", "-auto-approve"],
            capture_output=True,
            text=True,
            check=True,
        )
        os.chdir("..")
        print("Snowflake integration completed successfully!")
        return True

    except subprocess.CalledProcessError as e:
        os.chdir("..")  # Make sure we're back in root directory
        print("Failed to update Terraform:")
        print(f"Error: {e}")
        if e.stderr:
            print(f"Details: {e.stderr}")

        print("\nThis usually means one of these issues:")
        print("1. The Snowflake values were not copied correctly")
        print("2. The Snowflake integration was not created properly")
        print("3. There's a formatting issue with the ARN or External ID")

        print(f"\nYou can fix this manually by:")
        print(
            f"1. Verify the Snowflake integration was created: DESC STORAGE INTEGRATION s3_integration;"
        )
        print(f"2. Check terraform/terraform.tfvars has the correct values")
        print(f"3. Run: cd terraform && terraform plan && terraform apply")

        return False
    except Exception as e:
        os.chdir("..")
        print(f"Unexpected error during Terraform update: {e}")
        return False


def final_setup():
    """Complete final setup steps"""
    print_step(6, "Final Setup")

    if not os.path.exists("venv"):
        if not setup_python_environment():
            print("Virtual environment is required to continue.")
            return False

    try:
        # Generate config for notebooks
        print("Generating configuration for notebooks...")
        venv_python, _, _, _ = _get_venv_paths()
        subprocess.run([venv_python, "config_generator.py"], check=True)

        print("Setup complete!")
        print("\nNext steps:")
        print("1. Upload data to S3 (austin_animal_outcomes.csv is already included):")

        try:
            with open("terraform_outputs.json", "r") as f:
                outputs = json.load(f)
                bucket_name = outputs.get("s3_bucket_name", "YOUR_BUCKET")
                print(
                    f"   aws s3 cp data/austin_animal_outcomes.csv s3://{bucket_name}/raw/"
                )
        except:
            print("   aws s3 cp data/austin_animal_outcomes.csv s3://YOUR_BUCKET/raw/")

        print("\n2. Start Jupyter and begin the tutorial:")
        print("   jupyter lab")
        print("   Open: notebooks/01_data_exploration.ipynb")

        return True

    except Exception as e:
        print(f"Final setup error: {e}")
        return False


def main():
    """Main setup orchestration"""
    print("Welcome to Animal Insights Pipeline Setup!")
    print("This script will guide you through the complete setup process.")

    steps = [
        ("Check Prerequisites", check_prerequisites),
        ("Setup Python Environment", setup_python_environment),
        ("Configure AWS", configure_aws),
        ("Deploy Infrastructure", deploy_infrastructure),
        ("Setup Snowflake", setup_snowflake),
        ("Final Setup", final_setup),
    ]

    for i, (name, func) in enumerate(steps, 1):
        try:
            if not func():
                print(f"\nSetup failed at step {i}: {name}")
                print("Please resolve the issue and run the script again.")
                return False
        except KeyboardInterrupt:
            print("\nSetup interrupted by user.")
            return False
        except Exception as e:
            print(f"\nUnexpected error in step {i} ({name}): {e}")
            return False

    print("\n" + "=" * 60)
    print("Setup completed successfully!")
    print("=" * 60)
    print("\nYou now have a complete data pipeline infrastructure.")
    print("Follow the next steps printed above to start the tutorial.")


if __name__ == "__main__":
    main()
