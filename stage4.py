"""
Stage 4 minimal, single-file version (Colab friendly).
Inputs in CASES, outputs in OUTPUTS, no JSON files.
"""

from math import floor
from typing import Any, Dict, List

import pandas as pd
from IPython.display import display

from stage2 import OUTPUTS as STAGE2_OUTPUTS
from stage3 import OUTPUTS as STAGE3_OUTPUTS


CASES: Dict[str, Dict[str, Any]] = {
    "paper_prototype": {
        "horizon": {
            "T_years": 10,
            "r": 0.1,
        },
        "interruptions_cost": {
            "c_e_usd_per_kwh": 0.15,
            "fx_COP_per_USD": 4000.0,
        },
        "maintenance_model": {
            "mode": "cycle_lumps",
            "beta_D": 0.0,
        },
        "replacement_model": {
            "rep_cost_fraction_of_CAPEX_default": 0.15,
            "year_mapping": "round",
        },
        "alternatives_econ": [
            {
                "Code": "A1_GalvSteel_HighThkEpoxy",
                "CAPEX_COP": 5800000,
                "OpEx_10_years_COP": 900000,
                "Maintenance_years": 6,
                "Service_life_years": 12,
                "rep_cost_fraction_of_CAPEX": 0.15,
            },
            {
                "Code": "A2_PaintedCarbonSteel",
                "CAPEX_COP": 4700000,
                "OpEx_10_years_COP": 1400000,
                "Maintenance_years": 4,
                "Service_life_years": 8,
                "rep_cost_fraction_of_CAPEX": 0.15,
            },
            {
                "Code": "A3_SS304_Unpainted",
                "CAPEX_COP": 9200000,
                "OpEx_10_years_COP": 400000,
                "Maintenance_years": 10,
                "Service_life_years": 20,
                "rep_cost_fraction_of_CAPEX": 0.15,
            },
            {
                "Code": "A4_HDPE_Channel_MetalSupports",
                "CAPEX_COP": 5200000,
                "OpEx_10_years_COP": 600000,
                "Maintenance_years": 7,
                "Service_life_years": 15,
                "rep_cost_fraction_of_CAPEX": 0.15,
            },
        ],
    }
}


def _discount_factor(year: int, rate: float) -> float:
    return 1.0 / ((1.0 + rate) ** year)


def _maintenance_event_years(t_years: int, cycle_years: float) -> List[int]:
    years: List[int] = []
    if cycle_years <= 0.0:
        return years

    step = 1
    while True:
        year = int(round(step * cycle_years))
        if year > t_years:
            break
        if year > 0 and year not in years:
            years.append(year)
        step += 1
    return sorted(years)


def _replacement_years(t_years: int, t_econ: float, mode: str) -> List[int]:
    if t_econ <= 0.0 or t_econ >= t_years:
        return []

    years: List[int] = []
    n_rep = int(floor(t_years / t_econ))
    for k in range(1, n_rep + 1):
        raw_year = k * t_econ
        if mode == "floor":
            year = int(floor(raw_year))
        elif mode == "ceil":
            import math

            year = int(math.ceil(raw_year))
        else:
            year = int(round(raw_year))
        if 1 <= year <= t_years and year not in years:
            years.append(year)
    return sorted(years)


def _normalize_lcc_benefit(lcc_values: List[float]) -> List[float]:
    lcc_min = min(lcc_values)
    lcc_max = max(lcc_values)
    if lcc_max == lcc_min:
        return [1.0 for _ in lcc_values]
    return [(lcc_max - value) / (lcc_max - lcc_min) for value in lcc_values]


