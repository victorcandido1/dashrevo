"""
File Upload Routes
Handles Excel file upload and processing
"""
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from data_processor import DataProcessor
from config import Config
from routes.api import set_data_processor
import os
import pandas as pd
from datetime import datetime

upload_bp = Blueprint('upload', __name__)


@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.endswith(('.xlsx', '.xls')):
        # Save uploaded file
        filename = secure_filename(f"flight_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        upload_folder = current_app.config.get('UPLOAD_FOLDER', Config.UPLOAD_FOLDER)
        # Convert Path to string if needed
        if hasattr(upload_folder, '__fspath__'):
            upload_folder = str(upload_folder)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        try:
            # Process data
            processor = DataProcessor(filepath)
            processor.load_data()
            processor.initialize_filters()
            processor.apply_filters()
            
            # Calculate distances using real coordinates
            from services.distance_calculator import get_distance_calculator
            distance_calc = get_distance_calculator()
            total_nm = processor.calculate_distances(distance_calc)
            
            # Get distance statistics
            distance_stats = distance_calc.get_coverage_stats(processor.df_filtered)
            calculated_count = 0
            estimated_count = 0
            if processor.df_filtered is not None and 'Distance_Calculated' in processor.df_filtered.columns:
                calculated_count = int(processor.df_filtered['Distance_Calculated'].sum())
                estimated_count = len(processor.df_filtered) - calculated_count
            
            # Store processor globally
            set_data_processor(processor)
            
            # Save to cache automatically
            from services.cache_service import get_cache_service
            cache = get_cache_service()
            cache_saved = cache.save_processor_state(processor)
            
            # Store in session
            session['file_path'] = str(filepath)  # Convert Path to string for session
            session['data_loaded'] = True
            
            return jsonify({
                'success': True,
                'message': 'File uploaded and processed successfully',
                'records': len(processor.df_all) if processor.df_all is not None else 0,
                'filtered_records': len(processor.df_filtered) if processor.df_filtered is not None else 0,
                'total_nautical_miles': round(total_nm, 2),
                'distance_stats': {
                    'calculated_from_coords': calculated_count,
                    'estimated_from_time': estimated_count,
                    'coverage_percent': distance_stats.get('coverage', 0),
                    'missing_codes': distance_stats.get('missing_codes', [])
                },
                'cache_saved': cache_saved
            })
        except FileNotFoundError as e:
            import traceback
            return jsonify({
                'error': f'File not found: {str(e)}',
                'filepath': str(filepath),
                'traceback': traceback.format_exc()
            }), 500
        except pd.errors.EmptyDataError as e:
            import traceback
            return jsonify({
                'error': f'Excel file is empty or invalid: {str(e)}',
                'traceback': traceback.format_exc()
            }), 500
        except Exception as e:
            import traceback
            import sys
            exc_type, exc_value, exc_traceback = sys.exc_info()
            error_details = {
                'error': str(e),
                'error_type': str(type(e).__name__),
                'filepath': str(filepath),
                'traceback': traceback.format_exc()
            }
            # Log to console for debugging
            print("="*60)
            print("ERROR PROCESSING FILE:")
            print("="*60)
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {str(e)}")
            print(f"File Path: {filepath}")
            print("\nFull Traceback:")
            print(traceback.format_exc())
            print("="*60)
            return jsonify(error_details), 500
    
    return jsonify({'error': 'Invalid file type. Please upload .xlsx or .xls file'}), 400


@upload_bp.route('/upload/november', methods=['POST'])
def upload_november_data():
    """Handle November data upload in special format
    
    Expected format:
    - Column A: Passenger name
    - Column B: Flight type (Charter or Shuttle)
    - Column H: Flight revenue
    - Column J: Flight date
    
    File should have 3 sheets:
    1. Regular November data
    2. F1 flights (treated as category "F1")
    3. F1 Slots (treated as category "SLOTS")
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.endswith(('.xlsx', '.xls')):
        # Save uploaded file
        filename = secure_filename(f"november_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        upload_folder = current_app.config.get('UPLOAD_FOLDER', Config.UPLOAD_FOLDER)
        if hasattr(upload_folder, '__fspath__'):
            upload_folder = str(upload_folder)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(filepath)
            sheet_names = excel_file.sheet_names
            
            # Process each sheet
            all_flights = []
            
            # Sheet 1: Regular November data
            if len(sheet_names) > 0:
                df_regular = pd.read_excel(filepath, sheet_name=sheet_names[0], header=None)
                flights_regular = _process_november_sheet(df_regular, category='NOVEMBER')
                all_flights.extend(flights_regular)
            
            # Sheet 2: F1 flights
            if len(sheet_names) > 1:
                df_f1 = pd.read_excel(filepath, sheet_name=sheet_names[1], header=None)
                flights_f1 = _process_november_sheet(df_f1, category='F1')
                all_flights.extend(flights_f1)
            
            # Sheet 3: F1 Slots
            if len(sheet_names) > 2:
                df_slots = pd.read_excel(filepath, sheet_name=sheet_names[2], header=None)
                flights_slots = _process_november_sheet(df_slots, category='SLOTS')
                all_flights.extend(flights_slots)
            
            if not all_flights:
                return jsonify({'error': 'No valid flight data found in file'}), 400
            
            # Convert to DataFrame
            df_november = pd.DataFrame(all_flights)
            
            # Ensure Sheet_Month is integer type (not float or string)
            if 'Sheet_Month' in df_november.columns:
                df_november['Sheet_Month'] = df_november['Sheet_Month'].astype(int)
            
            # Get existing processor or create new one
            from routes.api import get_data_processor, set_data_processor
            processor = get_data_processor()
            
            # Check if processor exists and has data
            # IMPORTANT: Check if df_all exists AND has rows (not just None check)
            # Also check if df_all is a valid DataFrame with data
            has_existing_data = False
            existing_count = 0
            if processor is not None:
                if processor.df_all is not None:
                    try:
                        # Check if it's a DataFrame and has rows
                        if isinstance(processor.df_all, pd.DataFrame):
                            existing_count = len(processor.df_all)
                            has_existing_data = existing_count > 0
                        else:
                            has_existing_data = False
                            existing_count = 0
                    except Exception as e:
                        # If any error, assume no existing data
                        has_existing_data = False
                        existing_count = 0
                        print(f"Warning: Error checking existing data: {e}")
            
            # CRITICAL: Never replace existing data, always append
            # Only create new processor if processor is None or completely invalid
            if processor is None:
                # Create new processor with November data only
                processor = DataProcessor(None)
                processor.df_all = df_november.copy()
                processor.df_filtered = df_november.copy()
            elif not has_existing_data:
                # Processor exists but has no data - initialize with November data
                # This should not happen, but if it does, preserve the processor structure
                if processor.df_all is None or (isinstance(processor.df_all, pd.DataFrame) and len(processor.df_all) == 0):
                    processor.df_all = df_november.copy()
                    processor.df_filtered = df_november.copy()
                    # Skip the append logic since we just set the data
                    has_existing_data = False  # Flag to skip append
                else:
                    # Has data, proceed to append
                    has_existing_data = True
            
            if has_existing_data:
                # CRITICAL: Store original data count BEFORE any modifications
                original_count_all = len(processor.df_all) if processor.df_all is not None else 0
                original_count_filtered = len(processor.df_filtered) if processor.df_filtered is not None else 0
                
                # DEBUG: Print counts for verification
                print(f"DEBUG: Before append - Existing records: {original_count_all}, November records: {len(df_november)}")
                
                # Normalize Sheet_Month in existing data (convert 'Nov' to 11, etc.)
                month_map = {
                    'Jan': 1, 'Fev': 2, 'Mar': 3, 'Abr': 4, 'Mai': 5, 'Jun': 6,
                    'Jul': 7, 'Ago': 8, 'Set': 9, 'Out': 10, 'Nov': 11, 'Dez': 12
                }
                
                def normalize_month(value):
                    """Convert month to integer (1-12)"""
                    if pd.isna(value):
                        return value
                    if isinstance(value, str):
                        # Try to map month name
                        if value in month_map:
                            return month_map[value]
                        # Try to convert string number
                        try:
                            return int(float(value))
                        except:
                            return value
                    try:
                        return int(float(value))
                    except:
                        return value
                
                # Normalize Sheet_Month in existing dataframes BEFORE filtering
                if 'Sheet_Month' in processor.df_all.columns:
                    processor.df_all['Sheet_Month'] = processor.df_all['Sheet_Month'].apply(normalize_month)
                    # Ensure Sheet_Month is numeric (int) before comparison
                    processor.df_all['Sheet_Month'] = pd.to_numeric(processor.df_all['Sheet_Month'], errors='coerce').fillna(0).astype(int)
                    # Remove any existing November data (month 11) to avoid duplicates
                    # Only remove if there's actually November data to replace
                    november_existing = len(processor.df_all[processor.df_all['Sheet_Month'] == 11])
                    if november_existing > 0:
                        processor.df_all = processor.df_all[processor.df_all['Sheet_Month'] != 11].copy()
                
                if 'Sheet_Month' in processor.df_filtered.columns:
                    processor.df_filtered['Sheet_Month'] = processor.df_filtered['Sheet_Month'].apply(normalize_month)
                    # Ensure Sheet_Month is numeric (int) before comparison
                    processor.df_filtered['Sheet_Month'] = pd.to_numeric(processor.df_filtered['Sheet_Month'], errors='coerce').fillna(0).astype(int)
                    # Remove any existing November data (month 11) to avoid duplicates
                    # Only remove if there's actually November data to replace
                    november_existing_filtered = len(processor.df_filtered[processor.df_filtered['Sheet_Month'] == 11])
                    if november_existing_filtered > 0:
                        processor.df_filtered = processor.df_filtered[processor.df_filtered['Sheet_Month'] != 11].copy()
                
                # Ensure both dataframes have the same columns before concatenation
                # Get union of all columns
                all_columns_all = list(set(list(processor.df_all.columns) + list(df_november.columns)))
                all_columns_filtered = list(set(list(processor.df_filtered.columns) + list(df_november.columns)))
                
                # Reindex to ensure all columns exist (fill missing with None/NaN)
                processor.df_all = processor.df_all.reindex(columns=all_columns_all)
                df_november_aligned = df_november.reindex(columns=all_columns_all)
                
                processor.df_filtered = processor.df_filtered.reindex(columns=all_columns_filtered)
                df_november_aligned_filtered = df_november.reindex(columns=all_columns_filtered)
                
                # Append new November data (preserve existing data)
                # CRITICAL: Verify we have data to append
                if len(processor.df_all) > 0 and len(df_november_aligned) > 0:
                    processor.df_all = pd.concat([processor.df_all, df_november_aligned], ignore_index=True, sort=False)
                elif len(df_november_aligned) > 0:
                    # Only November data, use it directly
                    processor.df_all = df_november_aligned.copy()
                
                if len(processor.df_filtered) > 0 and len(df_november_aligned_filtered) > 0:
                    processor.df_filtered = pd.concat([processor.df_filtered, df_november_aligned_filtered], ignore_index=True, sort=False)
                elif len(df_november_aligned_filtered) > 0:
                    # Only November data, use it directly
                    processor.df_filtered = df_november_aligned_filtered.copy()
                
                # DEBUG: Print counts after append
                print(f"DEBUG: After append - Total records: {len(processor.df_all)}, Expected: {original_count_all + len(df_november)}")
                
                # Ensure Sheet_Month is integer type in both dataframes (final conversion)
                if 'Sheet_Month' in processor.df_all.columns:
                    processor.df_all['Sheet_Month'] = pd.to_numeric(processor.df_all['Sheet_Month'], errors='coerce').fillna(0).astype(int)
                if 'Sheet_Month' in processor.df_filtered.columns:
                    processor.df_filtered['Sheet_Month'] = pd.to_numeric(processor.df_filtered['Sheet_Month'], errors='coerce').fillna(0).astype(int)
                
                # Verify data was preserved
                final_count_all = len(processor.df_all)
                final_count_filtered = len(processor.df_filtered)
                # Ensure Sheet_Month is numeric before comparison
                if 'Sheet_Month' in processor.df_all.columns:
                    df_all_for_count = processor.df_all.copy()
                    df_all_for_count['Sheet_Month'] = pd.to_numeric(df_all_for_count['Sheet_Month'], errors='coerce').fillna(0).astype(int)
                    november_removed_count = len(df_all_for_count[df_all_for_count['Sheet_Month'] == 11])
                    expected_count_all = original_count_all - november_removed_count + len(df_november)
                else:
                    expected_count_all = original_count_all + len(df_november)
                
                if final_count_all < original_count_all:
                    # Log warning if data was lost
                    import logging
                    logging.warning(f"Data loss detected: Original={original_count_all}, Final={final_count_all}, November={len(df_november)}")
            
            # Ensure Date_Parsed exists if Flight_Date exists
            if 'Flight_Date' in processor.df_all.columns and 'Date_Parsed' not in processor.df_all.columns:
                processor.df_all['Date_Parsed'] = pd.to_datetime(processor.df_all['Flight_Date'], errors='coerce')
            if 'Flight_Date' in processor.df_filtered.columns and 'Date_Parsed' not in processor.df_filtered.columns:
                processor.df_filtered['Date_Parsed'] = pd.to_datetime(processor.df_filtered['Flight_Date'], errors='coerce')
            
            # Ensure required columns exist (add missing ones with default values)
            required_columns_defaults = {
                'Aircraft_Prefix': '',
                'Cliente': '',
                'Landings': 1
            }
            
            for col, default_val in required_columns_defaults.items():
                if col not in processor.df_all.columns:
                    processor.df_all[col] = default_val
                if col not in processor.df_filtered.columns:
                    processor.df_filtered[col] = default_val
            
            # Ensure Revenue is numeric in both dataframes (critical for revenue filters and analysis)
            if 'Revenue' in processor.df_all.columns:
                processor.df_all['Revenue'] = pd.to_numeric(processor.df_all['Revenue'], errors='coerce').fillna(0)
            if 'Revenue' in processor.df_filtered.columns:
                processor.df_filtered['Revenue'] = pd.to_numeric(processor.df_filtered['Revenue'], errors='coerce').fillna(0)
            
            # Ensure Pax is numeric (critical for passenger filters and analysis)
            if 'Pax' in processor.df_all.columns:
                processor.df_all['Pax'] = pd.to_numeric(processor.df_all['Pax'], errors='coerce').fillna(0).astype(int)
            if 'Pax' in processor.df_filtered.columns:
                processor.df_filtered['Pax'] = pd.to_numeric(processor.df_filtered['Pax'], errors='coerce').fillna(0).astype(int)
            
            # Ensure Flight_Time_Hours is numeric
            if 'Flight_Time_Hours' in processor.df_all.columns:
                processor.df_all['Flight_Time_Hours'] = pd.to_numeric(processor.df_all['Flight_Time_Hours'], errors='coerce').fillna(0)
            if 'Flight_Time_Hours' in processor.df_filtered.columns:
                processor.df_filtered['Flight_Time_Hours'] = pd.to_numeric(processor.df_filtered['Flight_Time_Hours'], errors='coerce').fillna(0)
            
            # Reinitialize and reapply all filters to ensure data is properly processed
            # This will recreate df_base, df_shuttle, df_charter, etc. with the new November data
            processor.initialize_filters()
            processor.apply_filters()
            
            # Recalculate distances for all data (including new November data)
            from services.distance_calculator import get_distance_calculator
            distance_calc = get_distance_calculator()
            processor.calculate_distances(distance_calc)
            
            # Recalculate costs for all data
            from routes.api import get_cost_service
            cost_service = get_cost_service()
            if processor.df_all is not None:
                cost_service.calculate_dataframe_costs(processor.df_all)
            if processor.df_filtered is not None:
                cost_service.calculate_dataframe_costs(processor.df_filtered)
            
            # Store processor globally
            set_data_processor(processor)
            
            # Force save to cache to update with new data
            from services.cache_service import get_cache_service
            cache = get_cache_service()
            cache_saved = cache.save_processor_state(processor)
            
            # Store in session
            session['file_path'] = str(filepath)
            session['data_loaded'] = True
            
            # Debug: Check November data
            november_count = 0
            november_revenue = 0
            november_in_base = 0
            if processor.df_all is not None and 'Sheet_Month' in processor.df_all.columns:
                # Ensure Sheet_Month is numeric before comparison
                df_all_numeric = processor.df_all.copy()
                df_all_numeric['Sheet_Month'] = pd.to_numeric(df_all_numeric['Sheet_Month'], errors='coerce').fillna(0).astype(int)
                df_nov = df_all_numeric[df_all_numeric['Sheet_Month'] == 11]
                november_count = len(df_nov)
                if 'Revenue' in df_nov.columns:
                    november_revenue = float(df_nov['Revenue'].sum())
            
            # Check if November data is in df_base (for revenue calculations)
            if processor.df_base is not None and 'Sheet_Month' in processor.df_base.columns:
                # Ensure Sheet_Month is numeric before comparison
                df_base_numeric = processor.df_base.copy()
                df_base_numeric['Sheet_Month'] = pd.to_numeric(df_base_numeric['Sheet_Month'], errors='coerce').fillna(0).astype(int)
                november_in_base = len(df_base_numeric[df_base_numeric['Sheet_Month'] == 11])
            
            # Calculate final counts for verification
            final_count_all = len(processor.df_all) if processor.df_all is not None else 0
            final_count_filtered = len(processor.df_filtered) if processor.df_filtered is not None else 0
            
            # Count records by month for verification
            month_distribution = {}
            if processor.df_all is not None and 'Sheet_Month' in processor.df_all.columns:
                month_counts = processor.df_all['Sheet_Month'].value_counts().to_dict()
                month_distribution = {int(k): int(v) for k, v in month_counts.items()}
            
            return jsonify({
                'success': True,
                'message': 'November data uploaded and processed successfully',
                'records': len(df_november),
                'existing_records_before': existing_count,
                'total_records': final_count_all,
                'filtered_records': final_count_filtered,
                'november_records_in_data': november_count,
                'november_revenue': november_revenue,
                'november_in_base': november_in_base,
                'month_distribution': month_distribution,
                'data_preserved': final_count_all >= (existing_count + len(df_november)) if existing_count > 0 else True,
                'cache_saved': cache_saved
            })
        except Exception as e:
            import traceback
            return jsonify({
                'error': f'Error processing November data: {str(e)}',
                'traceback': traceback.format_exc()
            }), 500
    
    return jsonify({'error': 'Invalid file type. Please upload .xlsx or .xls file'}), 400


def _process_november_sheet(df, category='NOVEMBER'):
    """Process a November data sheet into flight records
    
    Args:
        df: DataFrame with November data format
        category: Category to assign (NOVEMBER, F1, SLOTS)
    
    Returns:
        List of flight dictionaries
    """
    flights = []
    
    # Column mapping: A=0, B=1, H=7, J=9
    col_pax_name = 0  # Column A
    col_flight_type = 1  # Column B
    col_revenue = 7  # Column H
    col_date = 9  # Column J
    
    # Group by date and flight type to create flight records
    # First, extract all rows with valid data
    valid_rows = []
    for idx, row in df.iterrows():
        try:
            pax_name = str(row.iloc[col_pax_name]).strip() if pd.notna(row.iloc[col_pax_name]) else ''
            flight_type = str(row.iloc[col_flight_type]).strip().upper() if pd.notna(row.iloc[col_flight_type]) else ''
            revenue_str = row.iloc[col_revenue] if pd.notna(row.iloc[col_revenue]) else 0
            date_val = row.iloc[col_date] if pd.notna(row.iloc[col_date]) else None
            
            # Skip empty rows
            if not pax_name or pax_name == 'nan' or not flight_type or flight_type == 'NAN':
                continue
            
            # Parse revenue
            try:
                if isinstance(revenue_str, str):
                    revenue_str = revenue_str.replace('R$', '').replace(',', '.').strip()
                revenue = float(revenue_str) if revenue_str else 0
            except:
                revenue = 0
            
            # Parse date
            if date_val:
                if isinstance(date_val, pd.Timestamp):
                    flight_date = date_val
                elif isinstance(date_val, datetime):
                    flight_date = pd.Timestamp(date_val)
                else:
                    try:
                        flight_date = pd.to_datetime(date_val)
                    except:
                        continue
            else:
                continue
            
            valid_rows.append({
                'date': flight_date,
                'flight_type': flight_type,
                'revenue': revenue,
                'pax_name': pax_name
            })
        except Exception:
            continue
    
    if not valid_rows:
        return flights
    
    # Group by date and flight type to create flight records
    from collections import defaultdict
    grouped = defaultdict(list)
    
    for row in valid_rows:
        key = (row['date'], row['flight_type'])
        grouped[key].append(row)
    
    # Calculate total passengers for November (all unique passenger names across all flights)
    total_november_pax = len(set(r['pax_name'] for r in valid_rows))
    total_flights = len(grouped)
    
    # Calculate PAX per flight (divide total November PAX equally across all flights)
    pax_per_flight = total_november_pax / total_flights if total_flights > 0 else 0
    
    # Create flight records
    for (flight_date, flight_type), passengers in grouped.items():
        # Calculate revenue for this flight (sum of all passengers)
        flight_revenue = sum(p['revenue'] for p in passengers)
        
        # Use the calculated PAX per flight (equal distribution)
        pax_count = round(pax_per_flight)
        
        # Determine Sales Model based on flight type
        if flight_type in ['SHUTTLE', 'SHUTTLE FULL CABIN']:
            sales_model = flight_type
        elif flight_type == 'CHARTER':
            sales_model = 'CHARTER'
        else:
            sales_model = flight_type
        
        # Estimate Aircraft Model based on passenger count
        # EC135 capacity: 4-5, EC155 capacity: 6-8
        # Use EC155 if pax > 5, otherwise EC135
        if pax_count > 5:
            aircraft_model = 'EC155'
            aircraft_capacity = 6  # Standard capacity for EC155
        else:
            aircraft_model = 'EC135'
            aircraft_capacity = 4  # Standard capacity for EC135
        
        # Estimate Flight_Time_Hours based on typical flight times
        # Shuttle flights are typically shorter (0.5-1.5 hours)
        # Charter flights can be longer (1-3 hours)
        if flight_type in ['SHUTTLE', 'SHUTTLE FULL CABIN']:
            estimated_hours = 1.0  # Average shuttle flight time
        elif flight_type == 'CHARTER':
            estimated_hours = 1.5  # Average charter flight time
        else:
            estimated_hours = 1.0  # Default
        
        # Parse date properly
        if isinstance(flight_date, pd.Timestamp):
            date_parsed = flight_date
            date_str = flight_date.strftime('%Y-%m-%d')
        else:
            date_parsed = pd.to_datetime(flight_date, errors='coerce')
            date_str = date_parsed.strftime('%Y-%m-%d') if pd.notna(date_parsed) else str(flight_date)
        
        # Create flight record with estimated values
        flight_record = {
            'Flight_Date': date_str,
            'Date_Parsed': date_parsed,
            'Sheet_Month': 11,  # November as integer (1-12)
            'Sheet_Year': 2025,  # Assuming 2025 data
            'Sales Model': sales_model,
            'Classification': category,
            'Type of Flight': f'{flight_type} - {category}',  # Put flight_type first so it's recognized by categorization
            'Revenue': flight_revenue,
            'Pax': pax_count,
            'Aircraft_Model': aircraft_model,  # Estimated based on PAX
            'Aircraft_Prefix': '',  # Empty prefix (not available in November data)
            'Aircraft_Capacity': aircraft_capacity,  # For seat analysis
            'Flight_Time_Hours': estimated_hours,  # Estimated based on flight type
            'Origin': 'SBGR',  # Default to Guarulhos for November data
            'Destination': 'SBGR',  # Default to Guarulhos for November data
            'Departure': 'SBGR',
            'Arrival': 'SBGR',
            'Route': 'SBGR → SBGR',  # Default route
            'Distance_NM': 0,  # Will be calculated if origin/destination are known
            'Distance_Nautical_Miles': 0,
            'Distance_Calculated': False,
            'Estimated_Distance_NM': 0
        }
        
        flights.append(flight_record)
    
    return flights

