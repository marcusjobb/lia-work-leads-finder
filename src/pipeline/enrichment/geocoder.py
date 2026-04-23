import logging
import urllib.parse
import httpx

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "lia-leads-finder/1.0 (student project, non-commercial)"}
_cache: dict[str, tuple[float, float] | None] = {}


async def geocode(city: str) -> tuple[float, float] | None:
    """Return (lat, lon) for a Swedish city using Nominatim. None on failure."""
    key = city.lower().strip()
    if key in _cache:
        return _cache[key]

    q = urllib.parse.quote(f"{city}, Sverige")
    url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1&countrycodes=se"
    try:
        async with httpx.AsyncClient(timeout=6, headers=_HEADERS) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            if data:
                result = (float(data[0]["lat"]), float(data[0]["lon"]))
                _cache[key] = result
                return result
    except Exception as exc:
        logger.warning("Nominatim geocode failed for %s: %s", city, exc)

    _cache[key] = None
    return None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two lat/lon points."""
    from math import radians, sin, cos, sqrt, atan2
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))
