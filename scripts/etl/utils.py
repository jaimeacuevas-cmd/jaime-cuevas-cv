"""Utility validators and helpers for ETL pipeline."""

import re
from typing import Optional, Tuple


class ValidatorError(Exception):
    """Custom exception for validation failures."""
    pass


def validate_orcid(value: Optional[str]) -> Optional[str]:
    """
    Validate ORCID format: NNNN-NNNN-NNNN-NNN[0-9X]
    Returns validated ORCID or None if invalid/empty.
    """
    if not value or value in ('[N/A]', 'N/A', '[n/a]', 'n/a', '', 'N/D'):
        return None

    pattern = r'^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$'
    if re.match(pattern, str(value).strip()):
        return str(value).strip()

    return None


def validate_wikidata_qid(value: Optional[str]) -> Optional[str]:
    """
    Validate Wikidata QID format: Q followed by digits.
    Returns validated QID or None if invalid/empty.
    Rejects synthetic QIDs in range Q124618790-Q124618818.
    """
    if not value or value in ('[N/A]', 'N/A', '[n/a]', 'n/a', '', 'N/D'):
        return None

    value_str = str(value).strip()
    pattern = r'^Q(\d+)$'
    match = re.match(pattern, value_str)

    if not match:
        return None

    qid_num = int(match.group(1))
    # Reject synthetic QIDs
    if 124618790 <= qid_num <= 124618818:
        return None

    return value_str


def validate_id_format(entity_type: str, entity_id: int) -> str:
    """
    Generate and validate entity ID format: TYPE_NNNN
    Type codes: PER, ORG, LOC, EDU, POS, PUB, EXH, PRJ, MED, DGH, CON
    """
    type_map = {
        'Agent': 'PER',
        'Organization': 'ORG',
        'Location': 'LOC',
        'Education': 'EDU',
        'Position': 'POS',
        'Publication': 'PUB',
        'Exhibition': 'EXH',
        'Project': 'PRJ',
        'Media': 'MED',
        'DigitalHeritage': 'DGH',
        'Concept': 'CON',
    }

    if entity_type not in type_map:
        raise ValidatorError(f"Unknown entity type: {entity_type}")

    type_code = type_map[entity_type]
    generated_id = f"{type_code}_{entity_id:04d}"
    return generated_id


def validate_coordinates(lon: Optional[float], lat: Optional[float]) -> Tuple[float, float]:
    """
    Validate and normalize geographic coordinates (WGS84).
    Returns (longitude, latitude) or raises ValidatorError.
    """
    if lon is None or lat is None:
        raise ValidatorError("Coordinates cannot be None")

    try:
        lon_f = float(lon)
        lat_f = float(lat)
    except (ValueError, TypeError):
        raise ValidatorError(f"Invalid coordinate values: {lon}, {lat}")

    if not (-180 <= lon_f <= 180):
        raise ValidatorError(f"Longitude out of range: {lon_f}")

    if not (-90 <= lat_f <= 90):
        raise ValidatorError(f"Latitude out of range: {lat_f}")

    return (lon_f, lat_f)


def normalize_na_values(value: Optional[str]) -> Optional[str]:
    """
    Normalize N/A variants to None.
    """
    if value in ('[N/A]', 'N/A', '[n/a]', 'n/a', '', 'N/D', 'N/A '):
        return None

    if isinstance(value, str):
        return value.strip() if value.strip() else None

    return value


def normalize_url(url: Optional[str]) -> Optional[str]:
    """
    Normalize URLs: add https:// if missing, remove [N/A].
    """
    if not url or url in ('[N/A]', 'N/A', '[n/a]', 'n/a', '', 'N/D'):
        return None

    url_str = str(url).strip()

    if url_str.startswith('http://') or url_str.startswith('https://'):
        return url_str

    if url_str:
        return f"https://{url_str}"

    return None


def normalize_period(period: Optional[str]) -> Optional[dict]:
    """
    Normalize period strings: '2020-2023' or '2020-presente'
    Returns dict with 'start' and 'end' or None.
    """
    if not period or period in ('[N/A]', 'N/A', ''):
        return None

    period_str = str(period).strip()

    # Pattern: YYYY-YYYY or YYYY-presente
    pattern = r'^(\d{4})\s*-\s*(.+)$'
    match = re.match(pattern, period_str)

    if not match:
        return None

    start_year = int(match.group(1))
    end_str = match.group(2).lower().strip()

    end_year = None
    if end_str not in ('presente', 'present', 'ongoing', 'current'):
        try:
            end_year = int(end_str)
        except ValueError:
            return None

    return {
        'start': start_year,
        'end': end_year,
        'display': period_str,
    }
