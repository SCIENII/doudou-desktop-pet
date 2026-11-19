param([int]$TimeoutSeconds = 30)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$zip = Join-Path $root 'release/doudou-pet-v0.1.0-windows-x64.zip'
$checkDir = Join-Path $root ('build/portable-check-' + [guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $checkDir
$unpacked = Join-Path $checkDir 'unpacked'
Expand-Archive -LiteralPath $zip -DestinationPath $unpacked
$pet = Join-Path $unpacked 'DoudouPet'
$exe = Join-Path $pet 'DoudouPet.exe'
$report = Join-Path $checkDir 'smoke.json'
if (!(Test-Path (Join-Path $pet '_internal') -PathType Container)) { throw 'Runtime directory is missing' }
$process = Start-Process -FilePath $exe -ArgumentList @('--smoke-test', '--smoke-output', ('"{0}"' -f $report)) -WorkingDirectory $checkDir -PassThru
if (!$process.WaitForExit($TimeoutSeconds * 1000)) {
    $process.Kill()
    throw 'Portable smoke test timed out'
}
if (!(Test-Path -LiteralPath $report -PathType Leaf)) { throw "Portable smoke test did not report; exit code $($process.ExitCode)" }
$result = [System.IO.File]::ReadAllText($report) | ConvertFrom-Json
if ($process.ExitCode -ne 0 -or !$result.ok -or !$result.window_visible -or $result.skin_count -ne 4 -or (Compare-Object @('chef', 'classic', 'doctor', 'programmer') @($result.skin_ids))) {
    throw "Portable smoke test failed: $($result | ConvertTo-Json -Compress)"
}
$result | ConvertTo-Json -Compress
Get-FileHash -LiteralPath $zip -Algorithm SHA256
"Report: $report"
