$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$releaseRoot = Join-Path $root "release"
$packageName = "Foto-Studio-2.5"
$packageDir = Join-Path $releaseRoot $packageName
$zipPath = Join-Path $releaseRoot "$packageName.zip"

if (Test-Path $packageDir) {
    Remove-Item -LiteralPath $packageDir -Recurse -Force
}
New-Item -ItemType Directory -Path $packageDir | Out-Null

$windowsDir = Join-Path $packageDir "WINDOWS"
$macosDir = Join-Path $packageDir "MACOS"
$iconsDir = Join-Path $packageDir "IKONY"

New-Item -ItemType Directory -Path $windowsDir | Out-Null
New-Item -ItemType Directory -Path $macosDir | Out-Null
New-Item -ItemType Directory -Path $iconsDir | Out-Null

Copy-Item -LiteralPath (Join-Path $root "release-assets\README-URUCHOMIENIE.txt") -Destination $packageDir
Copy-Item -Path (Join-Path $root "icons\*") -Destination $iconsDir

Copy-Item -LiteralPath (Join-Path $root "dist\Foto-Studio") -Destination (Join-Path $windowsDir "Foto-Studio") -Recurse
Copy-Item -LiteralPath (Join-Path $root "release-assets\windows\Uruchom-Foto-Studio.bat") -Destination $windowsDir
Copy-Item -LiteralPath (Join-Path $root "release-assets\windows\Instaluj-Foto-Studio-Windows.bat") -Destination $windowsDir
Copy-Item -LiteralPath (Join-Path $root "release-assets\windows\Utworz-skrot-na-pulpicie-Windows.bat") -Destination $windowsDir
Copy-Item -LiteralPath (Join-Path $root "release-assets\windows\Utworz-skrot-na-pulpicie-Windows.ps1") -Destination $windowsDir
Copy-Item -LiteralPath (Join-Path $root "icons") -Destination (Join-Path $windowsDir "IKONY") -Recurse

$macFiles = @(
    "app.py",
    "index.html",
    "manifest.json",
    "sw.js",
    "requirements.txt",
    "LICENSE.txt",
    "README-Instrukcja.txt"
)
foreach ($file in $macFiles) {
    Copy-Item -LiteralPath (Join-Path $root $file) -Destination $macosDir
}
Copy-Item -LiteralPath (Join-Path $root "icons") -Destination (Join-Path $macosDir "icons") -Recurse
Copy-Item -LiteralPath (Join-Path $root "release-assets\macos\install-macos.sh") -Destination $macosDir
Copy-Item -LiteralPath (Join-Path $root "release-assets\macos\Instaluj-Foto-Studio-macOS.command") -Destination $macosDir
Copy-Item -LiteralPath (Join-Path $root "release-assets\macos\Uruchom-Foto-Studio.command") -Destination $macosDir
Copy-Item -LiteralPath (Join-Path $root "release-assets\macos\Utworz-skrot-na-pulpicie-macOS.command") -Destination $macosDir

if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}
Compress-Archive -LiteralPath $packageDir -DestinationPath $zipPath -CompressionLevel Optimal

Write-Host "Gotowe: $zipPath"
