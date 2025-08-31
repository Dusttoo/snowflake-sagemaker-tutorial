variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "snowflake_account_id" {
  description = "Snowflake AWS account ID for cross-account access"
  type        = string
  sensitive   = true
  default     = ""
  
  validation {
    condition     = length(var.snowflake_account_id) == 0 || can(regex("^[0-9]{12}$", var.snowflake_account_id))
    error_message = "Snowflake account ID must be a 12-digit AWS account number or empty for initial deployment."
  }
}

variable "snowflake_external_id" {
  description = "External ID for Snowflake role assumption"
  type        = string
  sensitive   = true
  default     = ""
  
  validation {
    condition     = length(var.snowflake_external_id) == 0 || length(var.snowflake_external_id) > 10
    error_message = "Snowflake external ID must be provided from Snowflake integration or empty for initial deployment."
  }
}

variable "enable_snowflake_integration" {
  description = "Enable Snowflake integration (requires snowflake_account_id and snowflake_external_id)"
  type        = bool
  default     = false
}
