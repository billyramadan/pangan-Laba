@echo off
cd /d "%~dp0"
start "pangan-tunnel" "%~dp0cloudflared.exe" tunnel --url http://localhost:8000
