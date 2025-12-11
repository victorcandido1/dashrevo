"""
API Routes for Flight Dashboard
REST endpoints for data access and analysis
"""
from flask import Blueprint, jsonify, request
from data_processor import DataProcessor
from services.analysis import AnalysisService
import pandas as pd
import numpy as np
from datetime import datetime

api_bp = Blueprint('api', __name__)

# Global data processor (in production, use proper session management)
_data_processor = None


def ensure_sheet_month_numeric(df):
    """Helper function to ensure Sheet_Month is numeric before any operations"""
    if df is not None and 'Sheet_Month' in df.columns:
        df = df.copy()
        df['Sheet_Month'] = pd.to_numeric(df['Sheet_Month'], errors='coerce').fillna(0).astype(int)
    return df


def get_data_processor():
    """Get or create data processor instance"""
    global _data_processor
    return _data_processor


def set_data_processor(processor):
    """Set data processor instance"""
    global _data_processor
    _data_processor = processor


@api_bp.route('/data/status')
def data_status():
    """Check if data is loaded"""
    processor = get_data_processor()
    
    # Try to load from cache if processor is None
    if processor is None:
        try:
            from services.cache_service import get_cache_service
            cache = get_cache_service()
            if cache.cache_exists():
                processor = cache.load_processor_state()
                if processor is not None:
                    set_data_processor(processor)
        except Exception as e:
            print(f"Erro ao carregar cache: {e}")
    
    if processor is None or processor.df_all is None:
        return jsonify({'loaded': False})
    
    return jsonify({
        'loaded': True,
        'total_records': len(processor.df_all),
        'filtered_records': len(processor.df_filtered) if processor.df_filtered is not None else 0
    })


@api_bp.route('/cache/status')
def cache_status():
    """Check cache status"""
    try:
        from services.cache_service import get_cache_service
        cache = get_cache_service()
        
        cache_info = cache.get_cache_info()
        exists = cache.cache_exists()
        
        return jsonify({
            'exists': exists,
            'info': cache_info
        })
    except Exception as e:
        return jsonify({
            'exists': False,
            'error': str(e)
        })


@api_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear cache"""
    try:
        from services.cache_service import get_cache_service
        cache = get_cache_service()
        cleared = cache.clear_cache()
        
        # Also clear processor
        set_data_processor(None)
        
        return jsonify({
            'success': cleared,
            'message': 'Cache limpo com sucesso' if cleared else 'Erro ao limpar cache'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/dashboard/summary')
def get_dashboard_summary():
    """Get dashboard summary KPIs"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    df = processor.df_filtered
    
    summary = {
        'total_flights': len(df),
        'total_revenue': float(df['Revenue'].sum()) if 'Revenue' in df.columns else 0,
        'total_passengers': int(df['Pax'].sum()) if 'Pax' in df.columns else 0,
        'total_hours': float(df['Flight_Time_Hours'].sum()) if 'Flight_Time_Hours' in df.columns else 0,
        'avg_revenue_per_flight': float(df['Revenue'].mean()) if 'Revenue' in df.columns else 0,
        'avg_passengers_per_flight': float(df['Pax'].mean()) if 'Pax' in df.columns else 0,
    }
    
    return jsonify(summary)


@api_bp.route('/dashboard/category-summary')
def get_category_summary():
    """Get summary statistics by category"""
    processor = get_data_processor()
    
    if processor is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    service = AnalysisService(processor)
    summary = service.get_summary_statistics()
    
    return jsonify(summary)


@api_bp.route('/charts/category-distribution')
def get_category_distribution():
    """Get category distribution for pie chart"""
    processor = get_data_processor()
    
    if processor is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    service = AnalysisService(processor)
    distribution = service.get_category_distribution()
    
    return jsonify(distribution)


@api_bp.route('/charts/revenue-by-category')
def get_revenue_by_category():
    """Get revenue by category for bar chart"""
    processor = get_data_processor()
    
    if processor is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    service = AnalysisService(processor)
    revenue_data = service.get_revenue_by_category()
    
    return jsonify(revenue_data)


@api_bp.route('/analysis/weekday-weekend')
def get_weekday_weekend():
    """Get weekday vs weekend comparison"""
    processor = get_data_processor()
    
    if processor is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    service = AnalysisService(processor)
    comparison = service.get_weekday_weekend_comparison()
    
    if comparison is None:
        return jsonify({'error': 'DayName column not found'}), 400
    
    return jsonify(comparison)


