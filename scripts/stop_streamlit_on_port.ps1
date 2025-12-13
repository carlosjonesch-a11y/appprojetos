param(
    [int]$Port = 8501
)

try {
    $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if (-not $conns) {
        Write-Host "Nenhum processo usando a porta $Port encontrado."
        exit 0
    }

    $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($pid in $pids) {
        try {
            $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "Parando processo $($proc.Id) - $($proc.ProcessName)"
                Stop-Process -Id $proc.Id -Force
            }
        } catch {
            Write-Warning "Falha ao parar processo $pid: $_"
        }
    }
} catch {
    Write-Error "Erro ao procurar processos na porta $Port: $_"
}
