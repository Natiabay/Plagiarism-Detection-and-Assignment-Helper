# Comprehensive Docker API Fix Script
Write-Host "=== Docker API Issue Diagnostic and Fix ===" -ForegroundColor Green
Write-Host ""

# Step 1: Check Docker Desktop Status
Write-Host "Step 1: Checking Docker Desktop processes..." -ForegroundColor Cyan
$dockerProcesses = Get-Process | Where-Object {$_.ProcessName -like "*Docker*"}
if ($dockerProcesses) {
    Write-Host "  [OK] Docker Desktop processes are running" -ForegroundColor Green
    $dockerProcesses | Select-Object ProcessName, Id | Format-Table
} else {
    Write-Host "  [ERROR] Docker Desktop is not running" -ForegroundColor Red
    Write-Host "  Starting Docker Desktop..." -ForegroundColor Yellow
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    Write-Host "  Waiting 60 seconds for Docker Desktop to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 60
}

# Step 2: Try to restart Docker service
Write-Host "`nStep 2: Attempting to restart Docker service..." -ForegroundColor Cyan
try {
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if ($isAdmin) {
        Write-Host "  Restarting Docker service..." -ForegroundColor Yellow
        net stop com.docker.service 2>&1 | Out-Null
        Start-Sleep -Seconds 5
        net start com.docker.service 2>&1 | Out-Null
        Write-Host "  [OK] Docker service restarted" -ForegroundColor Green
    } else {
        Write-Host "  [SKIP] Need admin privileges to restart service" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [SKIP] Could not restart service (may need admin)" -ForegroundColor Yellow
}

# Step 3: Wait for Docker API to be ready
Write-Host "`nStep 3: Waiting for Docker API to be ready (30 seconds)..." -ForegroundColor Cyan
Start-Sleep -Seconds 30

# Step 4: Test Docker connection with retry
Write-Host "`nStep 4: Testing Docker connection..." -ForegroundColor Cyan
$maxRetries = 5
$retryCount = 0
$connected = $false

while ($retryCount -lt $maxRetries -and -not $connected) {
    $retryCount++
    Write-Host "  Attempt $retryCount of $maxRetries..." -ForegroundColor Gray
    
    try {
        $testResult = docker version --format "{{.Server.Version}}" 2>&1
        if ($LASTEXITCODE -eq 0 -and $testResult -notmatch "error|Error|ERROR") {
            Write-Host "  [OK] Docker API is responding! Version: $testResult" -ForegroundColor Green
            $connected = $true
        } else {
            Write-Host "  [RETRY] Docker API not ready yet..." -ForegroundColor Yellow
            Start-Sleep -Seconds 10
        }
    } catch {
        Write-Host "  [RETRY] Connection attempt failed..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
    }
}

if (-not $connected) {
    Write-Host "`n  [ERROR] Docker API is not responding after $maxRetries attempts" -ForegroundColor Red
    Write-Host "`n  Possible solutions:" -ForegroundColor Yellow
    Write-Host "  1. Restart Docker Desktop manually:" -ForegroundColor White
    Write-Host "     - Right-click Docker icon in system tray" -ForegroundColor Gray
    Write-Host "     - Select 'Quit Docker Desktop'" -ForegroundColor Gray
    Write-Host "     - Wait 10 seconds" -ForegroundColor Gray
    Write-Host "     - Start Docker Desktop again" -ForegroundColor Gray
    Write-Host "`n  2. Reset Docker to factory defaults:" -ForegroundColor White
    Write-Host "     - Open Docker Desktop" -ForegroundColor Gray
    Write-Host "     - Settings > Troubleshoot > Reset to factory defaults" -ForegroundColor Gray
    Write-Host "`n  3. Check WSL 2 configuration:" -ForegroundColor White
    Write-Host "     - Run: wsl --update" -ForegroundColor Gray
    Write-Host "     - Restart computer" -ForegroundColor Gray
    exit 1
}

# Step 5: Navigate to project directory
Write-Host "`nStep 5: Navigating to project directory..." -ForegroundColor Cyan
$projectPath = "C:\Users\HP\Desktop\Academic Assignment Helper and plagiarism detector(RAG )"
if (Test-Path $projectPath) {
    Set-Location $projectPath
    Write-Host "  [OK] In project directory" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Project directory not found" -ForegroundColor Red
    exit 1
}

# Step 6: Stop any existing containers
Write-Host "`nStep 6: Stopping existing containers..." -ForegroundColor Cyan
docker-compose down 2>&1 | Out-Null
Write-Host "  [OK] Existing containers stopped" -ForegroundColor Green

# Step 7: Start services
Write-Host "`nStep 7: Starting Docker Compose services..." -ForegroundColor Cyan
$composeOutput = docker-compose up -d 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Services started successfully" -ForegroundColor Green
    Write-Host $composeOutput -ForegroundColor Gray
} else {
    Write-Host "  [ERROR] Failed to start services" -ForegroundColor Red
    Write-Host $composeOutput -ForegroundColor Red
    exit 1
}

# Step 8: Wait for services to be ready
Write-Host "`nStep 8: Waiting for services to initialize (45 seconds)..." -ForegroundColor Cyan
Start-Sleep -Seconds 45

# Step 9: Verify containers are running
Write-Host "`nStep 9: Verifying containers are running..." -ForegroundColor Cyan
$containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host $containers
    Write-Host "`n  [OK] Containers are running!" -ForegroundColor Green
} else {
    Write-Host "  [WARNING] Could not list containers" -ForegroundColor Yellow
    Write-Host $containers -ForegroundColor Red
}

# Step 10: Test PostgreSQL connection
Write-Host "`nStep 10: Testing PostgreSQL connection..." -ForegroundColor Cyan
Start-Sleep -Seconds 10
try {
    $dbTest = docker exec academic_postgres psql -U student -d academic_helper -c "SELECT 'Connection OK' as status;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Database connection successful!" -ForegroundColor Green
        Write-Host $dbTest -ForegroundColor Gray
    } else {
        Write-Host "  [WARNING] Database may still be initializing" -ForegroundColor Yellow
        Write-Host "  Wait a bit longer and try: docker exec academic_postgres psql -U student -d academic_helper -c 'SELECT 1;'" -ForegroundColor Gray
    }
} catch {
    Write-Host "  [WARNING] Could not test database (container may still be starting)" -ForegroundColor Yellow
}

# Summary
Write-Host "`n=== Summary ===" -ForegroundColor Green
Write-Host "Docker services should now be running!" -ForegroundColor Cyan
Write-Host "`nAccess services at:" -ForegroundColor Yellow
Write-Host "  - FastAPI: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - n8n: http://localhost:5678" -ForegroundColor White
Write-Host "  - pgAdmin: http://localhost:5050" -ForegroundColor White
Write-Host "`nNext step: Configure n8n PostgreSQL credentials!" -ForegroundColor Green

