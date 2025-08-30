#!/bin/bash
set -euo pipefail

# Create S3 bucket for images
awslocal s3 mb s3://images-bucket || true

# Create DynamoDB table for image metadata
awslocal dynamodb create-table \
	--table-name images \
	--attribute-definitions AttributeName=image_id,AttributeType=S AttributeName=user_id,AttributeType=S AttributeName=created_at,AttributeType=S \
	--key-schema AttributeName=image_id,KeyType=HASH \
	--billing-mode PAY_PER_REQUEST \
	--global-secondary-indexes 'IndexName=user_id-created_at-index,KeySchema=[{AttributeName=user_id,KeyType=HASH},{AttributeName=created_at,KeyType=RANGE}],Projection={ProjectionType=ALL}' || true