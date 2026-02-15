"""
Distance Calculator Service
Calculates flight distances from coordinates or estimates from flight time
"""
import pandas as pd
import numpy as np
import math

# Common Brazilian airport coordinates (ICAO -> lat, lon)
AIRPORT_COORDS = {
    'SBGR': (-23.4356, -46.4731),
    'SBSP': (-23.6261, -46.6564),
    'SBKP': (-23.0074, -47.1345),
    'SBSJ': (-23.2289, -45.8625),
    'SBJD': (-23.1817, -46.9436),
    'SDCO': (-23.4803, -47.4900),
    'SBRJ': (-22.9104, -43.1631),
    'SBGL': (-22.8090, -43.2506),
    'SBCF': (-19.6244, -43.9719),
    'SBCT': (-25.5285, -49.1758),
    'SBBH': (-19.8517, -43.9508),
    'SBBR': (-15.8711, -47.9186),
    'SBSV': (-12.9108, -38.3310),
    'SBRF': (-8.1268, -34.9236),
    'SBPA': (-29.9944, -51.1714),
    'SBFL': (-27.6702, -48.5525),
}


def haversine_nm(lat1, lon1, lat2, lon2):
    """Calculate distance in nautical miles between two points using Haversine formula"""
    R = 3440.065  # Earth radius in nautical miles
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


class DistanceCalculator:
    """Calculate flight distances from Departure/Arrival airports or Flight_Time_Hours"""
    
    def calculate_df_distances(self, df):
        """
        Calculate distances for a dataframe.
        Returns (distance_series, calculated_series) where calculated is True for coord-based, False for estimated.
        """
        n = len(df)
        distances = np.zeros(n)
        calculated = np.zeros(n, dtype=bool)
        
        dep_col = 'Departure' if 'Departure' in df.columns else None
        arr_col = 'Arrival' if 'Arrival' in df.columns else None
        
        for i in range(n):
            dep = str(df.iloc[i][dep_col]).strip().upper()[:4] if dep_col else None
            arr = str(df.iloc[i][arr_col]).strip().upper()[:4] if arr_col else None
            
            if dep and arr and dep in AIRPORT_COORDS and arr in AIRPORT_COORDS:
                lat1, lon1 = AIRPORT_COORDS[dep]
                lat2, lon2 = AIRPORT_COORDS[arr]
                distances[i] = haversine_nm(lat1, lon1, lat2, lon2)
                calculated[i] = True
            elif 'Flight_Time_Hours' in df.columns:
                hours = df.iloc[i]['Flight_Time_Hours']
                try:
                    hours = float(pd.to_numeric(hours, errors='coerce') or 0)
                except (TypeError, ValueError):
                    hours = 0
                distances[i] = hours * 400  # Est. 400 nm/hour
                calculated[i] = False
            else:
                distances[i] = 0
                calculated[i] = False
        
        return pd.Series(distances, index=df.index), pd.Series(calculated, index=df.index)
    
    def get_coverage_stats(self, df):
        """Get statistics on distance calculation coverage"""
        if df is None or len(df) == 0:
            return {'coverage': 0, 'missing_codes': []}
        
        if 'Distance_Calculated' not in df.columns:
            return {'coverage': 0, 'missing_codes': []}
        
        calculated_count = int(df['Distance_Calculated'].sum())
        total = len(df)
        coverage = (calculated_count / total * 100) if total > 0 else 0
        
        missing = []
        if 'Departure' in df.columns and 'Arrival' in df.columns:
            for _, row in df[~df['Distance_Calculated']].iterrows():
                dep, arr = str(row.get('Departure', '')).strip()[:4], str(row.get('Arrival', '')).strip()[:4]
                if dep and arr and (dep not in AIRPORT_COORDS or arr not in AIRPORT_COORDS):
                    missing.append(f"{dep}-{arr}")
            missing = list(set(missing))[:20]
        
        return {'coverage': round(coverage, 1), 'missing_codes': missing}


_calculator = None


def get_distance_calculator():
    global _calculator
    if _calculator is None:
        _calculator = DistanceCalculator()
    return _calculator
