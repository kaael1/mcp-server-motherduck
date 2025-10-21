# Upload script for Excel file
$filePath = "estrutura VBEP.XLSX"
$uploadUrl = "https://exciting-nature-production.up.railway.app/upload"
$token = "450c981e114c3073b6cdf07ece0c27982c0a39c267e4339524b40e2a288bfe57"

# Create multipart form data
$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"

# Read file bytes
$fileBytes = [System.IO.File]::ReadAllBytes($filePath)
$fileName = [System.IO.Path]::GetFileName($filePath)

# Build multipart body
$bodyLines = @(
    "--$boundary",
    "Content-Disposition: form-data; name=`"file`"; filename=`"$fileName`"",
    "Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "",
    [System.Text.Encoding]::GetEncoding("iso-8859-1").GetString($fileBytes),
    "--$boundary--",
    ""
) -join $LF

# Set headers
$headers = @{
    'Authorization' = "Bearer $token"
    'Content-Type' = "multipart/form-data; boundary=$boundary"
}

try {
    Write-Host "Uploading file: $fileName"
    $response = Invoke-RestMethod -Uri $uploadUrl -Method POST -Headers $headers -Body $bodyLines
    Write-Host "Upload successful:"
    $response | ConvertTo-Json -Depth 3
} catch {
    Write-Host "Upload error: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response body: $responseBody"
    }
}
