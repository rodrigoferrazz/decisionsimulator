"""Open-Meteo client utilities for the AgroVision simulator."""

from __future__ import annotations

from dataclasses import dataclass
import json
import ssl
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

DAILY_VARIABLES = (
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "precipitation_probability_max",
    "et0_fao_evapotranspiration",
)


@dataclass(frozen=True)
class WeatherLocation:
    """Representative weather lookup point for a Brazilian state."""

    state: str
    label: str
    latitude: float
    longitude: float


REGION_WEATHER_LOCATIONS: dict[str, WeatherLocation] = {
    "BA": WeatherLocation("BA", "Salvador, BA", -12.9777, -38.5016),
    "DF": WeatherLocation("DF", "Brasília, DF", -15.7939, -47.8828),
    "GO": WeatherLocation("GO", "Goiânia, GO", -16.6869, -49.2648),
    "MA": WeatherLocation("MA", "São Luís, MA", -2.5307, -44.3068),
    "MG": WeatherLocation("MG", "Belo Horizonte, MG", -19.9167, -43.9345),
    "MS": WeatherLocation("MS", "Campo Grande, MS", -20.4697, -54.6201),
    "MT": WeatherLocation("MT", "Cuiabá, MT", -15.6014, -56.0979),
    "PA": WeatherLocation("PA", "Belém, PA", -1.4558, -48.5044),
    "PI": WeatherLocation("PI", "Teresina, PI", -5.0892, -42.8019),
    "PR": WeatherLocation("PR", "Curitiba, PR", -25.4284, -49.2733),
    "RO": WeatherLocation("RO", "Porto Velho, RO", -8.7619, -63.9039),
    "RS": WeatherLocation("RS", "Porto Alegre, RS", -30.0346, -51.2177),
    "SC": WeatherLocation("SC", "Florianópolis, SC", -27.5949, -48.5482),
    "SP": WeatherLocation("SP", "São Paulo, SP", -23.5505, -46.6333),
    "TO": WeatherLocation("TO", "Palmas, TO", -10.2491, -48.3243),
}


def get_region_weather_location(region_state: str) -> WeatherLocation:
    """Return the representative Open-Meteo lookup point for a state."""
    return REGION_WEATHER_LOCATIONS.get(
        region_state,
        REGION_WEATHER_LOCATIONS["GO"],
    )


def build_farm_weather_location(
    latitude: float,
    longitude: float,
    label: str = "Farm location",
) -> WeatherLocation:
    """Return an exact Open-Meteo lookup point for the selected farm."""
    return WeatherLocation(
        state="Farm",
        label=label,
        latitude=latitude,
        longitude=longitude,
    )


def build_open_meteo_url(location: WeatherLocation) -> str:
    """Build the Open-Meteo forecast URL for the simulator's required variables."""
    query = urlencode(
        {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "daily": ",".join(DAILY_VARIABLES),
            "forecast_days": 7,
            "timezone": "America/Sao_Paulo",
        }
    )
    return f"{OPEN_METEO_FORECAST_URL}?{query}"


def fetch_open_meteo_forecast(location: WeatherLocation) -> dict[str, Any]:
    """Fetch a seven-day forecast from Open-Meteo."""
    with urlopen(
        build_open_meteo_url(location),
        timeout=12,
        context=_ssl_context(),
    ) as response:
        return json.loads(response.read().decode("utf-8"))


def _ssl_context() -> ssl.SSLContext:
    """Return a certificate context that works with local Python installs."""
    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())
