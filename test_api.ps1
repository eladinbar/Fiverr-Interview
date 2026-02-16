# URL of the API
$baseUrl = "http://localhost:8000/items"

Write-Host "--- 1. SANITY CHECK (GET ROOT) ---" -ForegroundColor Cyan
Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get

Write-Host "`n--- 2. CREATE ITEM (POST) ---" -ForegroundColor Cyan
$body = @{
    name = "Interview Item"
    description = "Created via PowerShell"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "$baseUrl/" -Method Post -Body $body -ContentType "application/json"
$id = $response.id
Write-Host "Created Item ID: $id" -ForegroundColor Green

Write-Host "`n--- 3. GET ALL ITEMS (GET) ---" -ForegroundColor Cyan
Invoke-RestMethod -Uri "$baseUrl/" -Method Get

Write-Host "`n--- 4. UPDATE ITEM (PUT - FULL UPDATE) ---" -ForegroundColor Cyan
$putBody = @{
    name = "Updated Name"
    description = "Updated Description"
} | ConvertTo-Json
Invoke-RestMethod -Uri "$baseUrl/$id" -Method Put -Body $putBody -ContentType "application/json"

Write-Host "`n--- 5. PARTIAL UPDATE (PATCH) ---" -ForegroundColor Cyan
$patchBody = @{
    description = "Patched Description Only"
} | ConvertTo-Json
Invoke-RestMethod -Uri "$baseUrl/$id" -Method Patch -Body $patchBody -ContentType "application/json"

Write-Host "`n--- 6. VERIFY UPDATE (GET SINGLE) ---" -ForegroundColor Cyan
Invoke-RestMethod -Uri "$baseUrl/$id" -Method Get

Write-Host "`n--- 7. DELETE ITEM (DELETE) ---" -ForegroundColor Cyan
Invoke-RestMethod -Uri "$baseUrl/$id" -Method Delete
Write-Host "Item $id deleted." -ForegroundColor Green

Write-Host "`n--- TEST COMPLETE ---" -ForegroundColor Yellow