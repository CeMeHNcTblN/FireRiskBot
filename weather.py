"""Погода через Open-Meteo: архив + прогноз, склейка."""
import datetime as dt
import logging
from dataclasses import dataclass

import pandas as pd
import requests_cache
from retry_requests import retry
from openmeteo_requests import Client

log = logging.getLogger(__name__)

_cache = requests_cache.CachedSession(".cache", expire_after=3600)
_session = retry(_cache, retries=5, backoff_factor=0.2)
_client = Client(session=_session)


@dataclass
class WeatherData:
    time: pd.Series
    temp: pd.Series
    dew: pd.Series
    rain: pd.Series

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame({
            "time": self.time,
            "temp": self.temp,
            "dew": self.dew,
            "rain": self.rain,
        })


def _extract(response) -> pd.DataFrame:
    hourly = response.Hourly()
    time = pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left",
    )
    return pd.DataFrame({
        "time": time,
        "temp": hourly.Variables(0).ValuesAsNumpy(),
        "dew": hourly.Variables(1).ValuesAsNumpy(),
        "rain": hourly.Variables(2).ValuesAsNumpy(),
    })


def get_history(lat: float, lon: float, days: int = 30) -> pd.DataFrame:
    """Погода за прошлые `days` дней через Archive API (ERA5)."""
    end = dt.date.today() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=days)

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat, "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "hourly": ["temperature_2m", "dew_point_2m", "rain"],
        "timezone": "Europe/Warsaw",
    }

    try:
        responses = _client.weather_api(url, params=params)
        return _extract(responses[0])
    except Exception as e:
        log.error("Ошибка Open-Meteo Archive: %s", e)
        return pd.DataFrame(columns=["time", "temp", "dew", "rain"])


def get_recent(lat: float, lon: float, past_days: int = 5) -> pd.DataFrame:
    """Погода за последние `past_days` через Forecast API (свежие данные)."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "hourly": ["temperature_2m", "dew_point_2m", "rain"],
        "past_days": past_days, "forecast_days": 1,
        "timezone": "Europe/Warsaw",
    }

    try:
        responses = _client.weather_api(url, params=params)
        return _extract(responses[0])
    except Exception as e:
        log.error("Ошибка Open-Meteo Forecast: %s", e)
        return pd.DataFrame(columns=["time", "temp", "dew", "rain"])


def get_weather_merged(lat: float, lon: float, days: int = 30) -> pd.DataFrame:
    """Склейка архива и свежего прогноза, дедупликация по timestamp."""
    old = get_history(lat, lon, days=days)
    recent = get_recent(lat, lon, past_days=5)

    merged = pd.concat([old, recent], ignore_index=True)
    merged = merged.drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
    return merged
