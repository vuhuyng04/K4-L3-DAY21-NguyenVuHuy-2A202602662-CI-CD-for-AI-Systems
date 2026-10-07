variable "region" {
  description = "AWS region cho bucket va VM"
  type        = string
  default     = "ap-southeast-1"
}

variable "bucket_name" {
  description = "Ten S3 bucket chua du lieu DVC (dvc/) va model (artifacts/)"
  type        = string
  default     = "income-lab-vuhuyng04-d21"
}

variable "local_iam_user" {
  description = "IAM user dung tren may ca nhan (dvc push); duoc cap quyen doc/ghi bucket. De trong de bo qua."
  type        = string
  default     = "huyaws"
}

variable "instance_type" {
  description = "Loai EC2 instance chay income-api"
  type        = string
  default     = "t3.micro"
}

variable "deploy_public_key_path" {
  description = "Public key cua cap khoa SSH ma GitHub Actions dung de deploy (secret SERVER_SSH_KEY la private key tuong ung)"
  type        = string
  default     = "~/.ssh/income_deploy.pub"
}

variable "ssh_allowed_cidrs" {
  description = "Dai IP duoc SSH vao VM. GitHub-hosted runner co IP thay doi nen mac dinh mo toan bo; chi xac thuc bang key."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
