#!/usr/bin/env pwsh
param(
    [Parameter(Position = 0, Mandatory = $true)]
    [ValidateSet("generate", "list", "revoke", "status")]
    [string]$Command,
    
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Rest
)

$GatewayUrl = "http://127.0.0.1:8090"
$AdminToken = "pb_master_token_2026"
$ApiBase = "$GatewayUrl/api/license"

function Invoke-LicenseApi {
    param(
        [string]$Path,
        [ValidateSet("GET", "POST", "PATCH", "DELETE")]
        [string]$Method = "GET",
        [hashtable]$Body
    )
    
    $headers = @{
        "Authorization" = "Bearer $AdminToken"
        "Content-Type"  = "application/json"
    }
    
    $uri = "$ApiBase$Path"
    
    try {
        if ($Body) {
            $bodyJson = $Body | ConvertTo-Json
            $response = Invoke-RestMethod -Uri $uri -Method $Method -Headers $headers -Body $bodyJson
        }
        else {
            $response = Invoke-RestMethod -Uri $uri -Method $Method -Headers $headers
        }
        return $response
    }
    catch {
        Write-Error "API Error: $($_.Exception.Message)"
        exit 1
    }
}

function Invoke-Generate {
    param([string[]]$Rest)
    
    $count = 1
    $duration = 30
    $plan = "VIP"
    
    $i = 0
    while ($i -lt $Rest.Count) {
        switch ($Rest[$i]) {
            "--count" { $count = [int]$Rest[++$i]; break }
            "--duration" { $duration = [int]$Rest[++$i]; break }
            "--plan" { $plan = $Rest[++$i]; break }
            default { Write-Error "Unknown option: $_"; exit 1 }
        }
        $i++
    }
    
    if ($count -gt 100) {
        Write-Error "Cannot generate more than 100 keys at once"
        exit 1
    }
    
    Write-Host "Generating $count license key(s) ($duration days, plan: $plan)..." -ForegroundColor Cyan
    
    $body = @{
        count         = $count
        duration_days = $duration
        plan_name     = $plan
    }
    
    $response = Invoke-LicenseApi -Path "/admin/generate" -Method POST -Body $body
    
    if ($response.code -eq 200) {
        Write-Host "Generated successfully" -ForegroundColor Green
        Write-Host ""
        $response.data.licenses | ForEach-Object {
            Write-Host "License Key: $($_.license_key)" -ForegroundColor Yellow
            Write-Host "  Status: $($_.status)"
            Write-Host "  Plan: $($_.plan_name)"
            Write-Host "  Duration: $($_.duration_days) days"
            Write-Host ""
        }
        Write-Host "Total: $($response.data.licenses.Count) keys" -ForegroundColor Green
    }
    else {
        Write-Error "Generation failed: $($response.message)"
        exit 1
    }
}

function Invoke-List {
    param([string[]]$Rest)
    
    $status = $null
    $page = 1
    $perPage = 20
    
    $i = 0
    while ($i -lt $Rest.Count) {
        switch ($Rest[$i]) {
            "--status" { $status = $Rest[++$i]; break }
            "--page" { $page = [int]$Rest[++$i]; break }
            "--per-page" { $perPage = [int]$Rest[++$i]; break }
            default { Write-Error "Unknown option: $_"; exit 1 }
        }
        $i++
    }
    
    [string]$path = "/admin/list?page=" + $page + [System.Uri]::EscapeDataString("&") + "per_page=" + $perPage
    if ($status) {
        $path = $path + [System.Uri]::EscapeDataString("&") + "status=" + $status
    }
    
    Write-Host "Fetching licenses..." -ForegroundColor Cyan
    
    $response = Invoke-LicenseApi -Path $path -Method GET
    
    if ($response.code -eq 200) {
        Write-Host "Found $($response.data.licenses.Count) license(s)" -ForegroundColor Green
        Write-Host ""
        
        $response.data.licenses | ForEach-Object {
            Write-Host "[$($_.status.ToUpper())] $($_.license_key)" -ForegroundColor Yellow
            Write-Host "  ID: $($_.id)"
            Write-Host "  Plan: $($_.plan_name)"
            Write-Host "  Device: $(if ($_.device_id) { $_.device_id } else { "(unbound)" })"
            Write-Host "  Created: $($_.created)"
            Write-Host ""
        }
    }
    else {
        Write-Error "List failed: $($response.message)"
        exit 1
    }
}

function Invoke-StatusCheck {
    param([string[]]$Rest)
    
    $deviceId = $null
    
    $i = 0
    while ($i -lt $Rest.Count) {
        switch ($Rest[$i]) {
            "--device-id" { $deviceId = $Rest[++$i]; break }
            default { Write-Error "Unknown option: $_"; exit 1 }
        }
        $i++
    }
    
    if (-not $deviceId) {
        Write-Error "Missing --device-id parameter"
        exit 1
    }
    
    Write-Host "Checking device: $deviceId" -ForegroundColor Cyan
    
    $response = Invoke-RestMethod -Uri "$GatewayUrl/api/license/status?device_id=$deviceId" -Method GET
    
    if ($response.code -eq 200) {
        if ($response.data.is_vip) {
            Write-Host "Device is VIP" -ForegroundColor Green
            Write-Host "  License: $($response.data.license_key)"
            Write-Host "  Plan: $($response.data.plan_name)"
        }
        else {
            Write-Host "Device is free tier (no VIP license)" -ForegroundColor Yellow
        }
    }
    else {
        Write-Error "Status check failed: $($response.message)"
        exit 1
    }
}

function Invoke-Revoke {
    param([string[]]$Args)
    Write-Error "Revoke endpoint not yet implemented"
    exit 1
}

switch ($Command) {
    "generate" { Invoke-Generate $Rest; break }
    "list" { Invoke-List $Rest; break }
    "status" { Invoke-StatusCheck $Rest; break }
    "revoke" { Invoke-Revoke $Rest; break }
    default { Write-Error "Unknown command: $Command"; exit 1 }
}
