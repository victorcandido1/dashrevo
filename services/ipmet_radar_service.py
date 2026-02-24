"""
IPMet radar GIF service.
Downloads radar animation and optionally trims to the last hour.
"""
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config import Config

try:
    from PIL import Image
except ImportError:
    Image = None


DEFAULT_IPMET_RADAR_GIF_URL = "https://www.ipmetradar.com.br/imagens/anima-survei/ppi.gif"


class IPMetRadarService:
    """Fetches and prepares IPMet radar GIF animations."""

    def __init__(self):
        self.radar_gif_url = (
            os.environ.get("REVO_IPMET_RADAR_GIF_URL", "").strip()
            or DEFAULT_IPMET_RADAR_GIF_URL
        )
        self.frames_last_hour = self._read_int_env("REVO_IPMET_LAST_HOUR_FRAMES", 12, minimum=1)
        self.images_dir = Config.CACHE_FOLDER / "weather_images"
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def _read_int_env(self, env_name, default_value, minimum=0):
        raw = os.environ.get(env_name)
        if raw is None:
            return default_value
        try:
            parsed = int(raw)
            if parsed < minimum:
                return default_value
            return parsed
        except Exception:
            return default_value

    def _download_radar_gif(self):
        """Download raw radar GIF from IPMet."""
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Referer": "https://www.ipmetradar.com.br/",
            "Accept": "image/gif,image/*;q=0.9,*/*;q=0.8",
        }
        request = Request(self.radar_gif_url, headers=headers, method="GET")

        with urlopen(request, timeout=45) as response:
            content = response.read()

        if not content.startswith(b"GIF"):
            raise ValueError("Downloaded IPMet payload is not a GIF")

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        raw_path = self.images_dir / f"ipmet_radar_raw_{ts}.gif"
        raw_path.write_bytes(content)
        return raw_path

    def _trim_to_last_hour(self, raw_path):
        """Trim GIF to the latest N frames (default: 12 ~ last hour)."""
        if Image is None:
            return raw_path

        with Image.open(raw_path) as img:
            total_frames = getattr(img, "n_frames", 1)
            if total_frames <= self.frames_last_hour:
                return raw_path

            start_idx = max(0, total_frames - self.frames_last_hour)
            frames = []
            durations = []

            for idx in range(start_idx, total_frames):
                img.seek(idx)
                frame = img.copy()
                frames.append(frame)
                durations.append(frame.info.get("duration", img.info.get("duration", 200)))

        if not frames:
            return raw_path

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        trimmed_path = self.images_dir / f"ipmet_radar_last_hour_{ts}.gif"
        frames[0].save(
            trimmed_path,
            save_all=True,
            append_images=frames[1:],
            duration=durations,
            loop=0,
            optimize=False,
        )
        return trimmed_path

    def get_last_hour_radar_gif(self):
        """Return GIF path for last hour radar animation."""
        raw_path = self._download_radar_gif()
        try:
            return self._trim_to_last_hour(raw_path)
        except Exception:
            # If trimming fails, still return the raw animation.
            return raw_path


_ipmet_radar_service = None


def get_ipmet_radar_service():
    """Get singleton IPMet radar service."""
    global _ipmet_radar_service
    if _ipmet_radar_service is None:
        _ipmet_radar_service = IPMetRadarService()
    return _ipmet_radar_service
