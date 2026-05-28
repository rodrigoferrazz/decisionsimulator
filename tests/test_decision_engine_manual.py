"""Manual verification checks for the Sprint 03 decision engine.

Run from this folder with:
python tests/test_decision_engine_manual.py
"""

from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from src.decision_engine import (  # noqa: E402
    DEFAULT_PAYOFF_MATRIX,
    DEFAULT_SCENARIO_PROBABILITIES,
    build_decision_summary,
    calculate_expected_values,
    calculate_minimax,
)


def test_expected_value_with_default_probabilities() -> None:
    result = calculate_expected_values(
        DEFAULT_PAYOFF_MATRIX,
        DEFAULT_SCENARIO_PROBABILITIES,
    )

    assert result.scores["Conservative Strategy"] == 66.10
    assert result.scores["Adaptive Strategy"] == 68.80
    assert result.scores["Intensive Strategy"] == 66.05
    assert result.recommendation == "Adaptive Strategy"


def test_minimax_with_default_payoff_matrix() -> None:
    result = calculate_minimax(DEFAULT_PAYOFF_MATRIX)

    assert result.scores["Conservative Strategy"] == 24.0
    assert result.scores["Adaptive Strategy"] == 12.0
    assert result.scores["Intensive Strategy"] == 17.0
    assert result.recommendation == "Adaptive Strategy"


def test_decision_summary_uses_expected_value_as_primary_criterion() -> None:
    summary = build_decision_summary(
        DEFAULT_PAYOFF_MATRIX,
        DEFAULT_SCENARIO_PROBABILITIES,
    )

    assert summary.final_recommendation == "Adaptive Strategy"
    assert summary.expected_value.recommendation == "Adaptive Strategy"
    assert summary.minimax.recommendation == "Adaptive Strategy"


if __name__ == "__main__":
    test_expected_value_with_default_probabilities()
    test_minimax_with_default_payoff_matrix()
    test_decision_summary_uses_expected_value_as_primary_criterion()
    print("Manual decision-engine checks passed.")
