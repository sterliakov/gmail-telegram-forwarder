data "aws_iam_policy_document" "lambda_execution_policy" {
  statement {
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = [
      aws_cloudwatch_log_group.main_logs.arn,
      "${aws_cloudwatch_log_group.main_logs.arn}:*",
    ]
  }
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.backend_main.arn]
  }

  statement {
    actions = [
      "dynamodb:BatchGetItem",
      "dynamodb:BatchWriteItem",
      "dynamodb:ConditionCheckItem",
      "dynamodb:PutItem",
      "dynamodb:DescribeTable",
      "dynamodb:DeleteItem",
      "dynamodb:GetItem",
      "dynamodb:Scan",
      "dynamodb:Query",
      "dynamodb:UpdateItem"
    ]
    resources = [
      aws_dynamodb_table.users.arn,
      aws_dynamodb_table.messages.arn,
    ]
  }
  statement {
    actions = ["dynamodb:DescribeLimits"]
    resources = [
      aws_dynamodb_table.users.arn,
      "${aws_dynamodb_table.users.arn}/index/*",
      aws_dynamodb_table.messages.arn,
      "${aws_dynamodb_table.messages.arn}/index/*",
    ]
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = "tg-forwarder-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role["lambda"].json
}
resource "aws_iam_policy" "lambda_policy" {
  name   = "tg-forwarder-execution-policy"
  policy = data.aws_iam_policy_document.lambda_execution_policy.json
}
resource "aws_iam_role_policy_attachment" "be_lambda" {
  policy_arn = aws_iam_policy.lambda_policy.arn
  role       = aws_iam_role.lambda_role.name
}

resource "aws_lambda_function" "backend_main" {
  function_name = "tg-forwarder-backend"
  role          = aws_iam_role.lambda_role.arn

  image_uri     = "${aws_ecr_repository.backend_lambda.repository_url}:${local.deployed_tag}"
  package_type  = "Image"
  architectures = ["x86_64"]
  publish       = true

  timeout     = 30
  memory_size = 512
  ephemeral_storage {
    size = 1024
  }

  environment {
    variables = {
      SECRET_NAME = aws_secretsmanager_secret.backend_main.name
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.main_logs.name
  }

  depends_on = [module.ecr_repo_image]
}

resource "aws_lambda_alias" "backend_stable" {
  name             = "stable"
  function_name    = aws_lambda_function.backend_main.arn
  function_version = "$LATEST"

  lifecycle {
    ignore_changes = [function_version, description]
  }
}

resource "aws_lambda_function_url" "backend" {
  function_name      = aws_lambda_function.backend_main.function_name
  qualifier          = aws_lambda_alias.backend_stable.name
  authorization_type = "NONE"

  cors {
    allow_credentials = true
    allow_origins     = ["*"]
    allow_methods     = ["*"]
  }
}

resource "aws_lambda_permission" "allow_cloudwatch_polling" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.backend_main.function_name
  qualifier     = aws_lambda_alias.backend_stable.name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.polling.arn
}
