resource "aws_secretsmanager_secret" "backend_main" {
  name                    = "tg-forwarder-core"
  description             = "Gmail-Telegram forwarder environment"
  recovery_window_in_days = 7
}
