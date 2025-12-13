param(
    [int]$StartPort = 8501,
    [int]$MaxTrials = 10,
    [switch]$KillConflicts
)

function Get-FreePort {
    param([int]$basePort, [int]$maxTrials)
    for ($p = $basePort; $p -lt $basePort + $maxTrials; $p++) {
        try {
            $conn = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue
            if (-not $conn) { return $p }
        } catch {
            # Fallback to netstat if Get-NetTCPConnection not available
            $busy = (netstat -ano | findstr ":$p ") -ne $null
            if (-not $busy) { return $p }
        }
    }
    return $null
}

$freePort = Get-FreePort -basePort $StartPort -maxTrials $MaxTrials
if (-not $freePort) {
    Write-Error "Não foi encontrado porto livre entre $StartPort e $($StartPort + $MaxTrials - 1)."; exit 1
}

if ($KillConflicts) {
    # Tenta parar processos que ocupam o porto alvo (apenas se a flag KillConflicts estiver setada)
    try {
        $conn = Get-NetTCPConnection -LocalPort $freePort -ErrorAction SilentlyContinue
        if ($conn) {
            $procId = $conn.OwningProcess
            if ($procId) {
                Write-Host "Matando processo $procId que usa a porta $freePort..."
                Stop-Process -Id $procId -Force
                Start-Sleep -Seconds 1
            }
        }
    } catch {
        # ignore
    }
}

# Resolve python binary inside venv if available, else fallback to `python`
$venvPython = Join-Path (Get-Location) "venv\Scripts\python.exe"
if (Test-Path $venvPython) { $python = $venvPython } else { $python = "python" }

Write-Host "Iniciando Streamlit em http://localhost:$freePort"
& $python -m streamlit run app.py --server.port $freePort --server.address localhost
