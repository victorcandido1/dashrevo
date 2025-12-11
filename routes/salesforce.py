"""
Salesforce API Routes
Handles Salesforce HTML report processing and analytics
"""

from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
import os
from pathlib import Path
from datetime import datetime

from services.salesforce_processor import SalesforceProcessor, RotaerProcessor

salesforce_bp = Blueprint('salesforce', __name__)

# Global processor instances
_salesforce_processor = None
_rotaer_processor = None


def get_rotaer_processor():
    """Get or create ROTAER processor instance"""
    global _rotaer_processor
    if _rotaer_processor is None:
        _rotaer_processor = RotaerProcessor()
    return _rotaer_processor


def get_salesforce_processor():
    """Get or create Salesforce processor instance"""
    global _salesforce_processor
    if _salesforce_processor is None:
        _salesforce_processor = SalesforceProcessor(get_rotaer_processor())
    return _salesforce_processor


@salesforce_bp.route('/status')
def get_status():
    """Get Salesforce data status"""
    processor = get_salesforce_processor()
    
    if processor.df is None or len(processor.df) == 0:
        return jsonify({
            'loaded': False,
            'message': 'No Salesforce data loaded'
        })
    
    return jsonify({
        'loaded': True,
        'total_records': len(processor.df),
        'total_revenue': float(processor.df['Receita'].sum())
    })


@salesforce_bp.route('/upload', methods=['POST'])
def upload_salesforce():
    """Upload and process Salesforce HTML report"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith(('.html', '.htm', '.xls')):
        return jsonify({'error': 'File must be HTML or XLS format'}), 400
    
    try:
        # Save uploaded file
        upload_folder = current_app.config.get('UPLOAD_FOLDER', Path('uploads'))
        if isinstance(upload_folder, Path):
            upload_folder = str(upload_folder)
        os.makedirs(upload_folder, exist_ok=True)
        
        filename = secure_filename(f"salesforce_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Process Salesforce report
        processor = get_salesforce_processor()
        result = processor.process(filepath)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Salesforce report processed successfully',
                'total_records': result['total_records'],
                'total_revenue': result['total_revenue']
            })
        else:
            return jsonify({'error': result.get('error', 'Processing failed')}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@salesforce_bp.route('/upload-rotaer', methods=['POST'])
def upload_rotaer():
    """Upload ROTAER Excel file for distance calculations"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'File must be Excel format'}), 400
    
    try:
        # Save uploaded file
        upload_folder = current_app.config.get('UPLOAD_FOLDER', Path('uploads'))
        if isinstance(upload_folder, Path):
            upload_folder = str(upload_folder)
        os.makedirs(upload_folder, exist_ok=True)
        
        filename = secure_filename(f"rotaer_{file.filename}")
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Load ROTAER
        rotaer = get_rotaer_processor()
        count = rotaer.load_rotaer(filepath)
        
        return jsonify({
            'success': True,
            'message': f'ROTAER loaded with {count} coordinates',
            'coordinates_loaded': count
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@salesforce_bp.route('/summary')
def get_summary():
    """Get Salesforce data summary"""
    processor = get_salesforce_processor()
    summary = processor.get_summary()
    
    if summary is None:
        return jsonify({'error': 'No data available'}), 400
    
    return jsonify(summary)


@salesforce_bp.route('/monthly')
def get_monthly_analysis():
    """Get monthly analysis"""
    processor = get_salesforce_processor()
    monthly = processor.get_monthly_analysis()
    
    return jsonify({'data': monthly})


@salesforce_bp.route('/flight-types')
def get_flight_types():
    """Get flight type analysis"""
    processor = get_salesforce_processor()
    by_type = processor.get_flight_type_analysis()
    
    return jsonify({'data': by_type})


@salesforce_bp.route('/routes')
def get_routes():
    """Get routes analysis"""
    processor = get_salesforce_processor()
    routes = processor.get_route_analysis()
    
    return jsonify({'data': routes})


@salesforce_bp.route('/aircraft')
def get_aircraft():
    """Get aircraft analysis"""
    processor = get_salesforce_processor()
    by_aircraft = processor.get_aircraft_analysis()
    
    return jsonify({'data': by_aircraft})


@salesforce_bp.route('/daily')
def get_daily():
    """Get daily analysis for charts"""
    processor = get_salesforce_processor()
    daily = processor.get_daily_analysis()
    
    return jsonify(daily)


@salesforce_bp.route('/export')
def export_salesforce():
    """Export Salesforce data to CSV"""
    processor = get_salesforce_processor()
    
    if processor.df is None or len(processor.df) == 0:
        return jsonify({'error': 'No data to export'}), 400
    
    try:
        # Create export file
        cache_dir = current_app.config.get('CACHE_DIR', Path('.cache'))
        export_path = Path(cache_dir) / f"salesforce_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        if processor.export_to_csv(str(export_path)):
            return send_file(
                str(export_path),
                mimetype='text/csv',
                as_attachment=True,
                download_name='salesforce_data.csv'
            )
        else:
            return jsonify({'error': 'Export failed'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@salesforce_bp.route('/data')
def get_data():
    """Get all Salesforce data"""
    processor = get_salesforce_processor()
    
    if processor.df is None:
        return jsonify({'error': 'No data available'}), 400
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    
    df = processor.df.copy()
    df['Data_Voo'] = df['Data_Voo'].astype(str)
    
    total = len(df)
    start = (page - 1) * per_page
    end = start + per_page
    
    # Select relevant columns
    columns = ['Numero_Voo', 'Data_Voo', 'Rota', 'Tipo_Voo', 'Prefixo', 'Modelo', 
               'Passageiros', 'Receita', 'Distancia_NM', 'RPNM']
    available_cols = [c for c in columns if c in df.columns]
    
    return jsonify({
        'data': df[available_cols].iloc[start:end].to_dict('records'),
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })










