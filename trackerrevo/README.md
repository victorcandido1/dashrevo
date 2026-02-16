# TrackRevo - Radar de Aeronaves e Dashboard

Aplicação Flask que combina **rastreamento de aeronaves em tempo real** (região de São Paulo) com **dashboard de dados de voos** (upload de Excel).

## Funcionalidades

- **Radar ao vivo**: Mapa com aeronaves em tempo real via OpenSky Network API
- **Rastreamento**: PR-OMB, PR-OMH, PR-OOE com notificações de decolagem/pouso
- **Dashboard**: Upload de Excel, KPIs, gráficos, filtros

## Instalação

```bash
cd trackerrevo
pip install -r requirements.txt
```

## Executar

```bash
cd trackerrevo
python app.py
```

Ou com porta customizada:
```bash
PORT=5050 python app.py
```

**Nota**: No macOS, a porta 5050 é usada por padrão para evitar conflito com o AirPlay Receiver (que usa 5000).

## URLs

- **Dashboard**: http://localhost:5050/
- **Radar ao vivo**: http://localhost:5050/tracker

## Estrutura

```
trackerrevo/
├── app.py              # Entrada principal Flask
├── config.py           # Configuração
├── data_processor.py   # Processamento de dados Excel
├── requirements.txt
├── Procfile            # Para deploy (Heroku, etc)
├── routes/             # API e rotas
│   ├── api.py          # Endpoints do dashboard
│   ├── tracker.py      # Endpoints do radar
│   ├── upload.py       # Upload de arquivos
│   └── ...
├── services/
│   ├── opensky_service.py    # API OpenSky (aeronaves)
│   ├── distance_calculator.py # Cálculo de distâncias
│   └── ...
├── static/             # CSS, JS, Leaflet
├── templates/          # HTML
└── uploads/            # Arquivos enviados (criado automaticamente)
```
