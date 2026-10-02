param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$siteUrl = 'http://127.0.0.1:8010/'
Set-Location -LiteralPath $projectRoot

function Test-LocalSite {
    try {
        $response = Invoke-WebRequest -Uri $siteUrl -UseBasicParsing -TimeoutSec 3
        return ($response.StatusCode -eq 200 -and $response.Content -match 'AssentTag')
    } catch { return $false }
}

if (-not (Test-LocalSite)) {
    $pythonChoices = @((Join-Path $projectRoot '.venv\Scripts\python.exe'), (Join-Path $projectRoot 'venv\Scripts\python.exe'), 'C:\adarsh\python.exe')
    $pythonPath = $pythonChoices | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $pythonPath) { $pythonPath = (Get-Command python -ErrorAction Stop).Source }
    Write-Host 'Checking chat setup...'
    & $pythonPath manage.py prepare_chat
    if ($LASTEXITCODE -ne 0) { throw 'Setup failed. Check that the local MySQL service is running.' }
    $logDirectory = Join-Path $projectRoot 'output'
    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
    $server = Start-Process -FilePath $pythonPath -ArgumentList @('manage.py','run_chat_server','127.0.0.1:8010','--noreload') -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDirectory 'server.stdout.log') -RedirectStandardError (Join-Path $logDirectory 'server.stderr.log') -PassThru
    $server.Id | Set-Content -LiteralPath (Join-Path $logDirectory 'local-server.pid')
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        if (Test-LocalSite) { break }
        $server.Refresh()
        if ($server.HasExited) { throw 'The server stopped. See output/server.stderr.log.' }
        Start-Sleep -Seconds 1
    }
    if (-not (Test-LocalSite)) { throw 'The website is not ready yet. See output/server.stderr.log.' }
}
Write-Host "AssentTag is ready: $siteUrl"
if (-not $NoBrowser) { Start-Process $siteUrl }
