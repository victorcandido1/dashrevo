"""
Configuration settings for Flight Dashboard Web Application
"""
import os
from pathlib import Path


class Config:
    """Flask configuration class"""
    # Base directory
    BASE_DIR = Path(__file__).parent
    
    # Flask configuration
    # In production, set SECRET_KEY as environment variable
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    CACHE_FOLDER = BASE_DIR / '.cache'
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    
    # Maximum upload size (50MB)
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    
    # Data processing settings
    DEFAULT_YEAR_FILTER = 2025  # Filter to 2025 data by default
    
    # Chart settings
    CHART_DPI = 150
    CHART_SIZES = {
        'small': (12, 8),
        'medium': (16, 10),
        'large': (18, 12),
        'xlarge': (20, 14),
        'wide': (18, 8),
        'tall': (12, 16),
        'dashboard': (20, 16)
    }
    
    @staticmethod
    def init_app(app):
        """Initialize application with config"""
        # Create necessary directories
        Config.UPLOAD_FOLDER.mkdir(exist_ok=True)
        Config.CACHE_FOLDER.mkdir(exist_ok=True)


# For backward compatibility - expose as module-level variables
BASE_DIR = Config.BASE_DIR
SECRET_KEY = Config.SECRET_KEY
UPLOAD_FOLDER = Config.UPLOAD_FOLDER
CACHE_FOLDER = Config.CACHE_FOLDER
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS
MAX_CONTENT_LENGTH = Config.MAX_CONTENT_LENGTH
DEFAULT_YEAR_FILTER = Config.DEFAULT_YEAR_FILTER
CHART_DPI = Config.CHART_DPI
CHART_SIZES = Config.CHART_SIZES

