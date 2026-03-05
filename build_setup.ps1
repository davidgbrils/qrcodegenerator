$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$distDir = Join-Path $root "dist"
$installerDir = Join-Path $root "build\setup_builder"
$setupOutput = Join-Path $distDir "QRCodeGeneratorSetup.exe"
$sourcePath = Join-Path $installerDir "QRCodeGeneratorSetup.cs"
$csc = Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"

if (-not (Test-Path $csc)) {
    $csc = Join-Path $env:WINDIR "Microsoft.NET\Framework\v4.0.30319\csc.exe"
}

$requiredFiles = @(
    (Join-Path $distDir "QRCodeGenerator.exe"),
    (Join-Path $root "installer\install.ps1")
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        throw "File tidak ditemukan: $file"
    }
}

if (-not (Test-Path $csc)) {
    throw "Compiler C# bawaan Windows tidak ditemukan."
}

New-Item -ItemType Directory -Force -Path $installerDir | Out-Null
New-Item -ItemType Directory -Force -Path $distDir | Out-Null

$emptyConfig = Join-Path $installerDir "telegram_config.ini"
$emptyHistory = Join-Path $installerDir "url_history.txt"

if (Test-Path (Join-Path $distDir "telegram_config.ini")) {
    $telegramConfig = Join-Path $distDir "telegram_config.ini"
} else {
    Set-Content -Path $emptyConfig -Value "[Telegram]`ntoken=`nchat_id=" -Encoding ASCII
    $telegramConfig = $emptyConfig
}

if (Test-Path (Join-Path $distDir "url_history.txt")) {
    $urlHistory = Join-Path $distDir "url_history.txt"
} else {
    Set-Content -Path $emptyHistory -Value "" -Encoding ASCII
    $urlHistory = $emptyHistory
}

$source = @'
using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Windows.Forms;

internal static class QRCodeGeneratorSetup
{
    [STAThread]
    private static int Main()
    {
        string tempDir = Path.Combine(Path.GetTempPath(), "QRCodeGeneratorSetup_" + Guid.NewGuid().ToString("N"));

        try
        {
            Directory.CreateDirectory(tempDir);

            Extract("QRCodeGenerator.exe", Path.Combine(tempDir, "QRCodeGenerator.exe"));
            Extract("install.ps1", Path.Combine(tempDir, "install.ps1"));
            Extract("telegram_config.ini", Path.Combine(tempDir, "telegram_config.ini"));
            Extract("url_history.txt", Path.Combine(tempDir, "url_history.txt"));

            ProcessStartInfo psi = new ProcessStartInfo();
            psi.FileName = "powershell.exe";
            psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File \"" + Path.Combine(tempDir, "install.ps1") + "\"";
            psi.WorkingDirectory = tempDir;
            psi.UseShellExecute = false;
            psi.CreateNoWindow = true;

            using (Process process = Process.Start(psi))
            {
                process.WaitForExit();
                if (process.ExitCode != 0)
                {
                    throw new Exception("Installer PowerShell gagal dengan kode " + process.ExitCode + ".");
                }
            }

            MessageBox.Show(
                "QR Code Generator berhasil dipasang.\n\nShortcut sudah dibuat di Desktop dan Start Menu.",
                "QR Code Generator Setup",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information);

            return 0;
        }
        catch (Exception ex)
        {
            MessageBox.Show(
                "Gagal memasang QR Code Generator:\n\n" + ex.Message,
                "QR Code Generator Setup",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error);
            return 1;
        }
        finally
        {
            try
            {
                if (Directory.Exists(tempDir))
                {
                    Directory.Delete(tempDir, true);
                }
            }
            catch
            {
            }
        }
    }

    private static void Extract(string resourceName, string outputPath)
    {
        Assembly assembly = Assembly.GetExecutingAssembly();
        using (Stream input = assembly.GetManifestResourceStream(resourceName))
        {
            if (input == null)
            {
                throw new FileNotFoundException("Resource installer tidak ditemukan: " + resourceName);
            }

            using (FileStream output = File.Create(outputPath))
            {
                input.CopyTo(output);
            }
        }
    }
}
'@

Set-Content -Path $sourcePath -Value $source -Encoding ASCII

& $csc `
    /nologo `
    /target:winexe `
    /optimize+ `
    /reference:System.Windows.Forms.dll `
    /out:$setupOutput `
    /resource:"$(Join-Path $distDir 'QRCodeGenerator.exe'),QRCodeGenerator.exe" `
    /resource:"$(Join-Path $root 'installer\install.ps1'),install.ps1" `
    /resource:"$telegramConfig,telegram_config.ini" `
    /resource:"$urlHistory,url_history.txt" `
    $sourcePath

if (-not (Test-Path $setupOutput)) {
    throw "Gagal membuat setup: $setupOutput"
}

Write-Host "Setup berhasil dibuat: $setupOutput"
