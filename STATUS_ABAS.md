# Status das Abas e Sub-Abas do Dashboard

## 📊 Estrutura Completa de Abas (14 abas principais)

### 1. **Dashboard** 📊
- **Status**: ✅ Definida
- **Sub-abas**: Nenhuma
- **Funcionalidade**: Dashboard geral com KPIs e gráficos

### 2. **Filtros** 🔍
- **Status**: ✅ Definida
- **Sub-abas**: Nenhuma
- **Funcionalidade**: Filtros de dados (tipo de voo, aeronave, mês, etc.)

### 3. **Custos** 💵
- **Status**: ✅ Definida
- **Sub-abas**: Nenhuma
- **Funcionalidade**: Configuração de custos por aeronave

### 4. **Temporal** ⏰
- **Status**: ✅ Definida
- **Sub-abas**: 4 sub-abas
  - 📅 Dias da Semana (`timeSubTab = 'weekday'`)
  - 📊 Mensal (`timeSubTab = 'monthly'`)
  - 🌡️ Sazonalidade (`timeSubTab = 'seasonality'`)
  - ⏰ Por Hora (`timeSubTab = 'hourly'`)
- **Funcionalidade**: Análise temporal e sazonalidade

### 5. **Frota** ✈️
- **Status**: ✅ Definida
- **Sub-abas**: Nenhuma
- **Funcionalidade**: Análise de frota e ociosidade

### 6. **Rotas** 🗺️
- **Status**: ✅ Definida
- **Sub-abas**: Nenhuma
- **Funcionalidade**: Análise de rotas

### 7. **Shuttle** 🚁
- **Status**: ✅ Definida
- **Sub-abas**: Nenhuma
- **Funcionalidade**: Shuttle Deep Dive

### 8. **KPIs** 📈
- **Status**: ✅ Definida
- **Sub-abas**: 3 sub-abas
  - 📊 KPI Geral (`kpiSubTab = 'general'`)
  - 📈 Gregorio's KPI (`kpiSubTab = 'gregorio'`)
  - 👥 Passenger Revenue (`kpiSubTab = 'passenger'`)
- **Funcionalidade**: Dashboard de KPIs
- **Endpoints API**:
  - `/api/kpis/all` ✅
  - `/api/kpis/cards` ✅
  - `/api/kpis/revenue` ✅
  - `/api/kpis/efficiency` ✅
  - `/api/kpis/profitability` ✅
  - `/api/kpis/by-category` ✅
  - `/api/kpis/by-aircraft` ✅
  - `/api/kpis/trends` ✅
- **Funções JavaScript**:
  - `loadKPISubTab()` ✅
  - `loadKPIDashboard()` ✅
  - `loadGregorioKPIs()` ✅
  - `loadPassengerRevenue()` ✅

### 9. **Lucro** 💰
- **Status**: ✅ Definida
- **Sub-abas**: Nenhuma
- **Funcionalidade**: Centro de lucro

### 10. **Load Factor** 📊
- **Status**: ✅ Definida
- **Sub-abas**: Nenhuma (mas tem categorias: all, shuttle, charter)
- **Funcionalidade**: Análise de ocupação

### 11. **Não-Receita** 🔄
- **Status**: ✅ Definida
- **Sub-abas**: Nenhuma
- **Funcionalidade**: Voos não-receita (empty legs, hangar flights)

### 12. **Manifesto** 📋
- **Status**: ✅ Definida
- **Sub-abas**: 7 sub-abas
  - 📁 Upload (`manifestoSubTab = 'upload'`)
  - 📊 Visão Geral (`manifestoSubTab = 'overview'`)
  - 👥 Passageiros Recorrentes (`manifestoSubTab = 'recurring'`)
  - ⭐ VIP (`manifestoSubTab = 'vip'`)
  - 🗺️ Rotas (`manifestoSubTab = 'routes'`)
  - 📅 Temporal (`manifestoSubTab = 'temporal'`)
  - 🆕 Novos Clientes (`manifestoSubTab = 'newcustomers'`)
- **Funcionalidade**: Manifesto de passageiros

### 13. **Salesforce** ☁️
- **Status**: ✅ Definida
- **Sub-abas**: Múltiplas (definidas em `salesforceSubTab`)
- **Funcionalidade**: Integração com Salesforce

### 14. **Exportar** 📤
- **Status**: ✅ Definida
- **Sub-abas**: Nenhuma
- **Funcionalidade**: Exportação de dados

### 15. **Logs** 📋
- **Status**: ✅ Definida
- **Sub-abas**: Nenhuma
- **Funcionalidade**: Logs do sistema

---

## ✅ Resumo

- **Total de abas principais**: 14
- **Abas com sub-abas**: 4
  - Temporal (4 sub-abas)
  - KPIs (3 sub-abas)
  - Manifesto (7 sub-abas)
  - Salesforce (múltiplas sub-abas)
- **Status geral**: ✅ Todas as abas estão definidas

---

## 🔍 Verificação da Aba KPI

### Sub-abas do KPI:
1. **KPI Geral** (`general`)
   - Cards de KPIs detalhados
   - Gráficos de receita por categoria e margem por aeronave
   - Endpoints: `/api/kpis/cards`, `/api/kpis/by-category`, `/api/kpis/by-aircraft`
   - Função: `loadKPIDashboard()`

2. **Gregorio's KPI** (`gregorio`)
   - KPIs específicos do Gregorio
   - Gráficos de tendência de receita e receita por aeronave
   - Endpoint: `/api/kpis/all`
   - Função: `loadGregorioKPIs()`

3. **Passenger Revenue** (`passenger`)
   - KPIs de receita por passageiro
   - Gráficos de passageiros por mês
   - Endpoint: `/api/kpis/all`
   - Função: `loadPassengerRevenue()`

### Status dos Endpoints:
- ✅ Todos os 8 endpoints de KPI estão definidos em `routes/api.py`
- ✅ Todas as 3 funções JavaScript estão implementadas
- ✅ A estrutura HTML está completa com os 3 sub-tabs

### Possíveis Problemas:
- ⚠️ Verificar se `KPICalculator` está funcionando corretamente
- ⚠️ Verificar se os dados estão sendo carregados corretamente
- ⚠️ Verificar se os gráficos Plotly estão sendo renderizados

---

## 📅 Restauração de Arquivos

**Nota**: Não há repositório Git configurado no projeto. Para restaurar arquivos de ontem às 20:00, seria necessário:

1. **Backups locais**: Verificar se há arquivos `.backup` ou cópias na pasta `new_dashboard`
2. **Histórico do Windows**: Usar o histórico de arquivos do Windows (se habilitado)
3. **Backup manual**: Se você tiver um backup manual, podemos restaurar a partir dele

**Arquivos que podem precisar de restauração**:
- `routes/api.py` (já foi restaurado recentemente)
- `templates/index.html` (já foi restaurado recentemente)
- `data_processor.py`
- `services/kpi_calculator.py`
- Outros arquivos que possam ter sido modificados

