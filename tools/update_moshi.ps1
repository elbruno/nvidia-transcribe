param(
    [string]$RepoUrl = "https://github.com/NVIDIA/personaplex.git"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$destRoot = Join-Path $root "scenario6\third_party"
$dest = Join-Path $destRoot "moshi"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

if (-not (Test-Path $destRoot)) {
    New-Item -ItemType Directory -Path $destRoot | Out-Null
}

if (Test-Path $dest) {
    $backup = Join-Path $destRoot ("moshi_prev_" + $timestamp)
    Move-Item -Path $dest -Destination $backup
    Write-Host "Backed up existing moshi to $backup"
}

$temp = Join-Path $env:TEMP ("personaplex-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $temp | Out-Null
$repo = Join-Path $temp "personaplex"

git clone --depth 1 $RepoUrl $repo
Copy-Item -Recurse -Force (Join-Path $repo "moshi") $dest

$license = Get-ChildItem -Path $repo -Filter "LICENSE*" | Select-Object -First 1
if ($license) {
    Copy-Item -Force $license.FullName (Join-Path $dest $license.Name)
}

$hash = (git -C $repo rev-parse HEAD).Trim()
$hash | Out-File -Encoding ascii (Join-Path $dest "MOSHI_VERSION")

Remove-Item -Recurse -Force $temp

Write-Host "Moshi vendored at $dest"
Write-Host "Version: $hash"
