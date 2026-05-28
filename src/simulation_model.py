"""Weather-driven simulation model for AgroVision.

This module converts external weather forecasts into the same decision inputs
already used by the Sprint 03 decision engine: scenario probabilities and a
productivity payoff matrix.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any

from src.data.historical_indicators import (
    get_crop_model_inputs,
    yield_to_bags_per_hectare,
)
from src.decision_engine import (
    DEFAULT_PAYOFF_MATRIX,
    DEFAULT_SCENARIO_PROBABILITIES,
    DecisionSummary,
    PayoffMatrix,
    ScenarioProbabilities,
    build_decision_summary,
)


DECISION_TREE_METHOD = "Decision Tree"
PAYOFF_MATRIX_METHOD = "Payoff Matrix"


@dataclass(frozen=True)
class WeatherDrivenSimulation:
    """Decision-engine inputs derived from field context and weather forecast."""

    simulation_method: str
    probabilities: ScenarioProbabilities
    payoff_matrix: PayoffMatrix
    weather_evidence: dict[str, object]
    climatic_condition: str
    expected_productivity_bags_ha: float
    recommendation_summary: str
    productivity_factors: dict[str, float]
    decision_summary: DecisionSummary | None = None


def build_weather_driven_simulation(
    field_context: dict[str, object],
    forecast: dict[str, Any],
    station_observation: dict[str, object] | None = None,
) -> WeatherDrivenSimulation:
    """Backward-compatible alias for the Decision Tree simulation engine."""
    return build_decision_tree_simulation(
        field_context,
        forecast,
        station_observation=station_observation,
    )


def build_decision_tree_simulation(
    field_context: dict[str, object],
    forecast: dict[str, Any],
    station_observation: dict[str, object] | None = None,
) -> WeatherDrivenSimulation:
    """Build decision inputs from a weather forecast and field context."""
    daily = forecast.get("daily", {})
    station_observation_factor = _station_observation_factor(station_observation)
    max_temps = _as_float_list(daily.get("temperature_2m_max", []))
    min_temps = _as_float_list(daily.get("temperature_2m_min", []))
    precipitation = _as_float_list(daily.get("precipitation_sum", []))
    precipitation_probability = _as_float_list(
        daily.get("precipitation_probability_max", [])
    )
    evapotranspiration = _as_float_list(daily.get("et0_fao_evapotranspiration", []))
    weather_codes = [int(code) for code in daily.get("weather_code", [])]

    if not _has_required_daily_data(
        max_temps,
        min_temps,
        precipitation,
        precipitation_probability,
        evapotranspiration,
        weather_codes,
    ):
        return WeatherDrivenSimulation(
            simulation_method=DECISION_TREE_METHOD,
            probabilities=dict(DEFAULT_SCENARIO_PROBABILITIES),
            payoff_matrix={
                strategy: dict(payoffs)
                for strategy, payoffs in DEFAULT_PAYOFF_MATRIX.items()
            },
            weather_evidence={
                "classification": "Limited data",
                "limited_data": True,
                "forecast_days": len(daily.get("time", [])),
                "location": _field_location_label(field_context),
                "source": _weather_source_label(station_observation),
                "station_observation": _station_observation_evidence(
                    station_observation,
                    station_observation_factor,
                ),
            },
            climatic_condition="Limited data",
            **_productivity_result(
                field_context,
                "Limited data",
                station_observation_factor=station_observation_factor,
            ),
        )

    average_temp = mean([(high + low) / 2 for high, low in zip(max_temps, min_temps)])
    total_precipitation = sum(precipitation)
    max_precipitation_probability = max(precipitation_probability, default=0.0)
    average_et0 = mean(evapotranspiration) if evapotranspiration else 0.0

    classification = _classify_weather(
        average_temp=average_temp,
        total_precipitation=total_precipitation,
        max_precipitation_probability=max_precipitation_probability,
        average_et0=average_et0,
        weather_codes=weather_codes,
    )
    weather_intensity_factor = _weather_intensity_factor(
        classification=classification,
        average_temp=average_temp,
        total_precipitation=total_precipitation,
        max_precipitation_probability=max_precipitation_probability,
        average_et0=average_et0,
        forecast_days=len(daily.get("time", [])),
    )
    combined_weather_factor = round(
        weather_intensity_factor * station_observation_factor,
        4,
    )

    probabilities = _probabilities_for_classification(classification)
    payoff_matrix = _adjust_payoff_matrix(
        classification=classification,
        field_context=field_context,
    )

    return WeatherDrivenSimulation(
        simulation_method=DECISION_TREE_METHOD,
        probabilities=probabilities,
        payoff_matrix=payoff_matrix,
        weather_evidence={
            "classification": classification,
            "average_temperature_c": round(average_temp, 1),
            "total_precipitation_mm": round(total_precipitation, 1),
            "max_precipitation_probability_pct": round(max_precipitation_probability),
            "average_et0_mm": round(average_et0, 1),
            "forecast_days": len(daily.get("time", [])),
            "weather_intensity_factor": weather_intensity_factor,
            "station_observation_factor": station_observation_factor,
            "combined_weather_factor": combined_weather_factor,
            "location": _field_location_label(field_context),
            "source": _weather_source_label(station_observation),
            "station_observation": _station_observation_evidence(
                station_observation,
                station_observation_factor,
            ),
            "limited_data": False,
        },
        climatic_condition=classification,
        **_productivity_result(
            field_context,
            classification,
            weather_intensity_factor=weather_intensity_factor,
            station_observation_factor=station_observation_factor,
        ),
    )


def build_payoff_matrix_simulation(
    field_context: dict[str, object],
    forecast: dict[str, Any],
    station_observation: dict[str, object] | None = None,
) -> WeatherDrivenSimulation:
    """Build a simulation result using the Payoff Matrix decision engine."""
    base_simulation = build_decision_tree_simulation(
        field_context,
        forecast,
        station_observation=station_observation,
    )
    decision_summary = build_decision_summary(
        base_simulation.payoff_matrix,
        base_simulation.probabilities,
    )
    final_strategy = decision_summary.final_recommendation
    expected_value = decision_summary.expected_value.scores[final_strategy]
    maximum_regret = decision_summary.minimax.scores[final_strategy]
    productivity_factors = {
        **base_simulation.productivity_factors,
        "decision_expected_value": expected_value,
        "decision_maximum_regret": maximum_regret,
    }

    return WeatherDrivenSimulation(
        simulation_method=PAYOFF_MATRIX_METHOD,
        probabilities=base_simulation.probabilities,
        payoff_matrix=base_simulation.payoff_matrix,
        weather_evidence=base_simulation.weather_evidence,
        climatic_condition=base_simulation.climatic_condition,
        expected_productivity_bags_ha=expected_value,
        recommendation_summary=(
            f"Payoff Matrix recommends {final_strategy}. "
            f"The selected strategy has Expected Value of {expected_value:.2f} "
            f"bags/ha and maximum regret of {maximum_regret:.2f} bags/ha under "
            "the forecast-derived scenario probabilities."
        ),
        productivity_factors=productivity_factors,
        decision_summary=decision_summary,
    )


def _classify_weather(
    *,
    average_temp: float,
    total_precipitation: float,
    max_precipitation_probability: float,
    average_et0: float,
    weather_codes: list[int],
) -> str:
    severe_weather = any(code >= 95 for code in weather_codes)
    dry_pressure = total_precipitation < 5.0 and average_et0 >= 4.5
    excessive_rain = total_precipitation > 70.0 or max_precipitation_probability >= 85.0
    temperature_stress = average_temp < 16.0 or average_temp > 31.0

    if severe_weather or dry_pressure or excessive_rain or temperature_stress:
        return "Unfavorable"

    moderate_rain = 8.0 <= total_precipitation <= 45.0
    moderate_temperature = 18.0 <= average_temp <= 28.0
    if moderate_rain and moderate_temperature:
        return "Favorable"

    return "Moderate"


def _probabilities_for_classification(classification: str) -> ScenarioProbabilities:
    if classification == "Favorable":
        return {
            "C1 - Favorable": 0.55,
            "C2 - Moderate": 0.30,
            "C3 - Unfavorable": 0.15,
        }
    if classification == "Unfavorable":
        return {
            "C1 - Favorable": 0.15,
            "C2 - Moderate": 0.30,
            "C3 - Unfavorable": 0.55,
        }
    return {
        "C1 - Favorable": 0.25,
        "C2 - Moderate": 0.50,
        "C3 - Unfavorable": 0.25,
    }


def _weather_intensity_factor(
    *,
    classification: str,
    average_temp: float,
    total_precipitation: float,
    max_precipitation_probability: float,
    average_et0: float,
    forecast_days: int,
) -> float:
    """Return a continuous productivity adjustment from Open-Meteo signals."""
    safe_days = max(forecast_days, 1)
    precipitation_per_day = total_precipitation / safe_days
    water_reference = max(average_et0, 1.0)
    water_balance = precipitation_per_day - average_et0
    water_fit = 1.0 - min(abs(water_balance) / water_reference, 1.0)

    ideal_temperature = 24.0
    temperature_fit = 1.0 - min(abs(average_temp - ideal_temperature) / 18.0, 1.0)
    precipitation_risk = min(max(max_precipitation_probability - 60.0, 0.0) / 40.0, 1.0)

    factor = 0.94 + (water_fit * 0.08) + (temperature_fit * 0.04)
    factor -= precipitation_risk * 0.04

    if classification == "Favorable":
        return round(_clamp(factor, 0.94, 1.06), 4)
    if classification == "Moderate":
        return round(_clamp(factor - 0.03, 0.88, 1.03), 4)
    if classification == "Unfavorable":
        return round(_clamp(factor - 0.10, 0.72, 0.98), 4)
    return 1.0


def _adjust_payoff_matrix(
    *,
    classification: str,
    field_context: dict[str, object],
) -> PayoffMatrix:
    payoff_matrix = {
        strategy: dict(payoffs) for strategy, payoffs in DEFAULT_PAYOFF_MATRIX.items()
    }

    if classification != "Unfavorable":
        return payoff_matrix

    intensive_penalty = 10.0
    if field_context.get("operation_type") == "High-density planting":
        intensive_penalty += 2.0
    if float(field_context.get("speed", 0.0) or 0.0) > 10.0:
        intensive_penalty += 2.0

    payoff_matrix["Conservative Strategy"]["C3 - Unfavorable"] -= 3.0
    payoff_matrix["Adaptive Strategy"]["C3 - Unfavorable"] -= 6.0
    payoff_matrix["Intensive Strategy"]["C3 - Unfavorable"] -= intensive_penalty

    return payoff_matrix


def _productivity_result(
    field_context: dict[str, object],
    classification: str,
    weather_intensity_factor: float = 1.0,
    station_observation_factor: float = 1.0,
) -> dict[str, object]:
    seed_type = _normalize_seed_type(field_context.get("seed_type") or field_context.get("crop"))
    crop_model = get_crop_model_inputs(seed_type)
    soil_ph = float(field_context.get("soil_ph", 6.2) or 6.2)
    planting_window = str(field_context.get("planting_window", "Ideal") or "Ideal")
    base_productivity = yield_to_bags_per_hectare(crop_model.median_yield)
    climate_factor = round(
        crop_model.climate_factors.get(classification, 1.0)
        * weather_intensity_factor,
        4,
    )
    combined_climate_factor = round(
        climate_factor * station_observation_factor,
        4,
    )
    soil_factor = _soil_ph_factor(
        soil_ph=soil_ph,
        soil_ph_min=crop_model.soil_ph_min,
        soil_ph_max=crop_model.soil_ph_max,
    )
    window_factor = crop_model.planting_window_factors.get(planting_window, 1.0)
    expected_productivity = round(
        base_productivity * combined_climate_factor * soil_factor * window_factor,
        2,
    )

    return {
        "expected_productivity_bags_ha": expected_productivity,
        "recommendation_summary": _recommendation_summary(
            seed_type=seed_type,
            classification=classification,
            soil_ph=soil_ph,
            planting_window=planting_window,
            expected_productivity=expected_productivity,
        ),
        "productivity_factors": {
            "base_productivity": base_productivity,
            "climate_factor": combined_climate_factor,
            "open_meteo_climate_factor": climate_factor,
            "weather_intensity_factor": weather_intensity_factor,
            "station_observation_factor": station_observation_factor,
            "soil_ph_factor": soil_factor,
            "planting_window_factor": window_factor,
            "bayer_records": crop_model.record_count,
        },
    }


def _normalize_seed_type(seed_type: object) -> str:
    normalized = str(seed_type or "soybean").strip().lower()
    if normalized in {"soybeans", "soybean"}:
        return "soybean"
    if normalized in {"corn", "maize"}:
        return "corn"
    return "soybean"


def _soil_ph_factor(*, soil_ph: float, soil_ph_min: float, soil_ph_max: float) -> float:
    if soil_ph_min <= soil_ph <= soil_ph_max:
        return 1.0
    nearest_boundary = soil_ph_min if soil_ph < soil_ph_min else soil_ph_max
    observed_width = max(soil_ph_max - soil_ph_min, 1.0)
    distance_ratio = abs(soil_ph - nearest_boundary) / observed_width
    return round(max(0.0, 1.0 - distance_ratio), 4)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def _station_observation_factor(station_observation: dict[str, object] | None) -> float:
    """Return a small local correction from observed station conditions."""
    if not station_observation:
        return 1.0

    observed_days = max(int(station_observation.get("observed_days", 1) or 1), 1)
    average_temp = _safe_float(
        station_observation.get("average_temperature_c"),
        default=24.0,
    )
    total_precipitation = _safe_float(
        station_observation.get("total_precipitation_mm"),
        default=0.0,
    )
    average_et0 = _safe_optional_float(station_observation.get("average_et0_mm"))
    average_humidity = _safe_float(
        station_observation.get("average_relative_humidity_pct"),
        default=75.0,
    )
    average_delta_t = _safe_float(
        station_observation.get("average_delta_t_c"),
        default=3.0,
    )

    temperature_fit = 1.0 - min(abs(average_temp - 24.0) / 18.0, 1.0)
    precipitation_per_day = total_precipitation / observed_days

    if average_et0 is not None:
        water_reference = max(average_et0, 1.0)
        water_balance = precipitation_per_day - average_et0
        water_fit = 1.0 - min(abs(water_balance) / water_reference, 1.0)
    elif precipitation_per_day < 1.0 and average_humidity < 70.0:
        water_fit = 0.25
    elif precipitation_per_day > 20.0:
        water_fit = 0.35
    else:
        water_fit = 0.75

    delta_t_penalty = 0.02 if average_delta_t >= 8.0 else 0.0
    factor = 0.98 + (temperature_fit * 0.02) + (water_fit * 0.02)
    factor -= delta_t_penalty
    return round(_clamp(factor, 0.94, 1.03), 4)


def _station_observation_evidence(
    station_observation: dict[str, object] | None,
    station_observation_factor: float,
) -> dict[str, object]:
    if not station_observation:
        return {
            "available": False,
            "station_observation_factor": 1.0,
        }

    return {
        **station_observation,
        "available": True,
        "station_observation_factor": station_observation_factor,
    }


def _weather_source_label(station_observation: dict[str, object] | None) -> str:
    if station_observation:
        return "Open-Meteo + local station database"
    return "Open-Meteo"


def _safe_float(value: object, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_optional_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _recommendation_summary(
    *,
    seed_type: str,
    classification: str,
    soil_ph: float,
    planting_window: str,
    expected_productivity: float,
) -> str:
    crop_label = "Soybean" if seed_type == "soybean" else "Corn"
    crop_model = get_crop_model_inputs(seed_type)
    low = crop_model.soil_ph_min
    high = crop_model.soil_ph_max
    ph_note = (
        "soil pH is inside the preferred range"
        if low <= soil_ph <= high
        else "soil pH is outside the preferred range and reduces the forecast"
    )
    window_note = (
        "the planting window is ideal"
        if planting_window == "Ideal"
        else f"the {planting_window.lower()} planting window adds timing risk"
    )
    climate_note = (
        "conditions support proceeding"
        if classification == "Favorable"
        else "conditions require caution"
        if classification == "Moderate"
        else "conditions are risky; postpone or reassess before planting"
        if classification == "Unfavorable"
        else "weather data is incomplete; use this as a baseline estimate"
    )
    return (
        f"{crop_label} expected productivity is {expected_productivity:.2f} bags/ha. "
        f"The Open-Meteo forecast classifies climatic conditions as {classification}; "
        f"{ph_note}, and {window_note}. Recommendation: {climate_note}."
    )


def _field_location_label(field_context: dict[str, object]) -> str:
    latitude = field_context.get("farm_latitude")
    longitude = field_context.get("farm_longitude")
    if latitude is not None and longitude is not None:
        return f"{float(latitude):.4f}, {float(longitude):.4f}"
    return str(field_context.get("region", ""))


def _has_required_daily_data(*series: list[object]) -> bool:
    lengths = {len(values) for values in series}
    return bool(lengths) and 0 not in lengths and len(lengths) == 1


def _as_float_list(values: list[object]) -> list[float]:
    return [float(value) for value in values]
