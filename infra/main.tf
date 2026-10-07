# -----------------------------------------------------------------------------
# S3 bucket: dvc/ (du lieu) va artifacts/ (model + report)
# Bucket da duoc tao bang CLI truoc do -> import vao state thay vi tao moi.
# -----------------------------------------------------------------------------
import {
  to = aws_s3_bucket.lab
  id = var.bucket_name
}

resource "aws_s3_bucket" "lab" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_public_access_block" "lab" {
  bucket                  = aws_s3_bucket.lab.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "aws_iam_policy_document" "bucket_rw" {
  statement {
    sid       = "ListLabBucket"
    actions   = ["s3:ListBucket", "s3:GetBucketLocation"]
    resources = [aws_s3_bucket.lab.arn]
  }
  statement {
    sid       = "ReadWriteLabObjects"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${aws_s3_bucket.lab.arn}/*"]
  }
}

data "aws_iam_policy_document" "bucket_read_model" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.lab.arn}/artifacts/current/*"]
  }
}

# -----------------------------------------------------------------------------
# IAM user cho GitHub Actions (secret STORAGE_CREDENTIALS) - chi co quyen tren bucket
# -----------------------------------------------------------------------------
resource "aws_iam_user" "ci" {
  name = "income-lab-ci"
}

resource "aws_iam_user_policy" "ci_bucket" {
  name   = "income-lab-bucket-rw"
  user   = aws_iam_user.ci.name
  policy = data.aws_iam_policy_document.bucket_rw.json
}

resource "aws_iam_access_key" "ci" {
  user = aws_iam_user.ci.name
}

# User tren may ca nhan cung can doc/ghi bucket de chay `dvc push`
resource "aws_iam_user_policy" "local_bucket" {
  count  = var.local_iam_user == "" ? 0 : 1
  name   = "income-lab-bucket-rw"
  user   = var.local_iam_user
  policy = data.aws_iam_policy_document.bucket_rw.json
}

# -----------------------------------------------------------------------------
# EC2: role chi doc artifacts/current/* -> VM khong can luu access key
# -----------------------------------------------------------------------------
data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "api" {
  name               = "income-api-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

resource "aws_iam_role_policy" "api_read_model" {
  name   = "read-current-model"
  role   = aws_iam_role.api.id
  policy = data.aws_iam_policy_document.bucket_read_model.json
}

resource "aws_iam_instance_profile" "api" {
  name = "income-api-profile"
  role = aws_iam_role.api.name
}

data "aws_vpc" "default" {
  default = true
}

resource "aws_security_group" "api" {
  name        = "income-api"
  description = "income-api: SSH (deploy) + 8080 (inference)"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH cho GitHub Actions deploy"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_allowed_cidrs
  }

  ingress {
    description = "Inference API"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_key_pair" "deploy" {
  key_name   = "income-deploy"
  public_key = file(pathexpand(var.deploy_public_key_path))
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

resource "aws_instance" "api" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.deploy.key_name
  iam_instance_profile   = aws_iam_instance_profile.api.name
  vpc_security_group_ids = [aws_security_group.api.id]

  associate_public_ip_address = true

  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    bucket   = aws_s3_bucket.lab.bucket
    region   = var.region
    serve_py = file("${path.module}/../src/serve.py")
  })
  user_data_replace_on_change = true

  root_block_device {
    volume_size = 16
    volume_type = "gp3"
  }

  tags = {
    Name = "income-api"
  }
}

# IP co dinh: khong doi khi VM stop/start -> secret SERVER_HOST khong phai sua
resource "aws_eip" "api" {
  instance = aws_instance.api.id
  domain   = "vpc"
}
