# Script para iniciar o dashboard e expor na rede local
# Execute: .\start_local_server.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Iniciando Dashboard REVO - Servidor Local" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Obter IP local
$ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" -or $_.IPAddress -like "172.*"} | Select-Object -First 1).IPAddress

if (-not $ipAddress) {
    Write-Host "⚠️  Não foi possível detectar IP local" -ForegroundColor Yellow
    Write-Host "Verifique sua conexão de rede." -ForegroundColor Yellow
    exit 1
}

Write-Host "IP Local detectado: $ipAddress" -ForegroundColor Green
Write-Host ""

# Verificar porta
$port = 5000
$portInUse = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "⚠️  Porta $port já está em uso!" -ForegroundColor Yellow
    $port = 8080
    $env:PORT = "8080"
    Write-Host "Usando porta $port..." -ForegroundColor Yellow
}

# Configurar firewall
Write-Host "Configurando firewall..." -ForegroundColor Cyan
try {
    $firewallRule = Get-NetFirewallRule -DisplayName "Flask Dashboard" -ErrorAction SilentlyContinue
    if (-not $firewallRule) {
        New-NetFirewallRule -DisplayName "Flask Dashboard" -Direction Inbound -LocalPort $port -Protocol TCP -Action Allow | Out-Null
        Write-Host "✓ Regra de firewall criada" -ForegroundColor Green
    } else {
        Write-Host "✓ Regra de firewall já existe" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Erro ao configurar firewall: $_" -ForegroundColor Yellow
    Write-Host "Você pode precisar executar como Administrador" -ForegroundColor Yellow
}

Write-Host ""

# Iniciar dashboard
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Iniciando Dashboard..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Acesse de:" -ForegroundColor White
Write-Host "  • Esta máquina: http://localhost:$port" -ForegroundColor Yellow
Write-Host "  • Rede local: http://$ipAddress`:$port" -ForegroundColor Yellow
Write-Host ""
Write-Host "Para parar: Pressione Ctrl+C" -ForegroundColor White
Write-Host ""

# Iniciar o dashboard
python app.py

