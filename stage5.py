"""
Stage 5 minimal, single-file version (Colab friendly).
Inputs in CASES, outputs in OUTPUTS, no JSON files.
"""

from typing import Any, Dict, List

import pandas as pd
from IPython.display import display

from stage2 import OUTPUTS as STAGE2_OUTPUTS
from stage3 import OUTPUTS as STAGE3_OUTPUTS
from stage4 import OUTPUTS as STAGE4_OUTPUTS


SAATY_RI: Dict[int, float] = {
    1: 0.00,
    2: 0.00,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
}


CASES: Dict[str, Dict[str, Any]] = {
    "paper_prototype": {
        "criteria": ["Hydraulic", "LCC", "Durability", "Reliability"],
        "pairwise_matrix_aggregated": [
            [1.0, 2.0, 1.0, 1.0],
            [0.5, 1.0, 0.5, 0.5],
            [1.0, 2.0, 1.0, 1.0],
            [1.0, 2.0, 1.0, 1.0],
        ],
        "hydraulic_scores": [
            {"Code": "A4_HDPE_Channel_MetalSupports", "Hydraulic_score": 1.0},
            {"Code": "A2_PaintedCarbonSteel", "Hydraulic_score": 0.0},
            {"Code": "A1_GalvSteel_HighThkEpoxy", "Hydraulic_score": 0.0},
            {"Code": "A3_SS304_Unpainted", "Hydraulic_score": 0.5},
        ],
    }
}


def _mat_vec(matrix: List[List[float]], vector: List[float]) -> List[float]:
    size = len(matrix)
    return [
        sum(float(matrix[row][col]) * float(vector[col]) for col in range(size))
        for row in range(size)
    ]


def _normalize_l1(vector: List[float]) -> List[float]:
    total = sum(abs(value) for value in vector)
    return [float(value) / total for value in vector]


def _ahp_weights(matrix: List[List[float]], max_iter: int = 5000, tol: float = 1e-13) -> Dict[str, float]:
    size = len(matrix)
    weights = [1.0 / size] * size
    lambda_prev = None

    for _ in range(max_iter):
        aw = _mat_vec(matrix, weights)
        weights_new = _normalize_l1(aw)

        ratios = [aw[i] / weights_new[i] for i in range(size) if weights_new[i] > 0.0]
        lambda_est = sum(ratios) / len(ratios)

        diff = max(abs(weights_new[i] - weights[i]) for i in range(size))
        weights = weights_new

        if lambda_prev is not None and diff < tol and abs(lambda_est - lambda_prev) < 1e-11:
            break
        lambda_prev = lambda_est

    lambda_max = float(lambda_prev if lambda_prev is not None else size)
    ci = 0.0 if size <= 1 else (lambda_max - size) / (size - 1)
    ri = float(SAATY_RI.get(size, 0.0))
    cr = 0.0 if ri == 0.0 else ci / ri

    return {
        "weights": [float(w) for w in weights],
        "lambda_max": lambda_max,
        "CI": float(ci),
        "CR": float(cr),
        "RI": ri,
    }


def compute_stage5(
    stage2_output: Dict[str, Any],
    stage3_output: Dict[str, Any],
    stage4_output: Dict[str, Any],
    case_data: Dict[str, Any],
) -> Dict[str, Any]:
    case_name = str(stage4_output.get("case_name", "UNKNOWN"))
    criteria = list(case_data["criteria"])
    pairwise_matrix = case_data["pairwise_matrix_aggregated"]
    ahp = _ahp_weights(pairwise_matrix)

    durability_map = {str(row["Code"]): float(row["T_eff_tilde"]) for row in stage2_output["alternatives"]}
    reliability_map = {str(row["Code"]): float(row["alpha_R"]) for row in stage3_output["alternatives"]}
    lcc_map = {str(row["Code"]): float(row["LCC_tilde"]) for row in stage4_output["alternatives"]}
    hydraulic_map = {
        str(row["Code"]): float(row["Hydraulic_score"]) for row in case_data["hydraulic_scores"]
    }

    alternatives: List[Dict[str, Any]] = []
    for alt in sorted(stage4_output["alternatives"], key=lambda row: str(row["Code"])):
        code = str(alt["Code"])
        scores = {
            "Hydraulic": hydraulic_map[code],
            "LCC": lcc_map[code],
            "Durability": durability_map[code],
            "Reliability": reliability_map[code],
        }
        weighted_score = sum(
            float(ahp["weights"][index]) * float(scores[criterion])
            for index, criterion in enumerate(criteria)
        )
        alternatives.append(
            {
                "Code": code,
                "scores": scores,
                "S_weighted": float(weighted_score),
            }
        )

    alternatives.sort(key=lambda row: float(row["S_weighted"]), reverse=True)
    for index, row in enumerate(alternatives, start=1):
        row["Ranking"] = index

    return {
        "case_name": case_name,
        "stage": "stage5_mcda_ahp",
        "criteria": criteria,
        "ahp": {
            "weights": ahp["weights"],
            "lambda_max": ahp["lambda_max"],
            "CI": ahp["CI"],
            "CR": ahp["CR"],
            "RI": ahp["RI"],
            "pairwise_matrix_used": pairwise_matrix,
        },
        "source_scores": {
            "Hydraulic": hydraulic_map,
            "Durability": durability_map,
            "Reliability": reliability_map,
            "LCC": lcc_map,
        },
        "alternatives": alternatives,
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


def print_stage5_tables(output: Dict[str, Any]) -> None:
    alternatives = list(output.get("alternatives", []))
    best_alt = alternatives[0] if alternatives else None
    ahp = output.get("ahp", {})

    summary_rows = [
        {"Metric": "Criteria count", "Value": _fmt(len(output.get("criteria", []))), "Source": "case_data"},
        {"Metric": "AHP lambda_max", "Value": _fmt(ahp.get("lambda_max", "-")), "Source": "computed"},
        {"Metric": "AHP CI", "Value": _fmt(ahp.get("CI", "-")), "Source": "computed"},
        {"Metric": "AHP CR", "Value": _fmt(ahp.get("CR", "-")), "Source": "computed"},
        {
            "Metric": "Alternatives evaluated",
            "Value": _fmt(len(alternatives)),
            "Source": "stages 2-4 + case_data",
        },
        {
            "Metric": "Top ranked code",
            "Value": str(best_alt["Code"]) if best_alt else "-",
            "Source": "computed",
        },
        {
            "Metric": "Top weighted score",
            "Value": _fmt(float(best_alt["S_weighted"])) if best_alt else "-",
            "Source": "computed",
        },
    ]
    summary_df = pd.DataFrame(summary_rows)
    display(_style(summary_df, "Stage 5 Summary"))


OUTPUTS: Dict[str, Dict[str, Any]] = {
    name: compute_stage5(STAGE2_OUTPUTS[name], STAGE3_OUTPUTS[name], STAGE4_OUTPUTS[name], case_data)
    for name, case_data in CASES.items()
}


if __name__ == "__main__":
    selected_case = "paper_prototype"
    print_stage5_tables(OUTPUTS[selected_case])
