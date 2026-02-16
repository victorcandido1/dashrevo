"""
Telegram notifier para o radar - revo_radar_bot
Mesmo padrão de mensagens do tracker_event_notifier.
Envia alertas de decolagem, pouso e detecção para o chat configurado.
Usa REVO_RADAR_BOT_TOKEN e REVO_RADAR_CHAT_ID (variáveis de ambiente).
"""
import os
import math
import urllib.request
import urllib.error
import json
import logging

logger = logging.getLogger(__name__)

TELEGRAM_API = 'https://api.telegram.org/bot{token}/sendMessage'

# Aeroportos para inferir origem/destino (mesmo do tracker_event_notifier)
_AIRPORTS = [
    {'icao': 'SBGR', 'lat': -23.4356, 'lon': -46.4731},
    {'icao': 'SBSP', 'lat': -23.6261, 'lon': -46.6564},
    {'icao': 'SBKP', 'lat': -23.0074, 'lon': -47.1345},
    {'icao': 'SBSJ', 'lat': -23.2289, 'lon': -45.8625},
    {'icao': 'SBJD', 'lat': -23.1817, 'lon': -46.9436},
    {'icao': 'SDCO', 'lat': -23.4803, 'lon': -47.4900},
    {'icao': 'SDTK', 'lat': -23.4267, 'lon': -47.1653},
    {'icao': 'SIIR', 'lat': -23.18, 'lon': -46.94},
    {'icao': 'SJSL', 'lat': -23.17, 'lon': -45.89},
    {'icao': 'SBRJ', 'lat': -22.9104, 'lon': -43.1631},
    {'icao': 'SBGL', 'lat': -22.8090, 'lon': -43.2506},
]


def _nearest_airport(lat, lon):
    if lat is None or lon is None:
        return None
    best, best_d = None, float('inf')
    for apt in _AIRPORTS:
        d = math.hypot(lat - apt['lat'], lon - apt['lon'])
        if d < best_d:
            best_d, best = d, apt['icao']
    return best if best_d < 0.5 else None


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _compute_flight_stats(trail_points):
    """Retorna {duration_min, distance_km, avg_speed_kt, origin_icao, destination_icao}"""
    if not trail_points or len(trail_points) < 2:
        return None
    first, last = trail_points[0], trail_points[-1]
    if isinstance(first, (list, tuple)):
        lat1, lon1 = first[0], first[1]
        lat2, lon2 = last[0], last[1]
        ts1, ts2 = None, None
        velocities = []
    else:
        lat1, lon1 = first.get('lat'), first.get('lon')
        lat2, lon2 = last.get('lat'), last.get('lon')
        ts1 = first.get('ts_unix') or first.get('ts')
        ts2 = last.get('ts_unix') or last.get('ts')
        velocities = [p.get('velocity_kt') for p in trail_points if isinstance(p, dict) and p.get('velocity_kt') is not None]

    origin_icao = _nearest_airport(lat1, lon1)
    destination_icao = _nearest_airport(lat2, lon2)
    distance_km = 0
    for i in range(1, len(trail_points)):
        p1, p2 = trail_points[i-1], trail_points[i]
        la1 = p1.get('lat', p1[0]) if isinstance(p1, dict) else p1[0]
        lo1 = p1.get('lon', p1[1]) if isinstance(p1, dict) else p1[1]
        la2 = p2.get('lat', p2[0]) if isinstance(p2, dict) else p2[0]
        lo2 = p2.get('lon', p2[1]) if isinstance(p2, dict) else p2[1]
        distance_km += _haversine_km(la1, lo1, la2, lo2)

    duration_min = None
    if ts1 is not None and ts2 is not None:
        try:
            if isinstance(ts1, (int, float)) and isinstance(ts2, (int, float)):
                duration_min = max(0, (ts2 - ts1) / 60)
            else:
                from datetime import datetime
                t1 = datetime.fromisoformat(str(ts1)[:19]).timestamp()
                t2 = datetime.fromisoformat(str(ts2)[:19]).timestamp()
                duration_min = max(0, (t2 - t1) / 60)
        except Exception:
            pass

    avg_speed_kt = None
    if velocities:
        avg_speed_kt = round(sum(velocities) / len(velocities), 1)
    elif duration_min and duration_min > 0 and distance_km > 0:
        avg_speed_kt = round((distance_km / 1.852) / (duration_min / 60), 1)

    return {
        'duration_min': round(duration_min, 1) if duration_min else None,
        'distance_km': round(distance_km, 1) if distance_km else None,
        'avg_speed_kt': avg_speed_kt,
        'origin_icao': origin_icao or '—',
        'destination_icao': destination_icao or '—',
    }


def _build_message(ev, trail_points=None):
    """Monta mensagem no padrão do tracker_event_notifier"""
    reg = ev.get('registration', 'N/A')
    msg = ev.get('message', '')
    hora = (ev.get('time') or '')[:19].replace('T', ' ')
    ev_type = ev.get('type', '')

    if ev_type == 'takeoff':
        return f"🛫 <b>DECOLAGEM</b>\n\n✈️ {reg}\n📍 {msg}\n⏰ {hora}"
    if ev_type == 'landing':
        text = f"🛬 <b>POUSO</b>\n\n✈️ {reg}\n📍 {msg}\n⏰ {hora}"
        if trail_points and len(trail_points) >= 2:
            stats = _compute_flight_stats(trail_points)
            if stats:
                parts = [f"\n🗺️ <b>Rota - {reg}</b>", f"📍 {stats['origin_icao']} → {stats['destination_icao']}"]
                if stats.get('duration_min') is not None:
                    parts.append(f"⏱ {stats['duration_min']:.1f} min")
                if stats.get('distance_km') is not None:
                    parts.append(f"📏 {stats['distance_km']:.1f} km")
                if stats.get('avg_speed_kt') is not None:
                    parts.append(f"✈️ {stats['avg_speed_kt']:.1f} kt")
                text += "\n" + "\n".join(parts)
        return text
    if ev_type == 'detected':
        return f"🔔 <b>DETECTADO</b>\n\n✈️ {reg}\n{msg}\n⏰ {hora}"
    return msg or f"{reg} - {ev_type}"


def _is_configured():
    return bool(os.environ.get('REVO_RADAR_BOT_TOKEN') and os.environ.get('REVO_RADAR_CHAT_ID'))


def send_event(event, trail_points=None):
    """Envia evento para o Telegram no padrão do outro bot"""
    if not _is_configured():
        return False
    token = os.environ.get('REVO_RADAR_BOT_TOKEN')
    chat_id = os.environ.get('REVO_RADAR_CHAT_ID')
    text = _build_message(event, trail_points)
    if not text:
        return False
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True,
    }
    url = TELEGRAM_API.format(token=token)
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), method='POST')
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 200
    except Exception as e:
        logger.warning('Telegram send error: %s', e)
        return False


def notify_events(events, get_trail_fn=None):
    """
    Envia lista de eventos para o Telegram.
    get_trail_fn: callable(icao24) -> list of points (para pouso com rota)
    """
    for ev in events or []:
        t = ev.get('type', '')
        if t not in ('landing', 'takeoff', 'detected'):
            continue
        trail = None
        if t == 'landing' and get_trail_fn:
            trail = get_trail_fn(ev.get('icao24', ''))
        send_event(ev, trail)
