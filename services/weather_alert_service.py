"""
Weather alert service (METAR/TAF) adapted from IPMET integration.
Collects weather data from AviationWeather and sends new alerts to Revo Bot.
"""
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from config import Config
from services.revo_bot_service import get_revo_bot_service


NOAA_API_BASE = "https://aviationweather.gov/api/data"

AIRPORT_INFO = {
    "SBGR": {"name": "Guarulhos"},
    "SBSP": {"name": "Congonhas"},
    "SBMT": {"name": "Campo de Marte"},
    "SBKP": {"name": "Viracopos"},
}

DEFAULT_AIRPORTS = list(AIRPORT_INFO.keys())

HELI_MINIMUMS = {
    "ceiling_ft": 600,
    "visibility_m": 3000,
}


class WeatherAlertService:
    """Checks weather conditions and notifies Revo Bot about new alerts."""

    def __init__(self):
        airports_env = os.environ.get("REVO_WEATHER_AIRPORTS", "").strip()
        if airports_env:
            self.airports = [
                code.strip().upper()
                for code in airports_env.split(",")
                if code.strip()
            ] or DEFAULT_AIRPORTS
        else:
            self.airports = DEFAULT_AIRPORTS

        state_file_env = os.environ.get("REVO_BOT_WEATHER_STATE_FILE", "").strip()
        if state_file_env:
            self.state_file = Path(state_file_env)
        else:
            self.state_file = Config.CACHE_FOLDER / "revo_bot_weather_alerts.json"

        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def _fetch_json(self, endpoint, params):
        """Fetch JSON from AviationWeather API."""
        query = urlencode(params)
        url = f"{NOAA_API_BASE}/{endpoint}?{query}"
        req = Request(url, headers={"User-Agent": "DashRevo-Weather/1.0"})
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def _determine_flight_category(self, ceiling_ft, visibility_m):
        """Determine VFR/MVFR/IFR/LIFR category."""
        vis_m = visibility_m if visibility_m is not None else 10000
        vis_sm = vis_m / 1609.34

        if ceiling_ft is not None and ceiling_ft < HELI_MINIMUMS["ceiling_ft"]:
            if ceiling_ft < 500 or vis_sm < 1:
                return "LIFR"
        if vis_m < HELI_MINIMUMS["visibility_m"] and vis_sm < 1:
            return "LIFR"

        if (ceiling_ft is not None and ceiling_ft < 500) or vis_sm < 1:
            return "LIFR"
        if (ceiling_ft is not None and ceiling_ft < 1000) or vis_sm < 3:
            return "IFR"
        if (ceiling_ft is not None and ceiling_ft < 3000) or vis_sm < 5:
            return "MVFR"
        return "VFR"

    def _check_ifr_closure(self, metar):
        """Return closure reasons for IFR/heli operations."""
        reasons = []

        ceiling = metar.get("ceiling_ft")
        vis_m = metar.get("visibility_m", 10000)
        weather = metar.get("weather", [])
        clouds = metar.get("clouds", [])
        wind_gust = metar.get("wind_gust")

        if ceiling is not None and ceiling < HELI_MINIMUMS["ceiling_ft"]:
            reasons.append(
                f"Teto abaixo do minimo HELI ({ceiling}ft < {HELI_MINIMUMS['ceiling_ft']}ft)"
            )
        if vis_m < HELI_MINIMUMS["visibility_m"]:
            reasons.append(
                f"Visibilidade abaixo do minimo HELI ({vis_m}m < {HELI_MINIMUMS['visibility_m']}m)"
            )
        if ceiling is not None and ceiling < 200:
            reasons.append(f"Teto muito baixo ({ceiling}ft < 200ft)")
        if vis_m < 550:
            reasons.append(f"Visibilidade muito baixa ({vis_m}m < 550m)")

        for wx in weather:
            if "TS" in wx:
                reasons.append(f"Trovoadas ativas ({wx})")
            if wx == "FG" or (wx.endswith("FG") and not wx.startswith(("BC", "MI"))):
                reasons.append(f"Nevoeiro ({wx})")

        if any("CB" in c for c in clouds):
            reasons.append("Cumulonimbus presente")

        if wind_gust and wind_gust > 35:
            reasons.append(f"Rajadas fortes ({wind_gust}kt > 35kt)")

        return len(reasons) > 0, reasons

    def _parse_metar(self, noaa_data):
        """Parse METAR JSON entry from AviationWeather."""
        raw = noaa_data.get("rawOb", "")
        metar_type = noaa_data.get("metarType", "METAR")
        icao = noaa_data.get("icaoId", "")

        vis_raw = noaa_data.get("visib", "6+")
        if vis_raw == "6+":
            visibility_m = 10000
        elif isinstance(vis_raw, (int, float)):
            visibility_m = int(vis_raw * 1609.34)
        else:
            visibility_m = 10000

        ceiling_ft = None
        clouds = []
        for cloud in noaa_data.get("clouds", []):
            cover = cloud.get("cover", "")
            base = cloud.get("base")
            if base:
                clouds.append(f"{cover}{base // 100:03d}")
                if cover in {"BKN", "OVC", "VV"} and ceiling_ft is None:
                    ceiling_ft = base
            else:
                clouds.append(cover)

        weather = []
        wx_raw = noaa_data.get("wxString", "")
        if wx_raw:
            weather = [token.strip() for token in wx_raw.split() if token.strip()]

        flight_category = noaa_data.get("fltCat") or self._determine_flight_category(
            ceiling_ft,
            visibility_m,
        )

        metar = {
            "raw": raw,
            "type": metar_type,
            "icao": icao,
            "visibility_m": visibility_m,
            "ceiling_ft": ceiling_ft,
            "clouds": clouds,
            "weather": weather,
            "wind_gust": noaa_data.get("wgst"),
            "flight_category": flight_category,
        }
        is_closed, closure_reasons = self._check_ifr_closure(metar)
        metar["is_ifr_closed"] = is_closed
        metar["closure_reasons"] = closure_reasons
        return metar

    def _parse_taf(self, noaa_data):
        """Parse TAF JSON entry from AviationWeather."""
        result = {
            "icao": noaa_data.get("icaoId", ""),
            "raw": noaa_data.get("rawTAF", ""),
            "has_ifr_forecast": False,
            "ifr_periods": [],
            "worst_period": None,
        }

        worst_ceiling = 99999
        worst_vis = 99999

        for fcst in noaa_data.get("fcsts", []):
            visib_raw = fcst.get("visib", "6+")
            if visib_raw == "6+":
                vis_m = 10000
            elif isinstance(visib_raw, (int, float)):
                vis_m = int(visib_raw * 1609.34)
            else:
                vis_m = 10000

            ceiling_ft = None
            for cloud in fcst.get("clouds", []):
                cover = cloud.get("cover", "")
                base = cloud.get("base")
                if cover in {"BKN", "OVC", "VV"} and base and ceiling_ft is None:
                    ceiling_ft = base

            wx_string = fcst.get("wxString", "") or ""
            change_type = fcst.get("fcstChange") or "BASE"
            prob = fcst.get("probability")

            is_ifr = False
            reasons = []
            if ceiling_ft and ceiling_ft < 1000:
                is_ifr = True
                reasons.append(f"Teto {ceiling_ft}ft")
            if vis_m < 5000:
                is_ifr = True
                reasons.append(f"Vis {vis_m}m")
            if any(token in wx_string for token in ("TS", "FG", "+RA")):
                is_ifr = True
                reasons.append(f"Tempo: {wx_string}")

            if is_ifr:
                result["has_ifr_forecast"] = True
                period_desc = f"{change_type} - {', '.join(reasons)}"
                if prob:
                    period_desc = f"{period_desc} ({prob}% chance)"
                result["ifr_periods"].append(period_desc)

                effective_ceiling = ceiling_ft or 99999
                if effective_ceiling < worst_ceiling or vis_m < worst_vis:
                    worst_ceiling = effective_ceiling
                    worst_vis = vis_m
                    result["worst_period"] = period_desc

        return result

    def check_weather(self):
        """Check METAR/TAF and build weather alerts list."""
        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metars": [],
            "tafs": [],
            "alerts": [],
            "has_critical_alert": False,
        }

        metars = self._fetch_json(
            "metar",
            {"ids": ",".join(self.airports), "format": "json"},
        )
        for data in metars:
            metar = self._parse_metar(data)
            result["metars"].append(metar)
            if metar["is_ifr_closed"]:
                airport = AIRPORT_INFO.get(metar["icao"], {})
                result["alerts"].append(
                    {
                        "type": metar["type"],
                        "icao": metar["icao"],
                        "airport_name": airport.get("name", metar["icao"]),
                        "category": metar["flight_category"],
                        "reasons": metar["closure_reasons"],
                        "raw": metar["raw"],
                    }
                )
                result["has_critical_alert"] = True

        tafs = self._fetch_json(
            "taf",
            {"ids": ",".join(self.airports), "format": "json"},
        )
        for data in tafs:
            taf = self._parse_taf(data)
            result["tafs"].append(taf)
            if taf["has_ifr_forecast"]:
                airport = AIRPORT_INFO.get(taf["icao"], {})
                result["alerts"].append(
                    {
                        "type": "TAF",
                        "icao": taf["icao"],
                        "airport_name": airport.get("name", taf["icao"]),
                        "category": "IFR PREVISTO",
                        "reasons": taf["ifr_periods"],
                        "worst_period": taf.get("worst_period"),
                        "raw": (taf["raw"] or "")[:220],
                    }
                )

        return result

    def _alert_key(self, alert):
        """Stable key for deduplicating weather alerts across checks."""
        reasons = "|".join(alert.get("reasons", [])[:3])
        parts = [
            alert.get("icao", ""),
            alert.get("type", ""),
            alert.get("category", ""),
            alert.get("worst_period", ""),
            reasons,
        ]
        normalized = [re.sub(r"\s+", " ", str(part).strip().upper()) for part in parts]
        return "|".join(normalized)

    def _load_last_alert_keys(self):
        """Load previously notified weather alert keys."""
        if not self.state_file.exists():
            return set()
        try:
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
            keys = data.get("alert_keys", [])
            return {str(key) for key in keys}
        except Exception:
            return set()

    def _save_last_alert_keys(self, keys):
        """Persist latest weather alert keys."""
        payload = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "alert_keys": sorted(keys),
        }
        self.state_file.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def check_and_notify(self, live_map_url=None):
        """Run weather check and send only new alerts to Revo Bot."""
        weather_data = self.check_weather()
        all_alerts = weather_data.get("alerts", [])
        current_keys = {self._alert_key(alert) for alert in all_alerts}
        previous_keys = self._load_last_alert_keys()

        new_alerts = [
            alert for alert in all_alerts if self._alert_key(alert) not in previous_keys
        ]

        revo_result = get_revo_bot_service().notify_weather_alerts(
            new_alerts,
            live_map_url=live_map_url,
        )

        # Persist current snapshot regardless of bot send outcome.
        self._save_last_alert_keys(current_keys)

        return {
            "airports_checked": self.airports,
            "total_alerts": len(all_alerts),
            "new_alerts": len(new_alerts),
            "weather_data": {
                "metars": len(weather_data.get("metars", [])),
                "tafs": len(weather_data.get("tafs", [])),
                "has_critical_alert": weather_data.get("has_critical_alert", False),
            },
            "revo_bot": revo_result,
        }


_weather_alert_service = None


def get_weather_alert_service():
    """Get singleton weather alert service."""
    global _weather_alert_service
    if _weather_alert_service is None:
        _weather_alert_service = WeatherAlertService()
    return _weather_alert_service
