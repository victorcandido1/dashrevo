"""
adsb.lol API Service - Camada extra gratuita de ADS-B
https://api.adsb.lol/docs
Usado como fallback quando OpenSky não retorna aeronaves rastreadas.
"""
import urllib.request
import urllib.error
import json
import time
import logging

logger = logging.getLogger(__name__)

BASE_URL = 'https://api.adsb.lol/v2'
REQUEST_TIMEOUT = 8
USER_AGENT = 'DashRevo-Tracker/1.0'

# Nossas 3 aeronaves para busca por matrícula
TRACKED_REGISTRATIONS = ['PR-OMB', 'PR-OMH', 'PR-OOE']

# Modelo por matrícula (ícones)
HELICOPTER_MODELS = {
    'PR-OMB': 'EC155',
    'PR-OMH': 'EC155',
    'PR-OOE': 'EC135',
}


def _fetch(url):
    """GET request to adsb.lol API"""
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as r:
        return json.loads(r.read().decode('utf-8'))


def _normalize_reg(reg):
    """Normalize registration for matching"""
    return (reg or '').upper().replace('-', '').replace(' ', '')


def _parse_ac_item(ac, registration=None):
    """
    Converte item da resposta adsb.lol para formato unificado do tracker.
    adsb.lol: hex, lat, lon, alt_baro, gs, track, r, baro_rate, category, type, etc.
    """
    lat = ac.get('lat')
    lon = ac.get('lon')
    if lat is None or lon is None:
        return None

    hex_code = ac.get('hex', '')
    icao24 = hex_code.lower() if hex_code else None
    if not icao24:
        return None

    # alt_baro: ADS-B em pés; gs: normalmente em nós
    alt_baro = ac.get('alt_baro')
    altitude_ft = round(alt_baro) if alt_baro is not None else None
    gs = ac.get('gs')
    velocity_kt = round(gs, 1) if gs is not None else None
    track = ac.get('track') or ac.get('calc_track')
    heading = round(track) if track is not None else None
    baro_rate = ac.get('baro_rate')
    vertical_rate = baro_rate  # ft/min
    reg = registration or ac.get('r') or ac.get('flight') or ''
    callsign = ac.get('flight') or reg or ''

    # category: adsb.lol pode usar "A0" (light), "A1", etc.; OpenSky usa 7/8 para rotorcraft
    cat_raw = ac.get('category')
    category = None
    if isinstance(cat_raw, (int, float)):
        category = int(cat_raw)
    elif isinstance(cat_raw, str) and len(cat_raw) >= 1:
        # "A1" -> 1, "B2" -> 2 (simplificação)
        try:
            category = int(cat_raw[1]) if len(cat_raw) > 1 else 0
        except (ValueError, IndexError):
            pass

    is_tracked = True  # Só buscamos nossas aeronaves ou da região filtrada
    ac_type = ac.get('t') or ac.get('type', '')
    # Helicópteros: H, category 7/8, ou tipo como EC35, EC55
    is_helicopter = (
        category in (7, 8) or
        (ac_type and any(x in ac_type.upper() for x in ['H', 'EC', 'EC35', 'EC55', 'EC135', 'EC155']))
    )
    model = HELICOPTER_MODELS.get(reg) if reg in HELICOPTER_MODELS else None
    seen = ac.get('seen') or ac.get('seen_pos')
    last_contact = int(seen) if seen is not None else int(time.time())

    # on_ground: inferência conservadora (não temos campo direto)
    on_ground = False
    if altitude_ft is not None and altitude_ft < 200 and (velocity_kt is None or velocity_kt < 30):
        on_ground = True

    return {
        'icao24': icao24,
        'callsign': callsign,
        'origin_country': None,
        'category': category,
        'latitude': float(lat),
        'longitude': float(lon),
        'altitude_m': altitude_ft / 3.28084 if altitude_ft else None,
        'altitude_ft': altitude_ft,
        'geo_altitude': altitude_ft,
        'on_ground': on_ground,
        'velocity_ms': (velocity_kt / 1.94384) if velocity_kt else None,
        'velocity_kt': velocity_kt,
        'heading': heading,
        'vertical_rate': vertical_rate,
        'squawk': str(ac.get('squawk', '')) if ac.get('squawk') else None,
        'is_tracked': is_tracked,
        'registration': reg or None,
        'is_helicopter': is_helicopter,
        'model': model,
        'last_contact': last_contact,
        'source': 'adsb.lol',
    }


def fetch_by_registration(registration):
    """
    Busca aeronave por matrícula (ex: PR-OMB, PROMB).
    Retorna lista de aeronaves no formato unificado, ou [] em caso de erro/sem dados.
    """
    reg_norm = _normalize_reg(registration)
    if not reg_norm:
        return []
    # adsb.lol aceita com ou sem hífen
    url = f"{BASE_URL}/reg/{registration}"
    try:
        data = _fetch(url)
        ac_list = data.get('ac', [])
        if not ac_list:
            return []
        result = []
        seen_hex = set()
        for ac in ac_list:
            parsed = _parse_ac_item(ac, registration=registration)
            if parsed and parsed['icao24'] not in seen_hex:
                seen_hex.add(parsed['icao24'])
                result.append(parsed)
        return result
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []
        logger.warning("adsb.lol reg/%s: HTTP %s", registration, e.code)
        return []
    except Exception as e:
        logger.warning("adsb.lol reg/%s: %s", registration, e)
        return []


def fetch_by_point(lat, lon, radius_nm=120):
    """
    Busca aeronaves em um raio (nm) ao redor do ponto.
    radius máximo 250nm.
    Retorna lista no formato unificado.
    """
    radius = min(int(radius_nm), 250)
    url = f"{BASE_URL}/point/{lat}/{lon}/{radius}"
    try:
        data = _fetch(url)
        ac_list = data.get('ac', [])
        result = []
        seen_hex = set()
        for ac in ac_list:
            parsed = _parse_ac_item(ac)
            if parsed and parsed['icao24'] not in seen_hex:
                seen_hex.add(parsed['icao24'])
                result.append(parsed)
        return result
    except Exception as e:
        logger.warning("adsb.lol point: %s", e)
        return []


def _in_bounds(lat, lon, bounds=None):
    """Verifica se (lat, lon) está dentro dos bounds da região monitorada"""
    if bounds is None:
        bounds = {
            'lamin': -25.0, 'lamax': -21.5,
            'lomin': -48.5, 'lomax': -43.0,
        }
    if lat is None or lon is None:
        return False
    return (
        bounds['lamin'] <= lat <= bounds['lamax'] and
        bounds['lomin'] <= lon <= bounds['lomax']
    )


def fetch_tracked_fallback(bounds=None):
    """
    Busca as 3 aeronaves rastreadas (PR-OMB, PR-OMH, PR-OOE).
    Só retorna aeronaves dentro dos bounds da região SP/sudeste.
    """
    all_ac = []
    seen_hex = set()
    for reg in TRACKED_REGISTRATIONS:
        acs = fetch_by_registration(reg)
        for ac in acs:
            if ac and ac['icao24'] not in seen_hex:
                lat, lon = ac.get('latitude'), ac.get('longitude')
                if lat is not None and lon is not None and _in_bounds(lat, lon, bounds):
                    seen_hex.add(ac['icao24'])
                    all_ac.append(ac)
    return all_ac
