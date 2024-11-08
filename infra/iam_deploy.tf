module "github_actions_deploy_lambda_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-github-oidc-role"
  version = "5.47.1"

  name     = "tg-forwarder-deploy"
  subjects = ["sterliakov/gmail-telegram-forwarder:*"]
  policies = {
    extra = aws_iam_policy.github_actions_deploy_lambda.arn
  }
}

resource "aws_iam_policy" "github_actions_deploy_lambda" {
  name   = "update-tg-forwarder-lambda"
  policy = data.aws_iam_policy_document.github_actions_deploy_lambda.json
}

data "aws_iam_policy_document" "github_actions_deploy_lambda" {
  statement {
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:GetRepositoryPolicy",
      "ecr:DescribeRepositories",
      "ecr:ListImages",
      "ecr:DescribeImages",
      "ecr:BatchGetImage",
      "ecr:ListTagsForResource",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:PutImage"
    ]
    resources = [aws_ecr_repository.backend_lambda.arn]
  }
  statement {
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "lambda:GetFunctionConfiguration",
      "lambda:GetFunction",
      "lambda:UpdateFunctionCode",
      "lambda:UpdateAlias",
      "lambda:InvokeFunction"
    ]
    resources = [
      aws_lambda_function.backend_main.arn,
      aws_lambda_alias.backend_stable.arn
    ]
  }
}
