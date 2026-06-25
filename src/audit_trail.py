"""Audit trail — logs simulation inputs and recommendations to Supabase."""

from __future__ import annotations

import os
from typing import Any


_SUPABASE_URL = os.getenv("SUPABASE_URL", "")
_SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
_TABLE = "simulation_logs"


def _client():
    from supabase import create_client
    return create_client(_SUPABASE_URL, _SUPABASE_KEY)


def log_simulation(simulation: Any, field_context: dict[str, Any]) -> bool:
    """Insert one simulation run into simulation_logs. Returns True on success."""
    if not _SUPABASE_URL or not _SUPABASE_KEY:
        return False

    from src.decision_engine import build_decision_summary

    try:
        payoff_matrix = simulation.payoff_matrix
        probabilities = simulation.probabilities
        summary = simulation.decision_summary or build_decision_summary(payoff_matrix, probabilities)

        ev_scores = summary.expected_value.scores
        sorted_ev = sorted(ev_scores.items(), key=lambda x: x[1], reverse=True)
        decision_margin = round(sorted_ev[0][1] - sorted_ev[1][1], 2)
        criteria_agree = (
            summary.expected_value.recommendation == summary.minimax.recommendation
        )

        row = {
            "simulation_method": getattr(simulation, "simulation_method", "unknown"),
            "seed_type": str(field_context.get("seed_type", "")),
            "soil_ph": float(field_context.get("soil_ph", 0)),
            "planting_window": str(field_context.get("planting_window", "")),
            "farm_location": str(field_context.get("weather_location", "")),
            "climatic_condition": str(getattr(simulation, "climatic_condition", "")),
            "recommended_strategy": summary.final_recommendation,
            "expected_value_bags_ha": float(simulation.expected_productivity_bags_ha),
            "decision_margin": decision_margin,
            "criteria_agree": criteria_agree,
        }

        _client().table(_TABLE).insert(row).execute()
        return True

    except Exception:
        return False
