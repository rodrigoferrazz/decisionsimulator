# Data Pipeline — AgroVision Simulator

This document describes the full data pipeline: where inputs come from, how they are processed by each simulation method, and how outputs are rendered in the BI layer.

---

## Pipeline Overview

```
User inputs (Streamlit form)
        │
        ├── Farm location (lat/lng)
        │        └─→ Open-Meteo API (live weather forecast)
        │                  └─→ Climate classification
        │                              └─→ Scenario probabilities
        │
        └── Seed type, soil pH, planting window, seed potential
                 └─→ Bayer internal datasets (CSV)
                           └─→ Historical crop model
                                     └─→ Base productivity + branch deltas
                                                   │
                              ┌───────────────────┤
                              │                   │
                     Decision Tree         Payoff Matrix / Monte Carlo
                              │                   │
                    Expected productivity    Strategy recommendation
                              │                   │
                              └───────────────────┘
                                         │
                                  Loading screen
                              (step-by-step progress)
                                         │
                              Recommendation Summary
                              ├── BI analytics panel
                              ├── What-if analysis
                              └── Method-specific charts
                                         │
                                  Audit trail log
                              (Supabase — async, silent)
```

---

## 1. Inputs

### 1.1 User-provided (Streamlit form — `Start Simulation` page)

| Field | Type | Used by |
|---|---|---|
| Farm latitude / longitude | float | Open-Meteo API request |
| Seed type | `soybean` or `corn` | Historical crop model lookup |
| Soil pH | float | Branch delta selection |
| Planting window | Early / Ideal / Late | Branch delta selection |
| Seed potential | High / Intermediate / Limited | Branch delta selection |
| Monte Carlo triangular params | min / mode / max per branch | Monte Carlo only |

### 1.2 External — Open-Meteo API (`src/weather_client.py`)

Called once per simulation run. Endpoint: `https://api.open-meteo.com/v1/forecast`

Variables fetched (7-day daily forecast):

| Variable | Field name |
|---|---|
| Max temperature | `temperature_2m_max` |
| Min temperature | `temperature_2m_min` |
| Precipitation sum | `precipitation_sum` |
| Precipitation probability | `precipitation_probability_max` |
| Evapotranspiration | `et0_fao_evapotranspiration` |
| Weather code | `weather_code` |

No API key required. If the request fails, the pipeline falls back to `DEFAULT_SCENARIO_PROBABILITIES` (Favorable 20%, Moderate 35%, Unfavorable 45%).

### 1.3 Internal — Bayer datasets (`data/`)

| File | Rows | Content |
|---|---|---|
| `planting_summary_brazil.csv` | ~thousands | field_uuid, crop_name, planting_date, soil_ph_min, soil_ph_max, soil_texture |
| `harvest_summary_brazil.csv` | ~thousands | field_uuid, crop_name, average_yield |

Loaded once at startup, cached in memory via `@lru_cache`. Merged on `field_uuid + crop_name` to produce one analytical frame per crop.

---

## 2. Processing

### 2.1 Weather → scenario probabilities (`src/simulation_model.py`)

The 7-day forecast is summarised into three aggregate signals:

- **Precipitation score**: mean daily precipitation sum
- **Temperature stress**: days where max temp > 35°C or min temp < 10°C
- **Evapotranspiration ratio**: total ET0 vs. precipitation (water deficit proxy)

These signals are combined into a **climate classification**:

| Classification | P(Favorable) | P(Moderate) | P(Unfavorable) |
|---|---|---|---|
| Favorable | 0.55 | 0.30 | 0.15 |
| Moderate | 0.25 | 0.50 | 0.25 |
| Unfavorable | 0.10 | 0.30 | 0.60 |

The classification also pulls an optional correction factor from the internal station dataset (`data/station_data.xls`) when the farm location matches a known station.

### 2.2 Historical crop model → base productivity (`src/data/historical_indicators.py`)

