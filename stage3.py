"""
Stage 3 minimal, single-file version (Colab friendly).
Inputs in CASES, outputs in OUTPUTS, no JSON files.
"""

from typing import Any, Dict, List

import pandas as pd
from IPython.display import display

from stage1 import OUTPUTS as STAGE1_OUTPUTS
from stage2 import OUTPUTS as STAGE2_OUTPUTS


CASES: Dict[str, Dict[str, Any]] = {
    "paper_prototype": {
        "reliability_case": {
            "N": 1.0,
            "U_bar_h": 3.0,
            "P_bar_kW": 10.0,
            "lambda_0": 0.1,
        },
        "alpha_R": {
            "SAIDI_max_h_per_year": 20.0,
            "SAIFI_max_events_per_year": 2.0,
            "w_D": 0.4,
            "w_F": 0.4,
            "w_M": 0.2,
        },
    }
}


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(value)))


def compute_stage3(
    stage1_output: Dict[str, Any],
    stage2_output: Dict[str, Any],
    case_data: Dict[str, Any],
) -> Dict[str, Any]:
    case_name = str(stage2_output.get("case_name", stage1_output.get("case_name", "UNKNOWN")))
    alpha_lambda = float(stage2_output["failure_coupling"]["alpha_lambda_max"])
    ia_bar = float(stage2_output["Ia_bar"])

    rc = case_data["reliability_case"]
    n = float(rc["N"])
    u_bar_h = float(rc["U_bar_h"])
    p_bar_kw = float(rc["P_bar_kW"])
    lambda_0 = float(rc["lambda_0"])

    ar = case_data["alpha_R"]
    saidi_max = float(ar["SAIDI_max_h_per_year"])
    saifi_max = float(ar["SAIFI_max_events_per_year"])
    w_d = float(ar["w_D"])
    w_f = float(ar["w_F"])
    w_m = float(ar["w_M"])

    materials_out: List[Dict[str, Any]] = []
    material_map: Dict[str, Dict[str, Any]] = {}

    for material in stage2_output["materials"]:
        material_id = str(material["Material"])
        alpha_mat = _clamp(float(material.get("alpha_mat", 1.0)))

        lambda_abr = alpha_lambda * (1.0 - alpha_mat)
        lambda_mi = lambda_0 + lambda_abr
        saifi = lambda_mi
        saidi = lambda_mi * u_bar_h
        ens = saidi * p_bar_kw

        term_d = w_d * (saidi / saidi_max)
        term_f = w_f * (saifi / saifi_max)
        term_m = w_m * (1.0 - alpha_mat)
        alpha_r = _clamp(1.0 - (term_d + term_f + term_m))

        row = {
            "Material": material_id,
            "Ia_bar": ia_bar,
            "alpha_mat": alpha_mat,
            "lambda_abr_events_per_year": lambda_abr,
            "lambda_Mi_events_per_year": lambda_mi,
            "SAIFI_events_per_year": saifi,
            "SAIDI_h_per_year": saidi,
            "ENS_kWh_per_year": ens,
            "alpha_R": alpha_r,
            "alphaR_terms": {
                "wD_SAIDI_norm": term_d,
                "wF_SAIFI_norm": term_f,
                "wM_damage": term_m,
            },
            "sanity": {
                "SAIDI_check_h_per_year": saifi * u_bar_h,
                "ENS_check_kWh_per_year": saidi * p_bar_kw,
                "delta_SAIDI_abs": 0.0,
                "delta_SAIDI_rel": 0.0,
                "delta_ENS_abs": 0.0,
                "delta_ENS_rel": 0.0,
                "flags": [],
            },
        }
        materials_out.append(row)
        material_map[material_id] = row

    alternatives_out: List[Dict[str, Any]] = []
    for alt in stage2_output.get("alternatives", []):
        code = str(alt["Code"])
        abrasive_surface = str(
            alt.get(
                "abrasive_control_surface",
                alt.get("coating_material", alt.get("base_material", "UNKNOWN")),
            )
        )
        row = material_map.get(abrasive_surface)

        if row is None:
            alternatives_out.append(
                {
                    "Code": code,
                    "abrasive_control_surface": abrasive_surface,
                    "Ia_bar": ia_bar,
                    "alpha_mat": float("nan"),
                    "lambda_abr_events_per_year": float("nan"),
                    "lambda_Mi_events_per_year": float("nan"),
                    "SAIFI_events_per_year": float("nan"),
                    "SAIDI_h_per_year": float("nan"),
                    "ENS_kWh_per_year": float("nan"),
                    "alpha_R": float("nan"),
                    "sanity": {"flags": ["missing_abrasive_surface_in_mat_map"]},
                }
            )
            continue

        alternatives_out.append(
            {
                "Code": code,
                "abrasive_control_surface": abrasive_surface,
                "Ia_bar": ia_bar,
                "alpha_mat": float(row["alpha_mat"]),
                "lambda_abr_events_per_year": float(row["lambda_abr_events_per_year"]),
                "lambda_Mi_events_per_year": float(row["lambda_Mi_events_per_year"]),
                "SAIFI_events_per_year": float(row["SAIFI_events_per_year"]),
                "SAIDI_h_per_year": float(row["SAIDI_h_per_year"]),
                "ENS_kWh_per_year": float(row["ENS_kWh_per_year"]),
                "alpha_R": float(row["alpha_R"]),
                "sanity": row["sanity"],
            }
        )

    return {
        "case_name": case_name,
        "stage": "stage3_reliability_penalty",
        "reliability_case": {
            "N": n,
            "U_bar_h": u_bar_h,
            "P_bar_kW": p_bar_kw,
            "lambda_0": lambda_0,
        },
        "alphaR_params": {
            "SAIDI_max_h_per_year": saidi_max,
            "SAIFI_max_events_per_year": saifi_max,
            "w_D": w_d,
            "w_F": w_f,
            "w_M": w_m,
        },
        "audit_inputs": {
            "stage1_case_name": stage1_output.get("case_name"),
            "stage2_case_name": stage2_output.get("case_name"),
            "Ia_bar": ia_bar,
            "alpha_lambda": alpha_lambda,
            "damage_model": stage2_output.get("damage_model", {}),
        },
        "Ia_bar": ia_bar,
        "materials": materials_out,
        "alternatives": alternatives_out,
        "stage4_ready": {
            "materials": materials_out,
            "alternatives": alternatives_out,
            "Ia_bar": ia_bar,
            "reliability_case": {
                "N": n,
                "U_bar_h": u_bar_h,
                "P_bar_kW": p_bar_kw,
                "lambda_0": lambda_0,
            },
            "alphaR_params": {
                "SAIDI_max_h_per_year": saidi_max,
                "SAIFI_max_events_per_year": saifi_max,
                "w_D": w_d,
                "w_F": w_f,
                "w_M": w_m,
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


def print_stage3_tables(output: Dict[str, Any]) -> None:
    alternatives = list(output.get("alternatives", []))
    best_alt = max(alternatives, key=lambda row: float(row.get("alpha_R", 0.0))) if alternatives else None

    rc = output.get("reliability_case", {})
    arp = output.get("alphaR_params", {})
    summary_rows = [
        {"Metric": "Ia_bar", "Value": _fmt(output["Ia_bar"]), "Source": "stage2"},
        {"Metric": "lambda_0 (events/year)", "Value": _fmt(rc.get("lambda_0", "-")), "Source": "case_data"},
        {"Metric": "U_bar (h)", "Value": _fmt(rc.get("U_bar_h", "-")), "Source": "case_data"},
        {"Metric": "P_bar (kW)", "Value": _fmt(rc.get("P_bar_kW", "-")), "Source": "case_data"},
        {
            "Metric": "SAIDI_max (h/year)",
            "Value": _fmt(arp.get("SAIDI_max_h_per_year", "-")),
            "Source": "case_data",
        },
        {
            "Metric": "SAIFI_max (events/year)",
            "Value": _fmt(arp.get("SAIFI_max_events_per_year", "-")),
            "Source": "case_data",
        },
        {"Metric": "Alternatives evaluated", "Value": _fmt(len(alternatives)), "Source": "computed"},
        {
            "Metric": "Best alpha_R code",
            "Value": str(best_alt["Code"]) if best_alt else "-",
            "Source": "computed",
        },
        {
            "Metric": "Best alpha_R",
            "Value": _fmt(float(best_alt["alpha_R"])) if best_alt else "-",
            "Source": "computed",
        },
    ]
    summary_df = pd.DataFrame(summary_rows)
    display(_style(summary_df, "Stage 3 Summary"))


OUTPUTS: Dict[str, Dict[str, Any]] = {
    name: compute_stage3(STAGE1_OUTPUTS[name], STAGE2_OUTPUTS[name], case_data)
    for name, case_data in CASES.items()
}


if __name__ == "__main__":
    selected_case = "paper_prototype"
    print_stage3_tables(OUTPUTS[selected_case])
