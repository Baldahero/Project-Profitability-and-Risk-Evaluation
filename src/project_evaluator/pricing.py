from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .models import AggregatedPricingEstimate, PricingEstimate, PricingInput

COMPANY_GLASS_MARGIN_RATE = 0.34
CUSTOMER_GLASS_MARGIN_RATE = 0.43
FABRICATION_TIME_OVERRIDES = {
    "Fixed window": 4.0,
}


def load_pricing_matrix(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = []
        for row in csv.DictReader(file):
            rows.append(
                {
                    "item": row["item"],
                    "element_type": row["element_type"],
                    "width_m": _to_float(row["width_m"]),
                    "height_m": _to_float(row["height_m"]),
                    "area_m2": _to_float(row["area_m2"]),
                    "glass_supply_model": row["glass_supply_model"],
                    "wind_load": row["wind_load"],
                    "thermal_performance": row["thermal_performance"],
                    "price_material_gbp": _to_float(row["price_material_gbp"]),
                    "price_glass_unit_gbp": _to_float(row["price_glass_unit_gbp"]),
                    "labour_work_gbp": _to_float(row["labour_work_gbp"]),
                    "coating_type": row["coating_type"],
                    "coating_total_gbp": _to_float(row["coating_total_gbp"]),
                    "margin_gbp": _to_float(row["margin_gbp"]),
                    "final_price_gbp": _to_float(row["final_price_gbp"]),
                    "fabrication_time_h": _fabrication_time(row),
                }
            )
        return rows


def get_pricing_options(rows: list[dict[str, Any]], field: str) -> list[str]:
    values = []
    for row in rows:
        value = row[field]
        if value not in values:
            values.append(value)
    return values


def estimate_price(pricing_input: PricingInput, rows: list[dict[str, Any]]) -> PricingEstimate:
    source_row = _find_source_row(pricing_input, rows)

    source_width = source_row["width_m"]
    source_area = source_row["area_m2"]

    material_rate_per_width = _safe_divide(source_row["price_material_gbp"], source_width)
    glass_rate_per_width = _safe_divide(source_row["price_glass_unit_gbp"], source_width)
    labour_rate_per_width = _safe_divide(source_row["labour_work_gbp"], source_width)
    coating_rate_per_m2 = _safe_divide(source_row["coating_total_gbp"], source_area)

    area_m2 = pricing_input.width_m * pricing_input.height_m
    material_gbp = material_rate_per_width * pricing_input.width_m
    glass_gbp = glass_rate_per_width * pricing_input.width_m
    labour_gbp = labour_rate_per_width * pricing_input.width_m
    coating_gbp = coating_rate_per_m2 * area_m2

    margin_rate, margin_base = _margin_rule(pricing_input, material_gbp, glass_gbp, coating_gbp)
    margin_gbp = margin_base * margin_rate
    final_price_gbp = material_gbp + glass_gbp + labour_gbp + coating_gbp + margin_gbp

    fabrication_time_hours_per_unit = _fabrication_time(source_row)

    quantity = pricing_input.quantity
    total_material_gbp = material_gbp * quantity
    total_glass_gbp = glass_gbp * quantity
    total_labour_gbp = labour_gbp * quantity
    total_coating_gbp = coating_gbp * quantity
    total_margin_gbp = margin_gbp * quantity
    total_final_price_gbp = final_price_gbp * quantity
    total_fabrication_time_hours = fabrication_time_hours_per_unit * quantity
    total_cost_before_margin_gbp = (
        total_material_gbp + total_glass_gbp + total_labour_gbp + total_coating_gbp
    )

    return PricingEstimate(
        source_item=source_row["item"],
        source_dimensions=f"{source_row['width_m']:g} x {source_row['height_m']:g} m",
        width_m=pricing_input.width_m,
        height_m=pricing_input.height_m,
        area_m2=area_m2,
        quantity=quantity,
        fabrication_time_hours_per_unit=round(fabrication_time_hours_per_unit, 2),
        total_fabrication_time_hours=round(total_fabrication_time_hours, 2),
        material_gbp=round(material_gbp, 2),
        glass_gbp=round(glass_gbp, 2),
        labour_gbp=round(labour_gbp, 2),
        coating_gbp=round(coating_gbp, 2),
        margin_gbp=round(margin_gbp, 2),
        final_price_gbp=round(final_price_gbp, 2),
        total_material_gbp=round(total_material_gbp, 2),
        total_glass_gbp=round(total_glass_gbp, 2),
        total_labour_gbp=round(total_labour_gbp, 2),
        total_coating_gbp=round(total_coating_gbp, 2),
        total_margin_gbp=round(total_margin_gbp, 2),
        total_final_price_gbp=round(total_final_price_gbp, 2),
        total_cost_before_margin_gbp=round(total_cost_before_margin_gbp, 2),
        margin_rate=round(margin_rate, 4),
        source_row=source_row,
    )


def aggregate_pricing_estimates(estimates: list[PricingEstimate]) -> AggregatedPricingEstimate:
    if not estimates:
        raise ValueError("At least one pricing estimate is required for aggregation.")

    bundled_estimates = tuple(estimates)
    total_quantity = sum(item.quantity for item in bundled_estimates)
    total_area_m2 = sum(item.area_m2 * item.quantity for item in bundled_estimates)
    total_fabrication_time_hours = sum(item.total_fabrication_time_hours for item in bundled_estimates)
    total_material_gbp = sum(item.total_material_gbp for item in bundled_estimates)
    total_glass_gbp = sum(item.total_glass_gbp for item in bundled_estimates)
    total_labour_gbp = sum(item.total_labour_gbp for item in bundled_estimates)
    total_coating_gbp = sum(item.total_coating_gbp for item in bundled_estimates)
    total_margin_gbp = sum(item.total_margin_gbp for item in bundled_estimates)
    total_final_price_gbp = sum(item.total_final_price_gbp for item in bundled_estimates)
    total_cost_before_margin_gbp = sum(item.total_cost_before_margin_gbp for item in bundled_estimates)
    margin_rates = {item.margin_rate for item in bundled_estimates}
    margin_rate = (
        next(iter(margin_rates))
        if len(margin_rates) == 1
        else _safe_divide(total_margin_gbp, total_cost_before_margin_gbp)
    )

    return AggregatedPricingEstimate(
        estimates=bundled_estimates,
        total_quantity=total_quantity,
        total_area_m2=round(total_area_m2, 2),
        fabrication_time_hours_per_unit=round(
            _safe_divide(total_fabrication_time_hours, total_quantity),
            2,
        ),
        total_fabrication_time_hours=round(total_fabrication_time_hours, 2),
        material_gbp=round(_safe_divide(total_material_gbp, total_quantity), 2),
        glass_gbp=round(_safe_divide(total_glass_gbp, total_quantity), 2),
        labour_gbp=round(_safe_divide(total_labour_gbp, total_quantity), 2),
        coating_gbp=round(_safe_divide(total_coating_gbp, total_quantity), 2),
        margin_gbp=round(_safe_divide(total_margin_gbp, total_quantity), 2),
        final_price_gbp=round(_safe_divide(total_final_price_gbp, total_quantity), 2),
        total_material_gbp=round(total_material_gbp, 2),
        total_glass_gbp=round(total_glass_gbp, 2),
        total_labour_gbp=round(total_labour_gbp, 2),
        total_coating_gbp=round(total_coating_gbp, 2),
        total_margin_gbp=round(total_margin_gbp, 2),
        total_final_price_gbp=round(total_final_price_gbp, 2),
        total_cost_before_margin_gbp=round(total_cost_before_margin_gbp, 2),
        margin_rate=round(margin_rate, 4),
    )


def _find_source_row(pricing_input: PricingInput, rows: list[dict[str, Any]]) -> dict[str, Any]:
    matches = [
        row
        for row in rows
        if row["element_type"] == pricing_input.element_type
        and row["glass_supply_model"] == pricing_input.glass_supply_model
        and row["wind_load"] == pricing_input.wind_load
        and row["thermal_performance"] == pricing_input.thermal_performance
        and row["coating_type"] == pricing_input.coating_type
    ]

    if not matches:
        raise ValueError("No matching pricing row was found for the selected parameters.")

    return matches[0]


def _margin_rule(
    pricing_input: PricingInput,
    material_gbp: float,
    glass_gbp: float,
    coating_gbp: float,
) -> tuple[float, float]:
    if pricing_input.glass_supply_model.startswith("External supplier"):
        return CUSTOMER_GLASS_MARGIN_RATE, material_gbp

    return COMPANY_GLASS_MARGIN_RATE, material_gbp + glass_gbp + coating_gbp


def _fabrication_time(row: dict[str, Any]) -> float:
    element_type = row["element_type"]
    if element_type in FABRICATION_TIME_OVERRIDES:
        return FABRICATION_TIME_OVERRIDES[element_type]
    return _to_float(row.get("fabrication_time_h", ""))


def _to_float(value: str | float | int | None) -> float:
    if value is None or value == "":
        return 0.0
    if isinstance(value, str):
        value = value.replace(",", ".")
    return float(value)


def _safe_divide(value: float, divisor: float, default: float = 0.0) -> float:
    if divisor == 0:
        return default
    return value / divisor
