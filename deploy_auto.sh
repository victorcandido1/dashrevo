#!/bin/bash
# Deploy automático: GitHub → Google Cloud Run
# Um comando: commit + push → GitHub Actions faz o deploy para o GCP

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MSG="${1:-Deploy automático: atualização trackerrevo}"

echo "=========================================="
echo "DEPLOY AUTOMÁTICO - Tracker REVO"
echo "=========================================="
echo "1. Git add + commit"
echo "2. Push para main"
echo "3. GitHub Actions → deploy no Google Cloud Run"
echo "=========================================="

# Garante que estamos em main
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" != "main" ]; then
    echo "Fazendo merge de $BRANCH em main..."
    git add -A
    git status --short
    if ! git diff --staged --quiet 2>/dev/null; then
        git commit -m "$MSG" || true
    fi
    git checkout main
    git merge "$BRANCH" -m "Merge $BRANCH"
fi

# Add e commit
git add trackerrevo/ .github/workflows/deploy-trackerrevo.yml
if git diff --staged --quiet 2>/dev/null; then
    echo "Nenhuma alteração para commitar."
else
    git commit -m "$MSG"
fi

# Push (dispara o deploy via GitHub Actions)
echo ""
echo "[Push] Enviando para origin/main..."
git push origin main

echo ""
echo "=========================================="
echo "✓ Push concluído!"
echo "  Deploy em andamento no GitHub Actions."
echo "  Acompanhe: https://github.com/victorcandido1/dashrevo/actions"
echo "  Após ~2–3 min: https://trackerrevo-xxx.run.app"
echo "=========================================="