For the selected seed type, the merged Bayer frame provides:

| Value | Calculation |
|---|---|
| `median_yield` | `DataFrame["average_yield"].median()` |
| `favorable_yield` | `quantile(0.75)` |
| `unfavorable_yield` | `quantile(0.25)` |
| `planting_window_factors` | Median yield by planting-month tertile vs. overall median |
| `climate_factors` | Ratio of P75/P50/P25 to median |

All yields are stored in kg and converted to 60 kg bags/ha before display.

**Base productivity** is fixed at **60.0 sc/ha** (`DECISION_TREE_BASE_PRODUCTIVITY_BAGS_HA`), with the historical crop model used to derive branch deltas and payoff matrix scaling.

### 2.3 Decision Tree method (`build_decision_tree_simulation`)

Applies deterministic branch deltas on top of the base productivity:

```
productivity = 60.0
             + planting_window_delta  (Early: +2, Normal: 0, Late: -4)
             + climate_delta          (Wet: +4, Normal: +2, Dry: -5)
             + soil_ph_delta          (Adequate: +3, Borderline: 0, Critical: -4)
             + seed_potential_delta   (High: +3, Intermediate: +1, Limited: -3)
```

Each branch delta is selected from the actual user input. No strategy comparison — outputs a single productivity estimate.

### 2.4 Payoff Matrix method (`build_payoff_matrix_simulation`)

1. Runs the Decision Tree first to get base productivity.
2. Builds a 3×3 payoff matrix (strategies × scenarios) by scaling the base:

| Strategy | Favorable | Moderate | Unfavorable |
|---|---|---|---|
| Conservative | base × 1.05 − 1 | base × 1.01 − 0.5 | base × 0.97 + 0.5 |
| Adaptive | base × 1.12 | base × 1.05 | base × 0.92 |
| Intensive | base × 1.18 + 2 | base × 1.08 + 1 | base × 0.82 − 2 |

3. Applies scenario probabilities from step 2.1 to calculate **Expected Value** per strategy.
4. Applies **Minimax Regret**: for each scenario, regret = best available payoff − strategy payoff. Selects strategy with lowest maximum regret.
5. If both criteria agree → that strategy is recommended. If they diverge → Expected Value takes priority.

### 2.5 Monte Carlo method (`build_monte_carlo_simulation`)

Replaces deterministic branch deltas with triangular probability distributions:

| Branch | Min (a) | Mode (c) | Max (b) |
|---|---|---|---|
| planting_window | −4.0 | 0.0 | +2.0 |
| climate | −5.0 | +2.0 | +4.0 |
| soil_ph | −4.0 | 0.0 | +3.0 |
| seed_potential | −3.0 | +1.0 | +3.0 |

The user can override these via the Monte Carlo parameter form before running.

**10,000 trials** are sampled (seed = 42 for reproducibility). Each trial draws one value per branch from its triangular distribution and sums them to base productivity.

Stored statistics: mean, std, P5, P10, P25, P50, P75, P90, P95, plus a sensitivity ranking (correlation of each branch with final productivity).

---

## 3. Output rendering (`src/ui_components.py`)

All three methods route to the `Recommendation Summary` page after execution.

### 3.1 Loading screen (`_render_loading_page`)

When the user clicks any simulation button, the app redirects immediately to a full-screen loading page that:
- Hides the sidebar and all other UI elements
- Shows a CSS spinner and the method name
- Runs the simulation synchronously in the background
- Redirects to Recommendation Summary on completion
- Falls back to default weather data silently if Open-Meteo is unreachable

### 3.2 Common output — shown for all methods

**Recommendation card**: strategy name, forecast scenario, Expected Value, maximum regret.

