"""Local station weather database parser for AgroVision."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any
from xml.etree import ElementTree as ET


PROJECT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_STATION_DATA_PATH = PROJECT_DIR / "data" / "station_data.xls"
SPREADSHEET_NS = "urn:schemas-microsoft-com:office:spreadsheet"


@dataclass(frozen=True)
class StationWeatherSummary:
    """Aggregated local station observations used as model evidence."""

    source: str
    file_name: str
    row_count: int
    observed_days: int
    start_time: str
    end_time: str
    average_temperature_c: float
    max_temperature_c: float
    min_temperature_c: float
    total_precipitation_mm: float
    average_relative_humidity_pct: float
    average_solar_radiation_w_m2: float
    average_wind_speed_m_s: float
    max_wind_speed_m_s: float
    average_delta_t_c: float
    average_et0_mm: float | None
    et0_observation_count: int

    def to_model_input(self) -> dict[str, object]:
        """Return JSON-like values that can be stored in simulation evidence."""
        return asdict(self)


def load_station_weather_summary(
    path: str | Path = DEFAULT_STATION_DATA_PATH,
) -> StationWeatherSummary | None:
    """Load and aggregate the local station Excel XML export."""
    source_path = Path(path)
    if not source_path.exists():
        return None

    rows = _read_excel_xml_rows(source_path)
    if len(rows) < 3:
        return None

    records = [_station_record(row) for row in rows[2:]]
    records = [record for record in records if record is not None]
    if not records:
        return None

    observed_dates = {record["timestamp"].date() for record in records}
    et0_values = _values(records, "et0_mm")

    return StationWeatherSummary(
        source="Local station database",
        file_name=source_path.name,
        row_count=len(records),
        observed_days=len(observed_dates),
        start_time=min(record["timestamp"] for record in records).strftime(
            "%Y-%m-%d %H:%M"
        ),
        end_time=max(record["timestamp"] for record in records).strftime(
            "%Y-%m-%d %H:%M"
        ),
        average_temperature_c=round(mean(_values(records, "temperature_avg_c")), 1),
        max_temperature_c=round(max(_values(records, "temperature_max_c")), 1),
        min_temperature_c=round(min(_values(records, "temperature_min_c")), 1),
        total_precipitation_mm=round(sum(_values(records, "precipitation_mm")), 1),
        average_relative_humidity_pct=round(
            mean(_values(records, "relative_humidity_avg_pct")),
            1,
        ),
        average_solar_radiation_w_m2=round(
            mean(_values(records, "solar_radiation_w_m2")),
            1,
        ),
        average_wind_speed_m_s=round(mean(_values(records, "wind_speed_avg_m_s")), 1),
        max_wind_speed_m_s=round(max(_values(records, "wind_speed_max_m_s")), 1),
        average_delta_t_c=round(mean(_values(records, "delta_t_avg_c")), 1),
        average_et0_mm=round(mean(et0_values), 1) if et0_values else None,
        et0_observation_count=len(et0_values),
    )


def _read_excel_xml_rows(path: Path) -> list[list[str]]:
    namespace = {"ss": SPREADSHEET_NS}
    root = ET.parse(path).getroot()
    worksheet = root.find("ss:Worksheet", namespace)
    if worksheet is None:
        return []
    table = worksheet.find("ss:Table", namespace)
    if table is None:
        return []
    return [_row_values(row) for row in table.findall("ss:Row", namespace)]


def _row_values(row: ET.Element) -> list[str]:
    namespace = {"ss": SPREADSHEET_NS}
    values: list[str] = []
    cursor = 1

    for cell in row.findall("ss:Cell", namespace):
        index = cell.attrib.get(f"{{{SPREADSHEET_NS}}}Index")
        if index:
            while cursor < int(index):
                values.append("")
                cursor += 1

        data = cell.find("ss:Data", namespace)
        text = "" if data is None or data.text is None else data.text.strip()
        merge_across = int(cell.attrib.get(f"{{{SPREADSHEET_NS}}}MergeAcross", "0"))

        values.append(text)
        cursor += 1
        for _ in range(merge_across):
            values.append(text)
            cursor += 1

    return values


def _station_record(row: list[str]) -> dict[str, Any] | None:
    padded = row + [""] * max(0, 25 - len(row))
    timestamp = _parse_timestamp(padded[0])
    if timestamp is None:
        return None

    return {
        "timestamp": timestamp,
        "temperature_avg_c": _number(padded[1]),
        "temperature_max_c": _number(padded[2]),
        "temperature_min_c": _number(padded[3]),
        "solar_radiation_w_m2": _number(padded[6]),
        "relative_humidity_avg_pct": _number(padded[9]),
        "precipitation_mm": _number(padded[12]),
        "wind_speed_avg_m_s": _number(padded[13]),
        "wind_speed_max_m_s": _number(padded[15]),
        "delta_t_avg_c": _number(padded[20]),
        "et0_mm": _number(padded[24]),
    }


def _parse_timestamp(value: str) -> datetime | None:
    for date_format in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue
    return None


def _number(value: str) -> float | None:
    normalized = str(value).strip().replace(",", ".")
    if normalized == "":
        return None
    try:
        return float(normalized)
    except ValueError:
        return None


def _values(records: list[dict[str, Any]], key: str) -> list[float]:
    values = []
    for record in records:
        value = record.get(key)
        if value is not None:
            values.append(float(value))
    return values
