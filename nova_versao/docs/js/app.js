/**
 * REVO Flight Analytics - Public Dashboard
 * This is a static version that reads from JSON files instead of API
 */

function publicDashboard() {
    return {
        // State
        loading: true,
        error: null,
        activeTab: 'dashboard',
        timeSubTab: 'monthly',
        commercialFilter: 'all',
        
        // Data
        metadata: null,
        flights: [],
        filteredFlights: [],
        kpis: null,
        filters: null,
        charts: null,
        costs: null,
        
        // Tabs configuration (subset of admin tabs)
        tabs: [
            { id: 'dashboard', name: 'Dashboard', icon: '📊' },
            { id: 'time', name: 'Temporal', icon: '⏰' },
            { id: 'fleet', name: 'Frota', icon: '✈️' },
            { id: 'routes', name: 'Rotas', icon: '🗺️' },
            { id: 'kpi', name: 'KPIs', icon: '📈' }
        ],
        
        async init() {
            try {
                this.loading = true;
                
                // Load all JSON data files
                const [metadataRes, flightsRes, kpisRes, filtersRes, chartsRes] = await Promise.all([
                    fetch('data/metadata.json'),
                    fetch('data/flights.json'),
                    fetch('data/kpis.json'),
                    fetch('data/filters.json'),
                    fetch('data/charts.json')
                ]);
                
                // Check for errors
                if (!metadataRes.ok) throw new Error('Dados não encontrados. A versão pública ainda não foi gerada.');
                
                this.metadata = await metadataRes.json();
                this.flights = await flightsRes.json();
                this.kpis = await kpisRes.json();
                this.filters = await filtersRes.json();
                this.charts = await chartsRes.json();
                
                // Apply initial filter
                this.applyFilter();
                
                // Load initial dashboard
                this.loadDashboard();
                
                this.loading = false;
            } catch (e) {
                this.error = e.message;
                this.loading = false;
                console.error('Error loading data:', e);
            }
        },
        
        applyFilter() {
            if (this.commercialFilter === 'all') {
                this.filteredFlights = this.flights;
            } else if (this.commercialFilter === 'commercial') {
                this.filteredFlights = this.flights.filter(f => f.Is_Commercial === true);
            } else {
                this.filteredFlights = this.flights.filter(f => f.Is_Commercial === false);
            }
        },
        
        setCommercialFilter(filter) {
            this.commercialFilter = filter;
            this.applyFilter();
            this.loadTabData(this.activeTab);
        },
        
        loadTabData(tabId) {
            switch(tabId) {
                case 'dashboard':
                    this.loadDashboard();
                    break;
                case 'time':
                    this.loadTimeData();
                    break;
                case 'fleet':
                    this.loadFleetData();
                    break;
                case 'routes':
                    this.loadRoutesData();
                    break;
                case 'kpi':
                    this.loadKPIData();
                    break;
            }
        },
        
        loadDashboard() {
            // Category distribution chart
            const categories = this.groupBy(this.filteredFlights, 'Flight_Category');
            const catLabels = Object.keys(categories);
            const catValues = catLabels.map(c => categories[c].length);
            
            Plotly.newPlot('category-chart', [{
                labels: catLabels,
                values: catValues,
                type: 'pie',
                marker: { colors: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'] }
            }], {
                title: 'Distribuição por Categoria',
                margin: { t: 40, b: 20, l: 20, r: 20 }
            }, { responsive: true });
            
            // Monthly trends from pre-computed data
            if (this.charts?.monthly_trends) {
                const trends = this.charts.monthly_trends;
                Plotly.newPlot('monthly-chart', [
                    { 
                        x: trends.map(t => t.month_name), 
                        y: trends.map(t => t.flights), 
                        name: 'Voos', 
                        type: 'bar', 
                        marker: { color: '#3b82f6' },
                        text: trends.map(t => `${t.hours.toFixed(0)}h`),
                        textposition: 'outside'
                    },
                    { 
                        x: trends.map(t => t.month_name), 
                        y: trends.map(t => t.revenue / 1000), 
                        name: 'Receita (mil)', 
                        type: 'scatter', 
                        mode: 'lines+markers', 
                        yaxis: 'y2', 
                        marker: { color: '#10b981' }
                    }
                ], {
                    title: 'Tendência Mensal',
                    yaxis: { title: 'Voos' },
                    yaxis2: { title: 'Receita (mil R$)', overlaying: 'y', side: 'right' },
                    margin: { t: 40, b: 40, l: 60, r: 60 },
                    legend: { orientation: 'h', y: -0.15 }
                }, { responsive: true });
            }
        },
        
        loadTimeData() {
            const df = this.filteredFlights;
            
            if (this.timeSubTab === 'monthly') {
                // Monthly breakdown
                const monthly = this.groupBy(df, 'Sheet_Month');
                const monthNames = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
                const months = Object.keys(monthly).filter(m => m && m !== 'null').sort((a, b) => parseInt(a) - parseInt(b));
                
                Plotly.newPlot('time-chart', [{
                    x: months.map(m => monthNames[parseInt(m) - 1] || m),
                    y: months.map(m => monthly[m].length),
                    type: 'bar',
                    marker: { color: '#3b82f6' },
                    text: months.map(m => {
                        const hours = monthly[m].reduce((sum, f) => sum + (f.Flight_Time_Hours || 0), 0);
                        return `${hours.toFixed(0)}h`;
                    }),
                    textposition: 'outside'
                }], {
                    title: 'Voos por Mês (horas voadas em cima)',
                    yaxis: { title: 'Voos' },
                    margin: { t: 60, b: 40, l: 60, r: 20 }
                }, { responsive: true });
                
                // Stats
                const totalFlights = df.length;
                const totalRevenue = df.reduce((sum, f) => sum + (f.Revenue || 0), 0);
                const totalHours = df.reduce((sum, f) => sum + (f.Flight_Time_Hours || 0), 0);
                
                document.getElementById('time-stats').innerHTML = `
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div class="bg-gray-100 p-4 rounded-lg">
                            <h4 class="text-sm font-semibold text-gray-600 mb-2">📊 Totais</h4>
                            <div class="text-sm">
                                <div>Voos: <strong>${totalFlights.toLocaleString()}</strong></div>
                                <div>Horas: <strong>${totalHours.toFixed(0)}h</strong></div>
                            </div>
                        </div>
                        <div class="bg-gray-100 p-4 rounded-lg">
                            <h4 class="text-sm font-semibold text-gray-600 mb-2">💰 Receita</h4>
                            <div class="text-xl font-bold text-green-600">R$ ${(totalRevenue/1000).toFixed(0)}k</div>
                        </div>
                        <div class="bg-gray-100 p-4 rounded-lg">
                            <h4 class="text-sm font-semibold text-gray-600 mb-2">📈 Média Mensal</h4>
                            <div class="text-sm">
                                <div>Voos: <strong>${(totalFlights / months.length).toFixed(0)}</strong></div>
                                <div>Horas: <strong>${(totalHours / months.length).toFixed(0)}h</strong></div>
                            </div>
                        </div>
                        <div class="bg-gray-100 p-4 rounded-lg">
                            <h4 class="text-sm font-semibold text-gray-600 mb-2">⏱️ Métricas</h4>
                            <div class="text-sm">
                                <div>Receita/Voo: <strong>R$ ${(totalRevenue / totalFlights).toFixed(0)}</strong></div>
                                <div>Receita/Hora: <strong>R$ ${(totalRevenue / totalHours).toFixed(0)}</strong></div>
                            </div>
                        </div>
                    </div>
                `;
                
            } else if (this.timeSubTab === 'weekday') {
                const days = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'];
                const byDay = this.groupBy(df, 'DayOfWeek');
                
                Plotly.newPlot('time-chart', [{
                    x: [0, 1, 2, 3, 4, 5, 6].map(d => days[d]),
                    y: [0, 1, 2, 3, 4, 5, 6].map(d => (byDay[d] || []).length),
                    type: 'bar',
                    marker: { color: [0, 1, 2, 3, 4, 5, 6].map(d => d >= 5 || d === 0 ? '#ef4444' : '#3b82f6') }
                }], {
                    title: 'Voos por Dia da Semana',
                    yaxis: { title: 'Voos' },
                    margin: { t: 40, b: 40, l: 60, r: 20 }
                }, { responsive: true });
                
            } else if (this.timeSubTab === 'hourly') {
                const byHour = this.groupBy(df, 'Takeoff_Hour');
                const hours = Object.keys(byHour).filter(h => h && h !== 'null').sort((a, b) => parseInt(a) - parseInt(b));
                
                Plotly.newPlot('time-chart', [{
                    x: hours.map(h => `${parseInt(h)}h`),
                    y: hours.map(h => byHour[h].length),
                    type: 'bar',
                    marker: { color: '#3b82f6' }
                }], {
                    title: 'Distribuição por Hora de Decolagem',
                    xaxis: { title: 'Hora' },
                    yaxis: { title: 'Voos' },
                    margin: { t: 40, b: 40, l: 60, r: 20 }
                }, { responsive: true });
            }
        },
        
        loadFleetData() {
            const df = this.filteredFlights;
            const byAircraft = this.groupBy(df, 'Aircraft_Model');
            const models = Object.keys(byAircraft).filter(m => m && m !== 'null');
            
            // Usage chart
            Plotly.newPlot('aircraft-usage-chart', [{
                x: models,
                y: models.map(m => byAircraft[m].length),
                type: 'bar',
                marker: { color: '#3b82f6' }
            }], {
                title: 'Voos por Aeronave',
                yaxis: { title: 'Voos' },
                margin: { t: 40, b: 40, l: 60, r: 20 }
            }, { responsive: true });
            
            // Revenue chart
            Plotly.newPlot('aircraft-revenue-chart', [{
                x: models,
                y: models.map(m => byAircraft[m].reduce((sum, f) => sum + (f.Revenue || 0), 0)),
                type: 'bar',
                marker: { color: '#10b981' }
            }], {
                title: 'Receita por Aeronave',
                yaxis: { title: 'Receita (R$)' },
                margin: { t: 40, b: 60, l: 80, r: 20 }
            }, { responsive: true });
            
            // Stats
            document.getElementById('fleet-stats').innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-${models.length} gap-4">
                    ${models.map(m => {
                        const flights = byAircraft[m];
                        const revenue = flights.reduce((sum, f) => sum + (f.Revenue || 0), 0);
                        const hours = flights.reduce((sum, f) => sum + (f.Flight_Time_Hours || 0), 0);
                        return `
                            <div class="bg-gray-100 p-4 rounded-lg">
                                <h4 class="text-sm font-semibold text-gray-600 mb-2">✈️ ${m}</h4>
                                <div class="text-sm space-y-1">
                                    <div>Voos: <strong>${flights.length}</strong></div>
                                    <div>Horas: <strong>${hours.toFixed(0)}h</strong></div>
                                    <div>Receita: <strong>R$ ${(revenue/1000).toFixed(0)}k</strong></div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
        },
        
        loadRoutesData() {
            const df = this.filteredFlights;
            const byRoute = this.groupBy(df, 'Route');
            const routes = Object.keys(byRoute)
                .filter(r => r && r !== 'null')
                .sort((a, b) => byRoute[b].length - byRoute[a].length)
                .slice(0, 15);
            
            Plotly.newPlot('routes-chart', [{
                y: routes,
                x: routes.map(r => byRoute[r].length),
                type: 'bar',
                orientation: 'h',
                marker: { color: '#10b981' }
            }], {
                title: 'Top 15 Rotas',
                xaxis: { title: 'Voos' },
                margin: { t: 40, b: 40, l: 150, r: 20 }
            }, { responsive: true });
            
            // Stats
            const topRoute = routes[0];
            const totalRoutes = Object.keys(byRoute).length;
            
            document.getElementById('routes-stats').innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div class="bg-gray-100 p-4 rounded-lg">
                        <h4 class="text-sm font-semibold text-gray-600 mb-2">📊 Resumo</h4>
                        <div class="text-sm">
                            <div>Total Rotas: <strong>${totalRoutes}</strong></div>
                            <div>Total Voos: <strong>${df.length.toLocaleString()}</strong></div>
                        </div>
                    </div>
                    <div class="bg-green-50 p-4 rounded-lg">
                        <h4 class="text-sm font-semibold text-green-600 mb-2">🏆 Rota Mais Popular</h4>
                        <div class="text-lg font-bold text-green-700">${topRoute}</div>
                        <div class="text-sm text-gray-600">${byRoute[topRoute].length} voos</div>
                    </div>
                    <div class="bg-gray-100 p-4 rounded-lg">
                        <h4 class="text-sm font-semibold text-gray-600 mb-2">📈 Top 5</h4>
                        <div class="text-xl font-bold text-blue-600">${routes.slice(0, 5).reduce((sum, r) => sum + byRoute[r].length, 0)}</div>
                        <div class="text-sm text-gray-500">voos nas top 5 rotas</div>
                    </div>
                    <div class="bg-gray-100 p-4 rounded-lg">
                        <h4 class="text-sm font-semibold text-gray-600 mb-2">📋 Média</h4>
                        <div class="text-xl font-bold text-purple-600">${(df.length / totalRoutes).toFixed(1)}</div>
                        <div class="text-sm text-gray-500">voos por rota</div>
                    </div>
                </div>
            `;
        },
        
        loadKPIData() {
            // Monthly trends chart
            if (this.charts?.monthly_trends) {
                const trends = this.charts.monthly_trends;
                
                Plotly.newPlot('kpi-monthly-chart', [
                    { 
                        x: trends.map(t => t.month_name), 
                        y: trends.map(t => t.flights), 
                        name: 'Voos', 
                        type: 'bar', 
                        marker: { color: '#3b82f6' }
                    },
                    { 
                        x: trends.map(t => t.month_name), 
                        y: trends.map(t => t.revenue / 1000), 
                        name: 'Receita (mil)', 
                        type: 'scatter', 
                        mode: 'lines+markers', 
                        yaxis: 'y2', 
                        marker: { color: '#10b981' }
                    },
                    { 
                        x: trends.map(t => t.month_name), 
                        y: trends.map(t => t.cost / 1000), 
                        name: 'Custo (mil)', 
                        type: 'scatter', 
                        mode: 'lines+markers', 
                        yaxis: 'y2', 
                        marker: { color: '#ef4444' }
                    }
                ], {
                    title: 'Tendências Mensais: Voos, Receita e Custo',
                    yaxis: { title: 'Voos' },
                    yaxis2: { title: 'Valor (mil R$)', overlaying: 'y', side: 'right' },
                    margin: { t: 40, b: 40, l: 60, r: 60 },
                    legend: { orientation: 'h', y: -0.15 }
                }, { responsive: true });
                
                // KPI Table
                let tableHtml = `
                    <table class="min-w-full bg-white border border-gray-200 text-sm">
                        <thead class="bg-gray-100">
                            <tr>
                                <th class="px-4 py-2 border text-left">Mês</th>
                                <th class="px-4 py-2 border text-right">Voos</th>
                                <th class="px-4 py-2 border text-right">Horas</th>
                                <th class="px-4 py-2 border text-right">Pax</th>
                                <th class="px-4 py-2 border text-right">Receita</th>
                                <th class="px-4 py-2 border text-right">Custo</th>
                                <th class="px-4 py-2 border text-right">Lucro</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                trends.forEach(t => {
                    const profit = t.revenue - t.cost;
                    tableHtml += `
                        <tr class="hover:bg-gray-50">
                            <td class="px-4 py-2 border font-medium">${t.month_name}</td>
                            <td class="px-4 py-2 border text-right">${t.flights}</td>
                            <td class="px-4 py-2 border text-right">${t.hours.toFixed(0)}h</td>
                            <td class="px-4 py-2 border text-right">${t.passengers.toLocaleString()}</td>
                            <td class="px-4 py-2 border text-right text-green-600">R$ ${(t.revenue/1000).toFixed(0)}k</td>
                            <td class="px-4 py-2 border text-right text-red-600">R$ ${(t.cost/1000).toFixed(0)}k</td>
                            <td class="px-4 py-2 border text-right ${profit >= 0 ? 'text-green-600' : 'text-red-600'}">R$ ${(profit/1000).toFixed(0)}k</td>
                        </tr>
                    `;
                });
                
                tableHtml += '</tbody></table>';
                document.getElementById('kpi-table').innerHTML = tableHtml;
            }
        },
        
        // Utility function to group array by key
        groupBy(array, key) {
            return array.reduce((result, item) => {
                const groupKey = item[key];
                if (!result[groupKey]) {
                    result[groupKey] = [];
                }
                result[groupKey].push(item);
                return result;
            }, {});
        }
    };
}

