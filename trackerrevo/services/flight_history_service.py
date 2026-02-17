"""
Flight History / Memory Cache
Guarda posições e trajetórias de aeronaves ao longo do tempo.
Persiste em arquivo (ou GCS no Cloud Run) para manter histórico.
Amostragem: mínimo 1 segundo entre pontos (throttle).
"""
import time
import json
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Histórico: icao24 -> lista de posições [{lat, lon, alt, velocity_kt, ...}, ...]
# Salvar aeronaves rastreadas: PR-OOE, PR-OMB, PR-OMH e todos os helicópteros (categoria 8)
TRACKED_REGISTRATIONS = frozenset({'PROOE', 'PROMB', 'PROMH'})
MAX_POINTS_PER_AIRCRAFT = 7200  # ~4h com polling a cada 2s
MAX_AGE_SECONDS = 14400  # 4 horas de retenção em memória (trail é salvo permanentemente no flight_log ao pousar)
MIN_INTERVAL_SEC = 1  # mínimo 1 segundo entre pontos
CACHE_FILENAME = 'aircraft_movement_cache.json'
GCS_BLOB = 'cache/aircraft_movement_cache.json'
SAVE_INTERVAL = 30  # Salvar no disco/GCS a cada 30 segundos


class FlightHistoryService:
    """Cache de memória das posições dos voos com persistência em arquivo"""

    def __init__(self, cache_dir=None):
        self._history = defaultdict(list)
        self._last_update = 0
        self._last_save = 0
        if cache_dir is None:
            try:
                from config import Config
                cache_dir = Path(Config.CACHE_FOLDER)
            except ImportError:
                cache_dir = Path(__file__).parent.parent / '.cache'
        self._cache_dir = Path(cache_dir)
        self._cache_file = self._cache_dir / CACHE_FILENAME
        self._use_gcs = bool(os.environ.get('K_SERVICE') or os.environ.get('GOOGLE_CLOUD_PROJECT'))
        self._load_from_file()

    @staticmethod
    def _is_tracked(ac_or_points):
        """Retorna True se aeronave/pontos são de PR-OOE, PR-OMB ou PR-OMH"""
        if isinstance(ac_or_points, dict):
            reg = (ac_or_points.get('registration') or ac_or_points.get('callsign') or '').upper().replace('-', '')
            return reg in TRACKED_REGISTRATIONS or ac_or_points.get('is_tracked')  # is_tracked = helicópteros
        if isinstance(ac_or_points, list):
            return any(FlightHistoryService._is_tracked(p) for p in ac_or_points)
        return False

    def _load_from_file(self):
        """Carrega histórico do arquivo cache ou GCS (apenas PR-OOE, PR-OMB, PR-OMH)"""
        if self._use_gcs:
            try:
                from .gcs_storage import gcs_read_json
                data = gcs_read_json(GCS_BLOB)
                if data:
                    for icao24, points in data.get('aircraft', {}).items():
                        if isinstance(points, list) and self._is_tracked(points):
                            self._history[icao24] = points
                    self._last_update = data.get('_meta', {}).get('last_update', 0)
                    self._prune_old()
            except Exception:
                pass
            return
        if not self._cache_file.exists():
            return
        try:
            with open(self._cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for icao24, points in data.get('aircraft', {}).items():
                if isinstance(points, list) and self._is_tracked(points):
                    self._history[icao24] = points
            self._last_update = data.get('_meta', {}).get('last_update', 0)
            self._prune_old()
        except Exception:
            pass

    def _save_to_file(self):
        """Salva histórico no arquivo cache ou GCS (apenas PR-OOE, PR-OMB, PR-OMH)"""
        try:
            self._prune_old()
            tracked_only = {k: v for k, v in self._history.items() if self._is_tracked(v)}
            data = {
                'aircraft': tracked_only,
                '_meta': {
                    'last_update': self._last_update,
                    'saved_at': datetime.now().isoformat(),
                    'aircraft_count': len(tracked_only),
                    'total_points': sum(len(p) for p in tracked_only.values()),
                }
            }
            if self._use_gcs:
                try:
                    from .gcs_storage import gcs_write_json
                    if gcs_write_json(GCS_BLOB, data):
                        self._last_save = time.time()
                except Exception:
                    pass
                return
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            self._last_save = time.time()
        except Exception:
            pass

    def add_positions(self, aircraft_list):
        """Adiciona posições atuais ao histórico"""
        now = time.time()
        ts = datetime.now().isoformat()

        for ac in aircraft_list:
            if not ac or ac.get('latitude') is None or ac.get('longitude') is None:
                continue
            if not self._is_tracked(ac):
                continue  # Guardar apenas PR-OOE, PR-OMB, PR-OMH

            icao24 = ac.get('icao24', 'unknown')
            history = self._history[icao24]
            last_ts = history[-1].get('ts_unix', 0) if history else 0
            if now - last_ts < MIN_INTERVAL_SEC and history:
                continue
            point = {
                'lat': ac['latitude'],
                'lon': ac['longitude'],
                'alt': ac.get('altitude_ft'),
                'velocity_kt': ac.get('velocity_kt'),
                'heading': ac.get('heading'),
                'vertical_rate': ac.get('vertical_rate'),
                'ts': ts,
                'ts_unix': now,
                'callsign': ac.get('callsign', ''),
                'registration': ac.get('registration'),
                'on_ground': ac.get('on_ground', False),
                'is_tracked': ac.get('is_tracked', False),
            }
            history.append(point)

            # Manter apenas últimos N pontos
            if len(history) > MAX_POINTS_PER_AIRCRAFT:
                self._history[icao24] = history[-MAX_POINTS_PER_AIRCRAFT:]

        self._last_update = now
        self._prune_old()
        if now - self._last_save >= SAVE_INTERVAL:
            self._save_to_file()

    def _prune_old(self):
        """Remove pontos mais antigos que MAX_AGE_SECONDS"""
        now = time.time()
        cutoff = now - MAX_AGE_SECONDS
        to_remove = []
        for icao24, points in self._history.items():
            self._history[icao24] = [p for p in points if p.get('ts_unix', 0) > cutoff]
            if not self._history[icao24]:
                to_remove.append(icao24)
        for k in to_remove:
            del self._history[k]

    def get_trail(self, icao24):
        """Retorna trajetória (lista de [lat, lon]) para uma aeronave"""
        points = self._history.get(icao24, [])
        return [[p['lat'], p['lon']] for p in points]

    def get_trail_full(self, icao24):
        """Retorna pontos completos com telemetria (lat, lon, alt, velocity_kt, etc.)"""
        return list(self._history.get(icao24, []))

    def get_full_history(self):
        """Retorna histórico completo para todas as aeronaves"""
        now = time.time()
        self._prune_old()
        return {
            icao24: {
                'trail': [[p['lat'], p['lon']] for p in points],
                'points': points,
                'last_seen': points[-1]['ts'] if points else None,
            }
            for icao24, points in self._history.items()
            if points
        }

    def get_tracked_trails(self):
        """Retorna apenas trajetórias das aeronaves rastreadas"""
        result = {}
        for icao24, points in self._history.items():
            tracked = any(p.get('is_tracked') for p in points)
            if tracked and points:
                result[icao24] = {
                    'trail': [[p['lat'], p['lon']] for p in points],
                    'registration': points[-1].get('registration') or points[-1].get('callsign', icao24),
                }
        return result

    def get_stats(self):
        """Estatísticas do cache"""
        self._prune_old()
        total_points = sum(len(p) for p in self._history.values())
        return {
            'aircraft_count': len(self._history),
            'total_points': total_points,
            'last_update': self._last_update,
            'cache_file': str(self._cache_file),
            'cache_exists': self._cache_file.exists(),
        }

    def save_now(self):
        """Força salvamento imediato no disco"""
        self._save_to_file()


_flight_history = None


def get_flight_history():
    global _flight_history
    if _flight_history is None:
        _flight_history = FlightHistoryService()
    return _flight_history
