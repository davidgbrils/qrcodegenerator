$ErrorActionPreference = "Stop"

$appName = "QRCodeGenerator"
$publisher = "QRCodeGenerator"
$sourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$installDir = Join-Path $env:LOCALAPPDATA "Programs\$appName"
$startMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\$appName"
$desktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "$appName.lnk"
$startMenuShortcut = Join-Path $startMenuDir "$appName.lnk"
$exePath = Join-Path $installDir "$appName.exe"

New-Item -ItemType Directory -Force -Path $installDir | Out-Null
New-Item -ItemType Directory -Force -Path $startMenuDir | Out-Null

Copy-Item -Force -Path (Join-Path $sourceDir "$appName.exe") -Destination $exePath

foreach ($fileName in @("telegram_config.ini", "url_history.txt")) {
    $sourceFile = Join-Path $sourceDir $fileName
    $targetFile = Join-Path $installDir $fileName
    if ((Test-Path $sourceFile) -and -not (Test-Path $targetFile)) {
        Copy-Item -Force -Path $sourceFile -Destination $targetFile
    }
}

$uninstallScript = @"
`$ErrorActionPreference = "Stop"
`$appName = "$appName"
`$installDir = Join-Path `$env:LOCALAPPDATA "Programs\`$appName"
`$startMenuDir = Join-Path `$env:APPDATA "Microsoft\Windows\Start Menu\Programs\`$appName"
`$desktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "`$appName.lnk"
if (Test-Path `$desktopShortcut) { Remove-Item -Force `$desktopShortcut }
if (Test-Path `$startMenuDir) { Remove-Item -Recurse -Force `$startMenuDir }
if (Test-Path `$installDir) { Remove-Item -Recurse -Force `$installDir }
"@
$uninstallPath = Join-Path $installDir "uninstall.ps1"
Set-Content -Path $uninstallPath -Value $uninstallScript -Encoding UTF8

$shell = New-Object -ComObject WScript.Shell
foreach ($shortcutPath in @($desktopShortcut, $startMenuShortcut)) {
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $exePath
    $shortcut.WorkingDirectory = $installDir
    $shortcut.IconLocation = $exePath
    $shortcut.Description = "QR Code Generator"
    $shortcut.Save()
}

$uninstallRegPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$appName"
New-Item -Force -Path $uninstallRegPath | Out-Null
Set-ItemProperty -Path $uninstallRegPath -Name DisplayName -Value "QR Code Generator"
Set-ItemProperty -Path $uninstallRegPath -Name DisplayVersion -Value "1.0.0"
Set-ItemProperty -Path $uninstallRegPath -Name Publisher -Value $publisher
Set-ItemProperty -Path $uninstallRegPath -Name InstallLocation -Value $installDir
Set-ItemProperty -Path $uninstallRegPath -Name DisplayIcon -Value $exePath
Set-ItemProperty -Path $uninstallRegPath -Name UninstallString -Value "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$uninstallPath`""
Set-ItemProperty -Path $uninstallRegPath -Name NoModify -Type DWord -Value 1
Set-ItemProperty -Path $uninstallRegPath -Name NoRepair -Type DWord -Value 1

Start-Process -FilePath $exePath
