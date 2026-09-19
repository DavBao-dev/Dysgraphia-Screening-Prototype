<#
run-dev.ps1 - Chay backend (FastAPI) + frontend (Next.js) bang 1 lenh.

  .\run-dev.ps1            # start ca 2 (chay nen, ghi log vao logs\)
  .\run-dev.ps1 -Attach    # start roi xem log truc tiep (Ctrl+C de dung ca 2)
  .\run-dev.ps1 -Prod      # frontend chay ban production (npm run build + npm start)
  .\run-dev.ps1 -Status    # xem trang thai 2 server
  .\run-dev.ps1 -Stop      # dung 2 server (do script start, hoac dang giu port 8000/3000)

Yeu cau: da `pip install -r requirements.txt`, va lan dau se tu chay `npm install`.
Luu y: next.config.ts proxy /api/* sang http://127.0.0.1:8000 nen backend phai o port 8000.
#>
[CmdletBinding()]
param(
    [switch]$Stop,
    [switch]$Status,
    [switch]$Attach,
    [switch]$Prod
)

$ErrorActionPreference = 'Stop'
$Root         = $PSScriptRoot
$FrontendDir  = Join-Path $Root 'frontend'
$LogDir       = Join-Path $Root 'logs'
$PidFile      = Join-Path $LogDir 'devservers.json'
$BackendPort  = 8000
$FrontendPort = 3000
$BackendUrl   = "http://127.0.0.1:$BackendPort"
$FrontendUrl  = "http://localhost:$FrontendPort"
$BackendLog   = Join-Path $LogDir 'backend.log'
$BackendErr   = Join-Path $LogDir 'backend.err.log'
$FrontendLog  = Join-Path $LogDir 'frontend.log'
$FrontendErr  = Join-Path $LogDir 'frontend.err.log'
$StdinFile    = Join-Path $LogDir '.stdin'   # giu server tach hoan toan khoi console cua ban

function Write-Step($msg)  { Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-WarnMsg($m) { Write-Host "  !!  $m" -ForegroundColor Yellow }
function Write-ErrMsg($m)  { Write-Host "  XX  $m" -ForegroundColor Red }

function Get-PortOwner([int]$Port) {
    $conn = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($conn) { return [int]$conn.OwningProcess }
    return $null
}

function Wait-Http([string]$Url, [int]$TimeoutSec) {
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 400) { return $true }
        } catch { }
        Start-Sleep -Milliseconds 700
    }
    return $false
}

function Ensure-Node {
    if (Get-Command npm -ErrorAction SilentlyContinue) { return $true }
    foreach ($dir in @("$env:ProgramFiles\nodejs", "$env:LOCALAPPDATA\Programs\nodejs")) {
        if (Test-Path (Join-Path $dir 'npm.cmd')) {
            $env:Path += ";$dir"
            Write-WarnMsg "npm khong co trong PATH cua phien nay - da them tam thoi: $dir"
            return $true
        }
    }
    return $false
}

function Stop-ProcessTree([int]$targetId) {
    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId=$targetId" -ErrorAction SilentlyContinue
    foreach ($child in $children) { Stop-ProcessTree -targetId ([int]$child.ProcessId) }
    Stop-Process -Id $targetId -Force -ErrorAction SilentlyContinue
}

function Stop-RepoProcesses {
    # Chi dong cac tien trinh cua repo nay (khong dung app node/python khac).
    $killed  = 0
    $targets = New-Object System.Collections.Generic.List[int]

    if (Test-Path $PidFile) {
        try {
            $saved = Get-Content $PidFile -Raw | ConvertFrom-Json
            foreach ($pidValue in @($saved.backend, $saved.frontend)) {
                if ($pidValue) { $targets.Add([int]$pidValue) }
            }
        } catch { }
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    }
    foreach ($port in @($BackendPort, $FrontendPort)) {
        $owner = Get-PortOwner $port
        if ($owner) { $targets.Add($owner) }
    }

    foreach ($t in ($targets | Select-Object -Unique)) {
        # uvicorn --reload: tien trinh con giu socket du tien trinh cha da chet
        $children = Get-CimInstance Win32_Process -Filter "ParentProcessId=$t" -ErrorAction SilentlyContinue
        foreach ($child in $children) { Stop-ProcessTree -targetId ([int]$child.ProcessId); $killed++ }
        Stop-Process -Id $t -Force -ErrorAction SilentlyContinue
        $killed++
    }

    # python cua .venv trong repo + node cua frontend trong repo
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.ExecutablePath -and $_.ExecutablePath -like "$Root*" } |
        ForEach-Object { Stop-ProcessTree -targetId ([int]$_.ProcessId); $killed++ }
    Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*$Root*" } |
        ForEach-Object { Stop-Process -Id ([int]$_.ProcessId) -Force -ErrorAction SilentlyContinue }

    # vong cuoi: don sach bat ky tien trinh nao con giu port
    for ($i = 0; $i -lt 6; $i++) {
        $busy = @()
        foreach ($port in @($BackendPort, $FrontendPort)) {
            $owner = Get-PortOwner $port
            if ($owner) { $busy += $owner }
        }
        if ($busy.Count -eq 0) { break }
        foreach ($owner in $busy) {
            Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
                Where-Object { $_.ParentProcessId -eq $owner } |
                ForEach-Object { Stop-ProcessTree -targetId ([int]$_.ProcessId) }
            Stop-Process -Id $owner -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Milliseconds 700
    }

    Start-Sleep -Seconds 1
    $left = @()
    foreach ($port in @($BackendPort, $FrontendPort)) {
        $owner = Get-PortOwner $port
        if ($owner) { $left += "$port (pid $owner)" }
    }
    if ($left.Count -eq 0) {
        Write-Ok "da dung $killed tien trinh - port $BackendPort/$FrontendPort da giai phong"
    } else {
        Write-WarnMsg ("van con giu port: " + ($left -join ', ') + " - hay mo Task Manager va ket thuc thu cong")
    }
}

function Show-Status {
    $targets = @(
        @{ Name = 'backend '; Port = $BackendPort;  Url = "$BackendUrl/api/health" },
        @{ Name = 'frontend'; Port = $FrontendPort; Url = $FrontendUrl }
    )
    foreach ($t in $targets) {
        $owner = Get-PortOwner $t.Port
        if ($owner) {
            $code = 'khong phan hoi'
            try { $code = (Invoke-WebRequest -Uri $t.Url -UseBasicParsing -TimeoutSec 5).StatusCode } catch { }
            Write-Ok ("{0}  port {1}  pid {2}  {3} -> {4}" -f $t.Name, $t.Port, $owner, $t.Url, $code)
        } else {
            Write-WarnMsg ("{0}  port {1}  KHONG chay" -f $t.Name, $t.Port)
        }
    }
    if (Test-Path $BackendLog) { Write-Host "`n--- logs\backend.log (20 dong cuoi) ---"; Get-Content $BackendLog -Tail 20 }
}

function Show-LogTail([string]$Path, [int]$Lines) {
    if (Test-Path $Path) { Get-Content $Path -Tail $Lines | ForEach-Object { "    $_" } }
}

# ---------------------------------------------------------------------------- main
New-Item -ItemType Directory -Force $LogDir | Out-Null
if (-not (Test-Path $StdinFile)) { New-Item -ItemType File -Force $StdinFile | Out-Null }

if ($Status) { Show-Status; exit 0 }
if ($Stop)   { Stop-RepoProcesses; exit 0 }

$backendPid  = $null
$frontendPid = $null

# --- Backend (FastAPI, port 8000) ------------------------------------------------
$backendPid = Get-PortOwner $BackendPort
if ($backendPid) {
    Write-WarnMsg "port $BackendPort dang duoc dung (pid $backendPid) - bo qua start backend"
} else {
    $pythonExe = Join-Path $Root '.venv\Scripts\python.exe'
    if (-not (Test-Path $pythonExe)) {
        $pythonExe = 'python'
        Write-WarnMsg 'khong thay .venv\Scripts\python.exe - dung python he thong'
    }
    Write-Step "start backend  $BackendUrl   (log: logs\backend.log)"
    $backendPid = (Start-Process -FilePath $pythonExe `
            -ArgumentList '-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', "$BackendPort" `
            -WorkingDirectory $Root -RedirectStandardInput $StdinFile `
            -RedirectStandardOutput $BackendLog -RedirectStandardError $BackendErr `
            -PassThru -WindowStyle Hidden).Id
}

if (-not (Wait-Http "$BackendUrl/api/health" 45)) {
    Write-ErrMsg 'backend khong san sang sau 45s. 20 dong cuoi cua logs\backend.err.log:'
    Show-LogTail $BackendErr 20
    Write-ErrMsg 'goi y: .\.venv\Scripts\python.exe -m pip install -r requirements.txt'
    exit 1
}
Write-Ok "backend san sang  $BackendUrl/api/health"

# --- Frontend (Next.js, port 3000) ----------------------------------------------
$frontendPid = Get-PortOwner $FrontendPort
if ($frontendPid) {
    Write-WarnMsg "port $FrontendPort dang duoc dung (pid $frontendPid) - bo qua start frontend"
} else {
    if (-not (Ensure-Node)) {
        Write-ErrMsg 'khong tim thay node/npm. Cai Node.js LTS: winget install OpenJS.NodeJS.LTS'
        Write-ErrMsg 'sau khi cai xong, mo terminal moi (hoac khoi dong lai VS Code) roi chay lai script'
        exit 1
    }
    if (-not (Test-Path (Join-Path $FrontendDir 'node_modules'))) {
        Write-Step 'frontend\node_modules chua co -> npm install (lan dau, vai phut)'
        Push-Location $FrontendDir
        try { npm install --no-audit --no-fund } finally { Pop-Location }
    }
    if ($Prod) {
        Write-Step 'build frontend (npm run build)'
        Push-Location $FrontendDir
        try { npm run build } finally { Pop-Location }
        $npmArgs = @('/c', 'npm', 'run', 'start')
    } else {
        $npmArgs = @('/c', 'npm', 'run', 'dev')
    }
    Write-Step "start frontend $FrontendUrl (log: logs\frontend.log)"
    $frontendPid = (Start-Process -FilePath 'cmd.exe' -ArgumentList $npmArgs `
            -WorkingDirectory $FrontendDir -RedirectStandardInput $StdinFile `
            -RedirectStandardOutput $FrontendLog -RedirectStandardError $FrontendErr `
            -PassThru -WindowStyle Hidden).Id
}

if (-not (Wait-Http $FrontendUrl 150)) {
    Write-ErrMsg 'frontend khong san sang sau 150s. 20 dong cuoi cua logs\frontend.err.log:'
    Show-LogTail $FrontendErr 20
    exit 1
}
Write-Ok "frontend san sang $FrontendUrl"

@{ backend = $backendPid; frontend = $frontendPid } | ConvertTo-Json | Set-Content -Path $PidFile -Encoding utf8

Write-Host ''
Write-Ok 'Ca 2 server dang chay.'
Write-Host "     Mo ung dung : $FrontendUrl"
Write-Host "     Backend API : $BackendUrl/api/health   (tai lieu: $BackendUrl/docs)"
Write-Host "     Log         : logs\backend.log, logs\frontend.log"
Write-Host "     Trang thai  : .\run-dev.ps1 -Status"
Write-Host "     Dung server : .\run-dev.ps1 -Stop"

if (-not $Attach) { exit 0 }

# --- Attach mode: xem log truc tiep, Ctrl+C de dung ca 2 server ------------------
Write-Host ''
Write-Step 'Dang xem log truc tiep - nhan Ctrl+C de dung ca 2 server'
$offsets = @{}
try {
    while ($true) {
        foreach ($name in @('backend.log', 'backend.err.log', 'frontend.log', 'frontend.err.log')) {
            $path = Join-Path $LogDir $name
            if (-not (Test-Path $path)) { continue }
            $size = (Get-Item $path).Length
            if (-not $offsets.ContainsKey($name)) { $offsets[$name] = 0 }
            if ($size -gt $offsets[$name]) {
                $stream = [System.IO.File]::Open($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
                try {
                    $stream.Seek($offsets[$name], [System.IO.SeekOrigin]::Begin) | Out-Null
                    $reader = New-Object System.IO.StreamReader($stream)
                    $text = $reader.ReadToEnd()
                    $reader.Dispose()
                    [Console]::Write($text)
                    $offsets[$name] = $size
                } finally { $stream.Dispose() }
            }
        }
        Start-Sleep -Milliseconds 800
    }
} finally {
    Stop-RepoProcesses
}

