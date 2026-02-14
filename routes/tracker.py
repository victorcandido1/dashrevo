"""
Aircraft Tracker Routes
Real-time aircraft tracking with map visualization for São Paulo region
"""
from flask import Blueprint, render_template, jsonify
from services.opensky_service import (
    get_opensky_service,
    SAO_PAULO_BOUNDS,
    TRACKED_AIRCRAFT,
    AIRPORTS,
)

tracker_bp = Blueprint('tracker', __name__)


@tracker_bp.route('/tracker')
def tracker_page():
    """Serve the aircraft tracker page"""
    return render_template('tracker.html')


@tracker_bp.route('/api/tracker/aircraft')
def get_aircraft():
    """Get all aircraft in the monitored region"""
    service = get_opensky_service()
    data = service.get_aircraft_in_region()
    return jsonify(data)


@tracker_bp.route('/api/tracker/events')
def get_events():
    """Get the event log"""
    service = get_opensky_service()
    events = service.get_event_log()
    return jsonify({'events': events})


@tracker_bp.route('/api/tracker/config')
def get_config():
    """Get tracker configuration"""
    return jsonify({
        'bounds': SAO_PAULO_BOUNDS,
        'tracked_registrations': list(TRACKED_AIRCRAFT.keys()),
        'airports': AIRPORTS,
        'refresh_interval': 15,
        'center': {
            'lat': -23.55,
            'lon': -46.63
        }
    })
