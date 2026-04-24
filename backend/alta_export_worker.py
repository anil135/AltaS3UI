import datetime as dt
import json
import os
import re
from typing import Dict, Iterable, List, Optional, Tuple

import boto3
import requests
from botocore.exceptions import ClientError

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
ssm = boto3.client("ssm")

MEDIA_INDEX_TABLE = os.environ["MEDIA_INDEX_TABLE"]
BUCKET_PREFIX = os.environ["BUCKET_PREFIX"]
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
ALTA_BASE_URL = os.environ["ALTA_BASE_URL"]
ALTA_API_TOKEN_PARAM = os.environ["ALTA_API_TOKEN_PARAM"]
ALTA_CONNECTOR_TOKEN_PARAM = os.environ["ALTA_CONNECTOR_TOKEN_PARAM"]
DEFAULT_LOOKBACK_MINUTES = int(os.environ.get("DEFAULT_LOOKBACK_MINUTES", "30"))
REQUEST_TIMEOUT_SECONDS = int(os.environ.get("REQUEST_TIMEOUT_SECONDS", "30"))

table = dynamodb.Table(MEDIA_INDEX_TABLE)


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _response(code: int, body: Dict) -> Dict:
    return {"statusCode": code, "body": json.dumps(body)}


def _safe_bucket_suffix(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9-]", "-", value.lower())
    return re.sub(r"-{2,}", "-", normalized).strip("-")


def _bucket_name_for_location(location_id: str) -> str:
    return f"{BUCKET_PREFIX}-{_safe_bucket_suffix(location_id)}"


def _ensure_bucket(bucket_name: str) -> None:
    try:
        s3.head_bucket(Bucket=bucket_name)
        return
    except ClientError:
        pass

    kwargs = {"Bucket": bucket_name}
    if AWS_REGION != "us-east-1":
        kwargs["CreateBucketConfiguration"] = {"LocationConstraint": AWS_REGION}
    s3.create_bucket(**kwargs)

    # Keep exports encrypted and private by default.
    s3.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration={
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"},
                    "BucketKeyEnabled": True,
                }
            ]
        },
    )

    s3.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )

    s3.put_bucket_tagging(
        Bucket=bucket_name,
        Tagging={"TagSet": [{"Key": "managed-by", "Value": "alta-export-lambda"}]},
    )


def _get_parameter(name: str) -> str:
    value = ssm.get_parameter(Name=name, WithDecryption=True)
    return value["Parameter"]["Value"]


def _get_auth_headers() -> Tuple[Dict[str, str], str]:
    alta_token = _get_parameter(ALTA_API_TOKEN_PARAM)
    connector_token = _get_parameter(ALTA_CONNECTOR_TOKEN_PARAM)
    return {"Authorization": f"Bearer {alta_token}"}, connector_token


def _parse_iso8601(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def _search_media_window(
    headers: Dict[str, str], start_time: dt.datetime, end_time: dt.datetime
) -> Iterable[Dict]:
    # This endpoint shape is an example. Replace path/params with your Alta tenant format.
    url = f"{ALTA_BASE_URL.rstrip('/')}/media/search"
    payload = {
        "startTime": start_time.isoformat().replace("+00:00", "Z"),
        "endTime": end_time.isoformat().replace("+00:00", "Z"),
        "limit": 1000,
    }
    response = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    data = response.json()
    return data.get("items", [])


def _download_binary(url: str, connector_token: str) -> bytes:
    headers = {"Authorization": f"Bearer {connector_token}"}
    response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.content


def _media_key(camera_id: str, capture_time: dt.datetime, media_id: str, media_type: str) -> str:
    ext = "jpg" if media_type == "image" else "mp4"
    return (
        f"alta/{camera_id}/{capture_time:%Y/%m/%d/%H/%M/%S}/"
        f"{media_id}.{ext}"
    )


def _put_index_item(
    location_id: str,
    camera_id: str,
    capture_time: dt.datetime,
    media_type: str,
    object_key: str,
    bucket: str,
) -> None:
    table.put_item(
        Item={
            "pk": f"LOCATION#{location_id}#CAMERA#{camera_id}",
            "sk": int(capture_time.timestamp() * 1000),
            "cameraId": camera_id,
            "locationId": location_id,
            "captureTime": capture_time.isoformat().replace("+00:00", "Z"),
            "mediaType": media_type,
            "objectKey": object_key,
            "bucketName": bucket,
        }
    )


def _normalize_media(raw: Dict) -> Optional[Dict]:
    try:
        return {
            "id": raw["id"],
            "locationId": raw["locationId"],
            "cameraId": raw["cameraId"],
            "captureTime": raw["captureTime"],
            "mediaType": raw["mediaType"],  # image | video
            "downloadUrl": raw["cloudConnectorUrl"],
        }
    except KeyError:
        return None


def _migrate_items(items: List[Dict], connector_token: str) -> Dict[str, int]:
    counters = {"indexed": 0, "uploaded": 0, "skipped": 0, "failed": 0}

    for raw in items:
        media = _normalize_media(raw)
        if not media:
            counters["skipped"] += 1
            continue

        location_id = media["locationId"]
        camera_id = media["cameraId"]
        capture_time = _parse_iso8601(media["captureTime"])
        media_type = media["mediaType"]
        media_id = media["id"]

        bucket = _bucket_name_for_location(location_id)
        object_key = _media_key(camera_id, capture_time, media_id, media_type)

        try:
            _ensure_bucket(bucket)
            payload = _download_binary(media["downloadUrl"], connector_token)
            s3.put_object(
                Bucket=bucket,
                Key=object_key,
                Body=payload,
                ContentType="image/jpeg" if media_type == "image" else "video/mp4",
            )
            counters["uploaded"] += 1
            _put_index_item(location_id, camera_id, capture_time, media_type, object_key, bucket)
            counters["indexed"] += 1
        except Exception:
            counters["failed"] += 1

    return counters


def lambda_handler(event, _context):
    lookback_minutes = int(event.get("lookbackMinutes", DEFAULT_LOOKBACK_MINUTES))
    end_time = _utc_now()
    start_time = end_time - dt.timedelta(minutes=lookback_minutes)

    if "startTimeIso" in event and "endTimeIso" in event:
        start_time = _parse_iso8601(event["startTimeIso"])
        end_time = _parse_iso8601(event["endTimeIso"])

    try:
        headers, connector_token = _get_auth_headers()
        items = list(_search_media_window(headers, start_time, end_time))
        results = _migrate_items(items, connector_token)
        return _response(
            200,
            {
                "windowStart": start_time.isoformat(),
                "windowEnd": end_time.isoformat(),
                "altaItems": len(items),
                **results,
            },
        )
    except requests.HTTPError as exc:
        return _response(502, {"message": "Alta API error", "details": str(exc)})
    except Exception as exc:
        return _response(500, {"message": "Migration failed", "details": str(exc)})
