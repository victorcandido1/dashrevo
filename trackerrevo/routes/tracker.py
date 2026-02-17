"""
Aircraft Tracker Routes
Real-time aircraft tracking with map visualization for São Paulo region
"""
import os
import logging
from flask import Blueprint, jsonify, Response, render_template, request
from services.opensky_service import (
    get_opensky_service,
    SAO_PAULO_BOUNDS,
    TRACKED_AIRCRAFT,
    AIRPORTS,
)
from services.flight_history_service import get_flight_history
from services.flight_log_service import get_flight_log

logger = logging.getLogger(__name__)

tracker_bp = Blueprint('tracker', __name__)


@tracker_bp.route('/radar')
@tracker_bp.route('/tracker')
@tracker_bp.route('/api/tracker/page')
def tracker_page():
    """Página do radar de aeronaves (ícones EC155/EC135 do ipmet)"""
    return render_template('tracker.html')


@tracker_bp.route('/historico')
def history_page():
    """Página de histórico de voos - visualizar rotas no mapa"""
    return render_template('history.html')


@tracker_bp.route('/api/tracker/aircraft')
def get_aircraft():
    """Get all aircraft in the monitored region + flight trails from cache"""
    service = get_opensky_service()
    data = service.get_aircraft_in_region()
    # Atualiza cache de memória dos voos
    if data.get('aircraft'):
        history = get_flight_history()
        history.add_positions(data['aircraft'])
        data['trails'] = history.get_tracked_trails()
        # Salva rota com telemetria no histórico persistente para eventos relevantes
        for ev in data.get('tracked_events', []):
            ev_type = ev.get('type', '')
            if ev_type in ('landing', 'takeoff', 'lost_signal'):
                points = history.get_trail_full(ev.get('icao24', ''))
                if points and len(points) >= 2:
                    log_svc = get_flight_log()
                    fid = log_svc.save_flight(
                        ev_type, ev.get('registration', ''), ev.get('icao24', ''),
                        points, ev.get('time')
                    )
                    if fid:
                        ev['flight_id'] = fid
        # Telegram revo_radar_bot
        try:
            from services.telegram_radar_notifier import notify_events
            notify_events(data.get('tracked_events', []), get_trail_fn=history.get_trail_full)
        except Exception as e:
            logger.warning("Telegram notification error: %s", e)
    else:
        data['trails'] = {}
    return jsonify(data)


@tracker_bp.route('/api/tracker/events')
def get_events():
    """Get the event log (recent in-memory events)"""
    service = get_opensky_service()
    events = service.get_event_log()
    return jsonify({'events': events})


@tracker_bp.route('/api/tracker/flight-history')
def get_flight_history_api():
    """Lista histórico de voos salvos (permanente).
    Query params: ?limit=N&offset=N (sem limit = retorna todos)"""
    log_svc = get_flight_log()
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', 0, type=int)
    flights = log_svc.get_all(limit=limit, offset=offset)
    return jsonify({'flights': flights, 'total': log_svc.get_stats()['count'], 'stats': log_svc.get_stats()})


@tracker_bp.route('/api/tracker/aircraft-info/<icao24>')
def get_aircraft_info(icao24):
    """Busca dados extras da aeronave (modelo, operador) via ADSBdb API"""
    import urllib.request
    icao24 = icao24.lower().strip()
    if not icao24 or len(icao24) != 6:
        return jsonify({'error': 'ICAO24 inválido'}), 400
    try:
        req = urllib.request.Request(
            f'https://api.adsbdb.com/v0/aircraft/{icao24}',
            headers={'User-Agent': 'DashRevo-Tracker/1.0'}
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            data = r.read().decode('utf-8')
        import json
        j = json.loads(data)
        ac = j.get('response', {}).get('aircraft', {})
        if not ac:
            return jsonify({})
        return jsonify({
            'type': ac.get('type'),
            'icao_type': ac.get('icao_type'),
            'manufacturer': ac.get('manufacturer'),
            'registration': ac.get('registration'),
            'operator': ac.get('registered_owner'),
            'operator_code': ac.get('registered_owner_operator_flag_code'),
            'country': ac.get('registered_owner_country_name'),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 502


@tracker_bp.route('/api/tracker/flight-route/<flight_id>')
def get_flight_route(flight_id):
    """Retorna rota de um voo por ID"""
    log_svc = get_flight_log()
    flight = log_svc.get_route(flight_id)
    if not flight:
        return jsonify({'error': 'Voo não encontrado'}), 404
    return jsonify({
        'id': flight['id'],
        'registration': flight.get('registration'),
        'type': flight.get('type'),
        'time': flight.get('time'),
        'route': flight.get('route', []),
        'route_points': flight.get('route_points', []),
        'takeoff': [flight.get('takeoff_lat'), flight.get('takeoff_lon')] if flight.get('takeoff_lat') else None,
        'landing': [flight.get('landing_lat'), flight.get('landing_lon')] if flight.get('landing_lat') else None,
        'origin_icao': flight.get('origin_icao'),
        'destination_icao': flight.get('destination_icao'),
        'avg_velocity_kt': flight.get('avg_velocity_kt'),
    })


@tracker_bp.route('/api/tracker/trails')
def get_trails():
    """Get flight trail history from cache"""
    history = get_flight_history()
    return jsonify({
        'trails': history.get_tracked_trails(),
        'stats': history.get_stats()
    })


@tracker_bp.route('/api/tracker/internal/poll')
def internal_poll():
    """Chamado pelo Cloud Scheduler a cada 1 min para atualizar cache (GCP)"""
    service = get_opensky_service()
    data = service.get_aircraft_in_region()
    if data.get('aircraft'):
        history = get_flight_history()
        history.add_positions(data['aircraft'])
        history.save_now()
        # Processar eventos para salvar no flight_log (histórico persistente)
        for ev in data.get('tracked_events', []):
            ev_type = ev.get('type', '')
            if ev_type in ('landing', 'takeoff', 'lost_signal'):
                points = history.get_trail_full(ev.get('icao24', ''))
                if points and len(points) >= 2:
                    log_svc = get_flight_log()
                    log_svc.save_flight(
                        ev_type, ev.get('registration', ''), ev.get('icao24', ''),
                        points, ev.get('time')
                    )
        try:
            from services.telegram_radar_notifier import notify_events
            notify_events(data.get('tracked_events', []), get_trail_fn=history.get_trail_full)
        except Exception as e:
            logger.warning("Telegram notification error (poll): %s", e)
    return jsonify({'ok': True, 'aircraft': len(data.get('aircraft', []))})


@tracker_bp.route('/api/tracker/telegram-status')
def telegram_status():
    """Status da configuração do Telegram (diagnóstico)"""
    try:
        from services.telegram_radar_notifier import get_status
        return jsonify(get_status())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tracker_bp.route('/api/tracker/config')
def get_config():
    """Get tracker configuration"""
    return jsonify({
        'bounds': SAO_PAULO_BOUNDS,
        'tracked_registrations': list(TRACKED_AIRCRAFT.keys()),
        'airports': AIRPORTS,
        'refresh_interval': 10,
        'center': {
            'lat': -23.55,
            'lon': -46.63
        }
    })
