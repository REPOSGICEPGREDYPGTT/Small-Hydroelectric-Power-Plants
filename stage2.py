"""
Stage 2 minimal, single-file version (Colab friendly).
Inputs in CASES, outputs in OUTPUTS, no JSON files.
"""

from typing import Any, Dict, List

import pandas as pd
from IPython.display import display

from stage1 import OUTPUTS as STAGE1_OUTPUTS


CASES: Dict[str, Dict[str, Any]] = {
    "paper_prototype": {
        "sediments": {
            "Cs_bar": 0.005,
            "k_s": 1.0,
            "phi_des": 0.35,
        },
        "damage_model": {
            "D_crit": 1.0,
            "t_years": 10.0,
        },
        "failure_coupling": {
            "alpha_lambda_max": 0.3,
        },
        "materials": [
            {"Material": "M1_Concrete", "k_M": 0.03, "n0": 0.015},
            {"Material": "M2_GalvSteel_Epoxy", "k_M": 0.02, "n0": 0.013},
            {"Material": "M3_HDPE_UV", "k_M": 0.012, "n0": 0.011},
            {"Material": "M4_BituminousMembrane", "k_M": 0.04, "n0": 0.016},
            {"Material": "M5_FRP", "k_M": 0.018, "n0": 0.012},
            {"Material": "M6_SS304", "k_M": 0.01, "n0": 0.012},
            {"Material": "M7_CeramicEpoxy", "k_M": 0.006, "n0": 0.011},
        ],
        "alternatives": [
            {
                "Code": "A1_GalvSteel_HighThkEpoxy",
                "base_material": "M2_GalvSteel_Epoxy",
                "coating_material": "M7_CeramicEpoxy",
            },
            {"Code": "A2_PaintedCarbonSteel", "base_material": "M2_GalvSteel_Epoxy"},
            {"Code": "A3_SS304_Unpainted", "base_material": "M6_SS304"},
            {"Code": "A4_HDPE_Channel_MetalSupports", "base_material": "M3_HDPE_UV"},
        ],
    }
}


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(value)))


