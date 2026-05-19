$ErrorActionPreference = "Stop"

$base = Split-Path -Parent $MyInvocation.MyCommand.Path
$exe = Join-Path $base "Foto-Studio\Foto-Studio.exe"
$icon = Join-Path $base "IKONY\icon-512.ico"

if (-not (Test-Path $exe)) {
    throw "Nie znaleziono aplikacji: $exe"
}

if (-not (Test-Path $icon)) {
    $icon = $exe
}

$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Foto-Studio.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $exe
$shortcut.WorkingDirectory = Split-Path -Parent $exe
$shortcut.IconLocation = $icon
$shortcut.Description = "Foto-Studio 2.5 - Marek Zettel"
$shortcut.Save()

Write-Host "Utworzono skrot: $shortcutPath"
