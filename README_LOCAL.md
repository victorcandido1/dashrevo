# 🖥️ Guia Rápido - Deploy Local

## 🚀 Início Rápido

### Opção 1: Com ngrok (Acesso de qualquer lugar)

```powershell
.\start_with_ngrok.ps1
```

Isso irá:
- ✅ Iniciar o dashboard
- ✅ Iniciar ngrok automaticamente
- ✅ Fornecer URL pública

### Opção 2: Rede Local (Apenas mesma rede Wi-Fi)

```powershell
.\start_local_server.ps1
```

Isso irá:
- ✅ Iniciar o dashboard
- ✅ Configurar firewall
- ✅ Mostrar IP para acesso na rede

### Opção 3: Apenas Local (localhost)

```powershell
python app.py
```

Acesse: `http://localhost:5000`

---

## 📋 Pré-requisitos

### Para ngrok:
1. Baixe: https://ngrok.com/download
2. Crie conta: https://dashboard.ngrok.com/signup
3. Configure: `ngrok config add-authtoken SEU_TOKEN`

### Para rede local:
- Nenhum pré-requisito adicional

---

## 🔗 URLs de Acesso

### Local
- `http://localhost:5000`

### Rede Local
- `http://SEU_IP:5000` (mostrado ao iniciar)

### Internet (ngrok)
- URL fornecida pelo ngrok (ex: `https://abc123.ngrok-free.app`)

---

## ⚙️ Configurações

### Mudar Porta

Edite `app.py`:
```python
port = int(os.environ.get('PORT', 8080))  # Mude aqui
```

Ou defina variável de ambiente:
```powershell
$env:PORT = "8080"
python app.py
```

---

## 🛑 Parar o Servidor

- Pressione `Ctrl+C` no terminal
- Se usar ngrok, feche também a janela do ngrok

---

## 📚 Documentação Completa

Veja `DEPLOY_LOCAL.md` para instruções detalhadas.

