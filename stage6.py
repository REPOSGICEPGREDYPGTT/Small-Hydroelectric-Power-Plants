"""
Stage 6 minimal, single-file version (Colab friendly).
Inputs in CASES, outputs in OUTPUTS, no JSON files.
"""

from typing import Any, Dict, List

import numpy as np
import pandas as pd
from IPython.display import display

from stage5 import OUTPUTS as STAGE5_OUTPUTS


CASES: Dict[str, Dict[str, Any]] = {
    "paper_prototype": {
        "criteria_order": ["Hydraulic", "LCC", "Durability", "Reliability"],
        "expert_points_100": [
            {"Expert": "E1", "Hydraulic": 32, "LCC": 10, "Durability": 26, "Reliability": 32},
            {"Expert": "E2", "Hydraulic": 30, "LCC": 12, "Durability": 26, "Reliability": 32},
            {"Expert": "E3", "Hydraulic": 31, "LCC": 11, "Durability": 25, "Reliability": 33},
            {"Expert": "E4", "Hydraulic": 25, "LCC": 22, "Durability": 25, "Reliability": 28},
            {"Expert": "E5", "Hydraulic": 26, "LCC": 20, "Durability": 24, "Reliability": 30},
        ],
        "egk": {
            "m": 2.0,
            "ep": 1e-4,
            "beta": 1e-3,
            "max_iter": 300,
            "M_candidates": [2, 3],
            "seed": 7,
        },
    }
}


def points100_to_matrix(experts: List[Dict[str, Any]], criteria: List[str]) -> np.ndarray:
    n = len(criteria)
    expert_count = len(experts)
    matrix = np.zeros((n, expert_count), dtype=float)

    for col, expert in enumerate(experts):
        points_sum = 0.0
        for row, criterion in enumerate(criteria):
            value = float(expert[criterion])
            matrix[row, col] = value
            points_sum += value
        matrix[:, col] /= points_sum

    return matrix


def _init_u(cluster_count: int, expert_count: int, rng: np.random.Generator) -> np.ndarray:
    u = rng.random((cluster_count, expert_count))
    return u / np.sum(u, axis=0, keepdims=True)


def _centers_from_u(weights_matrix: np.ndarray, u: np.ndarray, fuzziness: float) -> np.ndarray:
    u_m = u**fuzziness
    denom = np.sum(u_m, axis=1).reshape(1, -1)
    return (weights_matrix @ u_m.T) / denom


def _covariances(
    weights_matrix: np.ndarray,
    u: np.ndarray,
    centers: np.ndarray,
    fuzziness: float,
    beta: float,
) -> np.ndarray:
    n, expert_count = weights_matrix.shape
    cluster_count = u.shape[0]
    u_m = u**fuzziness
    identity = np.eye(n, dtype=float)
    covs = np.zeros((cluster_count, n, n), dtype=float)

    for k in range(cluster_count):
        denom = np.sum(u_m[k, :])
        if denom <= 1e-18:
            covs[k, :, :] = identity
            continue

        s_k = np.zeros((n, n), dtype=float)
        center = centers[:, k].reshape(n, 1)
        for i in range(expert_count):
            point = weights_matrix[:, i].reshape(n, 1)
            delta = point - center
            s_k += u_m[k, i] * (delta @ delta.T)

        covs[k, :, :] = (s_k / denom) + beta * identity

    return covs


def _distances(weights_matrix: np.ndarray, centers: np.ndarray, covs: np.ndarray) -> np.ndarray:
    _, expert_count = weights_matrix.shape
    cluster_count = covs.shape[0]
    d2 = np.zeros((cluster_count, expert_count), dtype=float)

    for k in range(cluster_count):
        inv_cov = np.linalg.inv(covs[k, :, :])
        center = centers[:, k].reshape(-1, 1)
        for i in range(expert_count):
            point = weights_matrix[:, i].reshape(-1, 1)
            delta = point - center
            d2[k, i] = float((delta.T @ inv_cov @ delta)[0, 0])

    return np.maximum(d2, 1e-18)