def compute_stage4(
    stage2_output: Dict[str, Any],
    stage3_output: Dict[str, Any],
    case_data: Dict[str, Any],
) -> Dict[str, Any]:
    case_name = str(stage3_output.get("case_name", stage2_output.get("case_name", "UNKNOWN")))

    horizon = case_data["horizon"]
    interruptions_cost = case_data["interruptions_cost"]
    maintenance_model = case_data["maintenance_model"]
    replacement_model = case_data["replacement_model"]

    t_years = int(horizon["T_years"])
    discount_rate = float(horizon["r"])
    c_e_cop_per_kwh = float(interruptions_cost["c_e_usd_per_kwh"]) * float(interruptions_cost["fx_COP_per_USD"])
    default_rep_fraction = float(replacement_model["rep_cost_fraction_of_CAPEX_default"])
    year_mapping = str(replacement_model["year_mapping"])

    alt_surface_map = {
        str(alt["Code"]): str(alt.get("abrasive_control_surface", alt.get("base_material", "")))
        for alt in stage2_output.get("alternatives", [])
    }
    ens_map = {
        str(material["Material"]): float(material["ENS_kWh_per_year"])
        for material in stage3_output.get("materials", [])
    }

    alternatives_out: List[Dict[str, Any]] = []
    audit_rows: List[Dict[str, Any]] = []

    for alt in case_data["alternatives_econ"]:
        code = str(alt["Code"])
        capex = float(alt["CAPEX_COP"])
        opex_t = float(alt["OpEx_10_years_COP"])
        maintenance_years = float(alt["Maintenance_years"])
        t_econ = float(alt["Service_life_years"])
        rep_fraction = float(alt.get("rep_cost_fraction_of_CAPEX", default_rep_fraction))

        abrasive_surface = alt_surface_map[code]
        ens_kwh_yr = float(ens_map[abrasive_surface])
        annual_interruptions_cost = ens_kwh_yr * c_e_cop_per_kwh

        pv_int = sum(
            annual_interruptions_cost * _discount_factor(year, discount_rate)
            for year in range(1, t_years + 1)
        )

        maintenance_mode = str(maintenance_model.get("mode", "cycle_lumps"))
        if maintenance_mode == "cycle_lumps":
            event_years = _maintenance_event_years(t_years, maintenance_years)
            lump = 0.0 if not event_years else opex_t / len(event_years)
            pv_maint = sum(lump * _discount_factor(year, discount_rate) for year in event_years)
            maintenance_audit = {"event_years": event_years, "lump_each_COP": lump}
        else:
            annual = opex_t / t_years
            pv_maint = sum(
                annual * _discount_factor(year, discount_rate) for year in range(1, t_years + 1)
            )
            maintenance_audit = {"annual_COP": annual}

        rep_years = _replacement_years(t_years, t_econ, year_mapping)
        rep_cost_each = rep_fraction * capex
        pv_rep = sum(rep_cost_each * _discount_factor(year, discount_rate) for year in rep_years)

        lcc = capex + pv_maint + pv_int + pv_rep

        alternatives_out.append(
            {
                "Code": code,
                "abrasive_control_surface": abrasive_surface,
                "T_econ_yr": t_econ,
                "rep_years": rep_years,
                "CAPEX_COP": capex,
                "PV_maint_COP": pv_maint,
                "PV_int_COP": pv_int,
                "PV_rep_COP": pv_rep,
                "LCC_COP": lcc,
            }
        )

        audit_rows.append(
            {
                "Code": code,
                "g(A)=abrasive_control_surface": abrasive_surface,
                "ENS_material_kWh_per_year": ens_kwh_yr,
                "c_e_COP_per_kwh": c_e_cop_per_kwh,
                "annual_interruptions_cost_COP": annual_interruptions_cost,
                "maintenance_mode_used": maintenance_mode,
                "maintenance_inputs": {
                    "OpEx_10_years_COP": opex_t,
                    "Maintenance_years": maintenance_years,
                },
                "maintenance_schedule_audit": maintenance_audit,
                "replacement": {
                    "T_econ_years": t_econ,
                    "rep_fraction": rep_fraction,
                    "rep_cost_each_COP": rep_cost_each,
                    "rep_years": rep_years,
                },
                "PV_breakdown_COP": {
                    "CAPEX": capex,
                    "PV_maint": pv_maint,
                    "PV_int": pv_int,
                    "PV_rep": pv_rep,
                    "LCC": lcc,
                },
            }
        )

    lcc_values = [float(row["LCC_COP"]) for row in alternatives_out]
    lcc_tilde_values = _normalize_lcc_benefit(lcc_values)
    for index, row in enumerate(alternatives_out):
        row["LCC_tilde"] = float(lcc_tilde_values[index])

    lcc_min = float(min(lcc_values))
    lcc_max = float(max(lcc_values))

    return {
        "case_name": case_name,
        "stage": "stage4_economic_lcc",
        "horizon": {
            "T_years": t_years,
            "r": discount_rate,
        },
        "interruptions_cost": {
            "c_e_usd_per_kwh": float(interruptions_cost["c_e_usd_per_kwh"]),
            "fx_COP_per_USD": float(interruptions_cost["fx_COP_per_USD"]),
            "c_e_COP_per_kwh": c_e_cop_per_kwh,
        },
        "maintenance_model": {
            "mode": str(maintenance_model.get("mode", "cycle_lumps")),
            "beta_D": float(maintenance_model.get("beta_D", 0.0)),
        },
        "replacement_model": {
            "rep_cost_fraction_of_CAPEX_default": default_rep_fraction,
            "year_mapping": year_mapping,
        },
        "ENS_material_map_kWh_per_year": ens_map,
        "alternatives": alternatives_out,
        "normalization": {
            "LCC_min_COP": lcc_min,
            "LCC_max_COP": lcc_max,
            "Eq35": "LCC_tilde = (LCC_max - LCC_i)/(LCC_max - LCC_min)",
        },
        "audit_rows": audit_rows,
        "stage5_ready": {
            "alternatives": alternatives_out,
            "normalization": {
                "LCC_min_COP": lcc_min,
                "LCC_max_COP": lcc_max,
            },
            "ENS_material_map_kWh_per_year": ens_map,
            "horizon": {
                "T_years": t_years,
                "r": discount_rate,
            },
        },
    }


