# Trackerrevo - Google Cloud Run
# Radar de aeronaves em tempo real (região São Paulo)
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run sets PORT env (default 8080)
ENV PORT=8080
EXPOSE 8080

# Diretórios para cache de movimento e uploads
RUN mkdir -p .cache uploads

CMD exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
