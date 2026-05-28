"""Input validation helpers for the AgroVision simulator.

These helpers are intentionally small so the interface can show clear messages
without mixing validation rules into the Streamlit page code.
"""

from __future__ import annotations

from src.decision_engine import PayoffMatrix, ScenarioProbabilities


def get_probability_total(probabilities: ScenarioProbabilities) -> float:
    """Return the probability total rounded for display and comparison."""
    return round(sum(probabilities.values()), 4)


def probability_total_is_valid(probabilities: ScenarioProbabilities) -> bool:
    """Check whether scenario probabilities sum to 1.00."""
    return abs(get_probability_total(probabilities) - 1.0) <= 0.001


def collect_input_messages(
    probabilities: ScenarioProbabilities,
    payoff_matrix: PayoffMatrix,
) -> list[str]:
    """Return simple user-facing messages for incomplete or inconsistent inputs."""
    messages: list[str] = []

    if not probability_total_is_valid(probabilities):
        total = get_probability_total(probabilities)
        messages.append(
            f"Scenario probabilities currently sum to {total:.2f}. "
            "Adjust them until the total is 1.00."
        )

    for alternative, scenario_payoffs in payoff_matrix.items():
        for scenario, payoff in scenario_payoffs.items():
            if payoff < 0:
                messages.append(
                    f"{alternative} has a negative productivity estimate in {scenario}. "
                    "Use zero or a positive value."
                )

    return messages
