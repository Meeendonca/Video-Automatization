$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) { throw 'Execute setup.ps1 primeiro.' }
    & .\.venv\Scripts\python.exe -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cu128
    if ($LASTEXITCODE -ne 0) { throw 'Falha na instalação PyTorch CUDA.' }
    & .\.venv\Scripts\python.exe -m pip install -r requirements-ai.txt
    if ($LASTEXITCODE -ne 0) { throw 'Falha nas dependências de geração.' }
    & .\.venv\Scripts\python.exe -X utf8 ai_images.py
    if ($LASTEXITCODE -ne 0) { throw 'Falha no download do modelo.' }
} finally { Pop-Location }
