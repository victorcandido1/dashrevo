# Script para configurar repositório GitHub
# Execute: .\setup_github.ps1

param(
    [Parameter(Mandatory=$true)]
    [string]$GitHubUser,
    
    [Parameter(Mandatory=$false)]
    [string]$RepoName = "dashrevo"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Configurando Repositório GitHub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se já existe remote
$existingRemote = git remote -v
if ($existingRemote) {
    Write-Host "⚠️  Já existe um repositório remoto configurado:" -ForegroundColor Yellow
    Write-Host $existingRemote -ForegroundColor Yellow
    Write-Host ""
    $overwrite = Read-Host "Deseja sobrescrever? (s/N)"
    if ($overwrite -ne "s" -and $overwrite -ne "S") {
        Write-Host "Operação cancelada." -ForegroundColor Red
        exit
    }
    git remote remove origin
}

# Adicionar remote
$remoteUrl = "https://github.com/$GitHubUser/$RepoName.git"
Write-Host "Adicionando repositório remoto: $remoteUrl" -ForegroundColor Cyan
git remote add origin $remoteUrl

Write-Host ""
Write-Host "✓ Repositório remoto configurado!" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Cyan
Write-Host "1. Crie o repositório no GitHub:" -ForegroundColor White
Write-Host "   https://github.com/new" -ForegroundColor Yellow
Write-Host "   Nome: $RepoName" -ForegroundColor Yellow
Write-Host "   NÃO marque 'Initialize with README'" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Após criar, execute:" -ForegroundColor White
Write-Host "   git push -u origin main" -ForegroundColor Yellow
Write-Host ""

