# Client Demo Flow (10-15 Minutes)

## Objective

Demonstrate that Avigilon Alta media can be exported and retrieved securely from AWS at scale across multiple locations/cameras/time ranges.

## Demo Script

1. Show architecture quickly:
   - Alta API + cloud connector -> Lambda -> S3 + DynamoDB -> Search API/UI.
2. Open S3 and show location buckets (`alta-export-demo-hq-north`, etc.).
3. Open one bucket and show timestamped camera object paths.
4. Run demo command from terminal:
   - `.\demo\run-demo.ps1 ...`
5. Show bootstrap response JSON.
6. Show export response (`altaItems`, `uploaded`, `indexed`).
7. Call search API and show signed URL results.
8. Open one signed URL to prove media playback/image access.
9. Open DynamoDB and show corresponding indexed item.

## Acceptance Criteria to Communicate

- Multi-location bucket strategy is in place.
- Camera + timestamp partitioning is present in object key naming.
- Export is serverless and schedulable.
- Retrieval is filtered by location/camera/time.
- Solution is production-ready baseline with security hardening path.
