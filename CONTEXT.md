# Sprint 03 Context - Scenario and Decision Simulator

## Source of Truth

The current scope and decision logic are defined in:

`SCOPE_AND_DECISION_LOGIC.md`

That document supersedes earlier simulator assumptions. The platform should now
be framed around seed density strategies as the main alternatives.

## Current Product Scope

AgroVision's Sprint 03 simulator supports agricultural decision-making by
helping users identify the best seed density strategy under environmental and
operational uncertainty.

The simulator should connect to prior sprint artifacts:

- Problem Framing;
- Payoff Matrix;
- Decision Tree;
- Data Characterization;
- Wireframe Prototype.

## Decision Alternatives

The simulator compares:

- `Conservative Strategy`;
- `Adaptive Strategy`;
- `Intensive Strategy`.

These represent seed density strategies rather than generic productivity/risk
labels.

## States of the World

The current states are:

- `C1 - Favorable`: stable rainfall and ideal conditions;
- `C2 - Moderate`: some instability but manageable production;
- `C3 - Unfavorable`: drought, irregular rainfall, or high operational risk.

Each state is associated with:

- a scenario probability;
- an expected productivity estimate;
- operational/agricultural risk interpretation.

## Decision Criteria

### Primary Criterion: Expected Value

Expected Value is the main recommendation criterion for Version 1.

The simulator calculates:

```text
EV = sum(probability_i * productivity_i)
```

The final recommendation follows the strategy with the highest Expected Value.

### Going Beyond Criterion: Minimax Regret

The simulator also displays Minimax Regret as a risk-aware comparison.

For each scenario, regret is calculated as:

```text
best productivity in scenario - strategy productivity in scenario
```

The Minimax strategy is the one with the lowest maximum regret. This should be
shown as a comparison, not as the primary final recommendation unless the team
explicitly changes the scope again.

## Configurable Inputs

The UI should include configurable inputs for:

- climate scenario probabilities;
- soil pH;
- seed density strategy context;
- expected productivity by strategy and scenario;
- risk level;
- field and operational context.

## Current Implementation

The prototype is implemented as a Streamlit app in this folder.

Important files:

- `app.py`: Streamlit entry point.
- `src/decision_engine.py`: Expected Value, Minimax Regret, and final
  recommendation logic.
- `src/input_validation.py`: validation helpers.
- `src/ui_components.py`: user interface and visual sections.
- `src/data/historical_indicators.py`: centralized local reference indicators.
- `tests/test_decision_engine_manual.py`: manual formula verification.

## Historical Insights Scope

`Historical Insights` means historical agricultural dataset context from prior
sprint analysis.

It does not mean:

- user search history;
- saved simulations;
- account-specific history;
- login-based records.

Because of this, Sprint 03 does not require a user database just to support the
Historical Insights page.

## Known Limitations

- The historical indicators are centralized local reference values, not runtime
  calculations from a live Bayer database.
- The prototype is designed for Sprint 03 validation, not production deployment.
- Public URL deployment still belongs to final testing/deployment work.
