from pipeline.enrichment.geocoder import haversine_km


def score_geo(
    company_city: str,
    target_city: str,
    all_sweden: bool,
    center_coords: tuple[float, float] | None = None,
    radius_km: int = 0,
) -> float:
    """Return 0–100 geographic score.

    With center_coords + radius_km: distance-based scoring within the radius.
    Without: city-name matching fallback.
    """
    if not target_city:
        return 60.0

    c = company_city.lower()
    t = target_city.lower()

    if t in c or c in t:
        return 100.0

    if all_sweden:
        return 60.0

    if center_coords and radius_km > 0:
        return 60.0

    return 30.0


async def score_geo_async(
    company_city: str,
    target_city: str,
    all_sweden: bool,
    center_coords: tuple[float, float] | None = None,
    radius_km: int = 0,
) -> float:
    """Distance-based geo scoring when center_coords are available."""
    if not target_city:
        return 60.0

    c = company_city.lower()
    t = target_city.lower()

    if t in c or c in t:
        return 100.0

    if all_sweden:
        return 60.0

    if center_coords and radius_km > 0:
        from pipeline.enrichment.geocoder import geocode
        company_coords = await geocode(company_city)
        if company_coords:
            dist = haversine_km(*center_coords, *company_coords)
            if dist <= radius_km * 0.4:
                return 90.0
            if dist <= radius_km * 0.7:
                return 75.0
            if dist <= radius_km:
                return 55.0
            return 20.0

    if all_sweden:
        return 60.0
    return 30.0