@api_bp.route('/charts/monthly-revenue')
def get_monthly_revenue():
    """Get monthly revenue data for chart"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    df = processor.df_filtered.copy()
    
    if 'Sheet_Month' not in df.columns or 'Revenue' not in df.columns:
        return jsonify({'error': 'Required columns not found'}), 400
    
    # CRITICAL: Convert Sheet_Month to numeric BEFORE groupby
    df = ensure_sheet_month_numeric(df)
    
    monthly = df.groupby('Sheet_Month')['Revenue'].sum().reset_index()
    monthly = monthly.sort_values('Sheet_Month')
    monthly['Month'] = monthly['Sheet_Month'].apply(lambda x: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'][int(x)-1] if 1 <= int(x) <= 12 else str(x))
    
    return jsonify({
        'months': monthly['Month'].tolist(),
        'revenue': monthly['Revenue'].tolist()
    })


@api_bp.route('/charts/flight-types')
def get_flight_types():
    """Get flight type distribution"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    df = processor.df_filtered
    
    if 'Type of Flight' not in df.columns:
        return jsonify({'error': 'Type of Flight column not found'}), 400
    
    flight_types = df['Type of Flight'].value_counts().head(10)
    
    return jsonify({
        'labels': flight_types.index.tolist(),
        'values': flight_types.values.tolist()
    })


@api_bp.route('/charts/aircraft-usage')
def get_aircraft_usage():
    """Get aircraft usage distribution"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    df = processor.df_filtered
    
    if 'Aircraft_Model' not in df.columns:
        return jsonify({'error': 'Aircraft_Model column not found'}), 400
    
    aircraft_counts = df['Aircraft_Model'].value_counts()
    
    return jsonify({
        'labels': aircraft_counts.index.tolist(),
        'values': aircraft_counts.values.tolist()
    })


@api_bp.route('/filters/options')
def get_filter_options():
    """Get available filter options"""
    processor = get_data_processor()
    
    if processor is None or processor.filter_options is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    # Convert datetime objects to strings for JSON serialization
    options = {}
    for key, value in processor.filter_options.items():
        if isinstance(value, list):
            options[key] = [str(v) for v in value]
        else:
            options[key] = value
    
    # Add current filter state
    filters = {}
    for key, value in processor.filters.items():
        if isinstance(value, (datetime, pd.Timestamp)):
            filters[key] = value.isoformat() if pd.notna(value) else None
        elif isinstance(value, list):
            filters[key] = [str(v) for v in value]
        else:
            filters[key] = value
    
    return jsonify({
        'options': options,
        'current_filters': filters
    })


@api_bp.route('/filters/apply', methods=['POST'])
def apply_filters():
    """Apply filters to data"""
    processor = get_data_processor()
    
    if processor is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    try:
        filters = request.json.get('filters', {})
        
        # Convert date strings back to datetime
        if 'date_start' in filters and filters['date_start']:
            filters['date_start'] = pd.to_datetime(filters['date_start'])
        if 'date_end' in filters and filters['date_end']:
            filters['date_end'] = pd.to_datetime(filters['date_end'])
        
        processor.apply_filters(filters)
        processor.calculate_distances()
        
        return jsonify({
            'success': True,
            'filtered_records': len(processor.df_filtered) if processor.df_filtered is not None else 0
        })
    except Exception as e:
        import traceback
        return jsonify({
            'error': f'Error applying filters: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


@api_bp.route('/analysis/routes')
def get_routes_analysis():
    """Get top routes analysis"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    df = processor.df_filtered
    
    if 'Departure' not in df.columns or 'Arrival' not in df.columns:
        return jsonify({'error': 'Route columns not found'}), 400
    
    df_routes = df[df['Departure'].notna() & df['Arrival'].notna()].copy()
    df_routes['Route'] = df_routes['Departure'].astype(str) + ' → ' + df_routes['Arrival'].astype(str)
    
    route_stats = df_routes.groupby('Route').agg({
        'Revenue': ['count', 'sum', 'mean'],
        'Pax': 'sum'
    }).reset_index()
    
    route_stats.columns = ['route', 'count', 'total_revenue', 'avg_revenue', 'total_pax']
    route_stats = route_stats.sort_values('count', ascending=False).head(20)
    
    return jsonify({
        'routes': route_stats.to_dict('records')
    })


@api_bp.route('/analysis/shuttle')
def get_shuttle_analysis():
    """Get shuttle analysis"""
    processor = get_data_processor()
    
    if processor is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    service = AnalysisService(processor)
    shuttle_data = service.get_shuttle_breakdown()
    
    return jsonify(shuttle_data)