def _fmt(value: Any) -> str:
    return f"{value:.6f}" if isinstance(value, (int, float)) else str(value)


def _style(df: pd.DataFrame, caption: str):
    return (
        df.style.set_caption(caption)
        .hide(axis="index")
        .set_table_styles(
            [
                {
                    "selector": "caption",
                    "props": [("font-size", "16px"), ("font-weight", "600"), ("text-align", "left")],
                },
                {
                    "selector": "th",
                    "props": [("background-color", "#1f2937"), ("color", "#ffffff"), ("padding", "8px")],
                },
                {"selector": "td", "props": [("padding", "8px"), ("border", "1px solid #d1d5db")]},
            ]
        )
    )


def print_stage4_tables(output: Dict[str, Any]) -> None:
    alternatives = list(output.get("alternatives", []))
    best_alt = max(alternatives, key=lambda row: float(row.get("LCC_tilde", 0.0))) if alternatives else None

    summary_rows = [
        {"Metric": "T horizon (years)", "Value": _fmt(output["horizon"]["T_years"]), "Source": "case_data"},
        {"Metric": "Discount rate r", "Value": _fmt(output["horizon"]["r"]), "Source": "case_data"},
        {
            "Metric": "c_e (COP/kWh)",
            "Value": _fmt(output["interruptions_cost"]["c_e_COP_per_kwh"]),
            "Source": "computed",
        },
        {"Metric": "Alternatives evaluated", "Value": _fmt(len(alternatives)), "Source": "case_data"},
        {
            "Metric": "LCC_min (COP)",
            "Value": _fmt(output["normalization"]["LCC_min_COP"]),
            "Source": "computed",
        },
        {
            "Metric": "LCC_max (COP)",
            "Value": _fmt(output["normalization"]["LCC_max_COP"]),
            "Source": "computed",
        },
        {
            "Metric": "Best LCC_tilde code",
            "Value": str(best_alt["Code"]) if best_alt else "-",
            "Source": "computed",
        },
        {
            "Metric": "Best LCC_tilde",
            "Value": _fmt(float(best_alt["LCC_tilde"])) if best_alt else "-",
            "Source": "computed",
        },
    ]
    summary_df = pd.DataFrame(summary_rows)
    display(_style(summary_df, "Stage 4 Summary"))


OUTPUTS: Dict[str, Dict[str, Any]] = {
    name: compute_stage4(STAGE2_OUTPUTS[name], STAGE3_OUTPUTS[name], case_data)
    for name, case_data in CASES.items()
}


if __name__ == "__main__":
    selected_case = "paper_prototype"
    print_stage4_tables(OUTPUTS[selected_case])
