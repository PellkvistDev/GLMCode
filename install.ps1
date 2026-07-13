# GLM Code installer: installs dependencies, puts `glm`/`glmapp` on your PATH,
# and creates a desktop shortcut for the app.
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host "Installing GLM Code dependencies..." -ForegroundColor Cyan
python -m pip install --user -r (Join-Path $root "requirements.txt")
if ($LASTEXITCODE -ne 0) { Write-Host "pip install failed" -ForegroundColor Red; exit 1 }

# Launchers that work from any directory
$launcherDir = Join-Path $env:USERPROFILE ".glmcode\bin"
New-Item -ItemType Directory -Force $launcherDir | Out-Null

@"
@echo off
set PYTHONPATH=$root;%PYTHONPATH%
python -m glmcode %*
"@ | Out-File -FilePath (Join-Path $launcherDir "glm.cmd") -Encoding ascii

@"
@echo off
set PYTHONPATH=$root;%PYTHONPATH%
start "" pythonw -m glmcode.gui %*
"@ | Out-File -FilePath (Join-Path $launcherDir "glmapp.cmd") -Encoding ascii

# Add to user PATH if missing
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$launcherDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$launcherDir", "User")
    Write-Host "Added $launcherDir to your user PATH (restart your terminal)." -ForegroundColor Yellow
}

# Desktop shortcut for the app
$pythonw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if ($pythonw) {
    $shell = New-Object -ComObject WScript.Shell
    $lnk = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath("Desktop")) "GLM Code.lnk"))
    $lnk.TargetPath = $pythonw
    $lnk.Arguments = "-m glmcode.gui"
    $lnk.WorkingDirectory = $root
    $lnk.Description = "GLM Code - free AI coding agent"
    $icoFile = Join-Path $root "glmcode\gui\app_icon.ico"
    if (Test-Path $icoFile) {
        $lnk.IconLocation = "$icoFile,0"
    }
    $lnk.Save()
    Write-Host "Created desktop shortcut: GLM Code" -ForegroundColor Green
}

Write-Host ""
Write-Host "Done! Set your free API key (from https://z.ai -> profile -> API Keys):" -ForegroundColor Green
Write-Host "  setx ZAI_API_KEY your-key-here    (or let the app ask on first launch)"
Write-Host "Launch the desktop app:  glmapp   (or the 'GLM Code' desktop shortcut)" -ForegroundColor Green
Write-Host "Terminal version:        glm"
