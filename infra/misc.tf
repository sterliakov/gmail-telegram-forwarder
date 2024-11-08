data "aws_iam_policy_document" "assume_role" {
  for_each = toset([
    "lambda"
  ])

  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["${each.key}.amazonaws.com"]
    }
  }
}
