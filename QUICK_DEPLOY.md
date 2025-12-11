# 🚀 Deploy Rápido - Dashboard REVO

Guia rápido para fazer deploy do dashboard no GitHub e torná-lo acessível online.

## ⚡ Passos Rápidos

### 1. Preparar Localmente

```bash
cd flight_dashboard_web
python prepare_for_github.py
```

Ou no PowerShell:
```powershell
.\prepare_deploy.ps1
```

### 2. Verificar Cache

Certifique-se de que `.cache/processor_cache.pkl` existe. Se não existir:

1. Execute: `python app.py`
2. Faça upload de um arquivo Excel
3. O cache será gerado automaticamente

### 3. Criar Repositório no GitHub

1. Acesse https://github.com/new
2. Nome: `dashrevo`
3. **NÃO** marque "Initialize with README"
4. Clique em "Create repository"

### 4. Fazer Push

```bash
# Se ainda não inicializou Git
git init

# Adicionar arquivos
git add .

# Verificar se cache está incluído
git status | grep cache

# Commit
git commit -m "Initial commit: Dashboard REVO"

# Adicionar remote (substitua SEU_USUARIO)
git remote add origin https://github.com/SEU_USUARIO/dashrevo.git

# Push
git branch -M main
git push -u origin main
```

### 5. Deploy no Railway (Mais Fácil)

1. Acesse https://railway.app
2. Login com GitHub
3. "New Project" > "Deploy from GitHub repo"
4. Selecione `dashrevo`
5. Pronto! Railway faz o resto automaticamente

### 6. Verificar

Acesse a URL fornecida pelo Railway. O dashboard deve:
- ✅ Carregar automaticamente (sem necessidade de upload)
- ✅ Mostrar dados imediatamente
- ✅ Ter interface de upload oculta

## 🔍 Verificações

### Cache carregado?
```
https://seu-app.railway.app/api/cache/status
```
Deve retornar: `{"exists": true}`

### Dados carregados?
```
https://seu-app.railway.app/api/data/status
```
Deve retornar: `{"loaded": true}`

## ⚠️ Problemas Comuns

**Cache não carrega?**
- Verifique se `.cache/processor_cache.pkl` está no repositório
- Verifique logs do Railway

**Erro ao iniciar?**
- Verifique se `requirements.txt` está completo
- Verifique logs de build no Railway

## 📚 Documentação Completa

Para instruções detalhadas, consulte:
- `DEPLOY.md` - Guia completo de deploy
- `README.md` - Documentação geral
- `DEPLOY_INSTRUCTIONS.md` - Instruções técnicas

