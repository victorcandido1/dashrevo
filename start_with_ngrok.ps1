# Script para iniciar o dashboard com ngrok automaticamente
# Execute: .\start_with_ngrok.ps1

# Token do ngrok (já configurado)
$ngrokToken = "cr_36hP3CWJgRY79fl3Ywc4LsP0XEd"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Iniciando Dashboard REVO com ngrok" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se ngrok está instalado
$ngrokPath = Get-Command ngrok -ErrorAction SilentlyContinue

# Se não estiver no PATH, verificar arquivo salvo
if (-not $ngrokPath) {
    $ngrokPathFile = Join-Path $PSScriptRoot ".ngrok_path.txt"
    if (Test-Path $ngrokPathFile) {
        $savedPath = Get-Content $ngrokPathFile -Raw | ForEach-Object { $_.Trim() }
        if (Test-Path $savedPath) {
            $ngrokPath = $savedPath
            Write-Host "✓ ngrok encontrado em: $savedPath" -ForegroundColor Green
        }
    }
}

# Se ainda não encontrou, pedir ao usuário
if (-not $ngrokPath) {
    Write-Host "⚠️  ngrok não encontrado!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Para instalar ngrok:" -ForegroundColor Cyan
    Write-Host "1. Baixe em: https://ngrok.com/download" -ForegroundColor White
    Write-Host "2. Extraia ngrok.exe" -ForegroundColor White
    Write-Host "3. Adicione ao PATH ou coloque neste diretório" -ForegroundColor White
    Write-Host ""
    Write-Host "Ou configure o caminho manualmente no script." -ForegroundColor Yellow
    Write-Host ""
    $manualPath = Read-Host "Digite o caminho completo do ngrok.exe (ou Enter para cancelar)"
    if ($manualPath -and (Test-Path $manualPath)) {
        $ngrokPath = $manualPath
        # Salvar caminho
        $ngrokPathFile = Join-Path $PSScriptRoot ".ngrok_path.txt"
        $manualPath | Out-File -FilePath $ngrokPathFile -Encoding UTF8
    } else {
        Write-Host "Cancelado. Iniciando apenas o dashboard..." -ForegroundColor Yellow
        python app.py
        exit
    }
}

# Verificar se Python está instalado
$pythonPath = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonPath) {
    Write-Host "❌ Python não encontrado!" -ForegroundColor Red
    Write-Host "Instale Python 3.8+ primeiro." -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ ngrok encontrado" -ForegroundColor Green
Write-Host "✓ Python encontrado" -ForegroundColor Green
Write-Host ""

# Verificar se porta 5000 está livre
$portInUse = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "⚠️  Porta 5000 já está em uso!" -ForegroundColor Yellow
    Write-Host "Tentando usar porta 8080..." -ForegroundColor Yellow
    $env:PORT = "8080"
    $dashboardPort = 8080
} else {
    $dashboardPort = 5000
}

Write-Host "Iniciando dashboard na porta $dashboardPort..." -ForegroundColor Cyan
Write-Host ""

# Iniciar dashboard em background
$dashboardJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    $env:PORT = $using:dashboardPort
    python app.py
}

# Aguardar um pouco para o dashboard iniciar
Start-Sleep -Seconds 3

# Verificar se o dashboard está rodando
$dashboardRunning = Get-NetTCPConnection -LocalPort $dashboardPort -ErrorAction SilentlyContinue
if (-not $dashboardRunning) {
    Write-Host "⚠️  Dashboard não iniciou corretamente. Verifique os logs." -ForegroundColor Yellow
    Stop-Job $dashboardJob
    Remove-Job $dashboardJob
    exit 1
}

Write-Host "✓ Dashboard iniciado na porta $dashboardPort" -ForegroundColor Green
Write-Host ""

# Configurar token do ngrok (se necessário)
Write-Host "Configurando token do ngrok..." -ForegroundColor Cyan
if ($ngrokPath -is [System.Management.Automation.ApplicationInfo]) {
    # ngrok está no PATH
    ngrok config add-authtoken $ngrokToken 2>&1 | Out-Null
} else {
    # ngrok está em caminho específico
    & $ngrokPath config add-authtoken $ngrokToken 2>&1 | Out-Null
}

# Iniciar ngrok
Write-Host "Iniciando ngrok..." -ForegroundColor Cyan
Write-Host ""

if ($ngrokPath -is [System.Management.Automation.ApplicationInfo]) {
    # ngrok está no PATH
    Start-Process ngrok -ArgumentList "http $dashboardPort" -NoNewWindow
} else {
    # ngrok está em caminho específico
    Start-Process $ngrokPath -ArgumentList "http $dashboardPort" -NoNewWindow
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Dashboard rodando!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Acesse localmente:" -ForegroundColor White
Write-Host "  http://localhost:$dashboardPort" -ForegroundColor Yellow
Write-Host ""
Write-Host "URL pública (ngrok):" -ForegroundColor White
Write-Host "  Verifique a janela do ngrok para a URL" -ForegroundColor Yellow
Write-Host "  Geralmente: https://xxxxx.ngrok-free.app" -ForegroundColor Yellow
Write-Host ""
Write-Host "Para parar:" -ForegroundColor White
Write-Host "  Pressione Ctrl+C neste terminal" -ForegroundColor Yellow
Write-Host "  Feche a janela do ngrok" -ForegroundColor Yellow
Write-Host ""

# Manter o script rodando e mostrar logs do dashboard
try {
    Receive-Job $dashboardJob -Wait
} catch {
    Write-Host "Dashboard parado." -ForegroundColor Yellow
} finally {
    Stop-Job $dashboardJob -ErrorAction SilentlyContinue
    Remove-Job $dashboardJob -ErrorAction SilentlyContinue
}

