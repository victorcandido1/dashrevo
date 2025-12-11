# Script para configurar token do ngrok
# Execute: .\config_ngrok.ps1

$ngrokToken = "cr_36hP3CWJgRY79fl3Ywc4LsP0XEd"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Configurando ngrok" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se ngrok está instalado
$ngrokPath = Get-Command ngrok -ErrorAction SilentlyContinue

if ($ngrokPath) {
    Write-Host "✓ ngrok encontrado" -ForegroundColor Green
    
    # Configurar token
    Write-Host "Configurando token..." -ForegroundColor Cyan
    ngrok config add-authtoken $ngrokToken
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Token configurado com sucesso!" -ForegroundColor Green
        
        # Verificar configuração
        Write-Host ""
        Write-Host "Verificando configuração..." -ForegroundColor Cyan
        ngrok config check
        
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "ngrok configurado e pronto para uso!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Agora você pode usar:" -ForegroundColor White
        Write-Host "  .\start_with_ngrok.ps1" -ForegroundColor Yellow
        Write-Host ""
    } else {
        Write-Host "⚠️  Erro ao configurar token" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  ngrok não encontrado no PATH" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Para instalar ngrok:" -ForegroundColor Cyan
    Write-Host "1. Baixe em: https://ngrok.com/download" -ForegroundColor White
    Write-Host "2. Extraia ngrok.exe" -ForegroundColor White
    Write-Host "3. Opções:" -ForegroundColor White
    Write-Host "   a) Adicione ao PATH do Windows" -ForegroundColor Yellow
    Write-Host "   b) Coloque ngrok.exe neste diretório" -ForegroundColor Yellow
    Write-Host "   c) Informe o caminho completo abaixo" -ForegroundColor Yellow
    Write-Host ""
    
    $manualPath = Read-Host "Digite o caminho completo do ngrok.exe (ou Enter para pular)"
    
    if ($manualPath -and (Test-Path $manualPath)) {
        Write-Host "Configurando token com ngrok em: $manualPath" -ForegroundColor Cyan
        & $manualPath config add-authtoken $ngrokToken
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Token configurado!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Salvando caminho do ngrok..." -ForegroundColor Cyan
            
            # Salvar caminho em arquivo para uso futuro
            $ngrokPathFile = Join-Path $PSScriptRoot ".ngrok_path.txt"
            $manualPath | Out-File -FilePath $ngrokPathFile -Encoding UTF8
            
            Write-Host "✓ Caminho salvo em .ngrok_path.txt" -ForegroundColor Green
        }
    } else {
        Write-Host ""
        Write-Host "Token do ngrok salvo:" -ForegroundColor Cyan
        Write-Host "  $ngrokToken" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Após instalar ngrok, execute:" -ForegroundColor White
        Write-Host "  ngrok config add-authtoken $ngrokToken" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Ou execute este script novamente após instalar." -ForegroundColor White
    }
}

Write-Host ""
