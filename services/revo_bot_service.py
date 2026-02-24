"""
Revo Bot integration for aircraft movement messages.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

from config import Config


class RevoBotService:
    """Send aircraft movement events to Revo Bot webhook."""

    def __init__(self):
        self.webhook_url = os.environ.get('REVO_BOT_WEBHOOK_URL', '').strip()
        self.token = os.environ.get('REVO_BOT_TOKEN', '').strip()
        self.live_map_url = os.environ.get('REVO_BOT_LIVE_MAP_URL', '').strip()
        self.timeout_seconds = self._read_int_env('REVO_BOT_TIMEOUT_SECONDS', 10, minimum=1)
        self.max_moves_per_run = self._read_int_env('REVO_BOT_MAX_MOVES_PER_RUN', 200, minimum=1)
        self.enabled = self._is_enabled()
        self.state_file = self._get_state_file_path()

    def _read_int_env(self, env_name, default_value, minimum=0):
        """Read integer environment variable with safe fallback."""
        raw_value = os.environ.get(env_name)
        if raw_value is None:
            return default_value
        try:
            parsed = int(raw_value)
            if parsed < minimum:
                return default_value
            return parsed
        except Exception:
            return default_value

    def _is_enabled(self):
        """Feature toggle via env var + webhook presence."""
        flag = os.environ.get('REVO_BOT_ENABLED', 'true').strip().lower()
        return bool(self.webhook_url) and flag not in {'0', 'false', 'no', 'off'}

    def _get_state_file_path(self):
        """Resolve persisted deduplication state file path."""
        custom_path = os.environ.get('REVO_BOT_STATE_FILE', '').strip()
        if custom_path:
            path = Path(custom_path)
        else:
            path = Config.CACHE_FOLDER / 'revo_bot_sent_moves.json'

        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _load_sent_move_ids(self):
        """Load already delivered movement IDs."""
        if not self.state_file.exists():
            return set()

        try:
            raw = self.state_file.read_text(encoding='utf-8')
            data = json.loads(raw)
            if isinstance(data, list):
                return {str(item) for item in data}
        except Exception:
            pass

        return set()

    def _save_sent_move_ids(self, sent_ids):
        """Persist movement IDs delivered to the bot."""
        try:
            payload = json.dumps(sorted(sent_ids), ensure_ascii=True, indent=2)
            self.state_file.write_text(payload, encoding='utf-8')
            return True
        except Exception:
            return False

    def _pick_column(self, df, candidates):
        """Find first existing column from the candidate list."""
        for column_name in candidates:
            if column_name in df.columns:
                return column_name
        return None

    def _safe_str(self, value):
        """Normalize values for outbound payload."""
        if pd.isna(value):
            return ''
        return str(value).strip()

    def _build_movement_time(self, row, date_col, time_col=None):
        """Parse movement datetime from available date/time columns."""
        if date_col is None:
            return None

        if time_col and time_col in row and pd.notna(row[time_col]):
            composed = f"{row[date_col]} {row[time_col]}"
            dt = pd.to_datetime(composed, errors='coerce', dayfirst=True)
        else:
            dt = pd.to_datetime(row[date_col], errors='coerce', dayfirst=True)

        if pd.isna(dt):
            return None

        # Convert pandas timestamp to Python datetime for stable formatting.
        if hasattr(dt, 'to_pydatetime'):
            dt = dt.to_pydatetime()

        return dt

    def _build_move_id(self, move):
        """Stable identifier used to avoid duplicate notifications."""
        parts = [
            move.get('prefix', ''),
            move.get('origin', ''),
            move.get('destination', ''),
            move.get('movement_time', ''),
            move.get('flight_number', ''),
        ]
        return '|'.join(part.strip().upper() for part in parts)

    def _resolve_live_map_url(self, live_map_url=None):
        """Resolve live map URL from parameter or environment."""
        if isinstance(live_map_url, str) and live_map_url.strip():
            return live_map_url.strip()
        return self.live_map_url

    def _format_message(self, move, live_map_url=''):
        """Build human-readable message sent to Revo Bot."""
        prefix = move.get('prefix') or move.get('model') or 'UNKNOWN_AIRCRAFT'
        origin = move.get('origin') or 'UNKNOWN_ORIGIN'
        destination = move.get('destination') or 'UNKNOWN_DESTINATION'

        movement_time = move.get('movement_time')
        if movement_time:
            try:
                dt = datetime.fromisoformat(movement_time)
                movement_time = dt.strftime('%Y-%m-%d %H:%M')
            except Exception:
                pass
        else:
            movement_time = 'UNKNOWN_TIME'

        base_message = f"{prefix} moved from {origin} to {destination} at {movement_time}"
        if live_map_url:
            return f"{base_message}\nLive map: {live_map_url}"
        return base_message

    def _send_payload(self, payload):
        """Send one webhook call to Revo Bot."""
        if not self.webhook_url:
            return False, None, 'Webhook URL not configured'

        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        request = Request(self.webhook_url, data=body, headers=headers, method='POST')

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                status_code = getattr(response, 'status', 200)
                response_text = response.read().decode('utf-8', errors='ignore')
                if 200 <= status_code < 300:
                    return True, status_code, response_text
                return False, status_code, response_text
        except HTTPError as exc:
            error_body = exc.read().decode('utf-8', errors='ignore')
            return False, exc.code, error_body
        except URLError as exc:
            return False, None, str(exc)
        except Exception as exc:
            return False, None, str(exc)

    def extract_moves(self, df, source='unknown'):
        """Extract unique aircraft movement events from a dataframe."""
        if df is None or len(df) == 0:
            return []

        prefix_col = self._pick_column(df, ['Aircraft_Prefix', 'Prefixo', 'registration'])
        model_col = self._pick_column(df, ['Aircraft_Model', 'Modelo', 'aircraft_type'])
        origin_col = self._pick_column(df, ['Departure', 'Origem', 'origin', 'Origin'])
        destination_col = self._pick_column(df, ['Arrival', 'Destino', 'destination', 'Destination'])
        flight_col = self._pick_column(df, ['Flight_Number', 'Numero_Voo', 'sheet', 'Sheet_Name'])
        date_col = self._pick_column(df, ['Date_Parsed', 'Data_Voo', 'Flight_Date', 'flight_date', 'Date'])
        time_col = self._pick_column(df, ['time', 'Time'])

        # No route info means no movement to report.
        if origin_col is None and destination_col is None:
            return []

        extracted = []
        for _, row in df.iterrows():
            prefix = self._safe_str(row[prefix_col]) if prefix_col else ''
            model = self._safe_str(row[model_col]) if model_col else ''
            origin = self._safe_str(row[origin_col]) if origin_col else ''
            destination = self._safe_str(row[destination_col]) if destination_col else ''
            flight_number = self._safe_str(row[flight_col]) if flight_col else ''

            if not prefix and not model:
                continue

            if not origin and not destination:
                continue

            movement_dt = self._build_movement_time(row, date_col, time_col)
            movement_time = movement_dt.isoformat(timespec='minutes') if movement_dt else ''

            move = {
                'source': source,
                'prefix': prefix,
                'model': model,
                'origin': origin,
                'destination': destination,
                'flight_number': flight_number,
                'movement_time': movement_time,
            }
            move['move_id'] = self._build_move_id(move)
            extracted.append(move)

        # Deduplicate by move_id while preserving insertion order.
        deduped = {}
        for move in extracted:
            deduped[move['move_id']] = move

        return list(deduped.values())

    def notify_moves(self, moves, live_map_url=None):
        """Notify Revo Bot for new aircraft movements."""
        resolved_live_map_url = self._resolve_live_map_url(live_map_url)
        detected_moves = len(moves)
        if detected_moves == 0:
            return {
                'enabled': self.enabled,
                'detected_moves': 0,
                'new_moves': 0,
                'sent': 0,
                'failed': 0,
                'already_sent': 0,
                'skipped_by_limit': 0,
                'live_map_url': resolved_live_map_url
            }

        if not self.enabled:
            return {
                'enabled': False,
                'detected_moves': detected_moves,
                'new_moves': 0,
                'sent': 0,
                'failed': 0,
                'already_sent': detected_moves,
                'skipped_by_limit': 0,
                'live_map_url': resolved_live_map_url,
                'reason': 'Revo Bot disabled or missing REVO_BOT_WEBHOOK_URL'
            }

        sent_ids = self._load_sent_move_ids()
        pending = [move for move in moves if move['move_id'] not in sent_ids]
        already_sent = detected_moves - len(pending)

        if self.max_moves_per_run > 0:
            to_send = pending[:self.max_moves_per_run]
            skipped_by_limit = max(0, len(pending) - len(to_send))
        else:
            to_send = pending
            skipped_by_limit = 0

        sent_count = 0
        failed_count = 0
        failures = []

        for move in to_send:
            payload = {
                'event': 'aircraft_move',
                'message': self._format_message(move, resolved_live_map_url),
                'aircraft_move': {
                    'source': move.get('source', ''),
                    'prefix': move.get('prefix', ''),
                    'model': move.get('model', ''),
                    'origin': move.get('origin', ''),
                    'destination': move.get('destination', ''),
                    'flight_number': move.get('flight_number', ''),
                    'movement_time': move.get('movement_time', ''),
                    'move_id': move.get('move_id', ''),
                    'live_map_url': resolved_live_map_url
                }
            }

            ok, status_code, response_text = self._send_payload(payload)
            if ok:
                sent_ids.add(move['move_id'])
                sent_count += 1
            else:
                failed_count += 1
                if len(failures) < 10:
                    failures.append({
                        'move_id': move.get('move_id', ''),
                        'status_code': status_code,
                        'error': response_text[:500] if response_text else 'Request failed'
                    })

        if sent_count > 0:
            self._save_sent_move_ids(sent_ids)

        result = {
            'enabled': True,
            'detected_moves': detected_moves,
            'new_moves': len(pending),
            'sent': sent_count,
            'failed': failed_count,
            'already_sent': already_sent,
            'skipped_by_limit': skipped_by_limit,
            'live_map_url': resolved_live_map_url
        }

        if failures:
            result['failures'] = failures

        return result

    def notify_dataframe_moves(self, df, source='unknown', live_map_url=None):
        """Extract and notify movement events from a dataframe."""
        moves = self.extract_moves(df, source=source)
        return self.notify_moves(moves, live_map_url=live_map_url)


_revo_bot_service = None


def get_revo_bot_service():
    """Get singleton Revo Bot service instance."""
    global _revo_bot_service
    if _revo_bot_service is None:
        _revo_bot_service = RevoBotService()
    return _revo_bot_service
