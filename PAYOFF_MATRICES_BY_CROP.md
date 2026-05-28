# Payoff Matrices by Crop

This document makes explicit how the simulator treats payoff matrices for the
two supported crops: soybean and corn.

## Source and Method

The soybean payoff matrix is copied from the Sprint 02 payoff matrix artifact
(`Sprint 02/Payoff Matrix/Bayer_PayoffMatrix_Spreadsheet.xlsx`). That artifact
states that payoff values are expressed as soybean sacks per hectare, using
60 kg sacks.

The corn payoff matrix is a crop-specific derived matrix. It preserves the
same strategic relationships from the Sprint 02 soybean matrix, but rescales
each climate-scenario column using corn productivity anchors calculated from
Bayer's internal historical database:

| Crop | C1 favorable anchor | C2 moderate anchor | C3 unfavorable anchor |
| --- | ---: | ---: | ---: |
| Soybean reference in Sprint 02 matrix | 88.0 | 75.0 | 68.0 |
| Corn historical anchor from Bayer internal data | 105.9 | 96.8 | 87.5 |

The corn anchors come from merged Bayer planting and harvest records:

- `C1 - Favorable`: corn 75th percentile productivity.
- `C2 - Moderate`: corn median productivity.
- `C3 - Unfavorable`: corn 25th percentile productivity.

Formula used for each corn payoff:

```text
corn_payoff = soybean_payoff / soybean_scenario_anchor * corn_scenario_anchor
```

This keeps the decision logic consistent across crops while avoiding the
mistake of applying soybean productivity values directly to corn.

## Soybean Payoff Matrix

Copied from the Sprint 02 payoff matrix artifact.

| Alternative | C1 - Favorable (sacks/ha) | C2 - Moderate (sacks/ha) | C3 - Unfavorable (sacks/ha) | Max | Min | Avg | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| A1: Maximize Productivity | 88.0 | 58.0 | 22.0 | 88.0 | 22.0 | 56.0 | Optimal seed density around 268k seeds/ha, pH 5.8-6.1, correct planting window |
| A2: Minimize Risk | 72.0 | 75.0 | 68.0 | 75.0 | 68.0 | 71.7 | pH warnings, drainage flags, off-season detection from dataset signals |
| A3: Balanced Approach | 82.0 | 70.0 | 52.0 | 82.0 | 52.0 | 68.0 | Multi-variable weighted model: soil, seed, temporal, and geographic context |

## Corn Payoff Matrix

Derived from Bayer internal historical corn productivity records, while
preserving the strategic ratios from the Sprint 02 soybean matrix.

| Alternative | C1 - Favorable (sacks/ha) | C2 - Moderate (sacks/ha) | C3 - Unfavorable (sacks/ha) | Max | Min | Avg | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| A1: Maximize Productivity | 105.9 | 74.9 | 28.3 | 105.9 | 28.3 | 69.7 | High productivity potential under favorable corn conditions, but large downside under unfavorable conditions |
| A2: Minimize Risk | 86.6 | 96.8 | 87.5 | 96.8 | 86.6 | 90.3 | Most stable corn alternative; aligned with the Bayer historical median and unfavorable anchor |
| A3: Balanced Approach | 98.7 | 90.3 | 66.9 | 98.7 | 66.9 | 85.3 | Intermediate corn alternative; trades some upside for better downside protection than A1 |

## Interpretation

The simulator can therefore be explained as having:

- a soybean payoff matrix copied from the Sprint 02 payoff matrix artifact;
- a corn payoff matrix derived from Bayer's internal corn data;
- the same decision alternatives and climate states for both crops;
- crop-specific productivity magnitudes, so soybean and corn are not mixed into
  one generic payoff table.

For the current app implementation, the decision engine still uses one editable
matrix object at runtime. This document provides the crop-specific payoff
reference that should be used when explaining or extending the simulator.
