"""
Cost Management Service
Handles aircraft cost configuration and calculations
"""
import json
import os
from pathlib import Path


class CostService:
    """Service for managing aircraft costs"""
    
    DEFAULT_COSTS = {
        'EC135': {
            'fixed_cost_per_hour': 0.0,
            'fuel_cost_per_hour': 0.0,
            'monthly_fixed_cost': 0.0,
            'capacity': 5
        },
        'EC155': {
            'fixed_cost_per_hour': 0.0,
            'fuel_cost_per_hour': 0.0,
            'monthly_fixed_cost': 0.0,
            'capacity': 8
        }
    }
    
    def __init__(self, cache_dir='.cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.costs_file = self.cache_dir / 'costs_config.json'
        self.costs = self._load_costs()
    
    def _load_costs(self):
        """Load costs from cache file"""
        if self.costs_file.exists():
            try:
                with open(self.costs_file, 'r') as f:
                    saved_costs = json.load(f)
                # Merge with defaults to ensure all keys exist
                costs = self.DEFAULT_COSTS.copy()
                for aircraft, values in saved_costs.items():
                    if aircraft in costs:
                        costs[aircraft].update(values)
                    else:
                        costs[aircraft] = values
                return costs
            except Exception as e:
                print(f"Error loading costs: {e}")
                return self.DEFAULT_COSTS.copy()
        return self.DEFAULT_COSTS.copy()
    
    def save_costs(self, costs=None):
        """Save costs to cache file"""
        if costs:
            self.costs = costs
        try:
            with open(self.costs_file, 'w') as f:
                json.dump(self.costs, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving costs: {e}")
            return False
    
    def get_costs(self):
        """Get current costs configuration"""
        return self.costs
    
    def update_aircraft_costs(self, aircraft_model, fixed_per_hour=None, fuel_per_hour=None, monthly_fixed=None, capacity=None):
        """Update costs for a specific aircraft model"""
        if aircraft_model not in self.costs:
            self.costs[aircraft_model] = self.DEFAULT_COSTS.get('EC135', {}).copy()
        
        if fixed_per_hour is not None:
            self.costs[aircraft_model]['fixed_cost_per_hour'] = float(fixed_per_hour)
        if fuel_per_hour is not None:
            self.costs[aircraft_model]['fuel_cost_per_hour'] = float(fuel_per_hour)
        if monthly_fixed is not None:
            self.costs[aircraft_model]['monthly_fixed_cost'] = float(monthly_fixed)
        if capacity is not None:
            self.costs[aircraft_model]['capacity'] = int(capacity)
        
        self.save_costs()
        return self.costs[aircraft_model]
    
    def calculate_flight_cost(self, aircraft_model, flight_time_hours):
        """Calculate cost for a single flight"""
        if aircraft_model not in self.costs:
            return 0.0
        
        cost_config = self.costs[aircraft_model]
        fixed_cost = flight_time_hours * cost_config.get('fixed_cost_per_hour', 0)
        fuel_cost = flight_time_hours * cost_config.get('fuel_cost_per_hour', 0)
        
        return fixed_cost + fuel_cost
    
    def calculate_dataframe_costs(self, df, month_hours_map=None):
        """Calculate costs for an entire dataframe
        
        Args:
            df: DataFrame with 'Aircraft_Model' and 'Flight_Time_Hours' columns
            month_hours_map: Optional dict mapping (aircraft, month) to total hours for monthly allocation
        
        Returns:
            DataFrame with Cost, Fixed_Cost, Fuel_Cost, Monthly_Cost_Allocation columns added
        """
        import pandas as pd
        import numpy as np
        
        if df is None or len(df) == 0:
            return df
        
        df = df.copy()
        
        # Initialize cost columns
        df['Cost'] = 0.0
        df['Fixed_Cost'] = 0.0
        df['Fuel_Cost'] = 0.0
        df['Monthly_Cost_Allocation'] = 0.0
        
        for aircraft_model in df['Aircraft_Model'].unique():
            if aircraft_model not in self.costs:
                continue
            
            mask = df['Aircraft_Model'] == aircraft_model
            aircraft_df = df[mask].copy()
            
            cost_config = self.costs[aircraft_model]
            fixed_per_hour = cost_config.get('fixed_cost_per_hour', 0)
            fuel_per_hour = cost_config.get('fuel_cost_per_hour', 0)
            monthly_cost = cost_config.get('monthly_fixed_cost', 0)
            
            # Calculate direct costs
            aircraft_df['Fixed_Cost'] = aircraft_df['Flight_Time_Hours'].fillna(0) * fixed_per_hour
            aircraft_df['Fuel_Cost'] = aircraft_df['Flight_Time_Hours'].fillna(0) * fuel_per_hour
            
            # Calculate monthly cost allocation
            if monthly_cost > 0 and 'Sheet_Month' in aircraft_df.columns:
                # Count unique aircraft of this model
                if 'Aircraft_Prefix' in aircraft_df.columns:
                    unique_aircraft = aircraft_df['Aircraft_Prefix'].nunique()
                else:
                    unique_aircraft = 1
                
                total_monthly_cost = monthly_cost * unique_aircraft
                
                # Allocate proportionally to flight hours per month
                # Ensure Sheet_Month is numeric before comparison
                aircraft_df_month = aircraft_df.copy()
                aircraft_df_month['Sheet_Month'] = pd.to_numeric(aircraft_df_month['Sheet_Month'], errors='coerce').fillna(0).astype(int)
                for month in aircraft_df_month['Sheet_Month'].unique():
                    month_mask = aircraft_df_month['Sheet_Month'] == month
                    total_month_hours = aircraft_df.loc[month_mask, 'Flight_Time_Hours'].sum()
                    
                    if total_month_hours > 0:
                        aircraft_df.loc[month_mask, 'Monthly_Cost_Allocation'] = (
                            total_monthly_cost * 
                            aircraft_df.loc[month_mask, 'Flight_Time_Hours'] / 
                            total_month_hours
                        )
            
            # Total cost
            aircraft_df['Cost'] = (
                aircraft_df['Fixed_Cost'] + 
                aircraft_df['Fuel_Cost'] + 
                aircraft_df['Monthly_Cost_Allocation']
            )
            
            # Update main dataframe
            df.loc[mask, 'Cost'] = aircraft_df['Cost'].values
            df.loc[mask, 'Fixed_Cost'] = aircraft_df['Fixed_Cost'].values
            df.loc[mask, 'Fuel_Cost'] = aircraft_df['Fuel_Cost'].values
            df.loc[mask, 'Monthly_Cost_Allocation'] = aircraft_df['Monthly_Cost_Allocation'].values
        
        return df
    
    def get_cost_summary(self, df):
        """Get cost summary statistics from a dataframe with costs calculated"""
        if df is None or len(df) == 0 or 'Cost' not in df.columns:
            return {}
        
        summary = {
            'total_cost': float(df['Cost'].sum()),
            'total_fixed_cost': float(df['Fixed_Cost'].sum()) if 'Fixed_Cost' in df.columns else 0,
            'total_fuel_cost': float(df['Fuel_Cost'].sum()) if 'Fuel_Cost' in df.columns else 0,
            'total_monthly_allocation': float(df['Monthly_Cost_Allocation'].sum()) if 'Monthly_Cost_Allocation' in df.columns else 0,
            'avg_cost_per_flight': float(df['Cost'].mean()),
            'avg_cost_per_hour': float(df['Cost'].sum() / df['Flight_Time_Hours'].sum()) if df['Flight_Time_Hours'].sum() > 0 else 0
        }
        
        # By aircraft
        if 'Aircraft_Model' in df.columns:
            summary['by_aircraft'] = {}
            for model in df['Aircraft_Model'].unique():
                model_df = df[df['Aircraft_Model'] == model]
                summary['by_aircraft'][model] = {
                    'total_cost': float(model_df['Cost'].sum()),
                    'flights': len(model_df),
                    'hours': float(model_df['Flight_Time_Hours'].sum()),
                    'avg_cost_per_flight': float(model_df['Cost'].mean()),
                    'avg_cost_per_hour': float(model_df['Cost'].sum() / model_df['Flight_Time_Hours'].sum()) if model_df['Flight_Time_Hours'].sum() > 0 else 0
                }
        
        return summary









