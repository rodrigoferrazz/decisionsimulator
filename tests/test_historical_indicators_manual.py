"""Manual checks for Bayer dataset-backed historical indicators.

Run from this folder with:
python tests/test_historical_indicators_manual.py
"""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from src.data.historical_indicators import (  # noqa: E402
    get_at_a_glance,
    get_historical_insights,
    load_bayer_historical_metrics,
)


def test_historical_indicators_are_calculated_from_source_csvs() -> None:
    with TemporaryDirectory() as temp_dir:
        data_dir = Path(temp_dir)
        planting_path = data_dir / "planting.csv"
        harvest_path = data_dir / "harvest.csv"

        planting_path.write_text(
            "\n".join(
                [
                    "field_uuid,crop_name,planting_date,soil_ph_min,soil_ph_max,soil_texture",
                    "f1,soybeans,01-09-2025,5.0,6.0,textura média",
                    "f2,soybeans,15-10-2025,5.0,6.0,textura média",
                    "f3,corn,10-02-2025,5.5,6.5,franca",
                    "f4,corn,20-03-2025,5.5,6.5,franca",
                ]
            ),
            encoding="utf-8",
        )
        harvest_path.write_text(
            "\n".join(
                [
                    "field_uuid,crop_name,average_yield",
                    "f1,soybeans,5000",
                    "f2,soybeans,5200",
                    "f3,corn,6000",
                    "f4,corn,6400",
                ]
            ),
            encoding="utf-8",
        )

        metrics = load_bayer_historical_metrics(planting_path, harvest_path)

    assert metrics.planting_rows == 4
    assert metrics.harvest_rows == 4
    assert metrics.merged_rows == 4
    assert metrics.crop_models["soybean"].median_yield == 5100
    assert metrics.crop_models["corn"].median_yield == 6200

    at_a_glance = get_at_a_glance(metrics)
    insights = get_historical_insights(metrics)

    assert at_a_glance[0]["value"] == "85.0"
    assert at_a_glance[0]["unit"] == "bags/ha"
    assert at_a_glance[1]["value"] == "85.8"
    assert at_a_glance[1]["unit"] == "bags/ha"
    assert at_a_glance[2]["value"] == "103.3"
    assert at_a_glance[2]["unit"] == "bags/ha"
    assert at_a_glance[3]["value"] == "105.0"
    assert at_a_glance[3]["unit"] == "bags/ha"
    assert insights[0]["title"] == "Corn productivity baseline"
    assert insights[0]["value"] == "103.3 bags/ha"
    assert insights[1]["title"] == "Corn favorable productivity"
    assert insights[1]["value"] == "105.0 bags/ha"
    assert insights[2]["title"] == "Soybean productivity baseline"
    assert insights[2]["value"] == "85.0 bags/ha"
    assert insights[3]["title"] == "Soybean favorable productivity"
    assert insights[3]["value"] == "85.8 bags/ha"


if __name__ == "__main__":
    test_historical_indicators_are_calculated_from_source_csvs()
    print("Manual historical-indicator checks passed.")
