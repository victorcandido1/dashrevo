# Flight Dashboard Web Application - REVO Analytics

Interactive HTML dashboard for flight data analysis, migrated from Tkinter desktop application.

## 🚀 Características Principais

- **Dados Pré-carregados**: Dashboard funciona sem necessidade de upload - dados já estão em cache
- **Interface Limpa**: Upload oculto quando dados já estão carregados - foco na visualização
- **Excel File Upload**: Opção de upload e processamento de dados de arquivos Excel (quando necessário)
- **Interactive Dashboard**: KPIs e gráficos em tempo real usando Plotly.js
- **Advanced Filtering**: Filtros por tipo de voo, aeronave, rotas, datas e mais
- **14 Consolidated Tabs**: Reduzido de 22 abas originais (36% de redução)
  - Dashboard (Summary + Statistics)
  - Filters
  - Time Analysis (Weekday/Weekend + Seasonality + Hours)
  - Fleet Analysis (Aircraft + Idle Analysis)
  - Route Analysis
  - Shuttle Deep Dive
  - KPI Dashboard (KPI + Gregorio's KPI + Passenger Revenue)
  - Profit Center (Profit + Costs)
  - Load Factor
  - Non-Revenue (Empty/Hangar)
  - Manifesto (12 sub-tabs)
  - Salesforce Dashboard
  - Export
  - Logs

## 📦 Instalação

1. Instale as dependências Python:
```bash
pip install -r requirements.txt
```

2. Os diretórios necessários são criados automaticamente:
- `uploads/` - Para arquivos Excel enviados por usuários
- `.cache/` - Para dados em cache (já pré-carregado)

### Integração com Revo Bot (movimentação de aeronaves)

Para enviar mensagens automáticas ao Revo Bot quando houver movimentação de aeronaves:

```bash
export REVO_BOT_WEBHOOK_URL="https://seu-endpoint-do-bot"
export REVO_BOT_TOKEN="opcional"
export REVO_BOT_ENABLED="true"
```

Variáveis opcionais:
- `REVO_BOT_TIMEOUT_SECONDS` (padrão: `10`)
- `REVO_BOT_MAX_MOVES_PER_RUN` (padrão: `200`)
- `REVO_BOT_STATE_FILE` (padrão: `.cache/revo_bot_sent_moves.json`)

O sistema evita reenvio duplicado de movimentos já notificados, usando arquivo de estado em cache.

## 🏃 Executando Localmente

```bash
python app.py
```

A aplicação estará disponível em `http://localhost:5000`

**Nota**: Se o cache estiver presente (`.cache/processor_cache.pkl`), os dados serão carregados automaticamente e a interface de upload ficará oculta.

## External Access (ngrok)

To allow others to access your local server:

1. Install ngrok: https://ngrok.com/download
2. Run the Flask app: `python app.py`
3. In another terminal, run: `ngrok http 5000`
4. Share the ngrok URL (e.g., `https://abc123.ngrok.io`)

## ☁️ Deploy em Nuvem

### Preparação para GitHub

Antes de fazer deploy, execute o script de preparação:

```bash
python prepare_for_github.py
```

Este script verifica se todos os arquivos necessários estão presentes, incluindo o cache pré-carregado.

### Railway
1. Crie uma conta em https://railway.app
2. Conecte seu repositório GitHub (`dashrevo`)
3. Railway detectará automaticamente Flask e fará o deploy
4. O cache será carregado automaticamente na primeira requisição

### Render
1. Crie uma conta em https://render.com
2. Crie um novo Web Service
3. Conecte o repositório GitHub
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
5. O cache será carregado automaticamente

### Verificar Cache Após Deploy

Após o deploy, verifique se o cache foi carregado:
- Acesse: `https://seu-app.com/api/cache/status`
- Deve retornar `{"exists": true}`

**Importante**: O arquivo `.cache/processor_cache.pkl` deve estar no repositório para que o dashboard funcione sem upload.

## Project Structure

```
flight_dashboard_web/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── data_processor.py     # Core data processing logic
├── requirements.txt      # Python dependencies
├── routes/
│   ├── api.py           # REST API endpoints
│   └── upload.py        # File upload handling
├── services/            # Analysis services (to be implemented)
├── static/
│   ├── css/            # Stylesheets
│   └── js/             # JavaScript files
├── templates/          # HTML templates
│   ├── base.html      # Base template
│   └── index.html     # Main dashboard
└── utils/             # Utility modules
    └── icao_mapping.py # ICAO code mappings
```

## API Endpoints

- `GET /api/data/status` - Check if data is loaded
- `POST /api/upload` - Upload Excel file
- `GET /api/dashboard/summary` - Get dashboard KPIs
- `GET /api/charts/monthly-revenue` - Monthly revenue data
- `GET /api/charts/flight-types` - Flight type distribution
- `GET /api/charts/aircraft-usage` - Aircraft usage data
- `GET /api/filters/options` - Get filter options
- `POST /api/filters/apply` - Apply filters

## Development Status

✅ Core structure and file upload
✅ Basic dashboard with KPIs
✅ Data processing pipeline
🔄 Filter system (in progress)
🔄 All analysis tabs (in progress)
⏳ Manifesto integration
⏳ Salesforce integration

## Notes

- Data is filtered to 2025 by default
- Excel files should follow the naming convention: `Model - Prefix - Month-Year`
- The application processes multiple sheets from a single Excel file










