"""
Script para preparar o projeto para upload no GitHub
Este script prepara os arquivos necessários e garante que o cache esteja incluído
"""
import os
import shutil
from pathlib import Path
import json

def main():
    base_dir = Path(__file__).parent
    cache_dir = base_dir / '.cache'
    
    print("="*60)
    print("Preparando projeto para GitHub")
    print("="*60)
    
    # 1. Verificar se o cache existe
    cache_file = cache_dir / 'processor_cache.pkl'
    if not cache_file.exists():
        print("⚠️  AVISO: Cache não encontrado!")
        print(f"   Arquivo esperado: {cache_file}")
        print("   O dashboard funcionará, mas será necessário fazer upload de dados.")
        print()
    else:
        cache_size = cache_file.stat().st_size / (1024 * 1024)  # MB
        print(f"✓ Cache encontrado: {cache_size:.2f} MB")
        print()
    
    # 2. Verificar estrutura de diretórios
    required_dirs = [
        'routes',
        'services',
        'static',
        'templates',
        'utils',
        '.cache'
    ]
    
    print("Verificando estrutura de diretórios:")
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            print(f"  ✓ {dir_name}/")
        else:
            print(f"  ✗ {dir_name}/ (FALTANDO)")
    
    print()
    
    # 3. Verificar arquivos essenciais
    required_files = [
        'app.py',
        'config.py',
        'data_processor.py',
        'requirements.txt',
        'README.md',
        '.gitignore'
    ]
    
    print("Verificando arquivos essenciais:")
    for file_name in required_files:
        file_path = base_dir / file_name
        if file_path.exists():
            print(f"  ✓ {file_name}")
        else:
            print(f"  ✗ {file_name} (FALTANDO)")
    
    print()
    
    # 4. Criar arquivo de instruções de deploy
    deploy_instructions = """# Instruções de Deploy - Dashboard REVO

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
"""
    
    deploy_file = base_dir / 'DEPLOY_INSTRUCTIONS.md'
    with open(deploy_file, 'w', encoding='utf-8') as f:
        f.write(deploy_instructions)
    
    print(f"✓ Arquivo de instruções criado: {deploy_file.name}")
    print()
    
    # 5. Criar checklist
    checklist = """# Checklist para Deploy

## Antes de Fazer Push

- [ ] Cache foi gerado e está em `.cache/processor_cache.pkl`
- [ ] Todos os arquivos necessários estão presentes
- [ ] `requirements.txt` está atualizado
- [ ] `.gitignore` está configurado corretamente
- [ ] README.md está atualizado
- [ ] Testado localmente

## Arquivos que DEVEM estar no repositório

- [ ] `.cache/processor_cache.pkl` (cache pré-carregado)
- [ ] Todos os arquivos Python (`.py`)
- [ ] `requirements.txt`
- [ ] `README.md`
- [ ] Templates HTML
- [ ] Arquivos estáticos (CSS, JS)
- [ ] `.gitignore`

## Arquivos que NÃO devem estar no repositório

- [ ] `uploads/` (pasta de uploads de usuários)
- [ ] `__pycache__/` (arquivos Python compilados)
- [ ] `.env` (variáveis de ambiente)
- [ ] Arquivos `.xlsx` ou `.xls` (exceto exemplos)
- [ ] Logs (`.log`)

## Após o Deploy

- [ ] Aplicação está acessível online
- [ ] Cache foi carregado automaticamente
- [ ] Dashboard mostra dados sem necessidade de upload
- [ ] Todas as abas funcionam corretamente
- [ ] Filtros funcionam
- [ ] Gráficos são exibidos corretamente
"""
    
    checklist_file = base_dir / 'DEPLOY_CHECKLIST.md'
    with open(checklist_file, 'w', encoding='utf-8') as f:
        f.write(checklist)
    
    print(f"✓ Checklist criado: {checklist_file.name}")
    print()
    
    print("="*60)
    print("Preparação concluída!")
    print("="*60)
    print()
    print("Próximos passos:")
    print("1. Verifique se o cache está presente: .cache/processor_cache.pkl")
    print("2. Revise o .gitignore para garantir que o cache será incluído")
    print("3. Leia DEPLOY_INSTRUCTIONS.md para instruções de deploy")
    print("4. Use DEPLOY_CHECKLIST.md como checklist")
    print("5. Faça commit e push para o GitHub")
    print()

if __name__ == '__main__':
    main()

