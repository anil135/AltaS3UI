# Avigilon Alta to AWS S3 Export + Retrieval

This project now includes an end-to-end implementation to:

- export Avigilon Alta images/videos to AWS S3 using Lambda
- create multiple buckets for multiple locations
- organize object keys by camera and timestamp
- index metadata in DynamoDB for fast lookup
- query and retrieve media via Lambda API (signed URLs)
- support client-ready demo execution and screenshots

## Project Structure

- `backend/alta_export_worker.py` - Alta export worker Lambda
- `backend/bootstrap_location_buckets.py` - creates buckets per location
- `backend/lambda_function.py` - search/retrieval Lambda
- `backend/template.yaml` - SAM deployment template
- `frontend/` static web UI
- `demo/` payloads and demo script
- `deployment.md` end-to-end deployment + demo runbook
- `SCREENSHOT_STEPS.md` screenshot checklist for client handoff

## Quick Start

1. Follow `deployment.md`.
2. Deploy stack using `backend/template.yaml`.
3. Run `demo/run-demo.ps1` to validate end-to-end flow.

## Existing UI Placeholders

Before using frontend search, replace placeholders in `frontend/app.js`:

- `REPLACE_WITH_API_DOMAIN`
- `REPLACE_WITH_COGNITO_DOMAIN_PREFIX`
- `REGION`
- `REPLACE_WITH_COGNITO_APP_CLIENT_ID`
- `REPLACE_WITH_UI_DOMAIN`
