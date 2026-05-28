"""Manual checks for the weather-driven simulation model.

Run from this folder with:
python tests/test_weather_simulation_manual.py
"""

from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from src.decision_engine import DEFAULT_SCENARIO_PROBABILITIES  # noqa: E402
from src.data.historical_indicators import (  # noqa: E402
    get_crop_model_inputs,
    yield_to_bags_per_hectare,
)
from src.simulation_model import (  # noqa: E402
    build_decision_tree_simulation,
    build_payoff_matrix_simulation,
    build_weather_driven_simulation,
)


def test_favorable_forecast_increases_favorable_scenario_probability() -> None:
    result = build_weather_driven_simulation(
        field_context={
            "farm_latitude": -16.6869,
            "farm_longitude": -49.2648,
            "seed_type": "soybean",
            "soil_ph": 5.5,
            "planting_window": "Ideal",
        },
        forecast={
            "daily": {
                "time": ["2026-05-26", "2026-05-27", "2026-05-28"],
                "temperature_2m_max": [27.0, 28.0, 26.5],
                "temperature_2m_min": [18.0, 19.0, 18.5],
                "precipitation_sum": [4.0, 5.0, 3.0],
                "precipitation_probability_max": [45, 50, 40],
                "weather_code": [2, 3, 3],
                "et0_fao_evapotranspiration": [3.8, 4.0, 3.6],
            }
        },
    )

    probabilities = result.probabilities

    assert round(sum(probabilities.values()), 2) == 1.00
    assert probabilities["C1 - Favorable"] > probabilities["C2 - Moderate"]
    assert probabilities["C1 - Favorable"] > probabilities["C3 - Unfavorable"]
    assert result.weather_evidence["classification"] == "Favorable"
    assert result.climatic_condition == "Favorable"
    assert result.simulation_method == "Decision Tree"
    assert result.decision_summary is None
    soybean_model = get_crop_model_inputs("soybean")
    assert result.expected_productivity_bags_ha == round(
        yield_to_bags_per_hectare(soybean_model.median_yield)
        * result.productivity_factors["climate_factor"]
        * result.productivity_factors["soil_ph_factor"]
        * soybean_model.planting_window_factors["Ideal"],
        2,
    )
    assert "Soybean" in result.recommendation_summary


def test_same_classification_forecasts_still_change_expected_productivity() -> None:
    field_context = {
        "farm_latitude": -13.5277,
        "farm_longitude": -56.0469,
        "seed_type": "soybean",
        "soil_ph": 6.2,
        "planting_window": "Ideal",
    }
    low_rain_forecast = {
        "daily": {
            "time": ["2026-05-26", "2026-05-27", "2026-05-28"],
            "temperature_2m_max": [27.0, 27.0, 27.0],
            "temperature_2m_min": [18.0, 18.0, 18.0],
            "precipitation_sum": [3.0, 3.0, 2.0],
            "precipitation_probability_max": [35, 40, 35],
            "weather_code": [2, 2, 2],
            "et0_fao_evapotranspiration": [3.4, 3.6, 3.5],
        }
    }
    high_rain_forecast = {
        "daily": {
            "time": ["2026-05-26", "2026-05-27", "2026-05-28"],
            "temperature_2m_max": [27.0, 27.0, 27.0],
            "temperature_2m_min": [18.0, 18.0, 18.0],
            "precipitation_sum": [15.0, 14.0, 13.0],
            "precipitation_probability_max": [70, 75, 70],
            "weather_code": [2, 2, 2],
            "et0_fao_evapotranspiration": [3.4, 3.6, 3.5],
        }
    }

    low_rain_result = build_weather_driven_simulation(
        field_context=field_context,
        forecast=low_rain_forecast,
    )
    high_rain_result = build_weather_driven_simulation(
        field_context=field_context,
        forecast=high_rain_forecast,
    )

    assert low_rain_result.weather_evidence["classification"] == "Favorable"
    assert high_rain_result.weather_evidence["classification"] == "Favorable"
    assert (
        low_rain_result.expected_productivity_bags_ha
        != high_rain_result.expected_productivity_bags_ha
    )
    assert (
        low_rain_result.productivity_factors["weather_intensity_factor"]
        != high_rain_result.productivity_factors["weather_intensity_factor"]
    )


def test_station_observations_adjust_productivity_and_evidence() -> None:
    field_context = {
        "farm_latitude": -13.5277,
        "farm_longitude": -56.0469,
        "seed_type": "soybean",
        "soil_ph": 6.2,
        "planting_window": "Ideal",
    }
    forecast = {
        "daily": {
            "time": ["2026-05-26", "2026-05-27", "2026-05-28"],
            "temperature_2m_max": [27.0, 28.0, 26.5],
            "temperature_2m_min": [18.0, 19.0, 18.5],
            "precipitation_sum": [4.0, 5.0, 3.0],
            "precipitation_probability_max": [45, 50, 40],
            "weather_code": [2, 3, 3],
            "et0_fao_evapotranspiration": [3.8, 4.0, 3.6],
        }
    }
    station_observation = {
        "source": "Local station database",
        "file_name": "station_data.xls",
        "row_count": 49,
        "observed_days": 3,
        "start_time": "2026-05-18 12:00",
        "end_time": "2026-05-20 12:00",
        "average_temperature_c": 18.4,
        "total_precipitation_mm": 5.2,
        "average_relative_humidity_pct": 92.7,
        "average_delta_t_c": 0.8,
        "average_et0_mm": 1.2,
    }

    forecast_only = build_weather_driven_simulation(
        field_context=field_context,
        forecast=forecast,
    )
    with_station = build_weather_driven_simulation(
        field_context=field_context,
        forecast=forecast,
        station_observation=station_observation,
    )

    assert with_station.weather_evidence["source"] == (
        "Open-Meteo + local station database"
    )
    assert with_station.weather_evidence["station_observation"]["available"] is True
    assert with_station.productivity_factors["station_observation_factor"] != 1.0
    assert (
        with_station.expected_productivity_bags_ha
        != forecast_only.expected_productivity_bags_ha
    )


