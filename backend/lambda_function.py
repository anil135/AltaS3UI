import base64
import datetime as dt
import json
import os
from typing import Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Key
from botocore.signers import CloudFrontSigner
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
TABLE_NAME = os.environ["MEDIA_INDEX_TABLE"]
CLOUDFRONT_DOMAIN = os.environ.get("CLOUDFRONT_DOMAIN")
CLOUDFRONT_KEY_PAIR_ID = os.environ.get("CLOUDFRONT_KEY_PAIR_ID")
CLOUDFRONT_PRIVATE_KEY_B64 = os.environ.get("CLOUDFRONT_PRIVATE_KEY_B64")
SIGNED_URL_TTL_SECONDS = int(os.environ.get("SIGNED_URL_TTL_SECONDS", "900"))

table = dynamodb.Table(TABLE_NAME)


def _response(code: int, body: Dict):
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
        },
        "body": json.dumps(body),
    }


def _parse_claims(event: Dict) -> Dict:
    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
    )
    return claims


def _private_key_signer(message: bytes) -> bytes:
    private_key_pem = base64.b64decode(CLOUDFRONT_PRIVATE_KEY_B64)
    private_key = serialization.load_pem_private_key(private_key_pem, password=None)
    return private_key.sign(message, padding.PKCS1v15(), hashes.SHA1())


def _cloudfront_url(object_key: str) -> str:
    signer = CloudFrontSigner(CLOUDFRONT_KEY_PAIR_ID, _private_key_signer)
    base_url = f"https://{CLOUDFRONT_DOMAIN}/{object_key}"
    expires_at = dt.datetime.utcnow() + dt.timedelta(seconds=SIGNED_URL_TTL_SECONDS)
    return signer.generate_presigned_url(base_url, date_less_than=expires_at)


def _s3_url(bucket_name: str, object_key: str) -> str:
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": object_key},
        ExpiresIn=SIGNED_URL_TTL_SECONDS,
    )


def _signed_media_url(bucket_name: Optional[str], object_key: str) -> str:
    if CLOUDFRONT_DOMAIN and CLOUDFRONT_KEY_PAIR_ID and CLOUDFRONT_PRIVATE_KEY_B64:
        return _cloudfront_url(object_key)
    if not bucket_name:
        raise ValueError("bucketName is required when CloudFront is not configured")
    return _s3_url(bucket_name, object_key)


def _parse_iso8601(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def _is_allowed_location(claims: Dict, requested_location: str) -> bool:
    cross_location = claims.get("custom:cross_location_access", "false").lower() == "true"
    if cross_location:
        return True
    locations = claims.get("custom:locations", "")
    allowed = [x.strip() for x in locations.split(",") if x.strip()]
    return requested_location in allowed


def _query_media(
    camera_id: str,
    location_id: str,
    start_time: dt.datetime,
    end_time: dt.datetime,
    media_type: Optional[str],
) -> List[Dict]:
    pk = f"LOCATION#{location_id}#CAMERA#{camera_id}"
    start_epoch = int(start_time.timestamp() * 1000)
    end_epoch = int(end_time.timestamp() * 1000)
    key_expr = Key("pk").eq(pk) & Key("sk").between(start_epoch, end_epoch)

    query_result = table.query(KeyConditionExpression=key_expr, Limit=1000)
    items = query_result.get("Items", [])
    while "LastEvaluatedKey" in query_result:
        query_result = table.query(
            KeyConditionExpression=key_expr,
            ExclusiveStartKey=query_result["LastEvaluatedKey"],
            Limit=1000,
        )
        items.extend(query_result.get("Items", []))

    if media_type and media_type != "all":
        items = [item for item in items if item.get("mediaType") == media_type]

    results = []
    for item in items:
        object_key = item["objectKey"]
        bucket_name = item.get("bucketName")
        results.append(
            {
                "cameraId": item["cameraId"],
                "locationId": item["locationId"],
                "captureTime": item["captureTime"],
                "mediaType": item["mediaType"],
                "objectKey": object_key,
                "bucketName": bucket_name,
                "url": _signed_media_url(bucket_name, object_key),
            }
        )
    return results


def lambda_handler(event, _context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return _response(200, {"ok": True})

    claims = _parse_claims(event)
    if not claims:
        return _response(401, {"message": "Unauthorized"})

    try:
        payload = json.loads(event.get("body") or "{}")
        camera_id = payload["cameraId"]
        location_id = payload["locationId"]
        start_time = _parse_iso8601(payload["startTimeIso"])
        end_time = _parse_iso8601(payload["endTimeIso"])
        media_type = payload.get("mediaType", "all")
    except Exception:
        return _response(400, {"message": "Invalid request payload"})

    if end_time <= start_time:
        return _response(400, {"message": "endTimeIso must be greater than startTimeIso"})

    if not _is_allowed_location(claims, location_id):
        return _response(403, {"message": "User is not allowed to access this location"})

    items = _query_media(camera_id, location_id, start_time, end_time, media_type)
    return _response(200, {"count": len(items), "items": items})
