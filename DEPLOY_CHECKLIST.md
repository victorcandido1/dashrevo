# Checklist para Deploy

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