@api_bp.route('/analysis/load-factor')
def get_load_factor():
    """Get load factor analysis"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    df = processor.df_filtered
    
    if 'Load_Factor' not in df.columns:
        return jsonify({'error': 'Load Factor not calculated'}), 400
    
    # Overall load factor
    overall_lf = float(df['Load_Factor'].mean())
    
    # By aircraft
    if 'Aircraft_Model' in df.columns:
        lf_by_aircraft = df.groupby('Aircraft_Model')['Load_Factor'].mean().to_dict()
    else:
        lf_by_aircraft = {}
    
    # By month - CRITICAL: Convert Sheet_Month to numeric
    if 'Sheet_Month' in df.columns:
        df = ensure_sheet_month_numeric(df)
        lf_by_month = df.groupby('Sheet_Month')['Load_Factor'].mean().to_dict()
    else:
        lf_by_month = {}
    
    return jsonify({
        'overall': overall_lf,
        'by_aircraft': {str(k): float(v) for k, v in lf_by_aircraft.items()},
        'by_month': {str(k): float(v) for k, v in lf_by_month.items()}
    })


@api_bp.route('/analysis/non-revenue')
def get_non_revenue():
    """Get non-revenue flights analysis"""
    processor = get_data_processor()
    
    if processor is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    result = {
        'empty_legs': {
            'count': len(processor.df_empty_legs) if processor.df_empty_legs is not None else 0,
            'hours': float(processor.df_empty_legs['Flight_Time_Hours'].sum()) if processor.df_empty_legs is not None and 'Flight_Time_Hours' in processor.df_empty_legs.columns else 0
        },
        'hangar_flights': {
            'count': len(processor.df_hangar_flights) if processor.df_hangar_flights is not None else 0,
            'hours': float(processor.df_hangar_flights['Flight_Time_Hours'].sum()) if processor.df_hangar_flights is not None and 'Flight_Time_Hours' in processor.df_hangar_flights.columns else 0
        },
        'marketing': {
            'count': len(processor.df_marketing) if processor.df_marketing is not None else 0
        },
        'courtesy': {
            'count': len(processor.df_courtesy) if processor.df_courtesy is not None else 0
        }
    }
    
    return jsonify(result)


@api_bp.route('/analysis/profit')
def get_profit_analysis():
    """Get profit analysis"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    df = processor.df_filtered
    
    total_revenue = float(df['Revenue'].sum()) if 'Revenue' in df.columns else 0
    
    # If costs are calculated
    total_costs = 0
    if 'Total_Cost' in df.columns:
        total_costs = float(df['Total_Cost'].sum())
    
    profit = total_revenue - total_costs
    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
    
    return jsonify({
        'total_revenue': total_revenue,
        'total_costs': total_costs,
        'profit': profit,
        'margin_percent': margin
    })


@api_bp.route('/analysis/hourly')
def get_hourly_analysis():
    """Get hourly distribution analysis"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    df = processor.df_filtered
    
    if 'Start_Hour' not in df.columns:
        return jsonify({'error': 'Start_Hour column not found'}), 400
    
    hourly = df.groupby('Start_Hour').agg({
        'Revenue': ['count', 'sum'],
        'Pax': 'sum'
    }).reset_index()
    hourly.columns = ['hour', 'flights', 'revenue', 'passengers']
    
    return jsonify({
        'hours': hourly['hour'].tolist(),
        'flights': hourly['flights'].tolist(),
        'revenue': hourly['revenue'].tolist(),
        'passengers': hourly['passengers'].tolist()
    })


@api_bp.route('/export/<format>')
def export_data(format):
    """Export data in various formats"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    df = processor.df_filtered.copy()
    
    # Remove internal columns for export
    cols_to_remove = [c for c in df.columns if c.startswith('_')]
    df = df.drop(columns=cols_to_remove, errors='ignore')
    
    from flask import Response
    import io
    
    if format == 'csv':
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=flight_data.csv'}
        )
    
    elif format == 'json':
        # Convert datetime columns to string
        for col in df.select_dtypes(include=['datetime64']).columns:
            df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        return Response(
            df.to_json(orient='records'),
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment; filename=flight_data.json'}
        )
    
    elif format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Dados', index=False)
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename=flight_data.xlsx'}
        )
    
    return jsonify({'error': f'Unknown format: {format}'}), 400


