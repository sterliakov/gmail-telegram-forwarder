resource "aws_cloudwatch_log_group" "main_logs" {
  name              = "/aws/lambda/tg-forwarder"
  retention_in_days = 365
  skip_destroy      = true
}
