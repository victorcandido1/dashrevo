"""
Salesforce Processor Service for Flight Dashboard Web
Processes Salesforce HTML reports and provides analytics
"""

import pandas as pd
import numpy as np
import os
import re
from math import radians, sin, cos, sqrt, asin
from datetime import datetime
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


# Aircraft model mapping
AERONAVE_MODELO = {
    'PR-OMH': 'EC155',
    'PR-OMB': 'EC155',
    'PR-OOE': 'EC135',
    'PS-HAH': 'H145'
}

# Passenger capacity per model
CAPACIDADE_PAX = {
    'EC155': 6,
    'EC135': 5,
    'H145': 5
}

# Status priority
STATUS_PRIORITY = {
    'Pago': 0,
    'Executado': 1,
    'Confirmado': 2,
    'Pré-Reservado': 3
}


def parse_brl_currency(series):
    """Parse BRL currency string to float"""
    def _parse_value(val):
        if pd.isna(val):
            return None
        val_str = str(val).strip()
        # Remove currency symbols and spaces
        val_str = val_str.replace('R$', '').replace('$', '').replace(' ', '')
        # Handle thousands and decimal separators
        if ',' in val_str and '.' in val_str:
            # Format: 1.234,56
            val_str = val_str.replace('.', '').replace(',', '.')
        elif ',' in val_str:
            # Format: 1234,56 or 1,56
            if val_str.count(',') == 1 and len(val_str.split(',')[1]) == 2:
                val_str = val_str.replace(',', '.')
            else:
                val_str = val_str.replace(',', '')
        try:
            return float(val_str)
        except:
            return None
    
    return pd.Series([_parse_value(v) for v in series])


