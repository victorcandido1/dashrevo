# 🖥️ Deploy Local - Usando sua Máquina como Servidor

Este guia explica como rodar o dashboard na sua máquina e torná-lo acessível online.

## 🚀 Opção 1: Usando ngrok (Recomendado - Mais Fácil)

### Passo 1: Instalar ngrok

1. Acesse: https://ngrok.com/download
2. Baixe o ngrok para Windows
3. Extraia o arquivo `ngrok.exe` em uma pasta (ex: `C:\ngrok\`)
4. (Opcional) Adicione ao PATH do Windows para usar de qualquer lugar

### Passo 2: Criar conta no ngrok (Gratuita)

1. Acesse: https://dashboard.ngrok.com/signup
2. Crie uma conta gratuita
3. Copie seu authtoken da página inicial

### Passo 3: Configurar ngrok

```powershell
# Execute uma vez para configurar seu token
ngrok config add-authtoken SEU_TOKEN_AQUI
```

### Passo 4: Iniciar o Dashboard

Abra **dois** terminais PowerShell:

**Terminal 1 - Dashboard:**
```powershell
cd "G:\Meu Drive\Journey\Modelos\Revo\Manifestoss\analytics e kpi's\flight_dashboard_web"
python app.py
```

**Terminal 2 - ngrok:**
```powershell
ngrok http 5000
```

### Passo 5: Acessar Online

O ngrok mostrará uma URL como:
```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:5000
```

Use essa URL para acessar o dashboard de qualquer lugar!

**Nota**: A URL do ngrok muda a cada vez que você reinicia (na versão gratuita). Para URL fixa, use a versão paga.

---

## 🌐 Opção 2: Expor Diretamente na Rede Local

### Passo 1: Descobrir seu IP Local

```powershell
ipconfig
```

Procure por "IPv4 Address" (ex: `192.168.1.100`)

### Passo 2: Configurar Firewall

```powershell
# Permitir porta 5000 no firewall do Windows
New-NetFirewallRule -DisplayName "Flask Dashboard" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

### Passo 3: Iniciar o Dashboard

```powershell
python app.py
```

### Passo 4: Acessar

- **Na sua rede local**: `http://SEU_IP:5000` (ex: `http://192.168.1.100:5000`)
- **De outros dispositivos na mesma rede**: Use o mesmo IP

**Limitação**: Só funciona na mesma rede Wi-Fi/Ethernet.

---

## 🔒 Opção 3: Expor na Internet (Avançado)

### Requisitos

1. IP Público fixo (ou serviço de DNS dinâmico)
2. Port forwarding configurado no roteador
3. Firewall configurado

### Passo 1: Configurar Port Forwarding no Roteador

1. Acesse o painel do roteador (geralmente `192.168.1.1` ou `192.168.0.1`)
2. Vá em "Port Forwarding" ou "Virtual Server"
3. Configure:
   - **Porta Externa**: 5000 (ou outra)
   - **Porta Interna**: 5000
   - **IP Interno**: IP da sua máquina (ex: `192.168.1.100`)
   - **Protocolo**: TCP

### Passo 2: Descobrir IP Público

```powershell
# Execute no PowerShell
Invoke-RestMethod -Uri "https://api.ipify.org?format=json"
```

### Passo 3: Iniciar Dashboard

```powershell
python app.py
```

### Passo 4: Acessar

Use: `http://SEU_IP_PUBLICO:5000`

**⚠️ AVISO**: Expor diretamente na internet pode ser um risco de segurança. Use apenas em redes confiáveis ou com autenticação.

---

## 🛠️ Scripts Automatizados

Use os scripts criados para facilitar:

### Iniciar com ngrok (Automático)

```powershell
.\start_with_ngrok.ps1
```

### Iniciar normalmente

```powershell
.\run.ps1
# ou
python app.py
```

---

## ✅ Verificações

### Dashboard está rodando?

Acesse: `http://localhost:5000`

Deve mostrar o dashboard.

### Cache carregado?

Acesse: `http://localhost:5000/api/cache/status`

Deve retornar: `{"exists": true}` (se você já fez upload antes)

### Acessível externamente?

- **ngrok**: Use a URL fornecida pelo ngrok
- **Rede local**: Use `http://SEU_IP:5000` de outro dispositivo na mesma rede
- **Internet**: Use `http://SEU_IP_PUBLICO:5000`

---

## 🔧 Troubleshooting

### Porta 5000 já em uso?

Altere a porta no `app.py`:
```python
port = int(os.environ.get('PORT', 8080))  # Mude para 8080
```

E no ngrok:
```powershell
ngrok http 8080
```

### Firewall bloqueando?

```powershell
# Permitir porta no firewall
New-NetFirewallRule -DisplayName "Flask Dashboard" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

### ngrok não funciona?

1. Verifique se está autenticado: `ngrok config check`
2. Verifique se o dashboard está rodando na porta correta
3. Tente reiniciar o ngrok

### Não acessa de outros dispositivos?

1. Verifique se estão na mesma rede
2. Verifique o firewall do Windows
3. Verifique se o IP está correto

---

## 📝 Notas Importantes

1. **Sua máquina precisa estar ligada** para o dashboard estar acessível
2. **ngrok gratuito** tem limitações (URL muda, pode ter limites de tráfego)
3. **Segurança**: Considere adicionar autenticação se expor publicamente
4. **Performance**: Depende da sua conexão de internet

---

## 🎯 Recomendação

Para uso rápido e fácil: **Use ngrok** (Opção 1)
Para uso permanente: **Use Railway/Render** (deploy na nuvem)

