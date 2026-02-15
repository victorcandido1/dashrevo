"""
Flight History / Memory Cache
Guarda posições e trajetórias de aeronaves ao longo do tempo.
Persiste em arquivo para manter histórico entre reinícios.
"""
import time
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Histórico: icao24 -> lista de posições [{lat, lon, alt, ts, callsign, ...}, ...]
# Mantém últimos 30 minutos (120 amostras a cada 15 seg)
MAX_POINTS_PER_AIRCRAFT = 120
MAX_AGE_SECONDS = 1800  # 30 min
CACHE_FILENAME = 'aircraft_movement_cache.json'
SAVE_INTERVAL = 60  # Salvar no disco a cada 60 segundos


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
        self._load_from_file()

    def _load_from_file(self):
        """Carrega histórico do arquivo cache"""
        if not self._cache_file.exists():
            return
        try:
            with open(self._cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for icao24, points in data.get('aircraft', {}).items():
                if isinstance(points, list):
                    self._history[icao24] = points
            self._last_update = data.get('_meta', {}).get('last_update', 0)
            self._prune_old()
        except Exception as e:
            pass

    def _save_to_file(self):
        """Salva histórico no arquivo cache"""
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            self._prune_old()
            data = {
                'aircraft': dict(self._history),
                '_meta': {
                    'last_update': self._last_update,
                    'saved_at': datetime.now().isoformat(),
                    'aircraft_count': len(self._history),
                    'total_points': sum(len(p) for p in self._history.values()),
                }
            }
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            self._last_save = time.time()
        except Exception as e:
            pass

    def add_positions(self, aircraft_list):
        """Adiciona posições atuais ao histórico"""
        now = time.time()
        ts = datetime.now().isoformat()

        for ac in aircraft_list:
            if not ac or ac.get('latitude') is None or ac.get('longitude') is None:
                continue

            icao24 = ac.get('icao24', 'unknown')
            point = {
                'lat': ac['latitude'],
                'lon': ac['longitude'],
                'alt': ac.get('altitude_ft'),
                'ts': ts,
                'ts_unix': now,
                'callsign': ac.get('callsign', ''),
                'registration': ac.get('registration'),
                'velocity_kt': ac.get('velocity_kt'),
                'heading': ac.get('heading'),
                'on_ground': ac.get('on_ground', False),
                'is_tracked': ac.get('is_tracked', False),
            }

            history = self._history[icao24]
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
