"""Decision-analysis logic for the AgroVision simulator.

The functions in this module are intentionally UI-independent. Streamlit
components should collect inputs and display outputs, while this file owns the
decision criteria and the traceable calculations behind each recommendation.
"""

from __future__ import annotations

from dataclasses import dataclass


Alternative = str
Scenario = str
PayoffMatrix = dict[Alternative, dict[Scenario, float]]
ScenarioProbabilities = dict[Scenario, float]


DEFAULT_SCENARIOS: tuple[Scenario, ...] = (
    "C1 - Favorable",
    "C2 - Moderate",
    "C3 - Unfavorable",
)

DEFAULT_ALTERNATIVES: tuple[Alternative, ...] = (
    "Conservative Strategy",
    "Adaptive Strategy",
    "Intensive Strategy",
)

DEFAULT_PAYOFF_MATRIX: PayoffMatrix = {
    "Conservative Strategy": {
        "C1 - Favorable": 72.0,
        "C2 - Moderate": 68.0,
        "C3 - Unfavorable": 62.0,
    },
    "Adaptive Strategy": {
        "C1 - Favorable": 84.0,
        "C2 - Moderate": 74.0,
        "C3 - Unfavorable": 58.0,
    },
    "Intensive Strategy": {
        "C1 - Favorable": 96.0,
        "C2 - Moderate": 76.0,
        "C3 - Unfavorable": 45.0,
    },
}

DEFAULT_SCENARIO_PROBABILITIES: ScenarioProbabilities = {
    "C1 - Favorable": 0.20,
    "C2 - Moderate": 0.35,
    "C3 - Unfavorable": 0.45,
}


@dataclass(frozen=True)
class CriterionResult:
    """Result returned by one decision criterion."""

    criterion: str
    recommendation: Alternative
    scores: dict[Alternative, float]
    trace: dict[Alternative, str]


@dataclass(frozen=True)
class DecisionSummary:
    """Combined recommendation using the selected decision criteria."""

    final_recommendation: Alternative
    expected_value: CriterionResult
    minimax: CriterionResult
    explanation: str


def calculate_expected_values(
    payoff_matrix: PayoffMatrix,
    scenario_probabilities: ScenarioProbabilities,
) -> CriterionResult:
    """Calculate Expected Value for each alternative.

    Expected Value formula:
    EV = payoff_C1 * probability_C1
       + payoff_C2 * probability_C2
       + payoff_C3 * probability_C3
    """
    scores: dict[Alternative, float] = {}
    trace: dict[Alternative, str] = {}

    for alternative, scenario_payoffs in payoff_matrix.items():
        terms: list[str] = []
        expected_value = 0.0

        for scenario, payoff in scenario_payoffs.items():
            probability = scenario_probabilities[scenario]
            contribution = payoff * probability
            expected_value += contribution
            terms.append(
                f"{payoff:.2f} x {probability:.2f} = {contribution:.2f}"
            )

        scores[alternative] = round(expected_value, 2)
        trace[alternative] = " + ".join(terms) + f" => {expected_value:.2f}"

    return CriterionResult(
        criterion="Expected Value",
        recommendation=_select_highest_score(scores),
        scores=scores,
        trace=trace,
    )


def calculate_minimax(payoff_matrix: PayoffMatrix) -> CriterionResult:
    """Calculate Minimax regret for each alternative.

    For each climate scenario, regret is the difference between the best payoff
    available in that scenario and the payoff delivered by the strategy. Minimax
    selects the strategy with the lowest maximum regret.
    """
    scores: dict[Alternative, float] = {}
    trace: dict[Alternative, str] = {}
    scenario_best_payoffs = {
        scenario: max(payoffs[scenario] for payoffs in payoff_matrix.values())
        for scenario in next(iter(payoff_matrix.values()))
    }

    for alternative, scenario_payoffs in payoff_matrix.items():
        regret_values = {
            scenario: scenario_best_payoffs[scenario] - payoff
            for scenario, payoff in scenario_payoffs.items()
        }
        maximum_regret = max(regret_values.values())
        scores[alternative] = round(maximum_regret, 2)
        regret_text = ", ".join(
            f"{scenario}: {regret:.2f}"
            for scenario, regret in regret_values.items()
        )
        trace[alternative] = f"max({regret_text}) => {maximum_regret:.2f}"

    return CriterionResult(
        criterion="Minimax",
        recommendation=_select_lowest_score(scores),
        scores=scores,
        trace=trace,
    )


def build_decision_summary(
    payoff_matrix: PayoffMatrix,
    scenario_probabilities: ScenarioProbabilities,
) -> DecisionSummary:
    """Build a combined recommendation from Expected Value and Minimax."""
    expected_value = calculate_expected_values(payoff_matrix, scenario_probabilities)
    minimax = calculate_minimax(payoff_matrix)

    final_recommendation = expected_value.recommendation
    if expected_value.recommendation == minimax.recommendation:
        final_recommendation = expected_value.recommendation
        explanation = (
            f"{final_recommendation} is recommended because both Expected Value "
            "and Minimax select the same seed density strategy."
        )
    else:
        explanation = (
            "The criteria show different decision perspectives. Expected Value "
            f"selects {expected_value.recommendation}, while Minimax selects "
            f"{minimax.recommendation}. Version 1 follows the project scope by "
            "using Expected Value as the primary recommendation criterion, while "
            "Minimax is displayed as a risk-aware comparison."
        )

    return DecisionSummary(
        final_recommendation=final_recommendation,
        expected_value=expected_value,
        minimax=minimax,
        explanation=explanation,
    )


def _select_highest_score(scores: dict[Alternative, float]) -> Alternative:
    """Return the alternative with the highest score.

    Ties are resolved by preserving insertion order from the input matrix. This
    keeps behavior deterministic and easy to explain in the interface.
    """
    return max(scores, key=scores.get)


def _select_lowest_score(scores: dict[Alternative, float]) -> Alternative:
    """Return the alternative with the lowest score.

    Ties are resolved by preserving insertion order from the input matrix.
    """
    return min(scores, key=scores.get)
