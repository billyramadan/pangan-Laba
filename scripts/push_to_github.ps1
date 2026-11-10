$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

$top = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) { throw 'Jalankan dari folder proyek Git yang valid.' }

Write-Host 'Masukkan fine-grained GitHub token dengan akses Contents: Read and write hanya untuk repo pangan-Laba.'
$secureToken = Read-Host 'GitHub token (input tersembunyi)' -AsSecureString
$tokenPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
$askPassFile = Join-Path $env:TEMP ('pangan-git-askpass-' + [guid]::NewGuid().ToString('N') + '.cmd')

try {
    $env:GITHUB_USER = 'billyramadan'
    $env:GITHUB_PAT = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($tokenPointer)
    $env:GIT_ASKPASS = $askPassFile
    $env:GIT_TERMINAL_PROMPT = '0'
    $askPassLines = @(
        '@echo off',
        'set "prompt=%~1"',
        'echo %prompt% | findstr /I "Username" >nul',
        'if not errorlevel 1 (',
        '  echo %GITHUB_USER%',
        ') else (',
        '  echo %GITHUB_PAT%',
        ')'
    )
    $askPassLines -join "`r`n" | Set-Content -Encoding ascii $askPassFile

    git push --set-upstream origin main
    if ($LASTEXITCODE -ne 0) { throw 'Push gagal. Periksa izin token dan akses repo lalu coba lagi.' }
    Write-Host 'Push berhasil.'
    git status -sb
    git ls-remote origin refs/heads/main
}
finally {
    Remove-Item -LiteralPath $askPassFile -Force -ErrorAction SilentlyContinue
    Remove-Item Env:GITHUB_PAT -ErrorAction SilentlyContinue
    Remove-Item Env:GITHUB_USER -ErrorAction SilentlyContinue
    Remove-Item Env:GIT_ASKPASS -ErrorAction SilentlyContinue
    Remove-Item Env:GIT_TERMINAL_PROMPT -ErrorAction SilentlyContinue
    if ($tokenPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenPointer)
    }
    $secureToken = $null
}
