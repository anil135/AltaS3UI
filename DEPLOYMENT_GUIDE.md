# Deployment Instructions (Manual via AWS Console)

This guide sets up a production-ready path for your client without CloudFormation or TypeScript.

## 1) Target Architecture

- Avigilon Alta exports media files to S3
- DynamoDB stores searchable metadata (camera/location/timestamp/objectKey/mediaType)
- API Gateway + Lambda queries DynamoDB and returns CloudFront signed URLs
- Cognito federates Microsoft Entra ID (Azure AD) for SSO
- CloudFront serves:
  - UI static site from S3
  - media from S3 (private origin)
- Route 53 hosts domain for HTTPS endpoints

## 2) DynamoDB Table (Fast Timestamp Retrieval)

Create table:

- Table name: `MediaIndex`
- Partition key: `pk` (String)
- Sort key: `sk` (Number)
- Billing mode: On-demand (recommended initially)

### Item format

Use this model (see `backend/dynamodb-item-example.json`):

- `pk = LOCATION#<locationId>#CAMERA#<cameraId>`
- `sk = <captureTimeEpochMillis>`
- additional attributes:
  - `cameraId`
  - `locationId`
  - `captureTime` (ISO8601)
  - `mediaType` (`image` or `video`)
  - `objectKey` (S3 object key)

This schema supports very fast range queries using time window and camera/location.

## 3) CloudFront for Media Delivery

1. Create CloudFront distribution for media origin:
   - Origin: private S3 bucket with Avigilon Alta objects
   - Enable Origin Access Control (OAC)
   - Restrict bucket to CloudFront only
2. Create Key Group and public key (CloudFront signed URL setup)
3. Associate Key Group with cache behavior as trusted signer
4. Keep media objects private (no public S3 access)

## 4) Lambda API Deployment

## 4.1 Create IAM Role for Lambda

Grant least privilege:

- `dynamodb:Query` on `MediaIndex`
- CloudWatch Logs write permissions

## 4.2 Deploy Lambda

1. Runtime: Python 3.12
2. Create zip package locally:
   - `lambda_function.py`
   - dependencies from `backend/requirements.txt` installed into same folder
3. Upload zip in Lambda Console
4. Set env vars:
   - `MEDIA_INDEX_TABLE=MediaIndex`
   - `CLOUDFRONT_DOMAIN=<media-distribution-domain>`
   - `CLOUDFRONT_KEY_PAIR_ID=<key-pair-id>`
   - `CLOUDFRONT_PRIVATE_KEY_B64=<base64-pem-private-key>`

> Keep private key in AWS Secrets Manager for production. If you do this, update code to read secret at runtime.

## 5) API Gateway (HTTP API)

1. Create HTTP API
2. Add Lambda integration to `POST /search`
3. Enable CORS for frontend domain
4. Add Cognito JWT authorizer (next section)
5. Deploy stage (for example: `prod`)

## 6) Cognito + Microsoft SSO

## 6.1 Create Cognito User Pool

1. Sign-in options: federation via external IdP
2. App client:
   - no client secret for browser app
   - callback URL: `https://<ui-domain>`
   - logout URL: `https://<ui-domain>`
   - allowed OAuth flow: implicit (as used by current frontend)
   - scopes: `openid`, `email`, `profile`

## 6.2 Add Microsoft Entra ID as Identity Provider

In Azure:

- Register app
- configure redirect URI to Cognito hosted UI callback
- capture tenant ID, client ID, client secret

In Cognito:

- add OIDC/SAML provider for Microsoft
- map claims to Cognito attributes:
  - `email` -> `email`
  - group/location claim -> `custom:locations`
  - policy flag -> `custom:cross_location_access`

## 6.3 Configure API Gateway JWT Authorizer

- Issuer: Cognito user pool issuer URL
- Audience: Cognito app client ID
- Attach authorizer to `POST /search`

## 7) Frontend Deployment

1. Update placeholders in `frontend/app.js`
2. Create S3 bucket for UI hosting artifacts
3. Upload `frontend/index.html`, `frontend/styles.css`, `frontend/app.js`
4. Create CloudFront distribution for UI bucket
5. Add ACM certificate (in us-east-1) and custom domain

## 8) Route 53 and HTTPS

Create DNS records:

- `portal.yourcompany.com` -> Alias to UI CloudFront distribution
- optionally `api.yourcompany.com` -> API custom domain mapping

All endpoints should be HTTPS-only.

## 9) Location Access Control Behavior

The Lambda enforces:

- if `custom:cross_location_access = true`: user can request any location
- else user can only request locations in `custom:locations` (comma-separated)

Examples:

- User A: `custom:locations = HQ-North,HQ-East`, `custom:cross_location_access = false`
- User B: `custom:cross_location_access = true` (global access)

## 10) Avigilon Alta Import Integration

Whichever process writes to S3 must also write one metadata item per object to DynamoDB using the above schema.

Minimum metadata fields:

- location
- camera
- capture timestamp
- media type
- object key

## 11) Validation Checklist

- Sign in with Microsoft account succeeds
- User without cross-location role gets 403 for unauthorized location
- Query by camera/location/day/hour/time range returns expected images/videos
- Media link opens through CloudFront URL (not direct S3 URL)
- UI and API are both HTTPS

## 12) Optional Hardening

- Replace implicit flow with authorization code + PKCE
- Store signing private key in Secrets Manager and cache in Lambda
- Use WAF on CloudFront and API
- Add CloudTrail + CloudWatch alarms for unusual access
