"""
OpenSky Network API Service
Provides real-time ADS-B aircraft data for the tracker
"""
import urllib.request
import urllib.error
import json
import time
from datetime import datetime

# São Paulo / Southeast Brazil region bounding box (wide enough to catch approaches)
SAO_PAULO_BOUNDS = {
    'lamin': -25.0,   # south (past Curitiba)
    'lamax': -21.5,   # north (includes Belo Horizonte corridor)
    'lomin': -48.5,   # west (past Sorocaba/Campinas)
    'lomax': -43.0    # east (includes Rio de Janeiro)
}

# Aircraft to track - registration and possible callsign patterns
TRACKED_AIRCRAFT = {
    'PR-OMB': ['PROMB', 'PROMB', 'PR-OMB', 'OMB'],
    'PR-OMH': ['PROMH', 'PROMH', 'PR-OMH', 'OMH'],
    'PR-OOE': ['PROOE', 'PROOE', 'PR-OOE', 'OOE'],
}

# Modelo do helicóptero por matrícula (ícones EC155 / EC135 do ipmet)
HELICOPTER_MODELS = {
    'PR-OMB': 'EC155',
    'PR-OMH': 'EC155',
    'PR-OOE': 'EC135',
}

# Major airports in the region for reference
AIRPORTS = [
    {'icao': 'SBGR', 'name': 'Guarulhos Intl', 'lat': -23.4356, 'lon': -46.4731},
    {'icao': 'SBSP', 'name': 'Congonhas', 'lat': -23.6261, 'lon': -46.6564},
    {'icao': 'SBKP', 'name': 'Viracopos/Campinas', 'lat': -23.0074, 'lon': -47.1345},
    {'icao': 'SBSJ', 'name': 'S. J. dos Campos', 'lat': -23.2289, 'lon': -45.8625},
    {'icao': 'SBJD', 'name': 'Jundiaí', 'lat': -23.1817, 'lon': -46.9436},
    {'icao': 'SDCO', 'name': 'Sorocaba', 'lat': -23.4803, 'lon': -47.4900},
    {'icao': 'SBRJ', 'name': 'Santos Dumont/RJ', 'lat': -22.9104, 'lon': -43.1631},
    {'icao': 'SBGL', 'name': 'Galeão/RJ', 'lat': -22.8090, 'lon': -43.2506},
    {'icao': 'SBCF', 'name': 'Confins/BH', 'lat': -19.6244, 'lon': -43.9719},
    {'icao': 'SBCT', 'name': 'Afonso Pena/Curitiba', 'lat': -25.5285, 'lon': -49.1758},
    {'icao': 'SBBH', 'name': 'Pampulha/BH', 'lat': -19.8517, 'lon': -43.9508},
    {'icao': 'SDTK', 'name': 'Catarina Executive', 'lat': -23.4267, 'lon': -47.1653},
]

# Stale timeout: remove aircraft state after 5 minutes without contact
STALE_TIMEOUT = 300


