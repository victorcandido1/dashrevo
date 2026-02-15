# Deploy via GitHub Actions (como ipmet)

Push em `main` na pasta `trackerrevo/` dispara deploy automático no Google Cloud Run.

## Configuração única

### 1. Criar Service Account no GCP

1. Acesse [IAM → Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts?project=codigos-465200)
2. Crie conta: `github-actions-trackerrevo` (ou use uma existente)
3. Roles necessárias: **Cloud Run Admin**, **Service Account User**, **Cloud Build Editor**, **Storage Admin**
4. Crie chave JSON: ⋮ → Manage keys → Add key → Create new key → JSON
5. Baixe o arquivo .json

### 2. Adicionar secret no GitHub

1. Repo: https://github.com/victorcandido1/dashrevo
2. Settings → Secrets and variables → Actions
3. New repository secret: nome `GCP_SA_KEY`, valor = conteúdo do JSON (todo o arquivo)

### 3. APIs habilitadas (se ainda não)

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project=codigos-465200
```

## Deploy

Após configurar o secret, qualquer push em `trackerrevo/**` na branch `main` dispara o deploy.

Para disparar manualmente: Actions → Deploy Tracker REVO → Run workflow
