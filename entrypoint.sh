#! /bin/sh

if [ -z "${AWS_LAMBDA_RUNTIME_API}" ]; then
  exec /usr/local/bin/aws-lambda-rie /usr/bin/env python -m awslambdaric "$@"
else
  exec /usr/bin/env python -m awslambdaric "$@"
fi
