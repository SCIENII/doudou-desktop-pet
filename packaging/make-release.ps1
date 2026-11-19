param(
    [string]$Python = 'python',
    [switch]$PackageOnly
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $root
try {
    $Python = (Get-Command $Python -CommandType Application).Source
    if (!$PackageOnly) {
        & $Python -m pytest -q
        if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
        $oldPath = $env:Path
        try {
            $env:Path = "$env:SystemRoot\System32;$env:SystemRoot;$(Split-Path $Python)"
            & $Python -I -m PyInstaller --noconfirm --clean --distpath build/public-dist --workpath build/public-work packaging/doudou-pet.spec
            if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed' }
        } finally { $env:Path = $oldPath }
    }
    $dist = (Resolve-Path 'build/public-dist/DoudouPet').Path
    foreach ($doc in @('README.md', 'LICENSE', 'ASSET-LICENSE.md', 'THIRD-PARTY-NOTICES.md')) {
        Copy-Item -LiteralPath (Join-Path $root $doc) -Destination $dist
    }
    $license = New-Item -ItemType Directory -Force (Join-Path $dist 'third-party-licenses')
    $pythonLicense = & $Python -I -c "import sys; from pathlib import Path; print(Path(sys.base_prefix) / 'LICENSE.txt')"
    if ($LASTEXITCODE -ne 0) { throw 'Could not locate Python license' }
    Copy-Item -LiteralPath $pythonLicense -Destination (Join-Path $license.FullName 'CPython-LICENSE.txt')
    $licenseUrls = @{
        'GPL-3.0.txt' = 'https://raw.githubusercontent.com/qt/qtbase/v6.12.0/LICENSES/GPL-3.0-only.txt'
        'LGPL-3.0.txt' = 'https://raw.githubusercontent.com/qt/qtbase/v6.12.0/LICENSES/LGPL-3.0-only.txt'
        'PyInstaller-COPYING.txt' = 'https://raw.githubusercontent.com/pyinstaller/pyinstaller/v6.21.0/COPYING.txt'
    }
    foreach ($name in $licenseUrls.Keys) {
        Invoke-WebRequest -Uri $licenseUrls[$name] -OutFile (Join-Path $license.FullName $name) -TimeoutSec 60
    }
    $out = New-Item -ItemType Directory -Force (Join-Path $root 'release')
    $portable = Join-Path $out.FullName 'doudou-pet-v0.1.0-windows-x64.zip'
    Compress-Archive -LiteralPath $dist -DestinationPath $portable -Force
    Get-FileHash -LiteralPath $portable -Algorithm SHA256 | ForEach-Object {
        '{0}  {1}' -f $_.Hash.ToLowerInvariant(), (Split-Path -Leaf $_.Path)
    } | Set-Content -LiteralPath (Join-Path $out.FullName 'SHA256SUMS.txt') -Encoding ascii
} finally { Pop-Location }
