"""
KPI Calculator Service
Comprehensive KPI calculations for flight analytics
"""
import pandas as pd
import numpy as np


class KPICalculator:
    """Calculate comprehensive KPIs for flight data"""
    
    def __init__(self, data_processor, cost_service=None):
        self.processor = data_processor
        self.cost_service = cost_service
    
    def _ensure_numeric_sheet_month(self, df):
        """Ensure Sheet_Month is numeric before any operations"""
        if df is not None and 'Sheet_Month' in df.columns:
            df = df.copy()
            df['Sheet_Month'] = pd.to_numeric(df['Sheet_Month'], errors='coerce').fillna(0).astype(int)
        return df
    
    def calculate_all_kpis(self):
        """Calculate all KPIs and return comprehensive results"""
        df = self.processor.df_filtered
        
        if df is None or len(df) == 0:
            return {'error': 'No data available'}
        
        # Ensure Sheet_Month is numeric
        df = self._ensure_numeric_sheet_month(df)
        
        kpis = {
            'overview': self._calculate_overview_kpis(df),
            'revenue': self._calculate_revenue_kpis(df),
            'efficiency': self._calculate_efficiency_kpis(df),
            'utilization': self._calculate_utilization_kpis(df),
            'profitability': self._calculate_profitability_kpis(df),
            'by_category': self._calculate_category_kpis(),
            'by_aircraft': self._calculate_aircraft_kpis(df),
            'by_route': self._calculate_route_kpis(df),
            'monthly_trends': self._calculate_monthly_trends(df)
        }
        
        return kpis
    
    def _calculate_overview_kpis(self, df):
        """Calculate overview KPIs"""
        total_flights = len(df)
        total_revenue = float(df['Revenue'].sum()) if 'Revenue' in df.columns else 0
        total_passengers = int(df['Pax'].sum()) if 'Pax' in df.columns else 0
        total_hours = float(df['Flight_Time_Hours'].sum()) if 'Flight_Time_Hours' in df.columns else 0
        total_landings = int(df['Landings'].sum()) if 'Landings' in df.columns else total_flights
        
        return {
            'total_flights': total_flights,
            'total_revenue': total_revenue,
            'total_passengers': total_passengers,
            'total_flight_hours': round(total_hours, 1),
            'total_landings': total_landings,
            'avg_revenue_per_flight': round(total_revenue / total_flights, 2) if total_flights > 0 else 0,
            'avg_passengers_per_flight': round(total_passengers / total_flights, 2) if total_flights > 0 else 0,
            'avg_flight_duration_min': round((total_hours * 60) / total_flights, 1) if total_flights > 0 else 0
        }
    
    def _calculate_revenue_kpis(self, df):
        """Calculate revenue-specific KPIs"""
        total_revenue = float(df['Revenue'].sum()) if 'Revenue' in df.columns else 0
        total_hours = float(df['Flight_Time_Hours'].sum()) if 'Flight_Time_Hours' in df.columns else 0
        total_pax = int(df['Pax'].sum()) if 'Pax' in df.columns else 0
        total_seats = int(df['Aircraft_Capacity'].sum()) if 'Aircraft_Capacity' in df.columns else 0
        
        # Revenue per nautical mile (if distance available)
        # Check both possible column names
        total_nm = 0
        if 'Distance_Nautical_Miles' in df.columns:
            total_nm = float(df['Distance_Nautical_Miles'].sum())
        elif 'Distance_NM' in df.columns:
            total_nm = float(df['Distance_NM'].sum())
        
        revenue_per_nm = total_revenue / total_nm if total_nm > 0 else 0
        
        # Cost per nautical mile
        total_cost = float(df['Cost'].sum()) if 'Cost' in df.columns else 0
        cost_per_nm = total_cost / total_nm if total_nm > 0 else 0
        
        return {
            'total_revenue': total_revenue,
            'revenue_per_flight_hour': round(total_revenue / total_hours, 2) if total_hours > 0 else 0,
            'revenue_per_passenger': round(total_revenue / total_pax, 2) if total_pax > 0 else 0,
            'revenue_per_seat_offered': round(total_revenue / total_seats, 2) if total_seats > 0 else 0,
            'revenue_per_nautical_mile': round(revenue_per_nm, 2),
            'cost_per_nautical_mile': round(cost_per_nm, 2),
            'total_nautical_miles': round(total_nm, 0),
            'avg_ticket_price': round(total_revenue / total_pax, 2) if total_pax > 0 else 0
        }
    
    def _calculate_efficiency_kpis(self, df):
        """Calculate efficiency KPIs"""
        # Load Factor
        if 'Load_Factor' in df.columns:
            avg_load_factor = float(df['Load_Factor'].mean())
        elif 'Pax' in df.columns and 'Aircraft_Capacity' in df.columns:
            df_valid = df[df['Aircraft_Capacity'] > 0]
            avg_load_factor = float((df_valid['Pax'] / df_valid['Aircraft_Capacity']).mean() * 100)
        else:
            avg_load_factor = 0
        
        # Empty seats
        total_pax = int(df['Pax'].sum()) if 'Pax' in df.columns else 0
        total_capacity = int(df['Aircraft_Capacity'].sum()) if 'Aircraft_Capacity' in df.columns else 0
        empty_seats = total_capacity - total_pax
        
        # Flights with full cabin
        full_cabin_flights = 0
        if 'Pax' in df.columns and 'Aircraft_Capacity' in df.columns:
            full_cabin_flights = len(df[df['Pax'] >= df['Aircraft_Capacity']])
        
        return {
            'average_load_factor': round(avg_load_factor, 1),
            'total_seats_offered': total_capacity,
            'total_passengers': total_pax,
            'empty_seats': empty_seats,
            'seat_utilization_rate': round((total_pax / total_capacity * 100), 1) if total_capacity > 0 else 0,
            'full_cabin_flights': full_cabin_flights,
            'full_cabin_rate': round((full_cabin_flights / len(df) * 100), 1) if len(df) > 0 else 0,
            'potential_revenue_lost': empty_seats * (df['Revenue'].sum() / total_pax) if total_pax > 0 else 0
        }
    
    def _calculate_utilization_kpis(self, df):
        """Calculate aircraft utilization KPIs"""
        total_hours = float(df['Flight_Time_Hours'].sum()) if 'Flight_Time_Hours' in df.columns else 0
        
        # Hours by aircraft model
        hours_by_model = {}
        if 'Aircraft_Model' in df.columns and 'Flight_Time_Hours' in df.columns:
            hours_by_model = df.groupby('Aircraft_Model')['Flight_Time_Hours'].sum().to_dict()
        
        # Hours by month - ensure Sheet_Month is numeric
        hours_by_month = {}
        if 'Sheet_Month' in df.columns and 'Flight_Time_Hours' in df.columns:
            df_month = self._ensure_numeric_sheet_month(df)
            hours_by_month = df_month.groupby('Sheet_Month')['Flight_Time_Hours'].sum().to_dict()
        
        # Average daily flights
        if 'Date_Parsed' in df.columns:
            unique_days = df['Date_Parsed'].nunique()
            avg_daily_flights = len(df) / unique_days if unique_days > 0 else 0
            avg_daily_hours = total_hours / unique_days if unique_days > 0 else 0
        else:
            avg_daily_flights = 0
            avg_daily_hours = 0
        
        return {
            'total_flight_hours': round(total_hours, 1),
            'hours_by_model': {k: round(v, 1) for k, v in hours_by_model.items()},
            'hours_by_month': {str(k): round(v, 1) for k, v in hours_by_month.items()},
            'avg_daily_flights': round(avg_daily_flights, 1),
            'avg_daily_hours': round(avg_daily_hours, 2),
            'avg_hours_per_flight': round(total_hours / len(df), 2) if len(df) > 0 else 0
        }
    
    def _calculate_profitability_kpis(self, df):
        """Calculate profitability KPIs"""
        total_revenue = float(df['Revenue'].sum()) if 'Revenue' in df.columns else 0
        
        # Cost calculations
        total_cost = 0
        total_fixed_cost = 0
        total_fuel_cost = 0
        total_monthly_alloc = 0
        
        if 'Cost' in df.columns:
            total_cost = float(df['Cost'].sum())
        if 'Fixed_Cost' in df.columns:
            total_fixed_cost = float(df['Fixed_Cost'].sum())
        if 'Fuel_Cost' in df.columns:
            total_fuel_cost = float(df['Fuel_Cost'].sum())
        if 'Monthly_Cost_Allocation' in df.columns:
            total_monthly_alloc = float(df['Monthly_Cost_Allocation'].sum())
        
        gross_profit = total_revenue - total_cost
        margin_percent = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        return {
            'total_revenue': total_revenue,
            'total_cost': round(total_cost, 2),
            'cost_breakdown': {
                'fixed_costs': round(total_fixed_cost, 2),
                'fuel_costs': round(total_fuel_cost, 2),
                'monthly_allocation': round(total_monthly_alloc, 2)
            },
            'gross_profit': round(gross_profit, 2),
            'profit_margin_percent': round(margin_percent, 1),
            'revenue_per_cost': round(total_revenue / total_cost, 2) if total_cost > 0 else 0,
            'cost_per_flight': round(total_cost / len(df), 2) if len(df) > 0 else 0,
            'profit_per_flight': round(gross_profit / len(df), 2) if len(df) > 0 else 0
        }
    
    def _calculate_category_kpis(self):
        """Calculate KPIs by flight category"""
        categories = {
            'Shuttle': self.processor.df_shuttle,
            'Shuttle FC': self.processor.df_shuttle_fc,
            'Charter': self.processor.df_charter,
            'FC + Charter': self.processor.df_fc_charter
        }
        
        result = {}
        for name, df in categories.items():
            if df is not None and len(df) > 0:
                # Ensure Sheet_Month is numeric
                df = self._ensure_numeric_sheet_month(df)
                revenue = float(df['Revenue'].sum()) if 'Revenue' in df.columns else 0
                pax = int(df['Pax'].sum()) if 'Pax' in df.columns else 0
                hours = float(df['Flight_Time_Hours'].sum()) if 'Flight_Time_Hours' in df.columns else 0
                cost = float(df['Cost'].sum()) if 'Cost' in df.columns else 0
                
                result[name] = {
                    'flights': len(df),
                    'revenue': revenue,
                    'passengers': pax,
                    'hours': round(hours, 1),
                    'cost': round(cost, 2),
                    'profit': round(revenue - cost, 2),
                    'avg_revenue_per_flight': round(revenue / len(df), 2) if len(df) > 0 else 0,
                    'avg_load_factor': round(float(df['Load_Factor'].mean()), 1) if 'Load_Factor' in df.columns else 0,
                    'revenue_per_hour': round(revenue / hours, 2) if hours > 0 else 0
                }
        
        return result
    
    def _calculate_aircraft_kpis(self, df):
        """Calculate KPIs by aircraft"""
        if 'Aircraft_Model' not in df.columns:
            return {}
        
        result = {}
        for model in df['Aircraft_Model'].unique():
            model_df = df[df['Aircraft_Model'] == model]
            revenue = float(model_df['Revenue'].sum()) if 'Revenue' in model_df.columns else 0
            pax = int(model_df['Pax'].sum()) if 'Pax' in model_df.columns else 0
            hours = float(model_df['Flight_Time_Hours'].sum()) if 'Flight_Time_Hours' in model_df.columns else 0
            cost = float(model_df['Cost'].sum()) if 'Cost' in model_df.columns else 0
            
            result[model] = {
                'flights': len(model_df),
                'revenue': revenue,
                'passengers': pax,
                'hours': round(hours, 1),
                'cost': round(cost, 2),
                'profit': round(revenue - cost, 2),
                'margin_percent': round((revenue - cost) / revenue * 100, 1) if revenue > 0 else 0,
                'revenue_per_hour': round(revenue / hours, 2) if hours > 0 else 0,
                'cost_per_hour': round(cost / hours, 2) if hours > 0 else 0,
                'avg_load_factor': round(float(model_df['Load_Factor'].mean()), 1) if 'Load_Factor' in model_df.columns else 0
            }
        
        return result
    
    def _calculate_route_kpis(self, df, top_n=10):
        """Calculate KPIs for top routes"""
        if 'Departure' not in df.columns or 'Arrival' not in df.columns:
            return []
        
        df_routes = df[df['Departure'].notna() & df['Arrival'].notna()].copy()
        df_routes['Route'] = df_routes['Departure'].astype(str) + ' → ' + df_routes['Arrival'].astype(str)
        
        route_stats = df_routes.groupby('Route').agg({
            'Revenue': ['count', 'sum', 'mean'],
            'Pax': 'sum',
            'Flight_Time_Hours': 'sum'
        }).reset_index()
        
        route_stats.columns = ['route', 'flights', 'total_revenue', 'avg_revenue', 'passengers', 'hours']
        route_stats = route_stats.sort_values('flights', ascending=False).head(top_n)
        
        result = []
        for _, row in route_stats.iterrows():
            result.append({
                'route': row['route'],
                'flights': int(row['flights']),
                'revenue': round(float(row['total_revenue']), 2),
                'avg_revenue': round(float(row['avg_revenue']), 2),
                'passengers': int(row['passengers']),
                'hours': round(float(row['hours']), 1),
                'revenue_per_hour': round(row['total_revenue'] / row['hours'], 2) if row['hours'] > 0 else 0
            })
        
        return result
    
    def _calculate_monthly_trends(self, df):
        """Calculate monthly trends"""
        if 'Sheet_Month' not in df.columns:
            return []
        
        # CRITICAL: Ensure Sheet_Month is numeric before sorting
        df = self._ensure_numeric_sheet_month(df)
        
        month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        
        result = []
        # Sort unique months as integers
        unique_months = sorted([int(m) for m in df['Sheet_Month'].unique() if pd.notna(m) and m > 0])
        
        for month in unique_months:
            month_df = df[df['Sheet_Month'] == month]
            revenue = float(month_df['Revenue'].sum()) if 'Revenue' in month_df.columns else 0
            cost = float(month_df['Cost'].sum()) if 'Cost' in month_df.columns else 0
            pax = int(month_df['Pax'].sum()) if 'Pax' in month_df.columns else 0
            hours = float(month_df['Flight_Time_Hours'].sum()) if 'Flight_Time_Hours' in month_df.columns else 0
            
            result.append({
                'month': int(month),
                'month_name': month_names[int(month) - 1] if 1 <= int(month) <= 12 else str(month),
                'flights': len(month_df),
                'revenue': round(revenue, 2),
                'cost': round(cost, 2),
                'profit': round(revenue - cost, 2),
                'passengers': pax,
                'hours': round(hours, 1),
                'avg_load_factor': round(float(month_df['Load_Factor'].mean()), 1) if 'Load_Factor' in month_df.columns else 0
            })
        
        return result
    
    def get_kpi_cards_data(self):
        """Get data formatted for KPI cards display"""
        kpis = self.calculate_all_kpis()
        
        if 'error' in kpis:
            return []
        
        cards = [
            {
                'title': 'Total de Voos',
                'value': f"{kpis['overview']['total_flights']:,}",
                'subtitle': f"{kpis['overview']['avg_flight_duration_min']:.0f} min médio",
                'icon': '✈️',
                'color': 'blue'
            },
            {
                'title': 'Receita Total',
                'value': f"R$ {kpis['overview']['total_revenue']:,.0f}",
                'subtitle': f"R$ {kpis['overview']['avg_revenue_per_flight']:,.0f}/voo",
                'icon': '💰',
                'color': 'green'
            },
            {
                'title': 'Passageiros',
                'value': f"{kpis['overview']['total_passengers']:,}",
                'subtitle': f"{kpis['overview']['avg_passengers_per_flight']:.1f}/voo",
                'icon': '👥',
                'color': 'purple'
            },
            {
                'title': 'Horas Voadas',
                'value': f"{kpis['overview']['total_flight_hours']:,.0f}h",
                'subtitle': f"R$ {kpis['revenue']['revenue_per_flight_hour']:,.0f}/hora",
                'icon': '⏱️',
                'color': 'orange'
            },
            {
                'title': 'Load Factor',
                'value': f"{kpis['efficiency']['average_load_factor']:.1f}%",
                'subtitle': f"{kpis['efficiency']['empty_seats']:,} assentos vazios",
                'icon': '📊',
                'color': 'cyan'
            },
            {
                'title': 'Lucro Bruto',
                'value': f"R$ {kpis['profitability']['gross_profit']:,.0f}",
                'subtitle': f"Margem: {kpis['profitability']['profit_margin_percent']:.1f}%",
                'icon': '📈',
                'color': 'emerald'
            }
        ]
        
        return cards
    
    def _calculate_commercial_hours(self, df):
        """Calculate commercial vs non-commercial hours by month, broken down by Shuttle and Charter"""
        if df is None or len(df) == 0:
            return {'by_month': [], 'by_category': {}}
        
        if 'Is_Commercial' not in df.columns or 'Sheet_Month' not in df.columns or 'Flight_Time_Hours' not in df.columns:
            return {'by_month': [], 'by_category': {}}
        
        # Ensure Flight_Category exists
        if 'Flight_Category' not in df.columns:
            # Try to infer from Type of Flight
            if 'Type of Flight' in df.columns:
                df['Flight_Category'] = 'Other'
                df.loc[df['Type of Flight'].astype(str).str.contains('Shuttle', case=False, na=False), 'Flight_Category'] = 'Shuttle'
                df.loc[df['Type of Flight'].astype(str).str.contains('Charter', case=False, na=False), 'Flight_Category'] = 'Charter'
            else:
                df['Flight_Category'] = 'Other'
        
        # Ensure Sheet_Month is numeric
        df = self._ensure_numeric_sheet_month(df)
        
        month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        
        # Group by month and commercial status
        monthly_data = df.groupby(['Sheet_Month', 'Is_Commercial'])['Flight_Time_Hours'].sum().reset_index()
        
        # Group by month, category, and commercial status
        category_monthly_data = df.groupby(['Sheet_Month', 'Flight_Category', 'Is_Commercial'])['Flight_Time_Hours'].sum().reset_index()
        
        # Create result structure by month
        result = []
        unique_months = sorted([int(m) for m in df['Sheet_Month'].unique() if pd.notna(m) and m > 0])
        
        for month in unique_months:
            month_df = monthly_data[monthly_data['Sheet_Month'] == month]
            commercial_hours = float(month_df[month_df['Is_Commercial'] == True]['Flight_Time_Hours'].sum()) if len(month_df[month_df['Is_Commercial'] == True]) > 0 else 0
            non_commercial_hours = float(month_df[month_df['Is_Commercial'] == False]['Flight_Time_Hours'].sum()) if len(month_df[month_df['Is_Commercial'] == False]) > 0 else 0
            
            result.append({
                'month': int(month),
                'month_name': month_names[int(month) - 1] if 1 <= int(month) <= 12 else str(month),
                'commercial_hours': round(commercial_hours, 1),
                'non_commercial_hours': round(non_commercial_hours, 1)
            })
        
        # Create result structure by category (Shuttle/Charter)
        category_result = {}
        for category in ['Shuttle', 'Charter']:
            cat_df = category_monthly_data[category_monthly_data['Flight_Category'] == category]
            if len(cat_df) > 0:
                category_result[category] = {}
                for month in unique_months:
                    month_cat_df = cat_df[cat_df['Sheet_Month'] == month]
                    commercial = float(month_cat_df[month_cat_df['Is_Commercial'] == True]['Flight_Time_Hours'].sum()) if len(month_cat_df[month_cat_df['Is_Commercial'] == True]) > 0 else 0
                    non_commercial = float(month_cat_df[month_cat_df['Is_Commercial'] == False]['Flight_Time_Hours'].sum()) if len(month_cat_df[month_cat_df['Is_Commercial'] == False]) > 0 else 0
                    if commercial > 0 or non_commercial > 0:
                        if category not in category_result:
                            category_result[category] = {}
                        category_result[category][month_names[int(month) - 1] if 1 <= int(month) <= 12 else str(month)] = {
                            'commercial': round(commercial, 1),
                            'non_commercial': round(non_commercial, 1)
                        }
        
        return {'by_month': result, 'by_category': category_result}
    
    def _calculate_costs_by_category(self, df):
        """Calculate costs by flight category"""
        if df is None or len(df) == 0:
            return {}
        
        # Ensure costs are calculated
        if 'Cost' not in df.columns and self.cost_service:
            df = self.cost_service.calculate_dataframe_costs(df)
        
        # Determine category column
        category_col = None
        if 'Classification' in df.columns:
            category_col = 'Classification'
        elif 'Type of Flight' in df.columns:
            category_col = 'Type of Flight'
        else:
            return {}
        
        # Get distance column
        distance_col = None
        if 'Distance_Nautical_Miles' in df.columns:
            distance_col = 'Distance_Nautical_Miles'
        elif 'Distance_NM' in df.columns:
            distance_col = 'Distance_NM'
        
        result = {}
        
        for category in df[category_col].unique():
            if pd.isna(category):
                continue
            
            cat_df = df[df[category_col] == category]
            
            total_cost = float(cat_df['Cost'].sum()) if 'Cost' in cat_df.columns else 0
            total_hours = float(cat_df['Flight_Time_Hours'].sum()) if 'Flight_Time_Hours' in cat_df.columns else 0
            total_nm = float(cat_df[distance_col].sum()) if distance_col and distance_col in cat_df.columns else 0
            total_passengers = int(cat_df['Pax'].sum()) if 'Pax' in cat_df.columns else 0
            
            result[str(category)] = {
                'total_cost': round(total_cost, 2),
                'cost_per_hour': round(total_cost / total_hours, 2) if total_hours > 0 else 0,
                'cost_per_nm': round(total_cost / total_nm, 2) if total_nm > 0 else 0,
                'total_hours': round(total_hours, 1),
                'total_nm': round(total_nm, 0),
                'total_passengers': total_passengers,
                'flights': len(cat_df)
            }
        
        return result
    
    def _calculate_accumulated_metrics(self, df):
        """Calculate accumulated revenue and cost by flight category (Shuttle/Charter)"""
        if df is None or len(df) == 0:
            return {}
        
        if 'Sheet_Month' not in df.columns:
            return {}
        
        # Ensure Flight_Category exists
        if 'Flight_Category' not in df.columns:
            # Try to infer from Type of Flight
            if 'Type of Flight' in df.columns:
                df['Flight_Category'] = 'Other'
                df.loc[df['Type of Flight'].astype(str).str.contains('Shuttle', case=False, na=False), 'Flight_Category'] = 'Shuttle'
                df.loc[df['Type of Flight'].astype(str).str.contains('Charter', case=False, na=False), 'Flight_Category'] = 'Charter'
            else:
                df['Flight_Category'] = 'Other'
        
        # Ensure costs are calculated
        if 'Cost' not in df.columns and self.cost_service:
            df = self.cost_service.calculate_dataframe_costs(df)
        
        # Ensure Sheet_Month is numeric
        df = self._ensure_numeric_sheet_month(df)
        
        month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        
        # Group by Flight_Category (Shuttle/Charter) and month
        agg_dict = {'Revenue': 'sum'}
        if 'Cost' in df.columns:
            agg_dict['Cost'] = 'sum'
        
        grouped = df.groupby(['Flight_Category', 'Sheet_Month']).agg(agg_dict).reset_index()
        
        result = {}
        
        # Only process Shuttle and Charter
        for category in ['Shuttle', 'Charter']:
            cat_df = grouped[grouped['Flight_Category'] == category].copy()
            if len(cat_df) == 0:
                continue
            
            cat_df = cat_df.sort_values('Sheet_Month')
            
            # Calculate cumulative sums
            cat_df['revenue_cumulative'] = cat_df['Revenue'].cumsum()
            if 'Cost' in cat_df.columns:
                cat_df['cost_cumulative'] = cat_df['Cost'].cumsum()
            else:
                cat_df['cost_cumulative'] = 0
            
            months = []
            revenue_cumulative = []
            cost_cumulative = []
            
            for _, row in cat_df.iterrows():
                month = int(row['Sheet_Month'])
                months.append(month_names[month - 1] if 1 <= month <= 12 else str(month))
                revenue_cumulative.append(round(float(row['revenue_cumulative']), 2))
                cost_cumulative.append(round(float(row['cost_cumulative']), 2))
            
            result[category] = {
                'months': months,
                'revenue_cumulative': revenue_cumulative,
                'cost_cumulative': cost_cumulative
            }
        
        return result
