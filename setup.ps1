param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
        & $Python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar ambiente Python.' }
    }
    & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar dependências.' }
    New-Item -ItemType Directory -Force models | Out-Null
    & .\.venv\Scripts\python.exe -m piper.download_voices --download-dir models en_US-joe-medium
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao baixar a voz.' }
    & .\.venv\Scripts\python.exe studio.py doctor
    if ($LASTEXITCODE -ne 0) { throw 'Falha na verificação.' }
} finally { Pop-Location }
