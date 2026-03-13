from typing import Any, Dict, List

import pandas as pd
from IPython.display import display


CASES: Dict[str, Dict[str, Any]] = {
    "paper_prototype": {
        "case_name": "paper_prototype",
        "Q": 0.00064,
        "H": 0.5,
        "rho": 1000.0,
        "g": 9.81,
        "channel": {
            "A": 0.002,
            "P": 0.14,
            "L": 3.0,
            "S": 0.0,
            "n": 0.013,
            "V_override": 0.32,
            "hf_override_m": 0.0132,
        },
        "desander": {"h_des": 0.0},
        "local_losses": [
            {"Element": "Gate/Inlet", "K": 1.32205078125},
            {"Element": "Curve", "K": 0.17244140625},
            {"Element": "Contraction to tangential nozzle", "K": 0.44068359375},
            {"Element": "Vortex chamber", "K": 0.09580078125},
            {"Element": "Nozzle to impeller runner", "K": 0.2682421875},
            {"Element": "Exit/Free depth", "K": 0.17244140625},
        ],
    }
}


def compute_stage1(case_data: Dict[str, Any]) -> Dict[str, Any]:
    q = float(case_data["Q"])
    h = float(case_data["H"])
    rho = float(case_data.get("rho", 1000.0))
    g = float(case_data.get("g", 9.81))

    channel = case_data["channel"]
    area = float(channel["A"])
    perimeter = float(channel["P"])
    length = float(channel["L"])
    slope = float(channel.get("S", 0.0))
    n_manning = float(channel.get("n", 0.0))
    rh = area / perimeter

    if channel.get("V_override") is not None:
        velocity = float(channel["V_override"])
        velocity_source = "override"
    elif n_manning > 0.0 and slope > 0.0:
        velocity = (1.0 / n_manning) * (rh ** (2.0 / 3.0)) * (slope ** 0.5)
        velocity_source = "manning"
    else:
        velocity = q / area
        velocity_source = "continuity"

    if channel.get("hf_override_m") is not None:
        hf = float(channel["hf_override_m"])
        hf_source = "override"
    else:
        hf = slope * length
        hf_source = "S*L"

    h_des = float(case_data.get("desander", {}).get("h_des", 0.0))

    loss_budget: List[Dict[str, Any]] = []
    h_l_sum = 0.0
    for item in case_data.get("local_losses", []):
        k = float(item.get("K", 0.0))
        h_l = k * (velocity**2) / (2.0 * g)
        h_l_sum += h_l
        loss_budget.append({"Element": str(item["Element"]), "K": k, "V_mps": velocity, "hL_m": h_l})

    total_losses = hf + h_l_sum + h_des
    h_n = h - total_losses
    p_h = rho * g * q * h_n

    return {
        "case_name": str(case_data.get("case_name", "UNKNOWN")),
        "results": {
            "V_mps": velocity,
            "V_source": velocity_source,
            "hf_m": hf,
            "hf_source": hf_source,
            "hL_sum_m": h_l_sum,
            "h_des_m": h_des,
            "total_losses_m": total_losses,
            "Hn_m": h_n,
            "Ph_W": p_h,
        },
        "loss_budget": loss_budget,
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


def print_stage1_tables(output: Dict[str, Any]) -> None:
    r = output["results"]
    summary_rows = [
        {"Metric": "V (m/s)", "Value": _fmt(r["V_mps"]), "Source": str(r["V_source"])},
        {"Metric": "hf (m)", "Value": _fmt(r["hf_m"]), "Source": str(r["hf_source"])},
        {"Metric": "hL sum (m)", "Value": _fmt(r["hL_sum_m"]), "Source": "-"},
        {"Metric": "h_des (m)", "Value": _fmt(r["h_des_m"]), "Source": "-"},
        {"Metric": "Total losses (m)", "Value": _fmt(r["total_losses_m"]), "Source": "-"},
        {"Metric": "Hn (m)", "Value": _fmt(r["Hn_m"]), "Source": "-"},
        {"Metric": "Ph (W)", "Value": _fmt(r["Ph_W"]), "Source": "-"},
    ]
    summary_df = pd.DataFrame(summary_rows)
    display(_style(summary_df, "Hydraulic Summary"))


OUTPUTS: Dict[str, Dict[str, Any]] = {
    name: compute_stage1(case_data) for name, case_data in CASES.items()
}


if __name__ == "__main__":
    print_stage1_tables(OUTPUTS["paper_prototype"])
