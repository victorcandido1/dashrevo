# Deploy do Tracker REVO para Google Cloud Run
# Mesmo padrao do ipmet (salesforceintegration)
# Execute: .\deploy_trackerrevo.ps1

$PROJECT_ID = "codigos-465200"
$REGION = "southamerica-east1"
$SERVICE_NAME = "trackerrevo"
$IMAGE = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "=========================================="
Write-Host "DEPLOY - Tracker REVO (Radar de Aeronaves)"
Write-Host "=========================================="
Write-Host "Projeto: $PROJECT_ID"
Write-Host "Regiao:  $REGION"
Write-Host "Imagem:  $IMAGE"
Write-Host "=========================================="

# 1. Build da imagem
Write-Host "[1/3] Building Docker image..."
gcloud builds submit --tag $IMAGE . --project=$PROJECT_ID
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Falha no build." -ForegroundColor Red
    exit 1
}

# 2. Deploy Cloud Run Service
Write-Host "[2/3] Deploying Cloud Run Service..."
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE `
    --region $REGION `
    --platform managed `
    --memory 512Mi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 5 `
    --timeout 120 `
    --allow-unauthenticated `
    --set-env-vars "TZ=America/Sao_Paulo,PYTHONUNBUFFERED=1" `
    --project=$PROJECT_ID

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Falha no deploy." -ForegroundColor Red
    exit 1
}

# 3. URL
Write-Host "[3/3] Deploy concluido!"
$URL = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)" --project=$PROJECT_ID
Write-Host ""
Write-Host "URL: $URL" -ForegroundColor Cyan
Write-Host "  /       - Dashboard"
Write-Host "  /tracker - Radar de aeronaves"
Write-Host ""
