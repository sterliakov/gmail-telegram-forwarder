resource "aws_dynamodb_table" "users" {
  name           = "tg-forwarder-users"
  billing_mode   = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5
  hash_key       = "chat_id"

  attribute {
    name = "chat_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "messages" {
  name           = "tg-forwarder-messages"
  billing_mode   = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5
  hash_key       = "day"
  range_key      = "chat_id"

  attribute {
    name = "day"
    type = "S"
  }

  attribute {
    name = "chat_id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
}
