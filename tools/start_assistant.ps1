$ErrorActionPreference = 'Stop'
$projectPath = Split-Path -Parent $PSScriptRoot
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) { throw 'Python 3.10 or later is required.' }
$outputPath = Join-Path $projectPath 'output'
New-Item -ItemType Directory -Path $outputPath -Force | Out-Null
$assistantProcess = Start-Process -FilePath $pythonCommand.Source -ArgumentList 'assistant_service.py' -WorkingDirectory $projectPath -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $outputPath 'assistant.log') -RedirectStandardError (Join-Path $outputPath 'assistant-error.log')
$assistantProcess.Id | Set-Content (Join-Path $outputPath 'assistant.pid')
Write-Output 'AssentTag assistant is starting at http://127.0.0.1:8030/login.html'
