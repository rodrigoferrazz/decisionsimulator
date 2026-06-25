# AgroVision Decision Simulator — Simulator integrated with BI (Sprint 05)

This folder is the self-contained Sprint 05 deliverable of AgroVision's decision
support simulator. It integrates the decision engine (Decision Tree, Payoff
Matrix, and Monte Carlo methods) with the BI/analytics layer. Everything needed
to run it is contained in this folder.

The current scope follows `SCOPE_AND_DECISION_LOGIC.md`: the simulator supports
agricultural decision-making by comparing seed density strategies under climate,
soil, productivity, and risk uncertainty.

Crop-specific payoff references are documented in
`PAYOFF_MATRICES_BY_CROP.md`, including the soybean matrix and the corn matrix
derived from Bayer internal historical records.

## Decision Scope

The simulator compares three seed density strategies:

- `Conservative Strategy`: lower operational risk and more stable productivity.
- `Adaptive Strategy`: balanced productivity and stability.
- `Intensive Strategy`: higher productivity potential with greater risk exposure.

The states of the world are:

- `C1 - Favorable`: stable rainfall and ideal conditions.
- `C2 - Moderate`: some instability but manageable production.
- `C3 - Unfavorable`: drought, irregular rainfall, or high operational risk.

## Decision Criteria

The simulator uses two decision perspectives:

- **Expected Value (primary criterion)**: calculates the weighted average
  productivity for each strategy using forecast-derived scenario probabilities.
  The final recommendation follows the highest Expected Value.
- **Minimax Regret (going beyond)**: compares each strategy's maximum regret
  against the best productivity available in each climate scenario. This is
  displayed as a risk-aware comparison, where lower values are better.

## Configurable Inputs

The interface includes inputs aligned with the new scope:

- region/state;
- crop type;
- soil texture;
- area in hectares;
- planting objective;
- operation type;
- operation speed.

The simulator uses Open-Meteo forecast data for the selected region/state. The
forecast is converted into `C1 - Favorable`, `C2 - Moderate`, and
`C3 - Unfavorable` probabilities, then passed into the existing Expected Value
and Minimax decision logic.

## Folder Structure

```text
Simulator integrated with BI/
├── app.py
├── requirements.txt
├── render.yaml
├── README.md
├── CONTEXT.md
├── SCOPE_AND_DECISION_LOGIC.md
├── PAYOFF_MATRICES_BY_CROP.md
├── DATA_PIPELINE.md
├── data/
│   ├── harvest_summary_brazil.csv
│   ├── planting_summary_brazil.csv
│   └── station_data.xls
├── src/
│   ├── __init__.py
│   ├── audit_trail.py
│   ├── decision_engine.py
│   ├── decision_tree_model.py
│   ├── input_validation.py
│   ├── simulation_model.py
│   ├── ui_components.py
│   ├── weather_client.py
│   └── data/
│       ├── __init__.py
│       ├── dataset_options.py
│       ├── historical_indicators.py
│       └── station_weather.py
└── tests/
    ├── test_decision_engine_manual.py
    ├── test_historical_indicators_manual.py
    ├── test_station_weather_manual.py
    ├── test_weather_client_manual.py
    └── test_weather_simulation_manual.py
```

## Responsibilities

- `app.py`: Streamlit entry point.
- `src/decision_engine.py`: Expected Value, Minimax Regret, and recommendation
  logic.
- `src/input_validation.py`: validation rules for scenario probabilities and
  productivity estimates.
- `src/ui_components.py`: Streamlit screens, explanations, input controls,
  visualizations, and recommendation output.
- `src/data/historical_indicators.py`: local reference indicators derived from
  the CSV files in `data/`.
- `tests/test_decision_engine_manual.py`: manual verification checks for the
  decision formulas.

## Run Locally

From inside this folder (`Simulator integrated with BI`):

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

## Deploy

The app is ready to deploy from GitHub as a Streamlit application.

### Streamlit Community Cloud

- Repository: `rodrigoferrazz/deploy-m6`
- Branch: `main`
- Main file path: `app.py`
- Python version: `3.12`

### Render

This repository includes `render.yaml` for Render Blueprint deploys. Render will
install `requirements.txt`, run Streamlit on the platform-provided `$PORT`, and
use `/_stcore/health` as the health check endpoint.

## Manual Verification

From inside this folder, run any of the manual test scripts:

```bash
python3 -m tests.test_decision_engine_manual
python3 -m tests.test_weather_simulation_manual
```

## Data Pipeline

See [`DATA_PIPELINE.md`](DATA_PIPELINE.md) for a full description of where
inputs come from, how each simulation method processes them, and how outputs
are rendered in the BI layer.

## Notes

- The deployment folder must include `data/planting_summary_brazil.csv` and
  `data/harvest_summary_brazil.csv`.
- Historical crop reference logic is centralized in `src/data/` so it is not
  scattered through the interface.
- The Monte Carlo engine uses seed = 42 for reproducibility across reruns.
