param(
  [Parameter(Mandatory = $true)][string]$BootstrapFunctionName,
  [Parameter(Mandatory = $true)][string]$ExportFunctionName,
  [Parameter(Mandatory = $true)][string]$SearchApiUrl
)

Write-Host "1) Bootstrap location buckets..."
aws lambda invoke `
  --function-name $BootstrapFunctionName `
  --payload fileb://demo/sample-bootstrap-locations.json `
  demo/bootstrap-response.json | Out-Null
Get-Content demo/bootstrap-response.json

Write-Host "2) Run Alta export for fixed time window..."
aws lambda invoke `
  --function-name $ExportFunctionName `
  --payload fileb://demo/sample-export-window.json `
  demo/export-response.json | Out-Null
Get-Content demo/export-response.json

Write-Host "3) Query API search endpoint..."
$searchBody = @{
  cameraId     = "CAM-101"
  locationId   = "HQ-North"
  startTimeIso = "2026-04-24T09:00:00Z"
  endTimeIso   = "2026-04-24T09:30:00Z"
  mediaType    = "all"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri $SearchApiUrl -Body $searchBody -ContentType "application/json"
