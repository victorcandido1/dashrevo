"""
Cache Service for Flight Dashboard
Handles automatic saving and loading of processor state
"""
import pickle
import pandas as pd
from pathlib import Path
from datetime import datetime
import os
from config import Config
from data_processor import DataProcessor


class CacheService:
    """Service for caching processor state"""
    
    def __init__(self, cache_dir=None):
        if cache_dir is None:
            cache_dir = Config.CACHE_FOLDER
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / 'processor_cache.pkl'
        self.metadata_file = self.cache_dir / 'cache_metadata.json'
    
    def save_processor_state(self, processor):
        """Save processor state to cache"""
        try:
            # Save processor dataframes
            cache_data = {
                'df_all': processor.df_all,
                'df_filtered': processor.df_filtered,
                'df_base': processor.df_base,
                'df_shuttle': processor.df_shuttle,
                'df_shuttle_fc': processor.df_shuttle_fc,
                'df_shuttle_total': processor.df_shuttle_total,
                'df_charter': processor.df_charter,
                'df_fc_charter': processor.df_fc_charter,
                'df_marketing': processor.df_marketing,
                'df_courtesy': processor.df_courtesy,
                'df_empty_legs': processor.df_empty_legs,
                'df_hangar_flights': processor.df_hangar_flights,
                'filters': processor.filters,
                'filter_options': processor.filter_options,
                'file_path': str(processor.file_path) if processor.file_path else None
            }
            
            # Save to pickle file
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Save metadata
            import json
            metadata = {
                'saved_at': datetime.now().isoformat(),
                'total_records': len(processor.df_all) if processor.df_all is not None else 0,
                'filtered_records': len(processor.df_filtered) if processor.df_filtered is not None else 0,
                'file_path': str(processor.file_path) if processor.file_path else None
            }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✓ Cache salvo: {len(processor.df_all) if processor.df_all is not None else 0} registros")
            return True
            
        except Exception as e:
            print(f"Erro ao salvar cache: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_processor_state(self):
        """Load processor state from cache"""
        if not self.cache_file.exists():
            return None
        
        try:
            # Load from pickle file
            with open(self.cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Create new processor instance
            processor = DataProcessor(None)
            
            # Restore dataframes
            processor.df_all = cache_data.get('df_all')
            processor.df_filtered = cache_data.get('df_filtered')
            processor.df_base = cache_data.get('df_base')
            processor.df_shuttle = cache_data.get('df_shuttle')
            processor.df_shuttle_fc = cache_data.get('df_shuttle_fc')
            processor.df_shuttle_total = cache_data.get('df_shuttle_total')
            processor.df_charter = cache_data.get('df_charter')
            processor.df_fc_charter = cache_data.get('df_fc_charter')
            processor.df_marketing = cache_data.get('df_marketing')
            processor.df_courtesy = cache_data.get('df_courtesy')
            processor.df_empty_legs = cache_data.get('df_empty_legs')
            processor.df_hangar_flights = cache_data.get('df_hangar_flights')
            processor.filters = cache_data.get('filters', {})
            processor.filter_options = cache_data.get('filter_options', {})
            processor.file_path = cache_data.get('file_path')
            
            # Ensure numeric columns are properly typed
            processor._ensure_numeric_columns()
            
            # Ensure new columns exist (for backward compatibility with old cache)
            if processor.df_all is not None and 'Is_Commercial' not in processor.df_all.columns:
                processor.df_all = processor._classify_flight_type(processor.df_all)
            if processor.df_filtered is not None and 'Is_Commercial' not in processor.df_filtered.columns:
                processor.df_filtered = processor._classify_flight_type(processor.df_filtered)
            
            print(f"✓ Cache carregado: {len(processor.df_all) if processor.df_all is not None else 0} registros")
            return processor
            
        except Exception as e:
            print(f"Erro ao carregar cache: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def cache_exists(self):
        """Check if cache exists"""
        return self.cache_file.exists()
    
    def get_cache_info(self):
        """Get cache metadata"""
        if not self.metadata_file.exists():
            return None
        
        try:
            import json
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def clear_cache(self):
        """Clear cache files"""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
            if self.metadata_file.exists():
                self.metadata_file.unlink()
            return True
        except Exception as e:
            print(f"Erro ao limpar cache: {e}")
            return False


# Global cache service instance
_cache_service = None

def get_cache_service():
    """Get or create cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service

