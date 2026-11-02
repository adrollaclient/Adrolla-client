# Installiert die neueste stabile Python-3-Version (nur fuer den aktuellen Benutzer, ohne Admin-Rechte).
# Aufruf durch START_ADROLLA.bat. Der Pfad zur python.exe wird in -OutFile geschrieben.
param([Parameter(Mandatory = $true)][string]$OutFile)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

try {
    $arch = 'amd64'
    if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64' -or $env:PROCESSOR_ARCHITEW6432 -eq 'ARM64') { $arch = 'arm64' }

    Write-Host 'Suche die neueste Python-Version auf python.org ...'
    $index = (Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/' -UseBasicParsing).Content
    $versions = [regex]::Matches($index, 'href="(\d+\.\d+\.\d+)/"') |
        ForEach-Object { [version]$_.Groups[1].Value } |
        Where-Object { $_.Major -eq 3 } |
        Sort-Object -Descending -Unique

    # Neueste Version, fuer die es wirklich einen Windows-Installer gibt
    $chosen = $null
    $url = $null
    foreach ($v in ($versions | Select-Object -First 15)) {
        $candidate = "https://www.python.org/ftp/python/$v/python-$v-$arch.exe"
        try {
            Invoke-WebRequest -Uri $candidate -Method Head -UseBasicParsing | Out-Null
            $chosen = $v
            $url = $candidate
            break
        } catch { continue }
    }
    if (-not $chosen) { throw 'Keine passende Python-Version auf python.org gefunden.' }

    $installer = Join-Path $env:TEMP "python-$chosen-$arch.exe"
    Write-Host "Lade Python $chosen herunter ..."
    Invoke-WebRequest -Uri $url -OutFile $installer -UseBasicParsing

    # Nur Installer akzeptieren, die gueltig von der Python Software Foundation signiert sind
    $signature = Get-AuthenticodeSignature -FilePath $installer
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Python Software Foundation') {
        Remove-Item $installer -Force -ErrorAction SilentlyContinue
        throw 'Die Signatur des Python-Installers ist ungueltig. Installation abgebrochen.'
    }

    Write-Host "Installiere Python $chosen (inklusive Tkinter, pip und PATH) ..."
    $process = Start-Process -FilePath $installer -Wait -PassThru -ArgumentList @(
        '/passive', 'InstallAllUsers=0', 'PrependPath=1', 'Include_launcher=1',
        'Include_tcltk=1', 'Include_pip=1', 'Include_test=0', 'Include_doc=0', 'Shortcuts=0'
    )
    Remove-Item $installer -Force -ErrorAction SilentlyContinue
    if ($process.ExitCode -ne 0 -and $process.ExitCode -ne 3010) {
        throw "Der Python-Installer wurde mit Code $($process.ExitCode) beendet."
    }

    $root = Join-Path $env:LOCALAPPDATA 'Programs\Python'
    $python = Get-ChildItem -Path $root -Directory -ErrorAction SilentlyContinue |
        Where-Object { Test-Path (Join-Path $_.FullName 'python.exe') } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if (-not $python) { throw 'python.exe wurde nach der Installation nicht gefunden.' }

    Set-Content -Path $OutFile -Value (Join-Path $python.FullName 'python.exe') -Encoding ASCII
    Write-Host "Python $chosen ist installiert."
    exit 0
} catch {
    Write-Host ('Fehler: ' + $_.Exception.Message)
    exit 1
}