def test_hot_dry_forecast_increases_unfavorable_probability_and_intensive_downside() -> None:
    result = build_weather_driven_simulation(
        field_context={
            "farm_latitude": -13.5277,
            "farm_longitude": -56.0469,
            "seed_type": "corn",
            "soil_ph": 4.4,
            "planting_window": "Late",
        },
        forecast={
            "daily": {
                "time": ["2026-05-26", "2026-05-27", "2026-05-28"],
                "temperature_2m_max": [35.0, 36.0, 34.0],
                "temperature_2m_min": [24.0, 25.0, 24.0],
                "precipitation_sum": [0.0, 0.0, 1.0],
                "precipitation_probability_max": [5, 8, 10],
                "weather_code": [0, 1, 1],
                "et0_fao_evapotranspiration": [5.6, 5.9, 5.8],
            }
        },
    )

    probabilities = result.probabilities
    payoff_matrix = result.payoff_matrix

    assert probabilities["C3 - Unfavorable"] > probabilities["C2 - Moderate"]
    assert probabilities["C3 - Unfavorable"] > probabilities["C1 - Favorable"]
    assert payoff_matrix["Intensive Strategy"]["C3 - Unfavorable"] < 45.0
    assert payoff_matrix["Conservative Strategy"]["C3 - Unfavorable"] >= 58.0
    assert result.weather_evidence["classification"] == "Unfavorable"
    corn_model = get_crop_model_inputs("corn")
    assert result.expected_productivity_bags_ha < yield_to_bags_per_hectare(
        corn_model.median_yield
    )
    assert "Corn expected productivity" in result.recommendation_summary
    assert "outside the preferred range" in result.recommendation_summary


def test_incomplete_forecast_uses_explicit_baseline_fallback() -> None:
    result = build_weather_driven_simulation(
        field_context={
            "region": "PR",
            "crop": "wheat",
            "soil_texture": "franca",
            "area": 80.0,
            "planting_objective": "Protect downside risk",
            "operation_type": "Conservative planting",
            "speed": 6.0,
        },
        forecast={"daily": {}},
    )

    assert result.probabilities == DEFAULT_SCENARIO_PROBABILITIES
    assert result.weather_evidence["classification"] == "Limited data"
    assert result.weather_evidence["limited_data"] is True


def test_explicit_decision_tree_builder_matches_backward_compatible_builder() -> None:
    field_context = {
        "farm_latitude": -16.6869,
        "farm_longitude": -49.2648,
        "seed_type": "soybean",
        "soil_ph": 6.0,
        "planting_window": "Ideal",
    }
    forecast = {
        "daily": {
            "time": ["2026-05-26", "2026-05-27", "2026-05-28"],
            "temperature_2m_max": [27.0, 28.0, 26.5],
            "temperature_2m_min": [18.0, 19.0, 18.5],
            "precipitation_sum": [4.0, 5.0, 3.0],
            "precipitation_probability_max": [45, 50, 40],
            "weather_code": [2, 3, 3],
            "et0_fao_evapotranspiration": [3.8, 4.0, 3.6],
        }
    }

    legacy_result = build_weather_driven_simulation(field_context, forecast)
    decision_tree_result = build_decision_tree_simulation(field_context, forecast)

    assert legacy_result.simulation_method == "Decision Tree"
    assert decision_tree_result.simulation_method == "Decision Tree"
    assert legacy_result.expected_productivity_bags_ha == (
        decision_tree_result.expected_productivity_bags_ha
    )
    assert legacy_result.probabilities == decision_tree_result.probabilities


def test_payoff_matrix_simulation_uses_decision_summary_engine() -> None:
    result = build_payoff_matrix_simulation(
        field_context={
            "farm_latitude": -13.5277,
            "farm_longitude": -56.0469,
            "seed_type": "corn",
            "soil_ph": 6.2,
            "planting_window": "Ideal",
        },
        forecast={
            "daily": {
                "time": ["2026-05-26", "2026-05-27", "2026-05-28"],
                "temperature_2m_max": [27.0, 27.0, 27.0],
                "temperature_2m_min": [18.0, 18.0, 18.0],
                "precipitation_sum": [3.0, 3.0, 2.0],
                "precipitation_probability_max": [35, 40, 35],
                "weather_code": [2, 2, 2],
                "et0_fao_evapotranspiration": [3.4, 3.6, 3.5],
            }
        },
    )

    assert result.simulation_method == "Payoff Matrix"
    assert result.decision_summary is not None
    assert result.expected_productivity_bags_ha == (
        result.decision_summary.expected_value.scores[
            result.decision_summary.final_recommendation
        ]
    )
    assert "Payoff Matrix recommends" in result.recommendation_summary
    assert round(sum(result.probabilities.values()), 2) == 1.00


if __name__ == "__main__":
    test_favorable_forecast_increases_favorable_scenario_probability()
    test_same_classification_forecasts_still_change_expected_productivity()
    test_station_observations_adjust_productivity_and_evidence()
    test_hot_dry_forecast_increases_unfavorable_probability_and_intensive_downside()
    test_incomplete_forecast_uses_explicit_baseline_fallback()
    test_explicit_decision_tree_builder_matches_backward_compatible_builder()
    test_payoff_matrix_simulation_uses_decision_summary_engine()
    print("Manual weather-simulation checks passed.")
