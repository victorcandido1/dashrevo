# Script PowerShell para preparar deploy
# Execute: .\prepare_deploy.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Preparando Dashboard REVO para Deploy" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar cache
$cacheFile = ".cache\processor_cache.pkl"
if (Test-Path $cacheFile) {
    $cacheSize = (Get-Item $cacheFile).Length / 1MB
    Write-Host "✓ Cache encontrado: $([math]::Round($cacheSize, 2)) MB" -ForegroundColor Green
} else {
    Write-Host "⚠️  AVISO: Cache não encontrado!" -ForegroundColor Yellow
    Write-Host "   Arquivo esperado: $cacheFile" -ForegroundColor Yellow
    Write-Host "   Execute o dashboard e faça upload de dados primeiro." -ForegroundColor Yellow
}
Write-Host ""

# Verificar estrutura
Write-Host "Verificando estrutura de diretórios:" -ForegroundColor Cyan
$requiredDirs = @("routes", "services", "static", "templates", "utils", ".cache")
foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Host "  ✓ $dir/" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $dir/ (FALTANDO)" -ForegroundColor Red
    }
}
Write-Host ""

# Verificar arquivos essenciais
Write-Host "Verificando arquivos essenciais:" -ForegroundColor Cyan
$requiredFiles = @("app.py", "config.py", "data_processor.py", "requirements.txt", "README.md", ".gitignore")
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file (FALTANDO)" -ForegroundColor Red
    }
}
Write-Host ""

# Verificar git
Write-Host "Verificando Git:" -ForegroundColor Cyan
if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Host "  ✓ Git instalado" -ForegroundColor Green
    
    # Verificar se é repositório git
    if (Test-Path ".git") {
        Write-Host "  ✓ Repositório Git inicializado" -ForegroundColor Green
        
        # Verificar status
        $gitStatus = git status --porcelain
        if ($gitStatus) {
            Write-Host "  ⚠️  Há arquivos não commitados:" -ForegroundColor Yellow
            $gitStatus | ForEach-Object { Write-Host "     $_" -ForegroundColor Yellow }
        } else {
            Write-Host "  ✓ Todos os arquivos estão commitados" -ForegroundColor Green
        }
        
        # Verificar se cache está no git
        $cacheInGit = git ls-files | Select-String "cache/processor_cache.pkl"
        if ($cacheInGit) {
            Write-Host "  ✓ Cache está no repositório Git" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  Cache NÃO está no repositório Git" -ForegroundColor Yellow
            Write-Host "     Execute: git add .cache/processor_cache.pkl" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ⚠️  Repositório Git não inicializado" -ForegroundColor Yellow
        Write-Host "     Execute: git init" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✗ Git não encontrado" -ForegroundColor Red
    Write-Host "     Instale Git: https://git-scm.com/downloads" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Próximos passos:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. Revise os arquivos acima" -ForegroundColor White
Write-Host "2. Se o cache não estiver no Git, adicione:" -ForegroundColor White
Write-Host "   git add .cache/processor_cache.pkl" -ForegroundColor Yellow
Write-Host "3. Faça commit:" -ForegroundColor White
Write-Host "   git commit -m 'Preparar para deploy'" -ForegroundColor Yellow
Write-Host "4. Crie repositório no GitHub e faça push" -ForegroundColor White
Write-Host "5. Siga as instruções em DEPLOY.md" -ForegroundColor White
Write-Host ""

