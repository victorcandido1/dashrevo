#!/bin/bash
# Deploy do Tracker REVO para Google Cloud Run
# Mesmo padrão do ipmet (salesforceintegration): gcr.io, PROJECT_ID, REGION
# Serviço separado do flight_monitor e demais programas

set -e

PROJECT_ID="codigos-465200"
REGION="southamerica-east1"
SERVICE_NAME="trackerrevo"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "DEPLOY - Tracker REVO (Radar de Aeronaves)"
echo "=========================================="
echo "Projeto: ${PROJECT_ID}"
echo "Região:  ${REGION}"
echo "Imagem:  ${IMAGE_NAME}"
echo "=========================================="

# 1. Build da imagem (igual ipmet)
echo "[1/3] Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME} . --project=${PROJECT_ID}

# 2. Deploy Cloud Run Service
echo "[2/3] Deploying Cloud Run Service..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --region ${REGION} \
    --platform managed \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 5 \
    --timeout 120 \
    --allow-unauthenticated \
    --set-env-vars "TZ=America/Sao_Paulo,PYTHONUNBUFFERED=1" \
    --project=${PROJECT_ID}

echo "[3/3] Deploy concluído!"
echo ""
echo "=========================================="
echo "URL do Tracker REVO:"
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format='value(status.url)' --project=${PROJECT_ID}
echo "=========================================="
echo ""
echo "Rotas: /  (dashboard) | /tracker (radar)"
echo ""
