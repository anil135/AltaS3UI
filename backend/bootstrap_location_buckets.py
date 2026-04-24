import json
import os
import re
from typing import Dict, List

import boto3
from botocore.exceptions import ClientError

s3 = boto3.client("s3")

BUCKET_PREFIX = os.environ["BUCKET_PREFIX"]
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


def _safe_bucket_suffix(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9-]", "-", value.lower())
    return re.sub(r"-{2,}", "-", normalized).strip("-")


def _bucket_name_for_location(location_id: str) -> str:
    return f"{BUCKET_PREFIX}-{_safe_bucket_suffix(location_id)}"


def _create_if_missing(bucket_name: str) -> bool:
    try:
        s3.head_bucket(Bucket=bucket_name)
        return False
    except ClientError:
        kwargs = {"Bucket": bucket_name}
        if AWS_REGION != "us-east-1":
            kwargs["CreateBucketConfiguration"] = {"LocationConstraint": AWS_REGION}
        s3.create_bucket(**kwargs)
        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        )
        return True


def _response(code: int, body: Dict):
    return {"statusCode": code, "body": json.dumps(body)}


def lambda_handler(event, _context):
    locations: List[str] = event.get("locations", [])
    if not locations:
        return _response(400, {"message": "Pass locations array in request body"})

    created = []
    existing = []
    for location_id in locations:
        bucket_name = _bucket_name_for_location(location_id)
        was_created = _create_if_missing(bucket_name)
        if was_created:
            created.append(bucket_name)
        else:
            existing.append(bucket_name)

    return _response(
        200,
        {
            "totalLocations": len(locations),
            "createdBuckets": created,
            "existingBuckets": existing,
        },
    )
