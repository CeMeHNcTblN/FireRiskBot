"""Очаги пожаров через NASA FIRMS Area API."""
import logging
import pandas as pd
import requests

log = logging.getLogger(__name__)

FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
DEFAULT_SOURCE = "VIIRS_SNPP_NRT"

# Колонки, которые есть в ответе FIRMS (для справки)
FIRE_COLUMNS = [
    "latitude", "longitude", "bright_ti4", "scan", "track",
    "acq_date", "acq_time", "satellite", "instrument",
    "confidence", "version", "bright_ti5", "frp", "daynight",
]


def get_fires(west: float, south: float, east: float, north: float,
              key: str, days: int = 3, source: str = DEFAULT_SOURCE) -> pd.DataFrame:
    """Возвращает DataFrame с очагами пожаров в bounding box."""
    bbox = f"{west},{south},{east},{north}"
    url = f"{FIRMS_BASE}/{key}/{source}/{bbox}/{days}"

    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
    except requests.HTTPError as e:
        log.error("FIRMS HTTP ошибка: %s — %s", e, r.text[:200])
        return pd.DataFrame(columns=FIRE_COLUMNS)
    except requests.RequestException as e:
        log.error("FIRMS сеть: %s", e)
        return pd.DataFrame(columns=FIRE_COLUMNS)

    from io import StringIO
    try:
        df = pd.read_csv(StringIO(r.text))
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=FIRE_COLUMNS)

    return df


def count_fires(df: pd.DataFrame) -> int:
    return 0 if df is None or df.empty else len(df)
