"""
Flight Dashboard Web Application
Main Flask application entry point
"""
from flask import Flask, render_template, session
from config import Config
from routes.api import api_bp, set_data_processor, get_data_processor
from routes.upload import upload_bp
from routes.manifesto import manifesto_bp
from routes.salesforce import salesforce_bp
import os

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)
app.secret_key = Config.SECRET_KEY

# Register blueprints
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(upload_bp, url_prefix='/api')
app.register_blueprint(manifesto_bp, url_prefix='/api/manifesto')
app.register_blueprint(salesforce_bp, url_prefix='/api/salesforce')

# Load cache automatically on first request
@app.before_request
def load_cache_if_needed():
    """Load cached data automatically if not already loaded"""
    processor = get_data_processor()
    if processor is None:
        try:
            from services.cache_service import get_cache_service
            cache = get_cache_service()
            
            if cache.cache_exists():
                processor = cache.load_processor_state()
                if processor is not None:
                    set_data_processor(processor)
        except Exception as e:
            pass  # Silently fail, will try again on next request


@app.route('/')
def index():
    """Main dashboard page"""
    # Flask automatically serves templates with UTF-8 encoding
    return render_template('index.html')


if __name__ == '__main__':
    print("="*60)
    print("Flight Dashboard Web Application")
    print("="*60)
    
    # Get port from environment (for production) or use default
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Running on http://0.0.0.0:{port}")
    print(f"Upload folder: {Config.UPLOAD_FOLDER}")
    print(f"Cache folder: {Config.CACHE_FOLDER}")
    print(f"Debug mode: {debug_mode}")
    print("="*60)
    
    # Load cache before starting server
    try:
        from services.cache_service import get_cache_service
        cache = get_cache_service()
        
        if cache.cache_exists():
            from routes.api import set_data_processor
            processor = cache.load_processor_state()
            if processor is not None:
                set_data_processor(processor)
                cache_info = cache.get_cache_info()
                if cache_info:
                    print(f"✓ Cache carregado: {cache_info.get('total_records', 0):,} registros")
                    print(f"  Salvo em: {cache_info.get('saved_at', 'N/A')}")
        else:
            print("⚠️  Cache não encontrado. Faça upload de dados para gerar cache.")
    except Exception as e:
        print(f"⚠️  Erro ao carregar cache: {e}")
    
    print("="*60)
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)

