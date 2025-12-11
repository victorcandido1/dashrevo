# 🚀 Guia de Deploy - Dashboard REVO

Este guia explica como fazer deploy do dashboard no GitHub e torná-lo acessível online.

## 📋 Pré-requisitos

- Python 3.8 ou superior instalado
- Conta no GitHub
- Conta em um serviço de hospedagem (Railway, Render, Heroku, etc.)
- Git instalado

## 🔧 Passo 1: Preparar o Projeto

### 1.1 Executar Script de Preparação

```bash
cd flight_dashboard_web
python prepare_for_github.py
```

Este script irá:
- ✅ Verificar se o cache está presente
- ✅ Verificar estrutura de diretórios
- ✅ Verificar arquivos essenciais
- ✅ Criar arquivos de instruções

### 1.2 Verificar Cache

O cache deve estar em `.cache/processor_cache.pkl`. Se não estiver:

1. Execute o dashboard localmente: `python app.py`
2. Faça upload de um arquivo Excel através da interface
3. O cache será gerado automaticamente em `.cache/processor_cache.pkl`
4. Pare o servidor e verifique se o arquivo foi criado

### 1.3 Verificar .gitignore

O arquivo `.gitignore` deve permitir o cache mas ignorar uploads:

```gitignore
# Cache - NOTE: .cache/processor_cache.pkl should be committed
.cache/cache_metadata.json
.cache/*.tmp

# Uploads (não commitar)
uploads/
*.xlsx
*.xls
```

## 📤 Passo 2: Criar Repositório no GitHub

### 2.1 Criar Repositório

1. Acesse https://github.com
2. Clique em "New repository"
3. Nome: `dashrevo`
4. Descrição: "Dashboard de Analytics REVO - Flight Data Analysis"
5. Público ou Privado (sua escolha)
6. **NÃO** inicialize com README, .gitignore ou license
7. Clique em "Create repository"

### 2.2 Preparar Arquivos Localmente

```bash
# Navegue até o diretório do projeto
cd "G:\Meu Drive\Journey\Modelos\Revo\Manifestoss\analytics e kpi's\flight_dashboard_web"

# Inicialize git (se ainda não foi feito)
git init

# Adicione todos os arquivos (exceto os ignorados pelo .gitignore)
git add .

# Verifique o que será commitado (importante!)
git status

# Certifique-se de que .cache/processor_cache.pkl está incluído
# Se não estiver, verifique o .gitignore
```

### 2.3 Fazer Commit e Push

```bash
# Commit inicial
git commit -m "Initial commit: Dashboard REVO com cache pré-carregado"

# Adicione o repositório remoto (substitua SEU_USUARIO)
git remote add origin https://github.com/SEU_USUARIO/dashrevo.git

# Push para o GitHub
git branch -M main
git push -u origin main
```

## 🌐 Passo 3: Deploy em Serviço de Hospedagem

### Opção A: Railway (Recomendado - Mais Fácil)

1. Acesse https://railway.app
2. Faça login com GitHub
3. Clique em "New Project"
4. Selecione "Deploy from GitHub repo"
5. Escolha o repositório `dashrevo`
6. Railway detectará automaticamente Flask
7. O deploy começará automaticamente
8. Após o deploy, Railway fornecerá uma URL (ex: `dashrevo.railway.app`)

**Variáveis de Ambiente (Opcional)**:
- `SECRET_KEY`: Gere uma chave secreta aleatória para produção

### Opção B: Render

1. Acesse https://render.com
2. Faça login com GitHub
3. Clique em "New" > "Web Service"
4. Conecte o repositório `dashrevo`
5. Configure:
   - **Name**: `dashrevo` (ou outro nome)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
6. Clique em "Create Web Service"
7. Render fornecerá uma URL (ex: `dashrevo.onrender.com`)

### Opção C: Heroku

```bash
# Instale Heroku CLI primeiro
# https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Criar app
heroku create dashrevo

# Push para Heroku
git push heroku main

# Abrir app
heroku open
```

## ✅ Passo 4: Verificar Deploy

### 4.1 Verificar Cache

Acesse: `https://seu-app.com/api/cache/status`

Deve retornar:
```json
{
  "exists": true,
  "info": {
    "saved_at": "2025-01-XX...",
    "total_records": 1234,
    "filtered_records": 1234
  }
}
```

### 4.2 Verificar Dados

Acesse: `https://seu-app.com/api/data/status`

Deve retornar:
```json
{
  "loaded": true,
  "total_records": 1234,
  "filtered_records": 1234
}
```

### 4.3 Testar Interface

1. Acesse a URL do seu app
2. A interface de upload deve estar **oculta** (dados já carregados)
3. O dashboard deve mostrar dados imediatamente
4. Todas as abas devem funcionar

## 🔄 Atualizar Dados

Para atualizar os dados no futuro:

1. **Localmente**:
   ```bash
   python app.py
   # Faça upload de novo arquivo pela interface
   # O cache será atualizado automaticamente
   ```

2. **Commit novo cache**:
   ```bash
   git add .cache/processor_cache.pkl
   git commit -m "Atualizar cache com novos dados"
   git push origin main
   ```

3. **Serviço de hospedagem**:
   - Railway/Render: Deploy automático após push
   - Heroku: `git push heroku main`

## 🐛 Troubleshooting

### Cache não carrega

**Problema**: Dashboard mostra "Por favor, faça upload de um arquivo"

**Soluções**:
1. Verifique se `.cache/processor_cache.pkl` está no repositório:
   ```bash
   git ls-files | grep cache
   ```
2. Verifique permissões no servidor
3. Verifique logs do servidor para erros
4. Tente recarregar o cache manualmente acessando `/api/data/status`

### Erro ao iniciar

**Problema**: Aplicação não inicia

**Soluções**:
1. Verifique se todas as dependências estão em `requirements.txt`
2. Verifique logs de build no serviço de hospedagem
3. Verifique se Python 3.8+ está configurado
4. Verifique variáveis de ambiente

### Dados não aparecem

**Problema**: Dashboard carrega mas não mostra dados

**Soluções**:
1. Verifique console do navegador (F12) para erros JavaScript
2. Verifique se cache foi carregado: `/api/cache/status`
3. Verifique se dados estão carregados: `/api/data/status`
4. Verifique logs do servidor

## 📝 Notas Importantes

1. **Cache Pré-carregado**: O arquivo `.cache/processor_cache.pkl` é essencial.
   Sem ele, os usuários precisarão fazer upload de dados.

2. **Tamanho do Cache**: O cache pode ser grande (vários MB).
   GitHub permite arquivos até 100MB. Se for maior, considere usar Git LFS.

3. **Segurança**: 
   - Configure `SECRET_KEY` como variável de ambiente em produção
   - Não commite arquivos `.env` com credenciais
   - Use HTTPS sempre

4. **Performance**: 
   - O cache é carregado na primeira requisição
   - Pode levar alguns segundos na primeira vez
   - Após carregado, fica em memória

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs do servidor
2. Verifique o console do navegador (F12)
3. Verifique os endpoints da API manualmente
4. Consulte a documentação do serviço de hospedagem

