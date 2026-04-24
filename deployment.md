# Avigilon Alta to AWS S3 - End-to-End Deployment

This package is designed for a client demo where media (images/videos) is exported from Avigilon Alta into AWS S3, indexed in DynamoDB, and retrieved by search API/UI.

## 1) What This Build Delivers

- Automatic export from Avigilon Alta API + cloud connector to AWS S3.
- Dynamic bucket strategy for multiple locations:
  - one bucket per location (`<bucket-prefix>-<location-id>`),
  - one key path per camera and timestamp.
- Fast lookup using DynamoDB (`location + camera + time range`).
- Retrieval API from Lambda (returns signed URLs).
- Demo script to prove bootstrap + export + retrieval flow.

## 2) Files Included for Client Demo

- `backend/alta_export_worker.py` - export worker Lambda (Alta -> S3 + DynamoDB).
- `backend/bootstrap_location_buckets.py` - creates per-location buckets.
- `backend/lambda_function.py` - search Lambda for querying exported media.
- `backend/template.yaml` - AWS SAM infrastructure template.
- `backend/requirements.txt` - Python dependencies.
- `demo/sample-bootstrap-locations.json` - bucket bootstrap payload.
- `demo/sample-export-window.json` - export time-window payload.
- `demo/run-demo.ps1` - end-to-end demo execution script.
- `SCREENSHOT_STEPS.md` - evidence checklist for customer handoff.

## 3) AWS Services Used

- AWS Lambda
- Amazon S3
- Amazon DynamoDB
- Amazon EventBridge Scheduler
- AWS Systems Manager Parameter Store (for secrets)
- API Gateway (for retrieval endpoint)
- CloudWatch Logs

Optional for production hardening:
- AWS KMS, WAF, CloudTrail, CloudFront

## 4) Prerequisites

- AWS CLI configured with deployment credentials.
- SAM CLI installed.
- Python 3.12 installed.
- Avigilon Alta tenant credentials:
  - API token
  - Cloud connector token
  - Base URL for your Alta API environment

## 5) Store Alta Secrets in Parameter Store

Create encrypted parameters:

```powershell
aws ssm put-parameter --name "/alta/apiToken" --type "SecureString" --value "REPLACE_ME" --overwrite
aws ssm put-parameter --name "/alta/connectorToken" --type "SecureString" --value "REPLACE_ME" --overwrite
```

## 6) Build and Deploy

From repo root:

```powershell
cd backend
python -m pip install -r requirements.txt -t .
sam build -t template.yaml
sam deploy --guided
```

Use these suggested guided deploy values:

- Stack Name: `alta-export-stack`
- AWS Region: your target region
- Parameter `BucketPrefix`: `alta-export-demo`
- Parameter `AltaBaseUrl`: your tenant endpoint (for example `https://api.avigilonalta.com`)
- Parameter `AltaApiTokenParam`: `/alta/apiToken`
- Parameter `AltaConnectorTokenParam`: `/alta/connectorToken`
- Parameter `ScheduleExpression`: `rate(5 minutes)`

## 7) Configure API Gateway for `lambda_function.py`

1. Create HTTP API.
2. Integrate route `POST /search` to `MediaSearchFunction`.
3. Enable CORS for your frontend domain.
4. Deploy stage (example `prod`).

If your architecture uses Cognito, attach JWT authorizer to `POST /search`.

## 8) Run End-to-End Demo

From repo root:

```powershell
.\demo\run-demo.ps1 `
  -BootstrapFunctionName "<stack-output-bootstrap-function-name>" `
  -ExportFunctionName "<stack-output-export-function-name>" `
  -SearchApiUrl "https://<api-id>.execute-api.<region>.amazonaws.com/prod/search"
```

Expected demo proof points:

1. Bucket bootstrap response shows created/existing location buckets.
2. Export response shows Alta records read, uploaded, and indexed.
3. Search response returns item metadata and signed URLs.

## 9) S3 Bucket and Key Naming Convention

- Bucket: `<bucket-prefix>-<location-id-lowercase>`
- Object key:
  - `alta/<camera-id>/<YYYY/MM/DD/HH/MM/SS>/<media-id>.jpg`
  - `alta/<camera-id>/<YYYY/MM/DD/HH/MM/SS>/<media-id>.mp4`

This gives clean partitioning across locations, cameras, and timestamps.

## 10) Client Demo Checklist

- Show Lambda list with 3 functions.
- Show DynamoDB table data for at least one camera query.
- Show location buckets and camera/timestamp folder structure in S3.
- Run `run-demo.ps1` live.
- Capture screenshots with `SCREENSHOT_STEPS.md`.

## 11) Production Notes

- Replace broad IAM permissions in template with account-specific least privilege.
- Move API to private networking if required by policy.
- Add retries and dead-letter queue for export failures.
- Add alarms on Lambda errors and export lag.
