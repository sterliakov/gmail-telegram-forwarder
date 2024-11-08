output "github_lambda_deploy_role" {
  value = module.github_actions_deploy_lambda_role.arn
}

output "backend_lambda_ecr_url" {
  value = aws_ecr_repository.backend_lambda.repository_url
}

output "lambda_url" {
  value = aws_lambda_function_url.backend.function_url
}

output "lambda_name" {
  value = aws_lambda_function.backend_main.function_name
}

output "lambda_alias" {
  value = aws_lambda_alias.backend_stable.name
}

output "deployed_tag" {
  value = local.deployed_tag
}