class RotaerProcessor:
    """Process ROTAER file and calculate distances"""
    
    def __init__(self):
        self.rotaer_coords = {}
        # Default coordinates for common heliports
        self.default_coords = {
            'SBGR': {'lat': -23.4356, 'lon': -46.4731, 'nome': 'Guarulhos'},
            'SDCO': {'lat': -23.5207, 'lon': -46.8556, 'nome': 'Alphaville'},
            'SBSP': {'lat': -23.6261, 'lon': -46.6564, 'nome': 'Congonhas'},
            'SBJD': {'lat': -23.1814, 'lon': -46.9436, 'nome': 'Jundiaí'},
            'SBRJ': {'lat': -22.9108, 'lon': -43.1631, 'nome': 'Santos Dumont'},
            'SBGL': {'lat': -22.8089, 'lon': -43.2436, 'nome': 'Galeão'},
            'SDKM': {'lat': -23.5489, 'lon': -46.6531, 'nome': 'Morumbi'},
            'SSXK': {'lat': -23.7019, 'lon': -46.6978, 'nome': 'Autódromo Interlagos'}
        }
        self.rotaer_coords.update(self.default_coords)
    
    def load_rotaer(self, rotaer_path):
        """Load coordinates from ROTAER Excel file"""
        try:
            df_rotaer = pd.read_excel(rotaer_path)
            
            # Find columns
            col_icao = None
            col_lat = None
            col_lon = None
            
            for col in df_rotaer.columns:
                col_lower = str(col).lower()
                if col_icao is None and ('icao' in col_lower or 'código' in col_lower):
                    col_icao = col
                if col_lat is None and 'lat' in col_lower:
                    col_lat = col
                if col_lon is None and ('lon' in col_lower or 'long' in col_lower):
                    col_lon = col
            
            if col_icao is None:
                col_icao = df_rotaer.columns[0]
            
            count = 0
            for _, row in df_rotaer.iterrows():
                icao = str(row.get(col_icao, '')).strip().upper()
                if icao and icao != 'NAN' and len(icao) >= 4:
                    lat = row.get(col_lat, None)
                    lon = row.get(col_lon, None)
                    
                    if pd.notna(lat) and pd.notna(lon):
                        try:
                            lat_float = float(lat)
                            lon_float = float(lon)
                            if -90 <= lat_float <= 90 and -180 <= lon_float <= 180:
                                self.rotaer_coords[icao] = {
                                    'lat': lat_float,
                                    'lon': lon_float,
                                    'nome': icao
                                }
                                count += 1
                        except:
                            continue
            
            return count
        except Exception as e:
            print(f"Error loading ROTAER: {e}")
            return 0
    
    def haversine(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points in nautical miles"""
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Earth radius in km
        return (c * r) / 1.852  # Convert to nautical miles
    
    def extract_icao(self, text):
        """Extract ICAO code from text"""
        text = str(text).strip().upper()
        
        # Direct ICAO code
        if re.match(r'^[A-Z][A-Z0-9]{3}$', text):
            return text
        
        # ICAO before " - "
        if ' - ' in text:
            icao = text.split(' - ')[0].strip()
            if re.match(r'^[A-Z][A-Z0-9]{3}$', icao):
                return icao
        
        # Find ICAO in text
        icaos = re.findall(r'\b([A-Z][A-Z0-9]{3})\b', text)
        if icaos:
            return icaos[0]
        
        # Name to ICAO mapping for common locations
        name_to_icao = {
            'GUARULHOS': 'SBGR',
            'GRU': 'SBGR',
            'ALPHAVILLE': 'SDCO',
            'CONGONHAS': 'SBSP',
            'SANTOS DUMONT': 'SBRJ',
            'GALEAO': 'SBGL',
            'JUNDIAI': 'SBJD',
            'MORUMBI': 'SDKM',
            'INTERLAGOS': 'SSXK',
            'AUTODROMO': 'SSXK'
        }
        
        text_upper = text.upper()
        for name, icao in name_to_icao.items():
            if name in text_upper:
                return icao
        
        return text
    
    def calculate_distance(self, origin, destination):
        """Calculate distance between origin and destination"""
        origin_icao = self.extract_icao(origin)
        dest_icao = self.extract_icao(destination)
        
        if origin_icao in self.rotaer_coords and dest_icao in self.rotaer_coords:
            orig = self.rotaer_coords[origin_icao]
            dest = self.rotaer_coords[dest_icao]
            return round(self.haversine(orig['lat'], orig['lon'], dest['lat'], dest['lon']), 1)
        
        return 0


class SalesforceProcessor:
    """Process Salesforce HTML reports"""
    
    def __init__(self, rotaer_processor=None):
        self.rotaer = rotaer_processor if rotaer_processor else RotaerProcessor()
        self.df = None
    
    def process(self, salesforce_path):
        """Process Salesforce HTML report"""
        if BeautifulSoup is None:
            return {'success': False, 'error': 'BeautifulSoup not installed. Run: pip install beautifulsoup4'}
        
        try:
            # Try different encodings
            content = None
            for encoding in ['iso-8859-1', 'utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(salesforce_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except:
                    continue
            
            if content is None:
                return {'success': False, 'error': 'Could not read file with any encoding'}
            
            soup = BeautifulSoup(content, 'html.parser')
            table = soup.find('table')
            
            if table is None:
                return {'success': False, 'error': 'No table found in HTML file'}
            
            headers = [th.get_text(strip=True) for th in table.find_all('th')]
            rows_data = []
            for tr in table.find_all('tr')[1:]:
                cells = tr.find_all('td')
                row = [td.get_text(strip=True) for td in cells]
                if len(row) == len(headers):
                    rows_data.append(row)
            
            df = pd.DataFrame(rows_data, columns=headers)
            
            # Parse revenue
            if 'Valor Total' in df.columns:
                df['Receita'] = parse_brl_currency(df['Valor Total']).fillna(0.0)
            else:
                df['Receita'] = 0.0
            
            # Find flight number column
            voo_col = None
            for col in df.columns:
                col_lower = str(col).lower()
                if ('número' in col_lower or 'numero' in col_lower) and 'voo' in col_lower:
                    voo_col = col
                    break
            
            if voo_col is None:
                voo_col = df.columns[0]
            
            # Parse date
            if 'Voo: Data e Hora do Voo' in df.columns:
                df['Data_Voo'] = pd.to_datetime(df['Voo: Data e Hora do Voo'], dayfirst=True, errors='coerce')
            else:
                df['Data_Voo'] = pd.to_datetime('today')
            
            df['Ano'] = df['Data_Voo'].dt.year
            df['Mes'] = df['Data_Voo'].dt.month
            df['Mes_Nome'] = df['Data_Voo'].dt.strftime('%Y-%m')
            
            # Parse routes
            if 'Voo: Rota (Extenso)' in df.columns:
                df['Origem'] = df['Voo: Rota (Extenso)'].str.split(' > ').str[0].str.strip()
                df['Destino'] = df['Voo: Rota (Extenso)'].str.split(' > ').str[-1].str.strip()
            elif 'Departure' in df.columns and 'Arrival' in df.columns:
                df['Origem'] = df['Departure'].str.strip()
                df['Destino'] = df['Arrival'].str.strip()
            else:
                df['Origem'] = ''
                df['Destino'] = ''
            
            df['Rota'] = df['Origem'] + ' → ' + df['Destino']
            
            # Extract ICAO codes for route
            df['Rota_ICAO'] = df.apply(
                lambda row: f"{self.rotaer.extract_icao(row['Origem'])} → {self.rotaer.extract_icao(row['Destino'])}",
                axis=1
            )
            
            df['Numero_Voo'] = df[voo_col]
            
            # Aircraft info
            if 'Voo: Prefixo' in df.columns:
                df['Prefixo'] = df['Voo: Prefixo']
                df['Modelo'] = df['Prefixo'].map(AERONAVE_MODELO).fillna('Desconhecido')
            else:
                df['Prefixo'] = ''
                df['Modelo'] = 'Desconhecido'
            
            # Flight type
            if 'Voo: Tipo' in df.columns:
                df['Tipo_Voo'] = df['Voo: Tipo'].apply(self._normalize_flight_type)
            else:
                df['Tipo_Voo'] = 'Outros'
            
            # Passengers
            if 'Voo: Contador Passageiros' in df.columns:
                df['Passageiros'] = pd.to_numeric(df['Voo: Contador Passageiros'], errors='coerce').fillna(0)
            else:
                df['Passageiros'] = 0
            
            # Adjusted passengers for charter/full cabin
            df['Passageiros_Ajustado'] = df.apply(
                lambda row: CAPACIDADE_PAX.get(row['Modelo'], row['Passageiros']) 
                if row['Tipo_Voo'] in ['Charter', 'Full Cabin'] 
                else row['Passageiros'], 
                axis=1
            )
            
            # Calculate distance
            df['Distancia_NM'] = df.apply(
                lambda row: self.rotaer.calculate_distance(row['Origem'], row['Destino']),
                axis=1
            )
            
            # Revenue per nautical mile
            df['RPNM'] = df.apply(
                lambda row: row['Receita'] / row['Distancia_NM'] 
                if row['Distancia_NM'] > 0 and row['Receita'] > 0 
                else 0,
                axis=1
            )
            
            self.df = df
            
            return {
                'success': True,
                'total_records': len(df),
                'total_revenue': float(df['Receita'].sum()),
                'columns': df.columns.tolist()
            }
            
        except Exception as e:
            print(f"Error processing Salesforce: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def _normalize_flight_type(self, tipo):
        """Normalize flight type"""
        if pd.isna(tipo) or str(tipo).strip() == '':
            return 'Outros'
        
        tipo_str = str(tipo).upper()
        if 'SHUTTLE' in tipo_str:
            return 'Shuttle'
        elif 'CHARTER' in tipo_str:
            return 'Charter'
        elif 'FULL CABIN' in tipo_str or 'FULL-CABIN' in tipo_str:
            return 'Full Cabin'
        else:
            return 'Outros'
    
    # ============================================================
    # ANALYTICS METHODS
    # ============================================================
    
    def get_summary(self):
        """Get summary statistics"""
        if self.df is None or len(self.df) == 0:
            return None
        
        df = self.df
        
        return {
            'total_flights': len(df),
            'total_revenue': float(df['Receita'].sum()),
            'total_passengers': int(df['Passageiros'].sum()),
            'avg_revenue_per_flight': float(df['Receita'].mean()),
            'total_distance_nm': float(df['Distancia_NM'].sum()),
            'avg_rpnm': float(df[df['RPNM'] > 0]['RPNM'].mean()) if len(df[df['RPNM'] > 0]) > 0 else 0,
            'date_range': {
                'start': df['Data_Voo'].min().strftime('%Y-%m-%d') if pd.notna(df['Data_Voo'].min()) else None,
                'end': df['Data_Voo'].max().strftime('%Y-%m-%d') if pd.notna(df['Data_Voo'].max()) else None
            }
        }
    
    def get_monthly_analysis(self):
        """Get monthly analysis"""
        if self.df is None or len(self.df) == 0:
            return []
        
        monthly = self.df.groupby('Mes_Nome').agg({
            'Receita': 'sum',
            'Passageiros': 'sum',
            'Numero_Voo': 'count',
            'RPNM': 'mean'
        }).reset_index()
        monthly.columns = ['month', 'revenue', 'passengers', 'flights', 'avg_rpnm']
        monthly = monthly.sort_values('month')
        
        return monthly.to_dict('records')
    
    def get_flight_type_analysis(self):
        """Get analysis by flight type"""
        if self.df is None or len(self.df) == 0:
            return []
        
        by_type = self.df.groupby('Tipo_Voo').agg({
            'Receita': 'sum',
            'Passageiros': 'sum',
            'Numero_Voo': 'count'
        }).reset_index()
        by_type.columns = ['type', 'revenue', 'passengers', 'flights']
        
        return by_type.to_dict('records')
    
    def get_route_analysis(self):
        """Get routes analysis"""
        if self.df is None or len(self.df) == 0:
            return []
        
        routes = self.df.groupby('Rota_ICAO').agg({
            'Receita': 'sum',
            'Passageiros': 'sum',
            'Numero_Voo': 'count',
            'RPNM': 'mean'
        }).reset_index()
        routes.columns = ['route', 'revenue', 'passengers', 'flights', 'avg_rpnm']
        routes = routes.sort_values('revenue', ascending=False)
        
        return routes.head(20).to_dict('records')
    
    def get_aircraft_analysis(self):
        """Get analysis by aircraft"""
        if self.df is None or len(self.df) == 0:
            return []
        
        by_aircraft = self.df.groupby(['Prefixo', 'Modelo']).agg({
            'Receita': 'sum',
            'Passageiros': 'sum',
            'Numero_Voo': 'count',
            'Distancia_NM': 'sum'
        }).reset_index()
        by_aircraft.columns = ['prefix', 'model', 'revenue', 'passengers', 'flights', 'total_nm']
        
        return by_aircraft.to_dict('records')
    
    def get_daily_analysis(self):
        """Get daily analysis for charts"""
        if self.df is None or len(self.df) == 0:
            return {'dates': [], 'revenue': [], 'flights': []}
        
        df = self.df.copy()
        df['Date'] = df['Data_Voo'].dt.date
        
        daily = df.groupby('Date').agg({
            'Receita': 'sum',
            'Numero_Voo': 'count'
        }).reset_index()
        daily = daily.sort_values('Date')
        
        return {
            'dates': [d.strftime('%Y-%m-%d') for d in daily['Date']],
            'revenue': daily['Receita'].tolist(),
            'flights': daily['Numero_Voo'].tolist()
        }
    
    def export_to_csv(self, output_path):
        """Export data to CSV"""
        if self.df is None or len(self.df) == 0:
            return False
        
        try:
            self.df.to_csv(output_path, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def to_dict(self):
        """Convert data to dict for JSON serialization"""
        if self.df is None:
            return None
        
        df = self.df.copy()
        df['Data_Voo'] = df['Data_Voo'].astype(str)
        return df.to_dict('records')










