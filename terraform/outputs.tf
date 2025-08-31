output "s3_bucket_name" {
  value       = aws_s3_bucket.data_bucket.id
  description = "Name of the S3 bucket for data storage"
}

output "snowflake_role_arn" {
  value       = aws_iam_role.snowflake_role.arn
  description = "ARN of the IAM role for Snowflake integration"
}

output "sagemaker_role_arn" {
  value       = aws_iam_role.sagemaker_role.arn
  description = "ARN of the IAM role for SageMaker execution"
}

output "snowflake_integration_status" {
  value       = var.enable_snowflake_integration ? "ENABLED - Secure cross-account access configured" : "DISABLED - Using temporary configuration"
  description = "Status of Snowflake integration security"
}

output "next_steps" {
  value = var.enable_snowflake_integration ? [
    "Infrastructure deployment complete!\n",
    "Upload your data: aws s3 cp data/austin_animal_outcomes.csv s3://${aws_s3_bucket.data_bucket.id}/raw/\n",
    "Use sql/snowflake_setup.sql to set up Snowflake database and tables\n",
    "Start with notebooks/data_exploration.py for data analysis\n"
    ] : [
    "Stage 1 complete - Initial infrastructure deployed\n",
    "Next: Set up Snowflake integration using this role ARN: ${aws_iam_role.snowflake_role.arn}\n",
    "Use SQL: CREATE STORAGE INTEGRATION s3_integration TYPE=EXTERNAL_STAGE STORAGE_PROVIDER='S3' STORAGE_AWS_ROLE_ARN='${aws_iam_role.snowflake_role.arn}' STORAGE_ALLOWED_LOCATIONS=('s3://${aws_s3_bucket.data_bucket.id}/')\n",
    "Then run: DESC STORAGE INTEGRATION s3_integration\n",
    "Update terraform.tfvars with the Snowflake values and run terraform apply again\n"
  ]
  description = "Next steps based on current deployment stage"
}
