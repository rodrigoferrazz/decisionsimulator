"""Manual checks for the Open-Meteo client helpers.

Run from this folder with:
python tests/test_weather_client_manual.py
"""

from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from src.weather_client import (  # noqa: E402
    build_farm_weather_location,
    build_open_meteo_url,
    get_region_weather_location,
)


def test_region_state_builds_forecast_url_with_required_daily_variables() -> None:
    location = get_region_weather_location("GO")
    url = build_open_meteo_url(location)

    assert location.label == "Goiânia, GO"
    assert "latitude=-16.6869" in url
    assert "longitude=-49.2648" in url
    assert "weather_code" in url
    assert "temperature_2m_max" in url
    assert "temperature_2m_min" in url
    assert "precipitation_sum" in url
    assert "precipitation_probability_max" in url
    assert "et0_fao_evapotranspiration" in url


def test_farm_coordinates_build_forecast_url_for_exact_location() -> None:
    location = build_farm_weather_location(-13.5277, -56.0469)
    url = build_open_meteo_url(location)

    assert location.label == "Farm location"
    assert "latitude=-13.5277" in url
    assert "longitude=-56.0469" in url


if __name__ == "__main__":
    test_region_state_builds_forecast_url_with_required_daily_variables()
    test_farm_coordinates_build_forecast_url_for_exact_location()
    print("Manual weather-client checks passed.")
