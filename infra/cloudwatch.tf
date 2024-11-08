resource "aws_cloudwatch_event_rule" "polling" {
  name                = "tg-forwarder-polling-event"
  schedule_expression = "rate(1 minute)"
}
resource "aws_cloudwatch_event_target" "polling" {
  rule = aws_cloudwatch_event_rule.polling.name
  arn  = aws_lambda_alias.backend_stable.arn
  input = jsonencode({
    action = "CHECK"
  })
}
