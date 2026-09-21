from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class LocationGeocoder:
    """Small, persistent cache around Nominatim for locality-level map previews."""

    def __init__(self, cache_path: Path) -> None:
        self.cache_path = cache_path
        self.lock = threading.Lock()
        self.last_request = 0.0
        self.cache = self._read_cache()

    def _read_cache(self) -> dict[str, dict[str, Any]]:
        try:
            payload = json.loads(self.cache_path.read_text())
            return payload if isinstance(payload, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

    def _save_cache(self) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.cache_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(self.cache, ensure_ascii=False, separators=(",", ":")))
            temporary.replace(self.cache_path)
        except OSError:
            # A map can still be shown during this process even when the disk cache is unavailable.
            pass

    def locate(self, query: str) -> dict[str, Any] | None:
        key = " ".join(query.split()).casefold()
        with self.lock:
            if key in self.cache:
                return self.cache[key] or None

            # Respect the public Nominatim service's one-request-per-second guidance.
            wait = 1.05 - (time.monotonic() - self.last_request)
            if wait > 0:
                time.sleep(wait)

            params = urlencode({"q": query, "format": "jsonv2", "limit": 1, "countrycodes": "ar"})
            request = Request(
                f"https://nominatim.openstreetmap.org/search?{params}",
                headers={"User-Agent": "OSMEDICA-Cartilla/1.0 (map-preview)"},
            )
            self.last_request = time.monotonic()
            try:
                with urlopen(request, timeout=8) as response:
                    results = json.loads(response.read())
            except (OSError, TimeoutError, json.JSONDecodeError):
                return None

            if not results:
                self.cache[key] = None
                self._save_cache()
                return None

            result = results[0]
            location = {
                "latitude": float(result["lat"]),
                "longitude": float(result["lon"]),
                "label": result.get("display_name", query),
            }
            self.cache[key] = location
            self._save_cache()
            return location
