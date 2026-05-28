"""Manual checks for the local station weather database parser.

Run from this folder with:
python tests/test_station_weather_manual.py
"""

from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from src.data.station_weather import load_station_weather_summary  # noqa: E402


def test_station_weather_summary_is_loaded_from_excel_xml() -> None:
    summary = load_station_weather_summary()

    assert summary is not None
    assert summary.file_name == "station_data.xls"
    assert summary.row_count == 49
    assert summary.observed_days == 3
    assert summary.start_time == "2026-05-18 12:00"
    assert summary.end_time == "2026-05-20 12:00"
    assert summary.total_precipitation_mm == 5.2
    assert summary.et0_observation_count == 2
    assert summary.to_model_input()["source"] == "Local station database"


if __name__ == "__main__":
    test_station_weather_summary_is_loaded_from_excel_xml()
    print("Manual station-weather checks passed.")
