@echo off
cd /d "%~dp0"
set PANGAN_OAUTH_REDIRECT_URI=https://product-motors-divisions-newport.trycloudflare.com/auth/callback
start "pangan-server" "%~dp0.venv\Scripts\python.exe" -m backend.server
