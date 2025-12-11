# Instruções de Deploy - Dashboard REVO

## Pré-requisitos

1. Python 3.8 ou superior
2. Conta no GitHub
3. Conta em um serviço de hospedagem (Railway, Render, Heroku, etc.)

## Passos para Deploy

### 1. Preparar o Repositório

```bash
# Clone ou crie o repositório
git clone https://github.com/seu-usuario/dashrevo.git
cd dashrevo

# Copie os arquivos do dashboard
cp -r flight_dashboard_web/* .

# Commit e push
git add .
git commit -m "Initial commit: Dashboard REVO com cache pré-carregado"
git push origin main
```

### 2. Deploy no Railway

1. Acesse https://railway.app
2. Clique em "New Project" > "Deploy from GitHub repo"
3. Selecione o repositório `dashrevo`
4. Railway detectará automaticamente Flask
5. Configure variáveis de ambiente (se necessário):
   - `SECRET_KEY`: Gere uma chave secreta aleatória
6. O deploy será automático

### 3. Deploy no Render

1. Acesse https://render.com
2. Clique em "New" > "Web Service"
3. Conecte seu repositório GitHub
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Environment**: Python 3
5. Clique em "Create Web Service"

### 4. Deploy no Heroku

1. Instale Heroku CLI
2. Execute:
```bash
heroku create dashrevo
git push heroku main
```

### 5. Verificar Cache

Após o deploy, verifique se o cache foi carregado:
- Acesse: `https://seu-app.com/api/cache/status`
- Deve retornar `{"exists": true}`

## Estrutura de Arquivos Importantes

- `.cache/processor_cache.pkl` - **DEVE estar no repositório** (dados pré-carregados)
- `uploads/` - **NÃO deve estar no repositório** (arquivos de usuários)
- `.cache/cache_metadata.json` - Opcional (pode ser ignorado)

## Notas Importantes

1. **Cache Pré-carregado**: O arquivo `.cache/processor_cache.pkl` contém os dados processados.
   Este arquivo deve estar no repositório para que o dashboard funcione sem upload.

2. **Upload Desabilitado**: A interface de upload está oculta quando os dados já estão carregados.
   Os usuários verão apenas a visualização dos dados.

3. **Atualização de Dados**: Para atualizar os dados:
   - Faça upload de um novo arquivo localmente
   - O cache será atualizado automaticamente
   - Commit o novo arquivo `.cache/processor_cache.pkl`
   - Faça push para o repositório

4. **Segurança**: 
   - Configure `SECRET_KEY` como variável de ambiente em produção
   - Não commite arquivos `.env` com credenciais

## Troubleshooting

### Cache não carrega
- Verifique se `.cache/processor_cache.pkl` existe no repositório
- Verifique permissões de leitura no servidor
- Verifique logs do servidor para erros

### Erro ao iniciar
- Verifique se todas as dependências estão em `requirements.txt`
- Verifique se Python 3.8+ está instalado
- Verifique logs de erro do servidor

### Dados não aparecem
- Verifique se o cache foi carregado: `/api/cache/status`
- Verifique se os dados estão carregados: `/api/data/status`
- Verifique console do navegador para erros JavaScript
