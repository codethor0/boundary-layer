variable "environment" {
  description = "Deployment environment name (staging or production)"
  type        = string
  default     = "staging"
}

variable "project_name" {
  description = "BoundaryLayer project identifier"
  type        = string
  default     = "boundary-layer"
}
