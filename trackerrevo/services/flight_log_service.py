"""
Histórico de Voos - Persiste voos completados com rotas e telemetria
Origem/destino, velocidade média, altitude por ponto.
Persiste em arquivo local ou GCS no Google Cloud.
"""
import time
import json
import os
from pathlib import Path
from datetime import datetime
import math

MAX_FLIGHTS = 500
LOG_FILENAME = 'flight_log.json'
GCS_BLOB = 'cache/flight_log.json'

# Aeroportos para inferir origem/destino (nearest)
_AIRPORTS = [
    {'icao': 'SBGR', 'lat': -23.4356, 'lon': -46.4731},
    {'icao': 'SBSP', 'lat': -23.6261, 'lon': -46.6564},
    {'icao': 'SBKP', 'lat': -23.0074, 'lon': -47.1345},
    {'icao': 'SBSJ', 'lat': -23.2289, 'lon': -45.8625},
    {'icao': 'SBJD', 'lat': -23.1817, 'lon': -46.9436},
    {'icao': 'SDCO', 'lat': -23.4803, 'lon': -47.4900},
    {'icao': 'SDXQ', 'lat': -23.4267, 'lon': -47.1653},
    {'icao': 'SDTK', 'lat': -23.4267, 'lon': -47.1653},
    {'icao': 'SDCY', 'lat': -23.00, 'lon': -47.5},
    {'icao': 'SIIR', 'lat': -23.18, 'lon': -46.94},
    {'icao': 'SJSL', 'lat': -23.17, 'lon': -45.89},
    {'icao': 'SDOF', 'lat': -22.9, 'lon': -47.3},
    {'icao': 'SDMN', 'lat': -23.5, 'lon': -47.4},
    {'icao': 'SBJH', 'lat': -23.2, 'lon': -46.0},
    {'icao': 'SBRJ', 'lat': -22.9104, 'lon': -43.1631},
    {'icao': 'SBGL', 'lat': -22.8090, 'lon': -43.2506},
    {'icao': 'SBCF', 'lat': -19.6244, 'lon': -43.9719},
    {'icao': 'SBCT', 'lat': -25.5285, 'lon': -49.1758},
]


def _nearest_airport(lat, lon):
    if lat is None or lon is None:
        return None
    best = None
    best_d = float('inf')
    for apt in _AIRPORTS:
        d = math.hypot(lat - apt['lat'], lon - apt['lon'])
        if d < best_d:
            best_d = d
            best = apt['icao']
    return best if best_d < 0.5 else None


class FlightLogService:
    """Persiste voos completados com rota completa e telemetria"""

    def __init__(self, cache_dir=None):
        self._flights = []
        if cache_dir is None:
            try:
                from config import Config
                cache_dir = Path(Config.CACHE_FOLDER)
            except ImportError:
                cache_dir = Path(__file__).parent.parent / '.cache'
        self._cache_dir = Path(cache_dir)
        self._log_file = self._cache_dir / LOG_FILENAME
        self._use_gcs = bool(os.environ.get('K_SERVICE') or os.environ.get('GOOGLE_CLOUD_PROJECT'))
        self._load()

    def _load(self):
        """Carrega histórico do arquivo ou GCS"""
        if self._use_gcs:
            try:
                from .gcs_storage import gcs_read_json
                data = gcs_read_json(GCS_BLOB)
                if data:
                    self._flights = data.get('flights', [])
            except Exception:
                pass
            return
        if not self._log_file.exists():
            return
        try:
            with open(self._log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._flights = data.get('flights', [])
        except Exception:
            pass

    def _save(self):
        """Salva no disco ou GCS"""
        try:
            data = {
                'flights': self._flights[-MAX_FLIGHTS:],
                '_meta': {
                    'saved_at': datetime.now().isoformat(),
                    'count': len(self._flights),
                }
            }
            if self._use_gcs:
                try:
                    from .gcs_storage import gcs_write_json
                    gcs_write_json(GCS_BLOB, data)
                except Exception:
                    pass
                return
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            with open(self._log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception:
            pass

    def save_flight(self, event_type, registration, icao24, route_points, time_iso=None, **extra):
        """
        Salva um voo completado.
        event_type: 'landing' | 'takeoff'
        route_points: lista de dicts com lat, lon, alt, velocity_kt, heading, ts, etc.
        Aceita também route como [[lat,lon],...] para retrocompatibilidade.
        """
        if not route_points or len(route_points) < 2:
            return None
        if isinstance(route_points[0], (list, tuple)):
            route_points = [{'lat': p[0], 'lon': p[1], 'ts': None} for p in route_points]
        flight_id = f"{icao24}_{int(time.time() * 1000)}"
        time_iso = time_iso or datetime.now().isoformat()
        first_pt = route_points[0]
        last_pt = route_points[-1]
        takeoff_lat = first_pt.get('lat') if isinstance(first_pt, dict) else first_pt[0]
        takeoff_lon = first_pt.get('lon') if isinstance(first_pt, dict) else first_pt[1]
        landing_lat = last_pt.get('lat') if isinstance(last_pt, dict) else last_pt[0]
        landing_lon = last_pt.get('lon') if isinstance(last_pt, dict) else last_pt[1]
        origin_icao = _nearest_airport(takeoff_lat, takeoff_lon)
        destination_icao = _nearest_airport(landing_lat, landing_lon)
        velocities = [p.get('velocity_kt') for p in route_points if isinstance(p, dict) and p.get('velocity_kt') is not None]
        avg_velocity_kt = round(sum(velocities) / len(velocities), 1) if velocities else None
        route_simple = [[p.get('lat'), p.get('lon')] if isinstance(p, dict) else [p[0], p[1]] for p in route_points]
        flight = {
            'id': flight_id,
            'type': event_type,
            'registration': registration,
            'icao24': icao24,
            'time': time_iso,
            'route': route_simple,
            'route_points': [p for p in route_points if isinstance(p, dict)],
            'takeoff_lat': takeoff_lat,
            'takeoff_lon': takeoff_lon,
            'landing_lat': landing_lat,
            'landing_lon': landing_lon,
            'origin_icao': origin_icao,
            'destination_icao': destination_icao,
            'avg_velocity_kt': avg_velocity_kt,
            **extra
        }
        self._flights.append(flight)
        if len(self._flights) > MAX_FLIGHTS:
            self._flights = self._flights[-MAX_FLIGHTS:]
        self._save()
        return flight_id

    def get_all(self, limit=100):
        """Retorna todos os voos (mais recentes primeiro)"""
        return list(reversed(self._flights[-limit:]))

    def get_route(self, flight_id):
        """Retorna rota de um voo por ID"""
        for f in self._flights:
            if f.get('id') == flight_id:
                return f
        return None

    def get_stats(self):
        return {'count': len(self._flights), 'file': str(self._log_file)}


_flight_log = None


def get_flight_log():
    global _flight_log
    if _flight_log is None:
        _flight_log = FlightLogService()
    return _flight_log
