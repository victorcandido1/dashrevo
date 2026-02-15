# Deploy do Tracker REVO no Google Cloud Run

Radar de aeronaves em tempo real (região São Paulo). Usa o **mesmo padrão do ipmet**: projeto, região, build gcr.io, scripts PowerShell.

## Configuração (igual ipmet)

| Parâmetro | Valor |
|-----------|-------|
| Projeto GCP | `codigos-465200` |
| Região | `southamerica-east1` (São Paulo) |
| Imagem | `gcr.io/codigos-465200/trackerrevo` |

## Pré-requisitos

```bash
gcloud auth login
gcloud config set project codigos-465200
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

## Deploy

**Bash (macOS/Linux):**
```bash
cd trackerrevo
chmod +x deploy_cloud.sh
./deploy_cloud.sh
```

**PowerShell (Windows):**
```powershell
cd trackerrevo
.\deploy_trackerrevo.ps1
```

**Manual (build + deploy):**
```bash
gcloud builds submit --tag gcr.io/codigos-465200/trackerrevo . --project=codigos-465200
gcloud run deploy trackerrevo --image gcr.io/codigos-465200/trackerrevo \
  --region southamerica-east1 --allow-unauthenticated --project=codigos-465200
```

## Arquivos (padrão ipmet)

| Arquivo | Descrição |
|---------|-----------|
| `deploy_cloud.sh` | Deploy via Bash (igual ipmet deploy_cloud.sh) |
| `deploy_trackerrevo.ps1` | Deploy via PowerShell |
| `cloudbuild.yaml` | Cloud Build config (como ipmet cloudbuild.yaml) |
| `Dockerfile` | Imagem Python 3.11 + gunicorn |
| `.dockerignore` / `.gcloudignore` | Ignorar arquivos desnecessários |
| `env_example.txt` | Exemplo de variáveis de ambiente |

## URLs pós-deploy

- `/` — Dashboard
- `/tracker` — Radar de aeronaves em tempo real
- `/api/tracker/aircraft` — API posições
- `/api/tracker/trails` — API trilhas

## Separação dos serviços ipmet

| Serviço | Tipo | Descrição |
|---------|------|-----------|
| revo-flight-monitor | Job | Briefing, voos, meteo, Telegram |
| trackerrevo | Service | Radar web 24/7 |
| weather-dashboard | Service | Dashboard meteorológico |

Todos no projeto `codigos-465200`, região `southamerica-east1`.