def _update_u(d2: np.ndarray, fuzziness: float) -> np.ndarray:
    cluster_count, expert_count = d2.shape
    power = 1.0 / (fuzziness - 1.0)
    u = np.zeros((cluster_count, expert_count), dtype=float)

    for i in range(expert_count):
        for k in range(cluster_count):
            denom = 0.0
            for j in range(cluster_count):
                denom += (d2[k, i] / d2[j, i]) ** power
            u[k, i] = 1.0 / denom

    return u / np.sum(u, axis=0, keepdims=True)


def _xie_beni(weights_matrix: np.ndarray, u: np.ndarray, centers: np.ndarray, fuzziness: float) -> float:
    _, expert_count = weights_matrix.shape
    cluster_count = u.shape[0]
    u_m = u**fuzziness

    numerator = 0.0
    for k in range(cluster_count):
        center = centers[:, k].reshape(-1, 1)
        delta = weights_matrix - center
        eu2 = np.sum(delta * delta, axis=0)
        numerator += float(np.sum(u_m[k, :] * eu2))

    min_sep2 = float("inf")
    for k in range(cluster_count):
        for l in range(k + 1, cluster_count):
            diff = centers[:, k] - centers[:, l]
            sep2 = float(np.dot(diff, diff))
            if sep2 < min_sep2:
                min_sep2 = sep2

    min_sep2 = max(min_sep2, 1e-12)
    return numerator / (expert_count * min_sep2)


def egk_fit(weights_matrix: np.ndarray, cluster_count: int, params: Dict[str, Any]) -> Dict[str, Any]:
    fuzziness = float(params["m"])
    ep = float(params["ep"])
    beta = float(params["beta"])
    max_iter = int(params["max_iter"])
    seed = int(params["seed"])
    expert_count = weights_matrix.shape[1]

    rng = np.random.default_rng(seed + 101 * cluster_count)
    u = _init_u(cluster_count, expert_count, rng)
    error = 10.0 * ep
    iteration = 0

    while iteration < max_iter and error > ep:
        iteration += 1
        centers = _centers_from_u(weights_matrix, u, fuzziness)
        covs = _covariances(weights_matrix, u, centers, fuzziness, beta)
        d2 = _distances(weights_matrix, centers, covs)
        u_new = _update_u(d2, fuzziness)
        error = float(np.max(np.sum(np.abs(u_new - u), axis=0)))
        u = u_new

    centers = _centers_from_u(weights_matrix, u, fuzziness)
    covs = _covariances(weights_matrix, u, centers, fuzziness, beta)
    d2 = _distances(weights_matrix, centers, covs)
    xb = _xie_beni(weights_matrix, u, centers, fuzziness)

    return {
        "M": cluster_count,
        "U": u,
        "V": centers,
        "F": covs,
        "D2": d2,
        "it": iteration,
        "err": error,
        "xie_beni": xb,
    }


def egk_select_m(weights_matrix: np.ndarray, candidates: List[int], params: Dict[str, Any]) -> Dict[str, Any]:
    all_results = [egk_fit(weights_matrix, int(m), params) for m in candidates]
    best = min(all_results, key=lambda row: row["xie_beni"])
    return {
        "best": best,
        "candidates": [
            {
                "M": row["M"],
                "it": row["it"],
                "err": row["err"],
                "xie_beni": row["xie_beni"],
            }
            for row in all_results
        ],
    }


def consensus_metrics(weights_matrix: np.ndarray, u: np.ndarray) -> Dict[str, Any]:
    centroid = np.mean(weights_matrix, axis=1)
    hard = np.argmax(u, axis=0)
    return {
        "overall_centroid": centroid.tolist(),
        "expert_L1_to_centroid": [
            float(np.sum(np.abs(weights_matrix[:, i] - centroid)))
            for i in range(weights_matrix.shape[1])
        ],
        "hard_assignment": hard.tolist(),
        "hard_counts": [int(np.sum(hard == k)) for k in range(u.shape[0])],
        "soft_mass": [float(np.sum(u[k, :])) for k in range(u.shape[0])],
    }


