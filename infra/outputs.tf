output "bucket" {
  description = "Gia tri cho secret ARTIFACT_BUCKET"
  value       = aws_s3_bucket.lab.bucket
}

output "server_host" {
  description = "Gia tri cho secret SERVER_HOST (Elastic IP)"
  value       = aws_eip.api.public_ip
}

output "server_user" {
  description = "Gia tri cho secret SERVER_USER"
  value       = "ubuntu"
}

output "storage_credentials" {
  description = "Gia tri cho secret STORAGE_CREDENTIALS (JSON access key cua user income-lab-ci)"
  sensitive   = true
  value = jsonencode({
    aws_access_key_id     = aws_iam_access_key.ci.id
    aws_secret_access_key = aws_iam_access_key.ci.secret
    region                = var.region
  })
}

output "api_urls" {
  value = {
    healthz = "http://${aws_eip.api.public_ip}:8080/healthz"
    score   = "http://${aws_eip.api.public_ip}:8080/score"
  }
}
