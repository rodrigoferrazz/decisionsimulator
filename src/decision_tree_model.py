"""Decision tree model for AgroVision.

This module translates the spreadsheet decision tree logic into reusable Python
logic for the simulator.
"""

from __future__ import annotations


BASE_PRODUCTIVITY = 60.0


PLANTING_WINDOW_EFFECTS = {
    "Early": 4.0,
    "Normal": 0.0,
    "Late": -8.0,
}

CLIMATE_EFFECTS = {
    "Dry": -3.0,
    "Normal": 2.0,
    "Wet": 3.0,
}

SOIL_PH_EFFECTS = {
    "s1": -3.0,
    "s2": 2.0,
    "s3": 3.0,
}

SEED_TYPE_EFFECTS = {
    "t1": -3.0,
    "t2": 2.0,
    "t3": 3.0,
}


def calculate_decision_tree_productivity(
    planting_window: str,
    climate_condition: str,
    soil_ph_class: str,
    seed_type: str,
) -> float:
    """Calculate productivity using the Sprint 03 decision tree logic."""

    productivity = BASE_PRODUCTIVITY

    productivity += PLANTING_WINDOW_EFFECTS.get(
        planting_window,
        0.0,
    )

    productivity += CLIMATE_EFFECTS.get(
        climate_condition,
        0.0,
    )

    productivity += SOIL_PH_EFFECTS.get(
        soil_ph_class,
        0.0,
    )

    productivity += SEED_TYPE_EFFECTS.get(
        seed_type,
        0.0,
    )

    return round(productivity, 2)