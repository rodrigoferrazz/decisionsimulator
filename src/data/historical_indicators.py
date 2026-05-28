"""Bayer dataset-backed historical indicators for the simulator."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[2]
BAYER_DATA_DIR = PROJECT_DIR / "data"
PLANTING_DATASET_PATH = BAYER_DATA_DIR / "planting_summary_brazil.csv"
HARVEST_DATASET_PATH = BAYER_DATA_DIR / "harvest_summary_brazil.csv"
SUPPORTED_CROPS = ("soybeans", "corn")
BAG_WEIGHT_KG = 60.0


HOME_CONTEXT = {
    "season": "Season 2026 - Bayer internal database",
    "subtitle": (
        "Estimate soybean and corn productivity from farm location, soil pH, "
        "planting window, Open-Meteo climatic conditions, and Bayer internal "
        "planting and harvest records."
    ),
}


QUICK_ACCESS_CARDS = (
    {
        "title": "Start Simulation",
        "body": "Configure your field conditions and run the simulation.",
        "target": "Start Simulation",
        "is_primary": True,
    },
    {
        "title": "Historical Insights",
        "body": "Review metrics calculated from Bayer internal planting and harvest data.",
        "target": "Historical Insights",
        "is_primary": False,
    },
)


@dataclass(frozen=True)
class CropHistoricalModel:
    """Dataset-derived model values for one supported crop."""

    crop_name: str
    record_count: int
    median_yield: float
    favorable_yield: float
    unfavorable_yield: float
    soil_ph_min: float
    soil_ph_max: float
    planting_window_factors: dict[str, float]
    climate_factors: dict[str, float]


@dataclass(frozen=True)
class BayerHistoricalMetrics:
    """Historical insights calculated from Bayer source datasets."""

    planting_rows: int
    harvest_rows: int
    merged_rows: int
    most_analyzed_crop: str
    most_analyzed_crop_rows: int
    dominant_planting_month: int
    dominant_planting_month_rows: int
    common_soil_ph_range: tuple[float, float]
    common_soil_texture: str
    crop_models: dict[str, CropHistoricalModel]


def get_data_source_note(metrics: BayerHistoricalMetrics | None = None) -> str:
    """Return a source note tied to the loaded Bayer datasets."""
    loaded = metrics or load_bayer_historical_metrics()
    return (
        "Metrics are calculated from Bayer's internal historical database "
        "(local app data extracts): "
        f"{PLANTING_DATASET_PATH.name} ({loaded.planting_rows:,} planting rows) "
        f"and {HARVEST_DATASET_PATH.name} ({loaded.harvest_rows:,} harvest rows), "
        f"merged by field and crop into {loaded.merged_rows:,} analytical rows."
    )


def get_at_a_glance(metrics: BayerHistoricalMetrics | None = None) -> tuple[dict[str, str | None], ...]:
    """Return home-page indicators calculated from Bayer datasets."""
    loaded = metrics or load_bayer_historical_metrics()
    soybean = loaded.crop_models["soybean"]
    corn = loaded.crop_models["corn"]
    return (
        {
            "label": "Soybean baseline",
            "value": _format_bags_per_hectare(soybean.median_yield),
            "unit": "bags/ha",
            "subtext": "Median productivity from Bayer internal harvest records",
        },
        {
            "label": "Soybean favorable",
            "value": _format_bags_per_hectare(soybean.favorable_yield),
            "unit": "bags/ha",
            "subtext": "75th percentile from Bayer internal harvest records",
        },
        {
            "label": "Corn baseline",
            "value": _format_bags_per_hectare(corn.median_yield),
            "unit": "bags/ha",
            "subtext": "Median productivity from Bayer internal harvest records",
        },
        {
            "label": "Corn favorable",
            "value": _format_bags_per_hectare(corn.favorable_yield),
            "unit": "bags/ha",
            "subtext": "75th percentile from Bayer internal harvest records",
        },
    )


def get_historical_insights(metrics: BayerHistoricalMetrics | None = None) -> tuple[dict[str, str], ...]:
    """Return Historical Insights cards calculated from Bayer datasets."""
    loaded = metrics or load_bayer_historical_metrics()
    soybean = loaded.crop_models["soybean"]
    corn = loaded.crop_models["corn"]
    return (
        {
            "title": "Corn productivity baseline",
            "value": f"{_format_bags_per_hectare(corn.median_yield)} bags/ha",
            "description": (
                "Median corn field productivity calculated from Bayer internal "
                "harvest records and converted to 60 kg bags per hectare."
            ),
        },
        {
            "title": "Corn favorable productivity",
            "value": f"{_format_bags_per_hectare(corn.favorable_yield)} bags/ha",
            "description": (
                "75th percentile corn productivity from Bayer internal harvest "
                "records, used as the favorable reference for yield potential."
            ),
        },
        {
            "title": "Soybean productivity baseline",
            "value": f"{_format_bags_per_hectare(soybean.median_yield)} bags/ha",
            "description": (
                "Median soybean field productivity calculated from Bayer internal "
                "harvest records and converted to 60 kg bags per hectare."
            ),
        },
        {
            "title": "Soybean favorable productivity",
            "value": f"{_format_bags_per_hectare(soybean.favorable_yield)} bags/ha",
            "description": (
                "75th percentile soybean productivity from Bayer internal harvest "
                "records, used as the favorable reference for yield potential."
            ),
        },
    )


def get_historical_insights_explanation(
    metrics: BayerHistoricalMetrics | None = None,
) -> str:
    """Return explanatory text grounded in the source datasets."""
    loaded = metrics or load_bayer_historical_metrics()
    return (
        "The simulator uses Bayer's internal planting database for crop frequency, "
        "planting timing, seed population, soil texture, and pH ranges, then merges "
        "those records with Bayer internal harvest data on field and crop to "
        "calculate field productivity in bags per hectare. The current analytical "
        "frame contains "
        f"{loaded.merged_rows:,} merged rows for soybean and corn."
    )


def get_crop_model_inputs(seed_type: str) -> CropHistoricalModel:
    """Return dataset-derived model inputs for the selected seed type."""
    crop_key = _normalize_seed_type(seed_type)
    return load_bayer_historical_metrics().crop_models[crop_key]


def yield_to_bags_per_hectare(average_yield: float) -> float:
    """Convert Bayer average_yield into 60 kg bags per hectare."""
    return average_yield / BAG_WEIGHT_KG


@lru_cache(maxsize=1)
def load_bayer_historical_metrics(
    planting_path: str | Path = PLANTING_DATASET_PATH,
    harvest_path: str | Path = HARVEST_DATASET_PATH,
) -> BayerHistoricalMetrics:
    """Load Bayer datasets and calculate historical simulator metrics."""
    planting = _load_planting_dataset(Path(planting_path))
    harvest = _load_harvest_dataset(Path(harvest_path))
    merged = _build_analytical_frame(planting, harvest)

    crop_counts = planting["crop_name"].value_counts()
    most_analyzed_crop = str(crop_counts.idxmax())
    planting_months = pd.to_datetime(
        planting["planting_date"],
        format="%d-%m-%Y",
        errors="coerce",
    ).dt.month
    month_counts = planting_months.dropna().astype(int).value_counts()
    ph_band_counts = (
        planting.dropna(subset=["soil_ph_min", "soil_ph_max"])
        .groupby(["soil_ph_min", "soil_ph_max"])
        .size()
        .sort_values(ascending=False)
    )

    return BayerHistoricalMetrics(
        planting_rows=len(planting),
        harvest_rows=len(harvest),
        merged_rows=len(merged),
        most_analyzed_crop=most_analyzed_crop,
        most_analyzed_crop_rows=int(crop_counts.iloc[0]),
        dominant_planting_month=int(month_counts.idxmax()),
        dominant_planting_month_rows=int(month_counts.iloc[0]),
        common_soil_ph_range=tuple(float(value) for value in ph_band_counts.index[0]),
        common_soil_texture=str(planting["soil_texture"].mode().iloc[0]),
        crop_models=_build_crop_models(merged),
    )


def _load_planting_dataset(path: Path) -> pd.DataFrame:
    return pd.read_csv(
        path,
        usecols=[
            "field_uuid",
            "crop_name",
            "planting_date",
            "soil_ph_min",
            "soil_ph_max",
            "soil_texture",
        ],
    )


def _load_harvest_dataset(path: Path) -> pd.DataFrame:
    return pd.read_csv(
        path,
        usecols=[
            "field_uuid",
            "crop_name",
            "average_yield",
        ],
    )


def _build_analytical_frame(
    planting: pd.DataFrame,
    harvest: pd.DataFrame,
) -> pd.DataFrame:
    planting = planting[planting["crop_name"].isin(SUPPORTED_CROPS)].copy()
    harvest = harvest[harvest["crop_name"].isin(SUPPORTED_CROPS)].copy()
    merged = planting.merge(
        harvest,
        on=["field_uuid", "crop_name"],
        how="inner",
    )
    merged["average_yield"] = pd.to_numeric(merged["average_yield"], errors="coerce")
    merged["planting_month"] = pd.to_datetime(
        merged["planting_date"],
        format="%d-%m-%Y",
        errors="coerce",
    ).dt.month
    return merged.dropna(subset=["average_yield", "planting_month"])


def _build_crop_models(merged: pd.DataFrame) -> dict[str, CropHistoricalModel]:
    models: dict[str, CropHistoricalModel] = {}
    for source_crop in SUPPORTED_CROPS:
        crop_frame = merged[merged["crop_name"] == source_crop]
        median_yield = float(crop_frame["average_yield"].median())
        favorable_yield = float(crop_frame["average_yield"].quantile(0.75))
        unfavorable_yield = float(crop_frame["average_yield"].quantile(0.25))
        crop_key = _normalize_seed_type(source_crop)
        models[crop_key] = CropHistoricalModel(
            crop_name=crop_key,
            record_count=len(crop_frame),
            median_yield=median_yield,
            favorable_yield=favorable_yield,
            unfavorable_yield=unfavorable_yield,
            soil_ph_min=float(crop_frame["soil_ph_min"].median()),
            soil_ph_max=float(crop_frame["soil_ph_max"].median()),
            planting_window_factors=_planting_window_factors(crop_frame, median_yield),
            climate_factors={
                "Favorable": _safe_ratio(favorable_yield, median_yield),
                "Moderate": _safe_ratio(median_yield, median_yield),
                "Unfavorable": _safe_ratio(unfavorable_yield, median_yield),
                "Limited data": _safe_ratio(median_yield, median_yield),
            },
        )
    return models


def _planting_window_factors(
    crop_frame: pd.DataFrame,
    baseline_yield: float,
) -> dict[str, float]:
    valid = crop_frame.dropna(subset=["planting_month", "average_yield"]).copy()
    valid["window"] = pd.qcut(
        valid["planting_month"],
        q=3,
        labels=["Early", "Ideal", "Late"],
        duplicates="drop",
    )
    medians = valid.groupby("window", observed=True)["average_yield"].median()
    return {
        window: _safe_ratio(float(medians.get(window, baseline_yield)), baseline_yield)
        for window in ("Early", "Ideal", "Late")
    }


def _normalize_seed_type(seed_type: str) -> str:
    normalized = seed_type.strip().lower()
    if normalized in {"soybean", "soybeans"}:
        return "soybean"
    if normalized in {"corn", "maize"}:
        return "corn"
    return "soybean"


def _crop_label(crop_name: str) -> str:
    if crop_name in {"soybean", "soybeans"}:
        return "Soybeans"
    if crop_name == "corn":
        return "Corn"
    return crop_name.title()


def _month_name(month: int) -> str:
    names = (
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    )
    return names[month - 1]


def _format_bags_per_hectare(average_yield: float) -> str:
    """Convert Bayer average_yield into 60 kg bags per hectare for display."""
    return f"{yield_to_bags_per_hectare(average_yield):,.1f}"


def _safe_ratio(value: float, baseline: float) -> float:
    if baseline == 0:
        return 1.0
    return round(value / baseline, 4)
