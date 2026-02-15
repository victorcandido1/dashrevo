"""
Core Data Processing Module
Handles Excel file loading, data cleaning, and basic transformations
"""
import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class DataProcessor:
    """Processes flight data from Excel files"""
    
    def __init__(self, file_path=None):
        self.file_path = file_path
        self.df_raw = None
        self.df_all = None
        self.df_filtered = None
        
        # Category dataframes
        self.df_base = None
        self.df_shuttle = None
        self.df_shuttle_fc = None
        self.df_shuttle_total = None
        self.df_charter = None
        self.df_fc_charter = None
        self.df_marketing = None
        self.df_courtesy = None
        self.df_empty_legs = None
        self.df_hangar_flights = None
        
        # Filter state
        self.filters = {
            'flight_types': [],
            'aircraft_models': [],
            'aircraft_prefixes': [],
            'sales_models': [],
            'classifications': [],
            'clientes': [],
            'routes': [],
            'months': [],
            'include_empty_leg': True,
            'include_hangar_flight': True,
            'date_start': None,
            'date_end': None,
            'hour_start': None,
            'hour_end': None,
            'pax_min': None,
            'pax_max': None,
            'revenue_min': None,
            'revenue_max': None,
            'landings_min': None,
            'landings_max': None,
        }
        
        self.filter_options = {}
        
        if file_path:
            self.load_data(file_path)
    
    def load_data(self, file_path=None):
        """Load data from Excel file"""
        if file_path:
            self.file_path = file_path
        
        if not self.file_path or not os.path.exists(self.file_path):
            return False
        
        try:
            # Load Excel file
            self.df_raw = pd.read_excel(self.file_path, sheet_name=None)
            # Process all sheets
            all_data = []
            for sheet_name, df in self.df_raw.items():
                # Remove total rows before processing
                df = self._remove_total_rows(df)
                if len(df) == 0:
                    continue  # Skip empty sheets after cleaning
                
                df['Sheet_Name'] = sheet_name
                all_data.append(df)
            
            if all_data:
                self.df_all = pd.concat(all_data, ignore_index=True)
                # Final check for total rows after concatenation
                self.df_all = self._remove_total_rows(self.df_all)
                # Classify flights as commercial/non-commercial
                self.df_all = self._classify_flight_type(self.df_all)
                self.df_filtered = self.df_all.copy()
                # CRITICAL: Ensure numeric columns immediately after loading
                self._ensure_numeric_columns()
                return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def _remove_total_rows(self, df):
        """Remove rows that represent totals/sums from the dataframe"""
        if df is None or len(df) == 0:
            return df
        
        # Patterns that indicate total rows
        total_patterns = 'TOTAL|SOMA|SUM|TOTAIS|GERAL|GRAND|SUBTOTAL'
        rows_to_remove = pd.Series([False] * len(df))
        
        # Check multiple columns for total patterns
        for col in ['Date', 'Departure', 'Arrival', 'Type of Flight']:
            if col in df.columns:
                rows_to_remove |= df[col].astype(str).str.upper().str.contains(total_patterns, na=False)
        
        # Remove total rows
        df = df[~rows_to_remove].copy()
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        return df
    
    def _classify_flight_type(self, df):
        """Classify flights as commercial or non-commercial and add Is_Commercial column"""
        if df is None or len(df) == 0:
            return df
        
        df = df.copy()
        df['Is_Commercial'] = True
        df['Flight_Category'] = 'Other'
        
        sales_model_str = df['Sales Model'].astype(str) if 'Sales Model' in df.columns else pd.Series([''] * len(df))
        type_of_flight_str = df['Type of Flight'].astype(str) if 'Type of Flight' in df.columns else pd.Series([''] * len(df))
        
        non_commercial_mask = (
            sales_model_str.str.contains('Marketing', case=False, na=False) |
            sales_model_str.str.contains('Courtesy', case=False, na=False) |
            type_of_flight_str.str.contains('Empty Leg', case=False, na=False) |
            type_of_flight_str.str.contains('Hangar', case=False, na=False)
        )
        df.loc[non_commercial_mask, 'Is_Commercial'] = False
        
        shuttle_mask = type_of_flight_str.str.contains('Shuttle', case=False, na=False)
        df.loc[shuttle_mask, 'Flight_Category'] = 'Shuttle'
        
        charter_mask = (
            type_of_flight_str.str.contains('Charter', case=False, na=False) |
            sales_model_str.str.contains('Full Cabin', case=False, na=False)
        )
        df.loc[charter_mask, 'Flight_Category'] = 'Charter'
        
        return df
    
    def _ensure_numeric_columns(self):
        """Ensure critical columns are numeric"""
        numeric_columns = [
            'Sheet_Month', 'Sheet_Year', 'Revenue', 'Pax', 'Passengers', 'Passageiros',
            'Flight_Time_Hours', 'Flight_Time', 'Hours', 'Horas', 'Landings',
            'Aircraft_Capacity', 'Capacity', 'Cost', 'Total_Cost', 'Fixed_Cost', 'Fuel_Cost',
            'Distance_NM', 'Distance_Nautical_Miles', 'Estimated_Distance_NM',
            'Load_Factor', 'Start_Hour', 'End_Hour', 'RPNM', 'Revenue_Per_NM'
        ]
        
        for target_df in [self.df_all, self.df_filtered]:
            if target_df is not None:
                for col in numeric_columns:
                    if col in target_df.columns:
                        target_df[col] = pd.to_numeric(target_df[col], errors='coerce').fillna(0)
                if 'Sheet_Month' in target_df.columns:
                    target_df['Sheet_Month'] = pd.to_numeric(target_df['Sheet_Month'], errors='coerce').fillna(0).astype(int)
                for pax_col in ['Pax', 'Passengers', 'Passageiros']:
                    if pax_col in target_df.columns:
                        target_df[pax_col] = pd.to_numeric(target_df[pax_col], errors='coerce').fillna(0).astype(int)
                if 'Landings' in target_df.columns:
                    target_df['Landings'] = pd.to_numeric(target_df['Landings'], errors='coerce').fillna(1).astype(int)
    
    def initialize_filters(self):
        """Initialize filter options from data"""
        if self.df_all is None or len(self.df_all) == 0:
            return
        
        self._ensure_numeric_columns()
        
        def safe_sorted(series):
            if series is None or len(series) == 0:
                return []
            unique_vals = series.unique().tolist()
            str_vals = [str(x) if pd.notna(x) else '' for x in unique_vals]
            str_vals = [x for x in str_vals if x]
            return sorted(str_vals)
        
        self.filter_options = {
            'flight_types': safe_sorted(self.df_all['Type of Flight']) if 'Type of Flight' in self.df_all.columns else [],
            'aircraft_models': safe_sorted(self.df_all['Aircraft_Model']) if 'Aircraft_Model' in self.df_all.columns else [],
            'aircraft_prefixes': safe_sorted(self.df_all['Aircraft_Prefix']) if 'Aircraft_Prefix' in self.df_all.columns else [],
            'sales_models': safe_sorted(self.df_all['Sales Model']) if 'Sales Model' in self.df_all.columns else [],
            'classifications': safe_sorted(self.df_all['Classification']) if 'Classification' in self.df_all.columns else [],
        }
    
    def apply_filters(self, filters=None):
        """Apply current filters to data"""
        if self.df_all is None:
            return
        
        if filters is not None:
            self.filters.update(filters)
        
        self.df_filtered = self.df_all.copy()
        
        if 'Is_Commercial' not in self.df_filtered.columns or 'Flight_Category' not in self.df_filtered.columns:
            self.df_filtered = self._classify_flight_type(self.df_filtered)
        
        self._ensure_numeric_columns()
        
        if self.filters.get('flight_types') and len(self.filters['flight_types']) > 0:
            if 'Type of Flight' in self.df_filtered.columns:
                self.df_filtered = self.df_filtered[self.df_filtered['Type of Flight'].isin(self.filters['flight_types'])]
        
        if self.filters.get('aircraft_models') and len(self.filters['aircraft_models']) > 0:
            if 'Aircraft_Model' in self.df_filtered.columns:
                self.df_filtered = self.df_filtered[self.df_filtered['Aircraft_Model'].isin(self.filters['aircraft_models'])]
        
        if self.filters.get('aircraft_prefixes') and len(self.filters['aircraft_prefixes']) > 0:
            if 'Aircraft_Prefix' in self.df_filtered.columns:
                self.df_filtered = self.df_filtered[self.df_filtered['Aircraft_Prefix'].isin(self.filters['aircraft_prefixes'])]
        
        if self.filters.get('sales_models') and len(self.filters['sales_models']) > 0:
            if 'Sales Model' in self.df_filtered.columns:
                self.df_filtered = self.df_filtered[self.df_filtered['Sales Model'].isin(self.filters['sales_models'])]
        
        if self.filters.get('classifications') and len(self.filters['classifications']) > 0:
            if 'Classification' in self.df_filtered.columns:
                self.df_filtered = self.df_filtered[self.df_filtered['Classification'].isin(self.filters['classifications'])]
        
        if self.filters.get('months') and len(self.filters['months']) > 0:
            if 'Sheet_Month' in self.df_filtered.columns:
                self.df_filtered['Sheet_Month'] = pd.to_numeric(self.df_filtered['Sheet_Month'], errors='coerce').fillna(0).astype(int)
                self.df_filtered = self.df_filtered[self.df_filtered['Sheet_Month'].isin(self.filters['months'])]
        
        if self.filters.get('date_start') is not None and 'Date_Parsed' in self.df_filtered.columns:
            self.df_filtered = self.df_filtered[self.df_filtered['Date_Parsed'] >= self.filters['date_start']]
        
        if self.filters.get('date_end') is not None and 'Date_Parsed' in self.df_filtered.columns:
            self.df_filtered = self.df_filtered[self.df_filtered['Date_Parsed'] <= self.filters['date_end']]
        
        if self.filters.get('revenue_min') is not None and 'Revenue' in self.df_filtered.columns:
            self.df_filtered['Revenue'] = pd.to_numeric(self.df_filtered['Revenue'], errors='coerce').fillna(0)
            self.df_filtered = self.df_filtered[self.df_filtered['Revenue'] >= self.filters['revenue_min']]
        
        if self.filters.get('revenue_max') is not None and 'Revenue' in self.df_filtered.columns:
            self.df_filtered['Revenue'] = pd.to_numeric(self.df_filtered['Revenue'], errors='coerce').fillna(0)
            self.df_filtered = self.df_filtered[self.df_filtered['Revenue'] <= self.filters['revenue_max']]
        
        if self.filters.get('pax_min') is not None and 'Pax' in self.df_filtered.columns:
            self.df_filtered['Pax'] = pd.to_numeric(self.df_filtered['Pax'], errors='coerce').fillna(0).astype(int)
            self.df_filtered = self.df_filtered[self.df_filtered['Pax'] >= self.filters['pax_min']]
        
        if self.filters.get('pax_max') is not None and 'Pax' in self.df_filtered.columns:
            self.df_filtered['Pax'] = pd.to_numeric(self.df_filtered['Pax'], errors='coerce').fillna(0).astype(int)
            self.df_filtered = self.df_filtered[self.df_filtered['Pax'] <= self.filters['pax_max']]
        
        if self.filters.get('landings_min') is not None and 'Landings' in self.df_filtered.columns:
            self.df_filtered['Landings'] = pd.to_numeric(self.df_filtered['Landings'], errors='coerce').fillna(1).astype(int)
            self.df_filtered = self.df_filtered[self.df_filtered['Landings'] >= self.filters['landings_min']]
        
        if self.filters.get('landings_max') is not None and 'Landings' in self.df_filtered.columns:
            self.df_filtered['Landings'] = pd.to_numeric(self.df_filtered['Landings'], errors='coerce').fillna(1).astype(int)
            self.df_filtered = self.df_filtered[self.df_filtered['Landings'] <= self.filters['landings_max']]
        
        if self.filters.get('hour_start') is not None and 'Start_Hour' in self.df_filtered.columns:
            self.df_filtered['Start_Hour'] = pd.to_numeric(self.df_filtered['Start_Hour'], errors='coerce').fillna(0)
            self.df_filtered = self.df_filtered[self.df_filtered['Start_Hour'] >= self.filters['hour_start']]
        
        if self.filters.get('hour_end') is not None and 'Start_Hour' in self.df_filtered.columns:
            self.df_filtered['Start_Hour'] = pd.to_numeric(self.df_filtered['Start_Hour'], errors='coerce').fillna(0)
            self.df_filtered = self.df_filtered[self.df_filtered['Start_Hour'] <= self.filters['hour_end']]
        
        if not self.filters.get('include_empty_leg', True) and 'Type of Flight' in self.df_filtered.columns:
            self.df_filtered = self.df_filtered[~self.df_filtered['Type of Flight'].str.contains('Empty Leg', case=False, na=False)]
        
        if not self.filters.get('include_hangar_flight', True) and 'Type of Flight' in self.df_filtered.columns:
            self.df_filtered = self.df_filtered[~self.df_filtered['Type of Flight'].str.contains('Hangar', case=False, na=False)]
        
        self._ensure_numeric_columns()
    
    def calculate_distances(self, distance_calculator=None):
        """Calculate flight distances. Returns total nautical miles (from filtered data)."""
        total_nm = 0.0
        for target_df in [self.df_all, self.df_filtered]:
            if target_df is not None and len(target_df) > 0:
                if distance_calculator:
                    nm_series, calc_series = distance_calculator.calculate_df_distances(target_df)
                    target_df['Distance_NM'] = nm_series
                    target_df['Distance_Calculated'] = calc_series
                else:
                    # Fallback: estimate from flight time (avg 400 nm/hour)
                    if 'Flight_Time_Hours' in target_df.columns:
                        target_df['Distance_NM'] = pd.to_numeric(target_df['Flight_Time_Hours'], errors='coerce').fillna(0) * 400
                    else:
                        target_df['Distance_NM'] = 0.0
                    target_df['Distance_Calculated'] = False
        if self.df_filtered is not None and len(self.df_filtered) > 0 and 'Distance_NM' in self.df_filtered.columns:
            total_nm = float(self.df_filtered['Distance_NM'].sum())
        return total_nm
    
    def categorize_flights(self):
        """Categorize flights into different types"""
        pass
