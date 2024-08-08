"""An AWS Python Pulumi program"""

import os
import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx

# Create an AWS resource (S3 Bucket)
bucket = aws.s3.BucketV2("bucketv2resource",
    bucket_prefix="food-truck-mapr",
    force_destroy=True,
    object_lock_enabled=False,
)

bucket_ownership_controls = aws.s3.BucketOwnershipControls("controls",
    bucket=bucket.id,
    rule={
        "object_ownership": "BucketOwnerPreferred",
    }
)

bucket_public_access_blocks = aws.s3.BucketPublicAccessBlock("accessblock",
    bucket=bucket.id,
    block_public_acls=False,
    block_public_policy=False,
    ignore_public_acls=False,
    restrict_public_buckets=False,
)

bucket_acl_v2 = aws.s3.BucketAclV2("acl",
    bucket=bucket.id,
    acl="public-read",
    opts = pulumi.ResourceOptions(depends_on=[bucket_ownership_controls, bucket_public_access_blocks])
)

bucket_website_config = aws.s3.BucketWebsiteConfigurationV2("bucketwebsite",
    bucket=bucket.id,
    index_document={
        "suffix": "map.html"
    }
)

# basic dynamodb table
dynamodb_table = aws.dynamodb.Table("basic-dynamodb-table",
    name="food-truk-mapr",
    billing_mode="PROVISIONED",
    read_capacity=20,
    write_capacity=20,
    hash_key="locationid",
    attributes=[
        {
            "name": "locationid",
            "type": "N",
        },
    ],
    tags={
        "Environment": "prod",
    })


repo = awsx.ecr.Repository("imagerepo",
    name="food-truk-mapr",
    force_delete=True,
)

image = awsx.ecr.Image("image",
    repository_url=repo.url
)

lambda_role = aws.iam.Role('lambdaRole',
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Effect": "Allow",
                "Sid": ""
            }
        ]
    }"""
)

# TODO: waaay too permissive :)
lambda_role_policy = aws.iam.RolePolicy('lambdaRolePolicy',
    role=lambda_role.id,
    policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:*"
                ],
                "Resource": [
                    "arn:aws:s3:::*",
                    "arn:aws:s3:::*/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:*"
                ],
                "Resource": [
                    "arn:aws:dynamodb:*:*:*",
                    "arn:aws:dynamodb:*:*:*/*"
                ]
            },
            {
            "Action": ["logs:*", "cloudwatch:*"],
            "Resource": "*",
            "Effect": "Allow"
            }
        ]
    }"""
)

lambda_function = aws.lambda_.Function("lambdafunction",
    role=lambda_role.arn,
    package_type='Image',
    image_uri=image.image_uri,
    timeout=300,
    memory_size=1024,
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "GOOGLE_MAPS_API_KEY": os.environ['GOOGLE_MAPS_API_KEY'],
            "S3_BUCKET": bucket.id,
            "DYNAMODB_TABLE_NAME": dynamodb_table.id,
        }
    )
)

every_hour_rule = aws.cloudwatch.EventRule("everyhour",
    schedule_expression="rate(1 hour)"
)

lambda_permission = aws.lambda_.Permission("lambda-permission",
    action="lambda:InvokeFunction",
    function=lambda_function.arn,
    principal="events.amazonaws.com",
    source_arn=every_hour_rule.arn,
)

event_target = aws.cloudwatch.EventTarget("event-target",
    rule=every_hour_rule.name,
    arn=lambda_function.arn,
)

pulumi.export('bucket_name', bucket.id)
pulumi.export('bucket_website', bucket_website_config.website_endpoint)
