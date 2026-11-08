$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path (Join-Path $PSScriptRoot ".."))
& .\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8502 --server.address 127.0.0.1
