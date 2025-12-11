#!/usr/bin/env python
# coding: utf-8
"""
ICAO to City Name Mapping Module
Converts ICAO airport codes to friendly city names
"""
import pandas as pd
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

# Global cache for mappings
_MAPPING_CACHE = None


def get_custom_mappings():
    """Get custom ICAO to city name overrides (highest priority)"""
    return {
        'SBGR': 'Aeroporto GRU',
        'SBMT': 'Marte',
        'SBSP': 'Congonhas',
        'SBJH': 'Catarina',
        'SDJB': 'Baronesa',
        'SNGL': 'Boa Vista',
        'Barueri': 'Alphaville',
        'Tamboré': 'Alphaville',
        'Santana de Parnaiba': 'Alphaville',
        'Santana de Parnaíba': 'Alphaville',
        'SBKP': 'Viracopos',
        'SBRP': 'Ribeirão Preto',
        'SBCF': 'Confins',
        'SBBR': 'Brasília',
        'SBGL': 'Galeão',
        'SBRJ': 'Santos Dumont',
        'SBSV': 'Salvador',
        'SBRF': 'Recife',
        'SBCT': 'Curitiba',
        'SBPA': 'Porto Alegre',
        'SBFL': 'Florianópolis',
        'SDAI': 'Alphaville',
        'SDSC': 'São Conrado',
        'SDJD': 'Jacarepaguá',
        'SDTF': 'Taubaté',
        'SDJF': 'Juiz de Fora',
        'SDCO': 'Campos',
        'SDRS': 'Rio de Janeiro',
        'SDUN': 'Angra dos Reis',
        'SDIY': 'Ilhabela',
        'SSUM': 'Ubatuba',
        'SDOW': 'Ouro Preto',
        'SDSV': 'Vitória',
        'SDCP': 'Cabo Frio',
        'SDBU': 'Búzios',
        'SIAV': 'Helipark',
        'SIIR': 'Brascan',
        'SWYD': 'Spazio',
        'SDXQ': 'IP Plaza 2',
        'SDMN': 'Cidade Jardim',
        'SIBH': 'Helicidade',
        'SN66': 'Baleia',
        'SDOF': 'Palladium',
        'SSOA': 'Bluetrhee',
        'SJTY': 'Tivoli',
        'SDPT': 'Parque Paulista',
        'SJSL': 'Sírio Libanês',
        'SDHV': 'Einstein',
        'SIF4': 'Grand Brasil',
        'SIDH': 'Brascan Alpha',
        'SDAM': 'Catarina',
        'SDJK': 'Juequehy',
        'SDJH': 'São Roque',
        'SDJG': 'Guarujá',
        'SSXK': 'F1',
    }


def load_rotaer_mappings():
    """Load ICAO mappings from rotaer.xlsx file"""
    try:
        rotaer_paths = [
            Path(__file__).parent.parent / 'rotaer.xlsx',
            Path(__file__).parent / 'rotaer.xlsx',
            Path('../rotaer.xlsx'),
            Path('rotaer.xlsx'),
        ]
        
        df = None
        for path in rotaer_paths:
            if path.exists():
                try:
                    df = pd.read_excel(path)
                    break
                except:
                    continue
        
        if df is None:
            return {}
        
        mapping = {}
        icao_col = None
        name_col = None
        
        for col in df.columns:
            col_lower = str(col).lower()
            if 'icao' in col_lower or 'código' in col_lower:
                icao_col = col
            if 'nome' in col_lower or 'name' in col_lower or 'cidade' in col_lower:
                if name_col is None:
                    name_col = col
        
        if icao_col and name_col:
            for _, row in df.iterrows():
                icao = str(row[icao_col]).strip().upper() if pd.notna(row[icao_col]) else None
                name = str(row[name_col]).strip() if pd.notna(row[name_col]) else None
                
                if icao and name and len(icao) >= 4:
                    icao_code = icao[:4]
                    mapping[icao_code] = name
        
        return mapping
        
    except Exception as e:
        return {}


def get_icao_to_city():
    """Get combined ICAO to city name mapping (cached)"""
    global _MAPPING_CACHE
    
    if _MAPPING_CACHE is not None:
        return _MAPPING_CACHE
    
    custom_mapping = get_custom_mappings()
    rotaer_mapping = load_rotaer_mappings()
    _MAPPING_CACHE = {**rotaer_mapping, **custom_mapping}
    
    return _MAPPING_CACHE


def format_location(icao_code):
    """Format ICAO code to 'CITY NAME (ICAO)' format"""
    if not icao_code or pd.isna(icao_code):
        return 'Unknown'
    
    code_str = str(icao_code).strip()
    if len(code_str) >= 4:
        code = code_str[:4].upper()
    else:
        code = code_str.upper()
    
    custom_mapping = get_custom_mappings()
    if code in custom_mapping:
        city_name = custom_mapping[code]
        if code == 'SSXK':
            return city_name
        return f"{city_name} ({code})"
    
    mapping = get_icao_to_city()
    if code in mapping:
        city_name = mapping[code]
        return f"{city_name} ({code})"
    else:
        return f"{code} ({code})"


def format_route(origin_icao, dest_icao):
    """Format route with city names"""
    origin_fmt = format_location(origin_icao)
    dest_fmt = format_location(dest_icao)
    return f"{origin_fmt} → {dest_fmt}"










