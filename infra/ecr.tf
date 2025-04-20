resource "aws_ecr_repository" "backend_lambda" {
  name = "tg-forwarder"
  image_scanning_configuration {
    scan_on_push = false
  }
}

resource "aws_ecr_lifecycle_policy" "remove_old_versions" {
  repository = aws_ecr_repository.backend_lambda.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

module "ecr_repo_image" {
  source  = "sterliakov/ecr-image/aws"
  version = "0.2.0"

  push_ecr_is_public = false
  push_repo_fqdn     = replace(aws_ecr_repository.backend_lambda.repository_url, "//.*$/", "") # remove everything after first slash
  push_repo_name     = aws_ecr_repository.backend_lambda.name
  push_image_tag     = local.deployed_tag
}