def ahp_weights_by_criteria(stage5_output: Dict[str, Any], criteria: List[str]) -> np.ndarray | None:
    stage5_criteria = stage5_output.get("criteria")
    weights = stage5_output.get("ahp", {}).get("weights")
    if not isinstance(stage5_criteria, list) or not isinstance(weights, list):
        return None
    if len(stage5_criteria) != len(weights):
        return None
    mapping = {str(c): float(w) for c, w in zip(stage5_criteria, weights)}
    try:
        return np.array([mapping[c] for c in criteria], dtype=float)
    except KeyError:
        return None


def compute_stage6(stage5_output: Dict[str, Any], case_data: Dict[str, Any]) -> Dict[str, Any]:
    case_name = str(stage5_output.get("case_name", "UNKNOWN"))
    criteria = list(case_data["criteria_order"])
    experts = list(case_data["expert_points_100"])
    params = dict(case_data["egk"])

    weights_matrix = points100_to_matrix(experts, criteria)
    candidates = [int(value) for value in params["M_candidates"]]
    selection = egk_select_m(weights_matrix, candidates, params)
    best = selection["best"]

    u = best["U"]
    v = best["V"]
    consensus = consensus_metrics(weights_matrix, u)
    centroid = np.array(consensus["overall_centroid"], dtype=float)

    ahp_weights = ahp_weights_by_criteria(stage5_output, criteria)
    l1_ahp_centroid = (
        float(np.sum(np.abs(ahp_weights - centroid))) if ahp_weights is not None else None
    )

    return {
        "case_name": case_name,
        "stage": "stage6_robustness_egk",
        "criteria_order": criteria,
        "X_weights_matrix_nxN": weights_matrix.tolist(),
        "egk_params": {
            "m": float(params["m"]),
            "ep": float(params["ep"]),
            "beta": float(params["beta"]),
            "max_iter": int(params["max_iter"]),
            "seed": int(params["seed"]),
        },
        "selection": {
            "M_candidates": candidates,
            "candidates": selection["candidates"],
            "best": {
                "M": int(best["M"]),
                "it": int(best["it"]),
                "err": float(best["err"]),
                "xie_beni": float(best["xie_beni"]),
                "U_MxN": u.tolist(),
                "V_nxM": v.tolist(),
            },
        },
        "consensus": consensus,
        "ahp_comparison": {
            "stage5_outputs_path": "in-memory:stage5.py",
            "ahp_weights": ahp_weights.tolist() if ahp_weights is not None else None,
            "L1_AHP_to_centroid": l1_ahp_centroid,
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


def print_stage6_tables(output: Dict[str, Any]) -> None:
    best = output["selection"]["best"]
    hard_counts = output["consensus"]["hard_counts"]
    hard_counts_text = ", ".join(f"C{k + 1}:{count}" for k, count in enumerate(hard_counts))

    summary_rows = [
        {
            "Metric": "Criteria count",
            "Value": _fmt(len(output.get("criteria_order", []))),
            "Source": "case_data",
        },
        {
            "Metric": "Experts count",
            "Value": _fmt(len(output.get("X_weights_matrix_nxN", [])[0] if output.get("X_weights_matrix_nxN") else [])),
            "Source": "case_data",
        },
        {
            "Metric": "Selected M",
            "Value": _fmt(best["M"]),
            "Source": "computed (Xie-Beni)",
        },
        {
            "Metric": "Best Xie-Beni",
            "Value": _fmt(best["xie_beni"]),
            "Source": "computed",
        },
        {"Metric": "EGK iterations", "Value": _fmt(best["it"]), "Source": "computed"},
        {"Metric": "EGK final error", "Value": _fmt(best["err"]), "Source": "computed"},
        {
            "Metric": "L1(AHP, centroid)",
            "Value": _fmt(output["ahp_comparison"]["L1_AHP_to_centroid"]),
            "Source": "stage5 + computed",
        },
        {"Metric": "Hard cluster counts", "Value": hard_counts_text, "Source": "computed"},
    ]
    summary_df = pd.DataFrame(summary_rows)
    display(_style(summary_df, "Stage 6 Summary"))


OUTPUTS: Dict[str, Dict[str, Any]] = {
    name: compute_stage6(STAGE5_OUTPUTS[name], case_data) for name, case_data in CASES.items()
}


if __name__ == "__main__":
    selected_case = "paper_prototype"
    print_stage6_tables(OUTPUTS[selected_case])