# Upload endpoint (alternative path)
@api_bp.route('/upload', methods=['POST'])
def api_upload():
    """Handle file upload via API route"""
    from werkzeug.utils import secure_filename
    from config import Config
    from flask import current_app
    import os
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.endswith(('.xlsx', '.xls')):
        filename = secure_filename(f"flight_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        upload_folder = current_app.config.get('UPLOAD_FOLDER', Config.UPLOAD_FOLDER)
        if hasattr(upload_folder, '__fspath__'):
            upload_folder = str(upload_folder)
        
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        try:
            processor = DataProcessor(filepath)
            processor.load_data()
            processor.initialize_filters()
            processor.apply_filters()
            processor.calculate_distances()
            
            set_data_processor(processor)
            
            return jsonify({
                'success': True,
                'message': 'File uploaded and processed successfully',
                'records': len(processor.df_all) if processor.df_all is not None else 0,
                'filtered_records': len(processor.df_filtered) if processor.df_filtered is not None else 0
            })
        except Exception as e:
            import traceback
            print("="*60)
            print(f"UPLOAD ERROR: {type(e).__name__}: {str(e)}")
            print(traceback.format_exc())
            print("="*60)
            return jsonify({
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc()
            }), 500
    
    return jsonify({'error': 'Invalid file type'}), 400


# ============================================================
# COSTS ENDPOINTS
# ============================================================

# Global cost service instance
_cost_service = None

def get_cost_service():
    """Get or create cost service instance"""
    global _cost_service
    if _cost_service is None:
        from services.costs import CostService
        _cost_service = CostService()
    return _cost_service


@api_bp.route('/costs', methods=['GET'])
def get_costs():
    """Get current cost configuration"""
    cost_service = get_cost_service()
    return jsonify({
        'costs': cost_service.get_costs()
    })


@api_bp.route('/costs', methods=['POST'])
def update_costs():
    """Update cost configuration"""
    cost_service = get_cost_service()
    
    try:
        data = request.json
        
        if 'costs' in data:
            # Update all costs at once
            for aircraft, values in data['costs'].items():
                cost_service.update_aircraft_costs(
                    aircraft,
                    fixed_per_hour=values.get('fixed_cost_per_hour'),
                    fuel_per_hour=values.get('fuel_cost_per_hour'),
                    monthly_fixed=values.get('monthly_fixed_cost'),
                    capacity=values.get('capacity')
                )
        elif 'aircraft' in data:
            # Update single aircraft
            cost_service.update_aircraft_costs(
                data['aircraft'],
                fixed_per_hour=data.get('fixed_cost_per_hour'),
                fuel_per_hour=data.get('fuel_cost_per_hour'),
                monthly_fixed=data.get('monthly_fixed_cost'),
                capacity=data.get('capacity')
            )
        
        # Recalculate costs if data is loaded
        processor = get_data_processor()
        if processor is not None and processor.df_filtered is not None:
            processor.df_filtered = cost_service.calculate_dataframe_costs(processor.df_filtered)
            processor.df_all = cost_service.calculate_dataframe_costs(processor.df_all)
        
        return jsonify({
            'success': True,
            'costs': cost_service.get_costs()
        })
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@api_bp.route('/costs/summary')
def get_cost_summary():
    """Get cost summary from current data"""
    processor = get_data_processor()
    cost_service = get_cost_service()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    # Ensure costs are calculated
    if 'Cost' not in processor.df_filtered.columns:
        processor.df_filtered = cost_service.calculate_dataframe_costs(processor.df_filtered)
    
    summary = cost_service.get_cost_summary(processor.df_filtered)
    return jsonify(summary)


@api_bp.route('/costs/recalculate', methods=['POST'])
def recalculate_costs():
    """Recalculate costs with current configuration"""
    processor = get_data_processor()
    cost_service = get_cost_service()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    try:
        processor.df_filtered = cost_service.calculate_dataframe_costs(processor.df_filtered)
        processor.df_all = cost_service.calculate_dataframe_costs(processor.df_all)
        
        summary = cost_service.get_cost_summary(processor.df_filtered)
        
        return jsonify({
            'success': True,
            'summary': summary
        })
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ============================================================
# ADVANCED KPI ENDPOINTS
# ============================================================

@api_bp.route('/kpis/all')
def get_all_kpis():
    """Get all comprehensive KPIs"""
    processor = get_data_processor()
    
    if processor is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    # Ensure costs are calculated
    cost_service = get_cost_service()
    if processor.df_filtered is not None and 'Cost' not in processor.df_filtered.columns:
        processor.df_filtered = cost_service.calculate_dataframe_costs(processor.df_filtered)
    
    from services.kpi_calculator import KPICalculator
    calculator = KPICalculator(processor, cost_service)
    
    kpis = calculator.calculate_all_kpis()
    return jsonify(kpis)


@api_bp.route('/kpis/cards')
def get_kpi_cards():
    """Get KPI data formatted for card display"""
    processor = get_data_processor()
    
    if processor is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    from services.kpi_calculator import KPICalculator
    calculator = KPICalculator(processor, get_cost_service())
    
    cards = calculator.get_kpi_cards_data()
    return jsonify({'cards': cards})


@api_bp.route('/kpis/revenue')
def get_revenue_kpis():
    """Get revenue-specific KPIs"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    from services.kpi_calculator import KPICalculator
    calculator = KPICalculator(processor, get_cost_service())
    
    kpis = calculator.calculate_all_kpis()
    return jsonify(kpis.get('revenue', {}))


@api_bp.route('/kpis/efficiency')
def get_efficiency_kpis():
    """Get efficiency KPIs"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    from services.kpi_calculator import KPICalculator
    calculator = KPICalculator(processor, get_cost_service())
    
    kpis = calculator.calculate_all_kpis()
    return jsonify(kpis.get('efficiency', {}))


@api_bp.route('/kpis/profitability')
def get_profitability_kpis():
    """Get profitability KPIs"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    from services.kpi_calculator import KPICalculator
    calculator = KPICalculator(processor, get_cost_service())
    
    kpis = calculator.calculate_all_kpis()
    return jsonify(kpis.get('profitability', {}))


@api_bp.route('/kpis/by-category')
def get_category_kpis():
    """Get KPIs by flight category"""
    processor = get_data_processor()
    
    if processor is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    from services.kpi_calculator import KPICalculator
    calculator = KPICalculator(processor, get_cost_service())
    
    kpis = calculator.calculate_all_kpis()
    return jsonify(kpis.get('by_category', {}))


@api_bp.route('/kpis/by-aircraft')
def get_aircraft_kpis():
    """Get KPIs by aircraft model"""
    processor = get_data_processor()
    
    if processor is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    from services.kpi_calculator import KPICalculator
    calculator = KPICalculator(processor, get_cost_service())
    
    kpis = calculator.calculate_all_kpis()
    return jsonify(kpis.get('by_aircraft', {}))


@api_bp.route('/kpis/trends')
def get_kpi_trends():
    """Get monthly KPI trends"""
    processor = get_data_processor()
    
    if processor is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    from services.kpi_calculator import KPICalculator
    calculator = KPICalculator(processor, get_cost_service())
    
    kpis = calculator.calculate_all_kpis()
    return jsonify({'trends': kpis.get('monthly_trends', [])})


@api_bp.route('/kpis/commercial-hours')
def get_commercial_hours():
    """Get commercial vs non-commercial hours by month"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    from services.kpi_calculator import KPICalculator
    calculator = KPICalculator(processor, get_cost_service())
    
    result = calculator._calculate_commercial_hours(processor.df_filtered)
    return jsonify(result)


@api_bp.route('/kpis/accumulated')
def get_accumulated_metrics():
    """Get accumulated revenue and cost by flight type"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    # Ensure costs are calculated
    cost_service = get_cost_service()
    if 'Cost' not in processor.df_filtered.columns:
        processor.df_filtered = cost_service.calculate_dataframe_costs(processor.df_filtered)
    
    from services.kpi_calculator import KPICalculator
    calculator = KPICalculator(processor, cost_service)
    
    result = calculator._calculate_accumulated_metrics(processor.df_filtered)
    return jsonify({'by_flight_type': result})


@api_bp.route('/kpis/accumulated')
def get_accumulated_metrics():
    """Get accumulated revenue and cost by flight type"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    from services.kpi_calculator import KPICalculator
    calculator = KPICalculator(processor, get_cost_service())
    
    result = calculator._calculate_accumulated_metrics(processor.df_filtered)
    return jsonify({'by_flight_type': result})


@api_bp.route('/kpis/costs-by-category')
def get_costs_by_category():
    """Get costs detailed by category"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    # Ensure costs are calculated
    cost_service = get_cost_service()
    if 'Cost' not in processor.df_filtered.columns:
        processor.df_filtered = cost_service.calculate_dataframe_costs(processor.df_filtered)
    
    from services.kpi_calculator import KPICalculator
    calculator = KPICalculator(processor, cost_service)
    
    result = calculator._calculate_costs_by_category(processor.df_filtered)
    return jsonify({'by_category': result})


@api_bp.route('/kpis/revenue-cost-per-nm')
def get_revenue_cost_per_nm():
    """Get revenue and cost per nautical mile"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    # Ensure costs are calculated
    cost_service = get_cost_service()
    if 'Cost' not in processor.df_filtered.columns:
        processor.df_filtered = cost_service.calculate_dataframe_costs(processor.df_filtered)
    
    from services.kpi_calculator import KPICalculator
    calculator = KPICalculator(processor, cost_service)
    
    kpis = calculator.calculate_all_kpis()
    revenue_kpis = kpis.get('revenue', {})
    
    return jsonify({
        'revenue_per_nm': revenue_kpis.get('revenue_per_nautical_mile', 0),
        'cost_per_nm': revenue_kpis.get('cost_per_nautical_mile', 0),
        'total_nm': revenue_kpis.get('total_nautical_miles', 0)
    })


@api_bp.route('/kpis/debug-classification')
def debug_classification():
    """Debug endpoint to check classification status"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    df = processor.df_filtered
    
    # Check what columns exist
    columns_info = {
        'has_is_commercial': 'Is_Commercial' in df.columns,
        'has_flight_category': 'Flight_Category' in df.columns,
        'has_type_of_flight': 'Type of Flight' in df.columns,
        'has_sales_model': 'Sales Model' in df.columns,
        'has_classification': 'Classification' in df.columns,
        'has_sheet_month': 'Sheet_Month' in df.columns,
        'has_flight_time_hours': 'Flight_Time_Hours' in df.columns
    }
    
    # Sample data
    sample_data = {}
    if len(df) > 0:
        sample_row = df.iloc[0].to_dict()
        sample_data = {
            'Type of Flight': str(sample_row.get('Type of Flight', 'N/A')),
            'Sales Model': str(sample_row.get('Sales Model', 'N/A')),
            'Classification': str(sample_row.get('Classification', 'N/A')),
            'Is_Commercial': sample_row.get('Is_Commercial', 'N/A'),
            'Flight_Category': sample_row.get('Flight_Category', 'N/A')
        }
    
    # Counts
    counts = {
        'total_rows': len(df),
        'commercial_count': int(df['Is_Commercial'].sum()) if 'Is_Commercial' in df.columns else 0,
        'non_commercial_count': int((~df['Is_Commercial']).sum()) if 'Is_Commercial' in df.columns else 0,
        'shuttle_count': int((df['Flight_Category'] == 'Shuttle').sum()) if 'Flight_Category' in df.columns else 0,
        'charter_count': int((df['Flight_Category'] == 'Charter').sum()) if 'Flight_Category' in df.columns else 0
    }
    
    # Unique values
    unique_values = {}
    if 'Type of Flight' in df.columns:
        unique_values['type_of_flight'] = df['Type of Flight'].unique().tolist()[:10]  # First 10
    if 'Sales Model' in df.columns:
        unique_values['sales_model'] = df['Sales Model'].unique().tolist()[:10]
    if 'Classification' in df.columns:
        unique_values['classification'] = df['Classification'].unique().tolist()[:10]
    
    return jsonify({
        'columns_info': columns_info,
        'sample_data': sample_data,
        'counts': counts,
        'unique_values': unique_values
    })


# ============================================================
# IDLE ANALYSIS ENDPOINTS
# ============================================================

@api_bp.route('/analysis/idle')
def get_idle_analysis():
    """Get aircraft idle time analysis"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    df = processor.df_filtered.copy()
    
    if 'Date_Parsed' not in df.columns or 'Aircraft_Prefix' not in df.columns:
        return jsonify({'error': 'Required columns not found'}), 400
    
    # Filter valid data
    df = df[
        (df['Date_Parsed'].notna()) & 
        (df['Aircraft_Prefix'].notna()) &
        (df['Flight_Time_Hours'] > 0)
    ].copy()
    
    if len(df) == 0:
        return jsonify({'error': 'No valid data for idle analysis'}), 400
    
    # Daily flight hours per aircraft
    daily_hours = df.groupby(['Date_Parsed', 'Aircraft_Prefix'])['Flight_Time_Hours'].sum().reset_index()
    daily_hours.columns = ['date', 'aircraft', 'hours']
    
    # Calculate daily averages
    daily_avg = daily_hours.groupby('date')['hours'].mean().reset_index()
    daily_avg['idle_hours'] = 8 - daily_avg['hours']  # Assuming 8 productive hours/day
    daily_avg['idle_hours'] = daily_avg['idle_hours'].clip(lower=0)
    
    # Get unique aircraft count
    unique_aircraft = df['Aircraft_Prefix'].nunique()
    
    # Calculate totals
    total_available_hours = unique_aircraft * 8 * len(daily_avg)
    total_flown_hours = float(df['Flight_Time_Hours'].sum())
    utilization_rate = (total_flown_hours / total_available_hours * 100) if total_available_hours > 0 else 0
    
    # Monthly idle analysis
    df['Month'] = df['Date_Parsed'].dt.to_period('M').astype(str)
    monthly = df.groupby('Month').agg({
        'Flight_Time_Hours': 'sum',
        'Date_Parsed': 'nunique'
    }).reset_index()
    monthly.columns = ['month', 'hours_flown', 'days']
    monthly['available_hours'] = monthly['days'] * unique_aircraft * 8
    monthly['idle_hours'] = monthly['available_hours'] - monthly['hours_flown']
    monthly['utilization_rate'] = (monthly['hours_flown'] / monthly['available_hours'] * 100)
    
    return jsonify({
        'summary': {
            'unique_aircraft': unique_aircraft,
            'total_days': len(daily_avg),
            'total_available_hours': round(total_available_hours, 1),
            'total_flown_hours': round(total_flown_hours, 1),
            'total_idle_hours': round(total_available_hours - total_flown_hours, 1),
            'utilization_rate': round(utilization_rate, 1)
        },
        'daily': {
            'dates': [d.strftime('%Y-%m-%d') for d in daily_avg['date']],
            'avg_hours_flown': daily_avg['hours'].tolist(),
            'avg_idle_hours': daily_avg['idle_hours'].tolist()
        },
        'monthly': monthly.to_dict('records')
    })


# ============================================================
# SEASONALITY ANALYSIS ENDPOINTS
# ============================================================

@api_bp.route('/analysis/seasonality')
def get_seasonality_analysis():
    """Get seasonality analysis with moving averages"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    category = request.args.get('category', 'all')
    
    # Select data based on category
    if category == 'shuttle':
        df = processor.df_shuttle.copy() if processor.df_shuttle is not None else pd.DataFrame()
    elif category == 'shuttle_fc':
        df = processor.df_shuttle_fc.copy() if processor.df_shuttle_fc is not None else pd.DataFrame()
    elif category == 'charter':
        df = processor.df_charter.copy() if processor.df_charter is not None else pd.DataFrame()
    else:
        df = processor.df_filtered.copy()
    
    if df is None or len(df) == 0:
        return jsonify({'error': f'No data for category: {category}'}), 400
    
    if 'Date_Parsed' not in df.columns:
        return jsonify({'error': 'Date column not found'}), 400
    
    # Daily counts and revenue
    daily = df.groupby('Date_Parsed').agg({
        'Revenue': ['count', 'sum'],
        'Pax': 'sum'
    }).reset_index()
    daily.columns = ['date', 'flights', 'revenue', 'passengers']
    daily = daily.sort_values('date')
    
    # Calculate moving averages
    daily['flights_ma7'] = daily['flights'].rolling(window=7, min_periods=1).mean()
    daily['flights_ma30'] = daily['flights'].rolling(window=30, min_periods=1).mean()
    daily['revenue_ma7'] = daily['revenue'].rolling(window=7, min_periods=1).mean()
    
    # Monthly aggregation
    df['Month'] = df['Date_Parsed'].dt.to_period('M')
    monthly = df.groupby('Month').agg({
        'Revenue': ['count', 'sum', 'mean'],
        'Pax': 'sum'
    }).reset_index()
    monthly.columns = ['month', 'flights', 'revenue', 'avg_revenue', 'passengers']
    monthly['month'] = monthly['month'].astype(str)
    
    # Day of week patterns
    df['DayOfWeek'] = df['Date_Parsed'].dt.dayofweek
    dow_names = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    dow_stats = df.groupby('DayOfWeek').agg({
        'Revenue': ['count', 'sum', 'mean'],
        'Pax': 'sum'
    }).reset_index()
    dow_stats.columns = ['dow', 'flights', 'revenue', 'avg_revenue', 'passengers']
    dow_stats['day_name'] = dow_stats['dow'].apply(lambda x: dow_names[x])
    
    return jsonify({
        'category': category,
        'daily': {
            'dates': [d.strftime('%Y-%m-%d') for d in daily['date']],
            'flights': daily['flights'].tolist(),
            'flights_ma7': daily['flights_ma7'].round(2).tolist(),
            'flights_ma30': daily['flights_ma30'].round(2).tolist(),
            'revenue': daily['revenue'].tolist(),
            'revenue_ma7': daily['revenue_ma7'].round(2).tolist()
        },
        'monthly': monthly.to_dict('records'),
        'day_of_week': dow_stats.to_dict('records')
    })


# ============================================================
# LOAD FACTOR ANALYSIS ENDPOINTS
# ============================================================

@api_bp.route('/analysis/load-factor-detailed')
def get_load_factor_detailed():
    """Get detailed load factor analysis with heatmap data"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    category = request.args.get('category', 'all')
    
    # Select data based on category
    if category == 'shuttle':
        df = processor.df_shuttle.copy() if processor.df_shuttle is not None else pd.DataFrame()
    elif category == 'shuttle_fc':
        df = processor.df_shuttle_fc.copy() if processor.df_shuttle_fc is not None else pd.DataFrame()
    elif category == 'charter':
        df = processor.df_charter.copy() if processor.df_charter is not None else pd.DataFrame()
    else:
        df = processor.df_filtered.copy()
    
    if df is None or len(df) == 0 or 'Load_Factor' not in df.columns:
        return jsonify({'error': 'No load factor data available'}), 400
    
    # Overall stats
    overall_lf = float(df['Load_Factor'].mean())
    
    # Load factor distribution (bins)
    bins = [0, 25, 50, 75, 100, 150]
    labels = ['0-25%', '25-50%', '50-75%', '75-100%', '>100%']
    df['LF_Bin'] = pd.cut(df['Load_Factor'], bins=bins, labels=labels, include_lowest=True)
    lf_distribution = df['LF_Bin'].value_counts().sort_index().to_dict()
    
    # By month (for heatmap) - CRITICAL: Convert Sheet_Month to numeric
    if 'Sheet_Month' in df.columns:
        df = ensure_sheet_month_numeric(df)
        monthly_lf = df.groupby('Sheet_Month')['Load_Factor'].mean().to_dict()
    else:
        monthly_lf = {}
    
    # By aircraft
    if 'Aircraft_Model' in df.columns:
        aircraft_lf = df.groupby('Aircraft_Model')['Load_Factor'].mean().to_dict()
    else:
        aircraft_lf = {}
    
    # By day of week
    if 'DayOfWeek' in df.columns:
        dow_lf = df.groupby('DayOfWeek')['Load_Factor'].mean().to_dict()
    else:
        dow_lf = {}
    
    # Heatmap data: Month x Aircraft - CRITICAL: Convert Sheet_Month to numeric
    if 'Sheet_Month' in df.columns and 'Aircraft_Model' in df.columns:
        df = ensure_sheet_month_numeric(df)
        heatmap = df.groupby(['Sheet_Month', 'Aircraft_Model'])['Load_Factor'].mean().reset_index()
        heatmap_data = heatmap.to_dict('records')
    else:
        heatmap_data = []
    
    return jsonify({
        'category': category,
        'overall_load_factor': round(overall_lf, 1),
        'distribution': {str(k): int(v) for k, v in lf_distribution.items()},
        'by_month': {str(k): round(v, 1) for k, v in monthly_lf.items()},
        'by_aircraft': {str(k): round(v, 1) for k, v in aircraft_lf.items()},
        'by_day_of_week': {str(k): round(v, 1) for k, v in dow_lf.items()},
        'heatmap': heatmap_data
    })


# ============================================================
# HOURS ANALYSIS ENDPOINTS
# ============================================================

@api_bp.route('/analysis/hours-detailed')
def get_hours_detailed():
    """Get detailed hourly distribution analysis"""
    processor = get_data_processor()
    
    if processor is None or processor.df_filtered is None:
        return jsonify({'error': 'Data not loaded'}), 400
    
    df = processor.df_filtered.copy()
    
    if 'Start_Hour' not in df.columns:
        return jsonify({'error': 'Start hour data not available'}), 400
    
    # Hourly distribution
    hourly = df.groupby('Start_Hour').agg({
        'Revenue': ['count', 'sum', 'mean'],
        'Pax': 'sum',
        'Load_Factor': 'mean'
    }).reset_index()
    hourly.columns = ['hour', 'flights', 'revenue', 'avg_revenue', 'passengers', 'avg_load_factor']
    
    # Peak hours
    peak_hour = hourly.loc[hourly['flights'].idxmax(), 'hour'] if len(hourly) > 0 else None
    
    # Morning vs Afternoon vs Evening
    df['TimeOfDay'] = df['Start_Hour'].apply(
        lambda h: 'Manhã (6-12)' if 6 <= h < 12 
        else ('Tarde (12-18)' if 12 <= h < 18 
        else ('Noite (18-22)' if 18 <= h < 22 
        else 'Fora Horário'))
    )
    
    time_of_day = df.groupby('TimeOfDay').agg({
        'Revenue': ['count', 'sum'],
        'Pax': 'sum'
    }).reset_index()
    time_of_day.columns = ['period', 'flights', 'revenue', 'passengers']
    
    # Heatmap: Hour x Day of Week
    if 'DayOfWeek' in df.columns:
        heatmap = df.groupby(['Start_Hour', 'DayOfWeek']).size().reset_index(name='count')
        heatmap_data = heatmap.to_dict('records')
    else:
        heatmap_data = []
    
    return jsonify({
        'hourly': hourly.to_dict('records'),
        'peak_hour': int(peak_hour) if peak_hour is not None else None,
        'time_of_day': time_of_day.to_dict('records'),
        'heatmap': heatmap_data
    })

