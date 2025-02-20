variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "api-cluster"
}

variable "mongodb_atlas_project_id" {
  description = "MongoDB Atlas Project ID"
  type        = string
}

variable "domain_name" {
  description = "Domain name for the API"
  type        = string
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID"
  type        = string
}
