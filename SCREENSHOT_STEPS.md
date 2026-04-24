# Screenshot Steps (Client-Ready)

Use this guide to capture consistent, professional screenshots for:

- UI
- Amazon Cognito
- API Gateway
- CloudFront
- Route 53

## 1) Before You Start

1. Sign in to AWS Console with an account that can view all required services.
2. In top-right AWS region selector, choose the region used by your deployment.
3. In browser:
   - zoom to 100%
   - maximize window
   - disable dark mode extensions (if any)
4. Prepare a folder named `client-screenshots`.
5. Use this filename pattern for every screenshot:
   - `01-ui-login.png`
   - `02-ui-search-filters.png`
   - `03-ui-results-video-image.png`
   - `04-cognito-user-pool-overview.png`
   - `05-cognito-sso-provider-mapping.png`
   - `06-api-gateway-routes-authorizer.png`
   - `07-api-gateway-domain-cors-stage.png`
   - `08-cloudfront-ui-distribution.png`
   - `09-cloudfront-media-signed-url-behavior.png`
   - `10-route53-records.png`

## 2) UI Screenshots

## 2.1 Login/Entry Screen

1. Open your UI domain in browser (for example `https://portal.yourcompany.com`).
2. If currently logged in, click `Sign out`.
3. Confirm page shows search panel and `Sign in (Microsoft SSO)` button.
4. Capture full browser viewport.
5. Save as: `01-ui-login.png`.

## 2.2 Search Filters Filled

1. Click `Sign in (Microsoft SSO)` and complete login.
2. In search form, enter:
   - Camera: `CAM-101`
   - Location: `HQ-North`
   - Date: any valid date with data
   - Start Time: `10:00`
   - End Time: `11:00`
   - Media Type: `All`
3. Do not click search yet.
4. Capture full browser viewport including header and filters.
5. Save as: `02-ui-search-filters.png`.

## 2.3 Search Results (Video + Image)

1. Click `Search`.
2. Wait until status text shows found item count.
3. Ensure at least one video and one image card are visible (if possible).
4. Capture results section with metadata (camera/location/timestamp/object key).
5. Save as: `03-ui-results-video-image.png`.

## 3) Cognito Screenshots

## 3.1 User Pool Overview

1. In AWS Console search bar, type `Cognito` and open `Amazon Cognito`.
2. Click `User pools`.
3. Click your user pool used by UI login.
4. Confirm overview page shows:
   - Pool name
   - Hosted UI domain
   - App clients summary
5. Capture the full central panel.
6. Save as: `04-cognito-user-pool-overview.png`.

## 3.2 Microsoft SSO Provider + Attribute Mapping

1. Inside same user pool, in left navigation click `Sign-in experience`.
2. Scroll to `Federated identity provider sign-in`.
3. Click Microsoft provider (OIDC/SAML, whichever configured).
4. Capture provider details page (issuer/client id endpoints as visible).
5. Save as: `05-cognito-sso-provider-mapping.png`.

If attribute mapping is on a separate page:

1. Open `Attribute mapping` section.
2. Ensure mapping for `email`, `custom:locations`, `custom:cross_location_access` is visible.
3. Replace previous screenshot or capture second variant with same filename if it better proves setup.

## 4) API Gateway Screenshots

## 4.1 Routes + Authorizer

1. In AWS Console, open `API Gateway`.
2. Select your HTTP API.
3. Click `Routes`.
4. Click `POST /search`.
5. Ensure integration target Lambda is visible.
6. Open attached authorizer details and ensure Cognito JWT authorizer is visible.
7. Capture route and authorizer in one frame if possible.
8. Save as: `06-api-gateway-routes-authorizer.png`.

## 4.2 Domain/CORS/Stage

1. In same API, click `CORS`.
2. Ensure allowed origin includes your UI domain.
3. Click `Stages` and open deployed stage (`prod` or your stage).
4. If custom domain mapping exists, open `Custom domain names` and select API domain.
5. Capture CORS + stage (or domain mapping) evidence.
6. Save as: `07-api-gateway-domain-cors-stage.png`.

## 5) CloudFront Screenshots

## 5.1 UI Distribution

1. Open `CloudFront` from AWS Console.
2. Click `Distributions`.
3. Select UI distribution (origin should point to UI S3 bucket).
4. In `General` tab, ensure these are visible:
   - Distribution domain name
   - Alternate domain name (CNAME) for portal
   - SSL certificate
   - Status: Enabled/Deployed
5. Capture this section.
6. Save as: `08-cloudfront-ui-distribution.png`.

## 5.2 Media Distribution + Trusted Signers

1. Back in `Distributions`, select media distribution (origin points to media S3 bucket).
2. Open `Behaviors` tab.
3. Click default behavior (or media behavior).
4. Ensure trusted key groups/signed URL behavior is visible.
5. Optionally open `Origins` tab to show OAC/private bucket usage.
6. Capture behavior settings proving signed URL protection.
7. Save as: `09-cloudfront-media-signed-url-behavior.png`.

## 6) Route 53 Screenshot

1. Open `Route 53`.
2. Click `Hosted zones`.
3. Click your organization domain hosted zone.
4. Ensure records for UI and API endpoints are visible (Alias to CloudFront/API domain).
5. Capture records list with:
   - record name
   - type (A/AAAA/CNAME as used)
   - value/alias target
6. Save as: `10-route53-records.png`.

## 7) Optional Security Redaction (Before Sharing)

Before sending to clients, review screenshots and blur/mask:

- account ID (if internal policy requires)
- client secret values
- private keys
- internal-only hostnames
- user email addresses (if needed)

Do not blur:

- domain names intended for client usage
- architecture evidence (service names/settings needed for sign-off)

## 8) Final Packaging for Client

1. Put all images in `client-screenshots` folder.
2. Verify filenames are in order `01` to `10`.
3. Create a zip:
   - `client-screenshots.zip`
4. Attach zip with:
   - `README.md`
   - `DEPLOYMENT_GUIDE.md`
   - this file `SCREENSHOT_STEPS.md`

This package gives the client deployment instructions plus visual proof of setup.
