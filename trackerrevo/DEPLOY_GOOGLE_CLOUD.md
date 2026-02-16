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

---

## Deploy automático via GitHub

**Um comando** – commit, push e deploy no Google Cloud Run:

```bash
./deploy_auto.sh
# ou com mensagem personalizada:
./deploy_auto.sh "Atualizar ícones do radar"
```

Fluxo: `deploy_auto.sh` → commit + push para `main` → GitHub Actions → deploy no Cloud Run.

**Configuração única:**
1. Configure o secret `GCP_SA_KEY` no repositório (Settings > Secrets > Actions).
2. Valor: JSON da Service Account do GCP com permissões Cloud Run Admin e Storage Admin.

---

## Persistência no Google Cloud (GCS)

No Cloud Run o disco é efêmero. O trackerrevo usa **Google Cloud Storage** para persistir:

- Cache de movimento das aeronaves
- Histórico de voos (rotas, telemetria, origem/destino)

**Criar o bucket:**
```bash
gsutil mb -p codigos-465200 -l southamerica-east1 gs://trackerrevo-cache
gsutil iam ch serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com:objectAdmin gs://trackerrevo-cache
```

(O Cloud Run usa a default compute SA; ajuste PROJECT_NUMBER.)

Variável de ambiente no Cloud Run: `GCS_BUCKET=trackerrevo-cache` (já configurada no workflow).

---

## Amostragem e telemetria

- **Throttle**: mínimo 1 segundo entre pontos armazenados
- **Dados salvos**: rota (lat/lon), velocidade (kt), altitude (ft), heading, vertical_rate, timestamp
- **Origem/destino**: inferidos pelo aeroporto mais próximo no primeiro/último ponto
- **Velocidade média**: calculada ao salvar o voo

Para amostragem mais frequente, use **Cloud Scheduler** chamando `/api/tracker/internal/poll` a cada 5–10 segundos.

---

## Ícones EC155 / EC135 (ipmet)

Copie os ícones da pasta ipmet para `trackerrevo/static/icons/`:
- `ec155.png` — PR-OMB, PR-OMH
- `ec135.png` — PR-OOE
