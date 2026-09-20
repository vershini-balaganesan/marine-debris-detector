"""Resolve human-readable place names to coordinates."""

from geopy.geocoders import Nominatim


def _location_label(address, fallback):
    """Choose the most useful place level returned by the geocoder."""
    for key in ("city", "town", "village", "municipality", "state", "country"):
        value = address.get(key)
        if value:
            return value
    return fallback


def geocode_place(place_name):
    """Return the best matching place and coordinates, or ``None``."""
    query = place_name.strip()
    if not query:
        return None

    geocoder = Nominatim(user_agent="marine_detection_prototype")
    location = geocoder.geocode(query, exactly_one=True, timeout=10)
    if location is None:
        return None

    address = location.raw.get("address", {})
    return {
        "display_name": location.address,
        "location_name": _location_label(address, location.address),
        "latitude": float(location.latitude),
        "longitude": float(location.longitude),
    }


def reverse_geocode(latitude, longitude):
    """Return a human-readable label for stored coordinates."""
    geocoder = Nominatim(user_agent="marine_detection_prototype")
    location = geocoder.reverse((latitude, longitude), exactly_one=True, timeout=10)
    if location is None:
        return None

    address = location.raw.get("address", {})
    return _location_label(address, location.address)