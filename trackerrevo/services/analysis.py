"""
Analysis Service Module
Provides analysis functions for flight data
"""
import pandas as pd
import numpy as np
from datetime import datetime


class AnalysisService:
    """Service for performing various analyses on flight data"""
    
    def __init__(self, data_processor):
        self.processor = data_processor
    
    def get_summary_statistics(self):
        """Get summary statistics for all categories"""
        categories = {
            'Shuttle': self.processor.df_shuttle,
            'Shuttle FC': self.processor.df_shuttle_fc,
            'Shuttle Total': self.processor.df_shuttle_total,
            'Charter': self.processor.df_charter,
            'FC + Charter': self.processor.df_fc_charter
        }
        
        summary = {}
        for name, df in categories.items():
            if df is not None and len(df) > 0:
                summary[name] = {
                    'flights': len(df),
                    'passengers': int(df['Pax'].sum()) if 'Pax' in df.columns else 0,
                    'revenue': float(df['Revenue'].sum()) if 'Revenue' in df.columns else 0,
                    'avg_revenue_per_flight': float(df['Revenue'].mean()) if 'Revenue' in df.columns else 0,
                    'avg_load_factor': float(df['Load_Factor'].mean()) if 'Load_Factor' in df.columns else 0,
                    'total_hours': float(df['Flight_Time_Hours'].sum()) if 'Flight_Time_Hours' in df.columns else 0
                }
            else:
                summary[name] = {
                    'flights': 0,
                    'passengers': 0,
                    'revenue': 0,
                    'avg_revenue_per_flight': 0,
                    'avg_load_factor': 0,
                    'total_hours': 0
                }
        
        return summary
    
    def get_category_distribution(self):
        """Get flight distribution by category for pie chart"""
        categories = {
            'Shuttle': (self.processor.df_shuttle, '#2ecc71'),
            'Shuttle FC': (self.processor.df_shuttle_fc, '#3498db'),
            'Charter': (self.processor.df_charter, '#e74c3c'),
            'FC + Charter': (self.processor.df_fc_charter, '#f39c12'),
        }
        
        flight_counts = []
        labels = []
        colors = []
        
        for name, (df, color) in categories.items():
            if df is not None and len(df) > 0:
                flight_counts.append(len(df))
                labels.append(f'{name}\n{len(df):,} voos')
                colors.append(color)
        
        return {
            'values': flight_counts,
            'labels': labels,
            'colors': colors
        }
    
    def get_revenue_by_category(self):
        """Get revenue by category for bar chart"""
        categories = {
            'Shuttle': (self.processor.df_shuttle, '#2ecc71'),
            'Shuttle FC': (self.processor.df_shuttle_fc, '#3498db'),
            'Charter': (self.processor.df_charter, '#e74c3c'),
            'FC + Charter': (self.processor.df_fc_charter, '#f39c12'),
        }
        
        cat_names = []
        revenues = []
        colors = []
        
        for name, (df, color) in categories.items():
            if df is not None and len(df) > 0 and 'Revenue' in df.columns:
                cat_names.append(name)
                revenues.append(float(df['Revenue'].sum()))
                colors.append(color)
        
        return {
            'categories': cat_names,
            'revenues': revenues,
            'colors': colors
        }
    
    def get_monthly_revenue(self):
        """Get monthly revenue breakdown"""
        df = self.processor.df_filtered
        
        if df is None or 'Sheet_Month' not in df.columns or 'Revenue' not in df.columns:
            return {'months': [], 'revenue': []}
        
        # Ensure Sheet_Month is numeric BEFORE groupby and sort
        df_month = df.copy()
        df_month['Sheet_Month'] = pd.to_numeric(df_month['Sheet_Month'], errors='coerce').fillna(0).astype(int)
        
        monthly = df_month.groupby('Sheet_Month')['Revenue'].sum().reset_index()
        monthly = monthly.sort_values('Sheet_Month')
        
        month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        monthly['Month'] = monthly['Sheet_Month'].apply(lambda x: month_names[x-1] if 1 <= x <= 12 else str(x))
        
        return {
            'months': monthly['Month'].tolist(),
            'revenue': monthly['Revenue'].tolist()
        }
    
    def get_flight_types_distribution(self, limit=10):
        """Get flight type distribution"""
        df = self.processor.df_filtered
        
        if df is None or 'Type of Flight' not in df.columns:
            return {'labels': [], 'values': []}
        
        flight_types = df['Type of Flight'].value_counts().head(limit)
        
        return {
            'labels': flight_types.index.tolist(),
            'values': flight_types.values.tolist()
        }
    
    def get_aircraft_usage(self):
        """Get aircraft usage distribution"""
        df = self.processor.df_filtered
        
        if df is None or 'Aircraft_Model' not in df.columns:
            return {'labels': [], 'values': []}
        
        aircraft_counts = df['Aircraft_Model'].value_counts()
        
        return {
            'labels': aircraft_counts.index.tolist(),
            'values': aircraft_counts.values.tolist()
        }
    
    def get_weekday_weekend_comparison(self):
        """Get weekday vs weekend comparison"""
        df = self.processor.df_filtered
        
        if df is None or 'DayName' not in df.columns:
            return None
        
        # Classify as weekday or weekend
        df = df.copy()
        df['IsWeekend'] = df['DayName'].isin(['Saturday', 'Sunday', 'Sábado', 'Domingo'])
        
        comparison = {
            'weekday': {
                'flights': len(df[~df['IsWeekend']]),
                'revenue': float(df[~df['IsWeekend']]['Revenue'].sum()) if 'Revenue' in df.columns else 0,
                'passengers': int(df[~df['IsWeekend']]['Pax'].sum()) if 'Pax' in df.columns else 0
            },
            'weekend': {
                'flights': len(df[df['IsWeekend']]),
                'revenue': float(df[df['IsWeekend']]['Revenue'].sum()) if 'Revenue' in df.columns else 0,
                'passengers': int(df[df['IsWeekend']]['Pax'].sum()) if 'Pax' in df.columns else 0
            }
        }
        
        return comparison
    
    def get_shuttle_breakdown(self):
        """Get shuttle breakdown by route"""
        shuttle_routes = {
            'FBV': self.processor.df_shuttle_fbv,
            'Baronesa': self.processor.df_shuttle_baronesa,
            'Laranjeiras': self.processor.df_shuttle_laranjeiras,
            'Alphaville': self.processor.df_shuttle_alphaville,
            'Catarina': self.processor.df_shuttle_catarina
        }
        
        result = {
            'routes': [],
            'total_shuttle': {
                'flights': len(self.processor.df_shuttle_total) if self.processor.df_shuttle_total is not None else 0,
                'revenue': float(self.processor.df_shuttle_total['Revenue'].sum()) if self.processor.df_shuttle_total is not None and 'Revenue' in self.processor.df_shuttle_total.columns else 0,
                'passengers': int(self.processor.df_shuttle_total['Pax'].sum()) if self.processor.df_shuttle_total is not None and 'Pax' in self.processor.df_shuttle_total.columns else 0
            }
        }
        
        for name, df in shuttle_routes.items():
            if df is not None and len(df) > 0:
                route_data = {
                    'name': name,
                    'flights': len(df),
                    'revenue': float(df['Revenue'].sum()) if 'Revenue' in df.columns else 0,
                    'passengers': int(df['Pax'].sum()) if 'Pax' in df.columns else 0,
                    'avg_load_factor': float(df['Load_Factor'].mean()) if 'Load_Factor' in df.columns else 0,
                    'avg_revenue_per_flight': float(df['Revenue'].mean()) if 'Revenue' in df.columns else 0
                }
                result['routes'].append(route_data)
        
        return result
    
    def get_kpi_metrics(self):
        """Get comprehensive KPI metrics"""
        df = self.processor.df_filtered
        
        if df is None or len(df) == 0:
            return {}
        
        metrics = {
            'total_flights': len(df),
            'total_revenue': float(df['Revenue'].sum()) if 'Revenue' in df.columns else 0,
            'total_passengers': int(df['Pax'].sum()) if 'Pax' in df.columns else 0,
            'total_hours': float(df['Flight_Time_Hours'].sum()) if 'Flight_Time_Hours' in df.columns else 0,
            'avg_revenue_per_flight': float(df['Revenue'].mean()) if 'Revenue' in df.columns else 0,
            'avg_passengers_per_flight': float(df['Pax'].mean()) if 'Pax' in df.columns else 0,
            'avg_load_factor': float(df['Load_Factor'].mean()) if 'Load_Factor' in df.columns else 0
        }
        
        # Revenue per mile/hour
        if metrics['total_hours'] > 0:
            metrics['revenue_per_hour'] = metrics['total_revenue'] / metrics['total_hours']
        else:
            metrics['revenue_per_hour'] = 0
        
        # Seats offered
        if 'Aircraft_Capacity' in df.columns:
            metrics['total_seats_offered'] = int(df['Aircraft_Capacity'].sum())
            if metrics['total_passengers'] > 0:
                metrics['seats_per_passenger'] = metrics['total_seats_offered'] / metrics['total_passengers']
        
        return metrics
    
    def get_daily_breakdown(self):
        """Get breakdown by day of week"""
        df = self.processor.df_filtered
        
        if df is None or 'DayName' not in df.columns:
            return None
        
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_names_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        
        daily = df.groupby('DayName').agg({
            'Revenue': ['count', 'sum'],
            'Pax': 'sum'
        }).reset_index()
        daily.columns = ['day', 'flights', 'revenue', 'passengers']
        
        # Sort by day of week
        daily['day_order'] = daily['day'].apply(lambda x: day_order.index(x) if x in day_order else 7)
        daily = daily.sort_values('day_order')
        
        return {
            'days': daily['day'].tolist(),
            'flights': daily['flights'].tolist(),
            'revenue': daily['revenue'].tolist(),
            'passengers': daily['passengers'].tolist()
        }