**Decision analytics panel** (BI layer — `_render_decision_analytics_panel`):
- *Decision margin*: EV gap between recommended and second-best strategy.
- *Payoff spread*: range between best and worst outcome across all strategies/scenarios.
- *Criteria agreement*: whether Expected Value and Minimax Regret selected the same strategy.
- *Risk–return scatter chart*: each strategy plotted by EV (Y) vs. max regret (X).
- *Probability sensitivity chart*: EV per strategy as P(Favorable) varies from 0% to 100%, with current probability marked.

**What-if analysis panel** (`_render_whatif_panel`):
- A selectbox lets the user override the soil pH category: Adequate (+3.0 sc/ha), Borderline (0.0), or Critical (−4.0 sc/ha).
- The panel recomputes the Decision Tree base productivity with the new soil pH delta and rebuilds the payoff matrix using the same additive formulas as `build_payoff_matrix_simulation`.
- A badge indicates whether the recommendation holds or changes under the new soil condition.
- A comparison table shows Original EV vs. What-if EV and Δ for each strategy.

### 3.3 Method-specific output

| Method | Additional output |
|---|---|
| Decision Tree | Calculation flow (base + each branch delta with label and value) |
| Payoff Matrix | Expected Value card (formula trace), Minimax Regret card, full payoff matrix table |
| Monte Carlo | Metric cards (mean, std, P5/P95, median, trials), risk threshold calculator, histogram, tornado/sensitivity chart |

### 3.4 Audit trail (`src/audit_trail.py`)

After every successful simulation, a record is written to the `simulation_logs` table in Supabase. This happens silently — if the write fails (no credentials, network error), the app continues normally.

Fields logged per run:

| Field | Source |
|---|---|
| `simulation_method` | `simulation.simulation_method` |
| `seed_type` | `field_context["seed_type"]` |
| `soil_ph` | `field_context["soil_ph"]` |
| `planting_window` | `field_context["planting_window"]` |
| `farm_location` | `field_context["weather_location"]` |
| `climatic_condition` | `simulation.climatic_condition` |
| `recommended_strategy` | `decision_summary.final_recommendation` |
| `expected_value_bags_ha` | `simulation.expected_productivity_bags_ha` |
| `decision_margin` | EV of #1 − EV of #2 |
| `criteria_agree` | whether EV and Minimax Regret agree |
| `created_at` | auto-generated by Supabase (`now()`) |

Credentials are read from environment variables `SUPABASE_URL` and `SUPABASE_KEY`. For local development, these are loaded from a `.env` file via `python-dotenv`. For cloud deployment, set them as environment variables on the hosting platform.

### 3.5 Export

A **PDF export** is available on Decision Tree and Payoff Matrix results. The `Save Simulation` button stores the run in the current session for cross-simulation comparison on the `Compare Simulations` page.

---

## 4. Module responsibilities

| Module | Responsibility |
|---|---|
| `app.py` | Streamlit entry point; loads `.env` via `python-dotenv`; delegates to `render_app_shell()` |
| `src/weather_client.py` | Open-Meteo API call; location → lat/lng mapping |
| `src/simulation_model.py` | All three simulation engines; climate classification; triangular param derivation |
| `src/decision_engine.py` | Expected Value, Minimax Regret, DecisionSummary |
| `src/audit_trail.py` | Supabase insert after each simulation run; silent on failure |
| `src/data/historical_indicators.py` | Bayer CSV loading, crop model derivation, base productivity reference values |
| `src/data/station_weather.py` | Station observation lookup from `data/station_data.xls` |
| `src/input_validation.py` | Numeric input validation rules |
| `src/ui_components.py` | All Streamlit pages, loading screen, BI panel, what-if panel, recommendation rendering |

---

## 5. Environment variables

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | For audit trail | Supabase project URL |
| `SUPABASE_KEY` | For audit trail | Supabase anon/public key |

Copy `.env.example` to `.env` and fill in the values for local development. On cloud platforms (Render, Streamlit Community Cloud), set these in the platform's environment variable panel. The app runs without them — audit logging is simply skipped.