class OpenSkyService:
    """Service for querying OpenSky Network API"""

    BASE_URL = 'https://opensky-network.org/api'

    def __init__(self, bounds=None, tracked=None):
        self.bounds = bounds or SAO_PAULO_BOUNDS
        self.tracked = tracked or TRACKED_AIRCRAFT
        self._aircraft_states = {}  # icao24 -> previous state for event detection
        self._event_log = []  # Recent events

    def get_aircraft_in_region(self):
        """Get all aircraft currently in the monitored region"""
        url = (
            f"{self.BASE_URL}/states/all?"
            f"lamin={self.bounds['lamin']}&"
            f"lamax={self.bounds['lamax']}&"
            f"lomin={self.bounds['lomin']}&"
            f"lomax={self.bounds['lomax']}"
        )

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'DashRevo-Tracker/1.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))

            if not data or not data.get('states'):
                return {
                    'aircraft': [],
                    'time': int(time.time()),
                    'total': 0,
                    'tracked_events': [],
                    'tracked_aircraft': self._get_tracked_summary()
                }

            aircraft_list = []
            tracked_events = []

            for state in data['states']:
                aircraft = self._parse_state_vector(state)
                if aircraft:
                    aircraft_list.append(aircraft)

                    # Check for tracked aircraft events
                    events = self._check_tracked_aircraft(aircraft)
                    tracked_events.extend(events)

            # Clean up stale states
            self._cleanup_stale()

            # Store events in log
            self._event_log.extend(tracked_events)
            # Keep only last 100 events
            self._event_log = self._event_log[-100:]

            return {
                'aircraft': aircraft_list,
                'time': data.get('time', int(time.time())),
                'total': len(aircraft_list),
                'tracked_events': tracked_events,
                'tracked_aircraft': self._get_tracked_summary()
            }

        except urllib.error.HTTPError as e:
            if e.code == 429:
                return {
                    'error': 'Limite de requisições excedido. Aguarde alguns segundos.',
                    'aircraft': [],
                    'total': 0,
                    'tracked_events': [],
                    'tracked_aircraft': self._get_tracked_summary()
                }
            return {
                'error': f'Erro na API: {e.code}',
                'aircraft': [],
                'total': 0,
                'tracked_events': [],
                'tracked_aircraft': self._get_tracked_summary()
            }
        except Exception as e:
            return {
                'error': str(e),
                'aircraft': [],
                'total': 0,
                'tracked_events': [],
                'tracked_aircraft': self._get_tracked_summary()
            }

    def get_event_log(self):
        """Return recent event log"""
        return list(self._event_log)

    def _parse_state_vector(self, state):
        """Parse an OpenSky state vector array into a dict"""
        if len(state) < 17:
            return None

        lat = state[6]
        lon = state[5]

        # Skip aircraft without position data
        if lat is None or lon is None:
            return None

        callsign = (state[1] or '').strip()

        # Determine if this is a tracked aircraft
        is_tracked = False
        registration = None
        for reg, patterns in self.tracked.items():
            normalized_callsign = callsign.upper().replace('-', '').replace(' ', '')
            normalized_patterns = [p.upper().replace('-', '').replace(' ', '') for p in patterns]
            if normalized_callsign and normalized_callsign in normalized_patterns:
                is_tracked = True
                registration = reg
                break

        velocity_ms = state[9]
        velocity_kt = round(velocity_ms * 1.94384, 1) if velocity_ms is not None else None
        altitude_m = state[7]
        altitude_ft = round(altitude_m * 3.28084) if altitude_m is not None else None

        # Helicopter: our tracked aircraft OR OpenSky category 7
        category = state[17] if len(state) > 17 else None
        is_helicopter = is_tracked or category == 7

        model = HELICOPTER_MODELS.get(registration) if registration else None
        return {
            'icao24': state[0],
            'callsign': callsign,
            'origin_country': state[2],
            'latitude': lat,
            'longitude': lon,
            'altitude_m': altitude_m,
            'altitude_ft': altitude_ft,
            'geo_altitude': state[13],
            'on_ground': state[8],
            'velocity_ms': velocity_ms,
            'velocity_kt': velocity_kt,
            'heading': state[10],
            'vertical_rate': state[11],
            'squawk': state[14],
            'is_tracked': is_tracked,
            'registration': registration,
            'is_helicopter': is_helicopter,
            'model': model,
            'last_contact': state[4],
        }

    def _check_tracked_aircraft(self, aircraft):
        """Check for state changes (takeoff/landing/detection) of tracked aircraft"""
        events = []

        if not aircraft.get('is_tracked'):
            return events

        icao24 = aircraft['icao24']
        reg = aircraft.get('registration', aircraft['callsign'])
        on_ground = aircraft.get('on_ground', False)
        now = datetime.now().isoformat()

        prev = self._aircraft_states.get(icao24)

        if prev is not None:
            was_on_ground = prev.get('on_ground', False)

            if was_on_ground and not on_ground:
                events.append({
                    'type': 'takeoff',
                    'registration': reg,
                    'callsign': aircraft['callsign'],
                    'icao24': icao24,
                    'latitude': aircraft['latitude'],
                    'longitude': aircraft['longitude'],
                    'time': now,
                    'message': f'{reg} DECOLOU!'
                })
            elif not was_on_ground and on_ground:
                events.append({
                    'type': 'landing',
                    'registration': reg,
                    'callsign': aircraft['callsign'],
                    'icao24': icao24,
                    'latitude': aircraft['latitude'],
                    'longitude': aircraft['longitude'],
                    'time': now,
                    'message': f'{reg} POUSOU!'
                })
        else:
            # First time seeing this tracked aircraft
            status = 'no solo' if on_ground else 'em voo'
            events.append({
                'type': 'detected',
                'registration': reg,
                'callsign': aircraft['callsign'],
                'icao24': icao24,
                'latitude': aircraft['latitude'],
                'longitude': aircraft['longitude'],
                'on_ground': on_ground,
                'time': now,
                'message': f'{reg} DETECTADO ({status})!'
            })

        # Update state
        self._aircraft_states[icao24] = {
            'on_ground': on_ground,
            'latitude': aircraft['latitude'],
            'longitude': aircraft['longitude'],
            'altitude_ft': aircraft.get('altitude_ft'),
            'velocity_kt': aircraft.get('velocity_kt'),
            'heading': aircraft.get('heading'),
            'registration': reg,
            'callsign': aircraft['callsign'],
            'last_seen': time.time()
        }

        return events

    def _get_tracked_summary(self):
        """Get summary of all tracked aircraft current status"""
        summary = {}
        now = time.time()
        for reg in self.tracked:
            summary[reg] = {'status': 'sem sinal', 'details': None}

        for icao24, state in self._aircraft_states.items():
            reg = state.get('registration')
            if reg and reg in summary:
                age = now - state.get('last_seen', 0)
                if age < STALE_TIMEOUT:
                    if state.get('on_ground'):
                        status = 'no solo'
                    else:
                        status = 'em voo'
                    summary[reg] = {
                        'status': status,
                        'details': {
                            'lat': state.get('latitude'),
                            'lon': state.get('longitude'),
                            'altitude_ft': state.get('altitude_ft'),
                            'velocity_kt': state.get('velocity_kt'),
                            'heading': state.get('heading'),
                            'last_seen': int(age),
                        }
                    }
                else:
                    summary[reg] = {'status': 'sinal perdido', 'details': None}

        return summary

    def _cleanup_stale(self):
        """Remove aircraft states that haven't been seen recently"""
        now = time.time()
        stale_keys = [
            k for k, v in self._aircraft_states.items()
            if now - v.get('last_seen', 0) > STALE_TIMEOUT
        ]
        for k in stale_keys:
            reg = self._aircraft_states[k].get('registration')
            if reg:
                self._event_log.append({
                    'type': 'lost_signal',
                    'registration': reg,
                    'time': datetime.now().isoformat(),
                    'message': f'{reg} - sinal perdido'
                })
            del self._aircraft_states[k]


# Singleton instance
_opensky_service = None


def get_opensky_service():
    global _opensky_service
    if _opensky_service is None:
        _opensky_service = OpenSkyService()
    return _opensky_service