def compute_stage2(stage1_output: Dict[str, Any], case_data: Dict[str, Any]) -> Dict[str, Any]:
    case_name = str(stage1_output.get("case_name", "UNKNOWN"))
    v_bar = float(stage1_output["results"]["V_mps"])

    sediments = case_data["sediments"]
    damage_model = case_data["damage_model"]
    failure_coupling = case_data["failure_coupling"]

    cs_bar = float(sediments["Cs_bar"])
    k_s = float(sediments["k_s"])
    phi_des = float(sediments["phi_des"])
    d_crit = float(damage_model["D_crit"])
    t_years = float(damage_model["t_years"])
    alpha_lambda_max = float(failure_coupling["alpha_lambda_max"])

    ia_bar = max(0.0, k_s * (phi_des * cs_bar) * (v_bar**2))
    materials_out: List[Dict[str, Any]] = []

    for material in case_data["materials"]:
        mid = str(material["Material"])
        k_m = float(material["k_M"])
        n0 = float(material["n0"])

        d_dot = k_m * ia_bar
        d_t = d_dot * t_years
        t_eff = float("inf") if d_dot == 0.0 else d_crit / d_dot

        alpha_mat = _clamp(1.0 - (d_t / d_crit))
        lambda_abr = alpha_lambda_max * (1.0 - alpha_mat)

        materials_out.append(
            {
                "Material": mid,
                "k_M": k_m,
                "n0": n0,
                "V_bar_mps": v_bar,
                "Ia_bar": ia_bar,
                "D_dot_per_year": d_dot,
                "D_t": d_t,
                "T_eff_years": t_eff,
                "alpha_mat": alpha_mat,
                "lambda_abr_events_per_year": lambda_abr,
                "T_eff_tilde": 1.0,
            }
        )

    finite_t_eff = [row["T_eff_years"] for row in materials_out if row["T_eff_years"] != float("inf")]
    if finite_t_eff:
        t_min = min(finite_t_eff)
        t_max = max(finite_t_eff)
        span = t_max - t_min
        for row in materials_out:
            t_eff = row["T_eff_years"]
            if t_eff == float("inf"):
                row["T_eff_tilde"] = 1.0
            elif span == 0.0:
                row["T_eff_tilde"] = 1.0
            else:
                row["T_eff_tilde"] = _clamp((t_eff - t_min) / span)

    materials_map = {row["Material"]: row for row in materials_out}
    alternatives_out: List[Dict[str, Any]] = []

    for alt in case_data["alternatives"]:
        code = str(alt["Code"])
        base = str(alt["base_material"])
        coating = alt.get("coating_material")
        abrasive = str(coating) if coating else base
        selected = materials_map[abrasive]

        alternatives_out.append(
            {
                "Code": code,
                "Material": abrasive,
                "abrasive_control_surface": abrasive,
                "base_material": base,
                "coating_material": coating,
                "k_M": float(selected["k_M"]),
                "Ia_bar": ia_bar,
                "alpha_mat": float(selected["alpha_mat"]),
                "lambda_abr_events_per_year": float(selected["lambda_abr_events_per_year"]),
                "T_eff_years": float(selected["T_eff_years"]),
                "T_eff_tilde": float(selected["T_eff_tilde"]),
            }
        )

    return {
        "case_name": case_name,
        "stage": "stage2_abrasion_degradation",
        "stage1_case_name": case_name,
        "sediments": {
            "Cs_bar": cs_bar,
            "k_s": k_s,
            "phi_des": phi_des,
        },
        "damage_model": {
            "D_crit": d_crit,
            "t_years": t_years,
        },
        "failure_coupling": {
            "alpha_lambda_max": alpha_lambda_max,
        },
        "V_bar_mps": v_bar,
        "Ia_bar": ia_bar,
        "materials": materials_out,
        "alternatives": alternatives_out,
        "stage3_ready": {
            "Ia_bar": ia_bar,
            "materials": materials_out,
            "alternatives": alternatives_out,
            "V_bar_mps": v_bar,
            "damage_model": {"D_crit": d_crit, "t_years": t_years},
            "failure_coupling": {"alpha_lambda_max": alpha_lambda_max},
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


def print_stage2_tables(output: Dict[str, Any]) -> None:
    alternatives = list(output.get("alternatives", []))
    best_alt = max(alternatives, key=lambda row: float(row.get("T_eff_tilde", 0.0))) if alternatives else None

    summary_rows = [
        {"Metric": "V_bar (m/s)", "Value": _fmt(output["V_bar_mps"]), "Source": "stage1"},
        {"Metric": "Ia_bar", "Value": _fmt(output["Ia_bar"]), "Source": "computed"},
        {
            "Metric": "alpha_lambda_max",
            "Value": _fmt(output["failure_coupling"]["alpha_lambda_max"]),
            "Source": "case_data",
        },
        {
            "Metric": "Materials evaluated",
            "Value": _fmt(len(output.get("materials", []))),
            "Source": "case_data",
        },
        {
            "Metric": "Alternatives evaluated",
            "Value": _fmt(len(alternatives)),
            "Source": "case_data",
        },
        {
            "Metric": "Best durability code",
            "Value": str(best_alt["Code"]) if best_alt else "-",
            "Source": "computed",
        },
        {
            "Metric": "Best T_eff_tilde",
            "Value": _fmt(float(best_alt["T_eff_tilde"])) if best_alt else "-",
            "Source": "computed",
        },
    ]
    summary_df = pd.DataFrame(summary_rows)
    display(_style(summary_df, "Stage 2 Summary"))


OUTPUTS: Dict[str, Dict[str, Any]] = {
    name: compute_stage2(STAGE1_OUTPUTS[name], case_data) for name, case_data in CASES.items()
}


if __name__ == "__main__":
    selected_case = "paper_prototype"
    print_stage2_tables(OUTPUTS[selected_case])
