from __future__ import annotations

import copy
import json
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import stage1
import stage2
import stage3
import stage4
import stage5
import stage6


ARTICLE_SOURCE_PATH = r"c:\Users\ajust\OneDrive\Escritorio\Eduardo\DarioQuintero_articulo\Articulo_IAS_2026_R4.docx"
ARTICLE_PUBLICATION_URL = ""
ARTICLE_PUBLICATION_STATUS = "Under peer review"


PLATFORM_HIGHLIGHTS: List[str] = [
    "Integrated six-stage pipeline: hydraulic -> abrasion -> reliability -> LCC -> MCDA-AHP -> EGK robustness.",
    "Reliability indicators (SAIDI, SAIFI, ENS) are embedded as operational criteria in the decision process.",
    "Economic stage evaluates CAPEX, maintenance, interruptions, and replacement in discounted present value.",
    "Final ranking is produced by AHP consistency-checked weights and validated by fuzzy clustering robustness.",
]


METHODOLOGY_STAGES: List[Dict[str, str]] = [
    {
        "stage": "Stage 1",
        "name": "Hydraulic Foundation",
        "inputs": "Flow, head, channel geometry, and local-loss coefficients.",
        "process": "Computes hydraulic losses, net head, and hydraulic power under physical constraints.",
        "outputs": "Hydraulic state variables used by all downstream decisions.",
    },
    {
        "stage": "Stage 2",
        "name": "Sediment and Abrasion",
        "inputs": "Sediment concentration, material parameters, and wear model constants.",
        "process": "Quantifies abrasion intensity and material durability performance.",
        "outputs": "Durability-linked indicators and material response basis for alternatives.",
    },
    {
        "stage": "Stage 3",
        "name": "Reliability Layer",
        "inputs": "Abrasion-driven failure rates and reliability operating assumptions.",
        "process": "Estimates SAIFI, SAIDI, ENS, and normalized reliability performance.",
        "outputs": "Operational risk metrics integrated as decision criteria.",
    },
    {
        "stage": "Stage 4",
        "name": "Life-Cycle Economics",
        "inputs": "CAPEX, maintenance behavior, interruption cost, replacement logic, and discount rate.",
        "process": "Builds discounted present-value decomposition of total life-cycle cost.",
        "outputs": "Economic ranking metrics and normalized LCC performance.",
    },
    {
        "stage": "Stage 5",
        "name": "MCDA-AHP Decision Core",
        "inputs": "Criteria matrix and stage-derived performance scores.",
        "process": "Performs AHP weighting with consistency checks and weighted score aggregation.",
        "outputs": "Transparent alternative ranking with explainable criterion influence.",
    },
    {
        "stage": "Stage 6",
        "name": "EGK Robustness Validation",
        "inputs": "Expert preference distributions and candidate cluster configurations.",
        "process": "Runs fuzzy clustering and consensus diagnostics for ranking robustness.",
        "outputs": "Robustness evidence and confidence context for final decision support.",
    },
]


ARTICLE_REFERENCE = {
    "stage1": {
        "V_mps": 0.32,
        "hf_m": 0.0132,
        "total_losses_m": 0.0261,
        "Hn_m": 0.4739,
    },
    "stage2": {"Ia_bar": 1.79e-4},
    "stage5": {
        "weights": {
            "Hydraulic": 0.285714,
            "LCC": 0.142857,
            "Durability": 0.285714,
            "Reliability": 0.285714,
        },
        "ranking": [
            "A4_HDPE_Channel_MetalSupports",
            "A1_GalvSteel_HighThkEpoxy",
            "A3_SS304_Unpainted",
            "A2_PaintedCarbonSteel",
        ],
        "top_score": 0.824502,
    },
    "stage6": {"L1_AHP_to_centroid": 0.067429, "best_M": 2},
}


OLADE_TURBINES = pd.DataFrame(
    [
        {
            "Alternative": "A1",
            "Turbine": "Pelton (micro adaptation)",
            "NetHead_m": 1.4,
            "Flow_m3s": 0.60,
            "HydraulicPower_kW": 8.24,
            "Efficiency_pct": 60,
            "ExpectedOutput_kW": 4.9,
        },
        {
            "Alternative": "A2",
            "Turbine": "Crossflow (Michel-Banki)",
            "NetHead_m": 1.2,
            "Flow_m3s": 0.90,
            "HydraulicPower_kW": 10.59,
            "Efficiency_pct": 78,
            "ExpectedOutput_kW": 8.3,
        },
        {
            "Alternative": "A3",
            "Turbine": "Axial (Propeller)",
            "NetHead_m": 1.0,
            "Flow_m3s": 1.20,
            "HydraulicPower_kW": 11.77,
            "Efficiency_pct": 84,
            "ExpectedOutput_kW": 9.9,
        },
        {
            "Alternative": "A4",
            "Turbine": "Kaplan (Low-Head)",
            "NetHead_m": 0.9,
            "Flow_m3s": 1.50,
            "HydraulicPower_kW": 13.24,
            "Efficiency_pct": 88,
            "ExpectedOutput_kW": 11.6,
        },
    ]
)


SCENARIO_WEIGHTS = {
    "Cost-dominant": {"Hydraulic": 0.20, "LCC": 0.40, "Durability": 0.20, "Reliability": 0.20},
    "Balanced": {"Hydraulic": 0.25, "LCC": 0.25, "Durability": 0.25, "Reliability": 0.25},
    "Durability-priority": {"Hydraulic": 0.20, "LCC": 0.15, "Durability": 0.45, "Reliability": 0.20},
}


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
            html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
            .block-container { padding-top: 1.0rem; padding-bottom: 1.8rem; }
            .hero {
                border-radius: 14px;
                padding: 18px 22px;
                background: radial-gradient(1200px 280px at 0% 0%, rgba(0,157,255,.23), transparent 52%),
                            linear-gradient(125deg, #0b1626 0%, #132440 58%, #203d67 100%);
                border: 1px solid rgba(54,146,255,.35);
                color: #f6fbff;
                margin-bottom: 14px;
            }
            .hero h1 { margin: 0; font-size: 1.45rem; font-weight: 700; }
            .hero p { margin: 6px 0 0 0; color: #d8e9ff; font-size: .95rem; }
            .card {
                border-radius: 12px;
                padding: 10px 12px;
                border: 1px solid #d9e4f2;
                background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
                color: #1f3550 !important;
            }
            .card b {
                color: #102941 !important;
                font-weight: 700;
            }
            .badge {
                display: inline-block;
                border: 1px solid #acc9ef;
                background: #edf5ff;
                border-radius: 999px;
                padding: 3px 10px;
                margin-right: 6px;
                margin-bottom: 6px;
                font-size: .79rem;
                color: #294766;
            }
            .method-card {
                border-radius: 12px;
                border: 1px solid #d7e4f3;
                background: linear-gradient(180deg, #ffffff 0%, #f6fbff 100%);
                padding: 12px 14px;
                margin-bottom: 10px;
                min-height: 236px;
            }
            .method-stage {
                display: inline-block;
                font-size: .75rem;
                font-weight: 700;
                letter-spacing: .04em;
                text-transform: uppercase;
                color: #1d4f85;
                background: #eaf3ff;
                border: 1px solid #c7dcf6;
                border-radius: 999px;
                padding: 2px 9px;
                margin-bottom: 8px;
            }
            .method-title {
                margin: 0 0 6px 0;
                font-size: 1.02rem;
                color: #11283e;
                font-weight: 700;
            }
            .method-line {
                margin: 0 0 7px 0;
                font-size: .84rem;
                color: #2a425d;
                line-height: 1.35;
            }
            .method-line b {
                color: #13385a;
                font-weight: 600;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_case_name() -> str:
    if "paper_prototype" in stage1.CASES:
        return "paper_prototype"
    return next(iter(stage1.CASES.keys()))


CASE_NAME = get_case_name()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return float(default)
    except TypeError:
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if pd.isna(value):
            return int(default)
    except TypeError:
        pass
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return int(default)


def _safe_str(value: Any, default: str = "") -> str:
    try:
        if pd.isna(value):
            return default
    except TypeError:
        pass
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _none_if_empty(value: Any) -> str | None:
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _editable_table(df: pd.DataFrame, key: str, num_rows: str = "dynamic") -> pd.DataFrame:
    return st.data_editor(df, hide_index=True, width="stretch", num_rows=num_rows, key=key)


def _metric_row(current: Dict[str, float], baseline: Dict[str, float], labels: Dict[str, str]) -> None:
    cols = st.columns(len(current))
    for i, (key, val) in enumerate(current.items()):
        b = baseline.get(key)
        delta = None if b is None else val - b
        cols[i].metric(labels.get(key, key), f"{val:,.6f}", None if delta is None else f"{delta:+,.6f}")


def _step_from_default(default: Any, min_step: float = 1e-6) -> float:
    base = abs(_safe_float(default, 0.0))
    step = base * 0.10
    return float(max(step, min_step))


def _int_step_from_default(default: Any, min_step: int = 1) -> int:
    base = abs(_safe_int(default, 0))
    step = int(round(base * 0.10))
    return int(max(step, min_step))


def _build_stage_inputs() -> Dict[str, Dict[str, Any]]:
    s1_default = copy.deepcopy(stage1.CASES[CASE_NAME])
    s2_default = copy.deepcopy(stage2.CASES[CASE_NAME])
    s3_default = copy.deepcopy(stage3.CASES[CASE_NAME])
    s4_default = copy.deepcopy(stage4.CASES[CASE_NAME])
    s5_default = copy.deepcopy(stage5.CASES[CASE_NAME])
    s6_default = copy.deepcopy(stage6.CASES[CASE_NAME])

    reset_table_keys = {"s1_losses", "s2_materials", "s2_alts", "s4_econ", "s5_matrix", "s5_hyd", "s6_experts"}
    st.markdown("### Stage Inputs")
    top1, top2 = st.columns([1, 3])
    with top1:
        if st.button("Load default data", key="inp_reset_defaults"):
            for k in list(st.session_state.keys()):
                if k.startswith("inp_") or k in reset_table_keys:
                    st.session_state.pop(k, None)
            st.rerun()
    with top2:
        st.caption("Interactive parameterization for all six stages. Numeric spinner increment = 10% of the original default value.")

    def _init_widget_state(key: str, value: Any) -> None:
        if key not in st.session_state:
            st.session_state[key] = value

    def _float_input(
        label: str,
        default: Any,
        key: str,
        min_value: float = 0.0,
        fmt: str = "%.6f",
        container: Any = st,
    ) -> float:
        _init_widget_state(key, float(_safe_float(default)))
        return float(
            container.number_input(
                label,
                min_value=float(min_value),
                step=_step_from_default(default),
                format=fmt,
                key=key,
            )
        )

    def _int_input(label: str, default: Any, key: str, min_value: int = 0, container: Any = st) -> int:
        _init_widget_state(key, int(_safe_int(default)))
        return int(container.number_input(label, min_value=int(min_value), step=_int_step_from_default(default), key=key))

    def _toggle_input(label: str, default: bool, key: str, container: Any = st) -> bool:
        _init_widget_state(key, bool(default))
        return bool(container.toggle(label, key=key))

    def _select_input(label: str, options: List[str], default: str, key: str, container: Any = st) -> str:
        if key not in st.session_state or st.session_state.get(key) not in options:
            st.session_state[key] = default
        return str(container.selectbox(label, options=options, key=key))

    def _text_input(label: str, default: str, key: str, container: Any = st) -> str:
        _init_widget_state(key, str(default))
        return str(container.text_input(label, key=key))

    def _multiselect_int(label: str, options: List[int], default: List[int], key: str, container: Any = st) -> List[int]:
        if key not in st.session_state:
            st.session_state[key] = list(default)
        cleaned = [int(v) for v in st.session_state.get(key, []) if int(v) in options]
        if not cleaned:
            cleaned = list(default)
            st.session_state[key] = cleaned
        vals = container.multiselect(label, options=options, key=key)
        return [int(v) for v in vals]

    with st.expander("Stage 1 - Hydraulic model", expanded=True):
        c1, c2, c3 = st.columns(3)
        q = _float_input("Q [m^3/s]", s1_default["Q"], "inp_s1_q", container=c1)
        h = _float_input("H [m]", s1_default["H"], "inp_s1_h", container=c2)
        rho = _float_input("rho [kg/m^3]", s1_default.get("rho", 1000.0), "inp_s1_rho", fmt="%.3f", container=c3)
        g = float(_safe_float(s1_default.get("g", 9.81), 9.81))
        st.caption(f"g [m/s^2] is fixed internally at {g:.4f}.")

        st.markdown("**Channel geometry**")
        ch = s1_default["channel"]
        c1, c2, c3, c4, c5 = st.columns(5)
        area = _float_input("A [m^2]", ch["A"], "inp_s1_area", container=c1)
        perimeter = _float_input("P [m]", ch["P"], "inp_s1_perimeter", container=c2)
        length = _float_input("L [m]", ch["L"], "inp_s1_length", container=c3)
        slope = _float_input("S [-]", ch.get("S", 0.0), "inp_s1_slope", container=c4)
        n_manning = _float_input("n Manning", ch.get("n", 0.013), "inp_s1_n", container=c5)

        c1, c2 = st.columns(2)
        use_v = _toggle_input("Use V override", ch.get("V_override") is not None, "inp_s1_use_v", container=c1)
        use_hf = _toggle_input("Use hf override", ch.get("hf_override_m") is not None, "inp_s1_use_hf", container=c2)

        v_override = None
        hf_override = None
        if use_v:
            v_override = _float_input("V_override [m/s]", ch.get("V_override", 0.0), "inp_s1_v_override")
        if use_hf:
            hf_override = _float_input("hf_override_m [m]", ch.get("hf_override_m", 0.0), "inp_s1_hf_override")

        h_des = _float_input("h_des [m]", s1_default.get("desander", {}).get("h_des", 0.0), "inp_s1_h_des", fmt="%.3f")

        st.markdown("**Local losses K**")
        losses_df = pd.DataFrame(s1_default["local_losses"])
        losses_edit = _editable_table(losses_df, key="s1_losses")

    with st.expander("Stage 2 - Sediment abrasion", expanded=False):
        sed = s2_default["sediments"]
        dmg = s2_default["damage_model"]
        coup = s2_default["failure_coupling"]

        c1, c2, c3 = st.columns(3)
        cs_bar = _float_input("Cs_bar", sed["Cs_bar"], "inp_s2_cs_bar", container=c1)
        k_s = _float_input("k_s", sed["k_s"], "inp_s2_k_s", container=c2)
        phi_des = _float_input("phi_des", sed["phi_des"], "inp_s2_phi_des", container=c3)

        c1, c2, c3 = st.columns(3)
        d_crit = _float_input("D_crit", dmg["D_crit"], "inp_s2_d_crit", container=c1)
        t_years_s2 = _float_input("t_years", dmg["t_years"], "inp_s2_t_years", container=c2)
        alpha_lambda_max = _float_input("alpha_lambda_max", coup["alpha_lambda_max"], "inp_s2_alpha_lambda_max", container=c3)

        st.markdown("**Materials**")
        materials_edit = _editable_table(pd.DataFrame(s2_default["materials"]), key="s2_materials")

        st.markdown("**Alternatives mapping**")
        alternatives_edit = _editable_table(pd.DataFrame(s2_default["alternatives"]), key="s2_alts")

    with st.expander("Stage 3 - Reliability", expanded=False):
        rc = s3_default["reliability_case"]
        ar = s3_default["alpha_R"]
        c1, c2, c3, c4 = st.columns(4)
        n = _float_input("N", rc["N"], "inp_s3_n", container=c1)
        u_bar_h = _float_input("U_bar_h", rc["U_bar_h"], "inp_s3_u_bar_h", container=c2)
        p_bar_kw = _float_input("P_bar_kW", rc["P_bar_kW"], "inp_s3_p_bar_kw", container=c3)
        lambda_0 = _float_input("lambda_0", rc["lambda_0"], "inp_s3_lambda_0", container=c4)

        c1, c2, c3, c4, c5 = st.columns(5)
        saidi_max = _float_input("SAIDI_max_h_per_year", ar["SAIDI_max_h_per_year"], "inp_s3_saidi_max", container=c1)
        saifi_max = _float_input("SAIFI_max_events_per_year", ar["SAIFI_max_events_per_year"], "inp_s3_saifi_max", container=c2)
        w_d = _float_input("w_D", ar["w_D"], "inp_s3_w_d", container=c3)
        w_f = _float_input("w_F", ar["w_F"], "inp_s3_w_f", container=c4)
        w_m = _float_input("w_M", ar["w_M"], "inp_s3_w_m", container=c5)

    with st.expander("Stage 4 - LCC economics", expanded=False):
        hzn = s4_default["horizon"]
        intr = s4_default["interruptions_cost"]
        maint = s4_default["maintenance_model"]
        repl = s4_default["replacement_model"]

        c1, c2 = st.columns(2)
        t_years_s4 = _int_input("T_years", hzn["T_years"], "inp_s4_t_years", min_value=1, container=c1)
        discount = _float_input("Discount rate r", hzn["r"], "inp_s4_discount", container=c2)

        c1, c2 = st.columns(2)
        ce_usd = _float_input("c_e_usd_per_kwh", intr["c_e_usd_per_kwh"], "inp_s4_ce_usd", container=c1)
        fx = _float_input("fx_COP_per_USD", intr["fx_COP_per_USD"], "inp_s4_fx", container=c2)

        c1, c2, c3 = st.columns(3)
        mode = _select_input("maintenance mode", ["cycle_lumps", "annual_uniform"], str(maint.get("mode", "cycle_lumps")), "inp_s4_mode", container=c1)
        beta_d = _float_input("beta_D", maint.get("beta_D", 0.0), "inp_s4_beta_d", container=c2)
        year_mapping = _select_input("replacement year mapping", ["round", "floor", "ceil"], _safe_str(repl.get("year_mapping", "round"), "round"), "inp_s4_year_mapping", container=c3)

        rep_fraction = _float_input("default replacement fraction", repl["rep_cost_fraction_of_CAPEX_default"], "inp_s4_rep_fraction")

        st.markdown("**Economic alternatives**")
        econ_edit = _editable_table(pd.DataFrame(s4_default["alternatives_econ"]), key="s4_econ")

    with st.expander("Stage 5 - MCDA AHP", expanded=False):
        criteria_text = _text_input("Criteria (comma separated)", ", ".join(s5_default["criteria"]), "inp_s5_criteria_text")
        criteria = [c.strip() for c in criteria_text.split(",") if c.strip()]
        if not criteria:
            criteria = list(s5_default["criteria"])
            st.warning("Criteria restored to defaults.")

        n_criteria = len(criteria)
        matrix_default = np.array(s5_default["pairwise_matrix_aggregated"], dtype=float)
        if matrix_default.shape != (n_criteria, n_criteria):
            matrix_default = np.eye(n_criteria, dtype=float)
        matrix_df = pd.DataFrame(matrix_default, columns=criteria, index=criteria)
        st.markdown("**Pairwise matrix**")
        matrix_edit = st.data_editor(matrix_df, width="stretch", key="s5_matrix")

        st.markdown("**Hydraulic scores**")
        hydraulic_edit = _editable_table(pd.DataFrame(s5_default["hydraulic_scores"]), key="s5_hyd")

    with st.expander("Stage 6 - EGK robustness", expanded=False):
        criteria_order_text = _text_input("Criteria order (comma separated)", ", ".join(s6_default["criteria_order"]), "inp_s6_criteria_order")
        criteria_order = [c.strip() for c in criteria_order_text.split(",") if c.strip()]
        if not criteria_order:
            criteria_order = list(s6_default["criteria_order"])
            st.warning("Criteria order restored to defaults.")

        st.markdown("**Experts 100-point distribution**")
        experts_edit = _editable_table(pd.DataFrame(s6_default["expert_points_100"]), key="s6_experts")

        egk = s6_default["egk"]
        c1, c2, c3, c4, c5 = st.columns(5)
        m_val = _float_input("m", egk["m"], "inp_s6_m", min_value=1.01, container=c1)
        ep_val = _float_input("ep", egk["ep"], "inp_s6_ep", container=c2)
        beta_val = _float_input("beta", egk["beta"], "inp_s6_beta", container=c3)
        max_iter_val = _int_input("max_iter", egk["max_iter"], "inp_s6_max_iter", min_value=1, container=c4)
        seed_val = _int_input("seed", egk["seed"], "inp_s6_seed", min_value=0, container=c5)

        default_candidates = [int(x) for x in egk.get("M_candidates", [2, 3])]
        m_candidates = _multiselect_int("M_candidates", [2, 3, 4, 5, 6], default_candidates, "inp_s6_m_candidates")
        if not m_candidates:
            m_candidates = default_candidates
            st.warning("M_candidates restored to defaults.")

    stage1_case = {
        "case_name": CASE_NAME,
        "Q": float(q),
        "H": float(h),
        "rho": float(rho),
        "g": float(g),
        "channel": {
            "A": float(area),
            "P": float(perimeter),
            "L": float(length),
            "S": float(slope),
            "n": float(n_manning),
            "V_override": None if v_override is None else float(v_override),
            "hf_override_m": None if hf_override is None else float(hf_override),
        },
        "desander": {"h_des": float(h_des)},
        "local_losses": [
            {"Element": _safe_str(r.get("Element"), "Element"), "K": _safe_float(r.get("K"), 0.0)}
            for r in losses_edit.to_dict("records")
            if _safe_str(r.get("Element"), "") != ""
        ],
    }

    stage2_case = {
        "sediments": {"Cs_bar": float(cs_bar), "k_s": float(k_s), "phi_des": float(phi_des)},
        "damage_model": {"D_crit": float(d_crit), "t_years": float(t_years_s2)},
        "failure_coupling": {"alpha_lambda_max": float(alpha_lambda_max)},
        "materials": [
            {"Material": _safe_str(r.get("Material"), "Material"), "k_M": _safe_float(r.get("k_M"), 0.0), "n0": _safe_float(r.get("n0"), 0.0)}
            for r in materials_edit.to_dict("records")
            if _safe_str(r.get("Material"), "") != ""
        ],
        "alternatives": [
            {"Code": _safe_str(r.get("Code"), "ALT"), "base_material": _safe_str(r.get("base_material"), ""), "coating_material": _none_if_empty(r.get("coating_material"))}
            for r in alternatives_edit.to_dict("records")
            if _safe_str(r.get("Code"), "") != ""
        ],
    }

    stage3_case = {
        "reliability_case": {"N": float(n), "U_bar_h": float(u_bar_h), "P_bar_kW": float(p_bar_kw), "lambda_0": float(lambda_0)},
        "alpha_R": {"SAIDI_max_h_per_year": float(saidi_max), "SAIFI_max_events_per_year": float(saifi_max), "w_D": float(w_d), "w_F": float(w_f), "w_M": float(w_m)},
    }

    stage4_case = {
        "horizon": {"T_years": int(t_years_s4), "r": float(discount)},
        "interruptions_cost": {"c_e_usd_per_kwh": float(ce_usd), "fx_COP_per_USD": float(fx)},
        "maintenance_model": {"mode": str(mode), "beta_D": float(beta_d)},
        "replacement_model": {"rep_cost_fraction_of_CAPEX_default": float(rep_fraction), "year_mapping": str(year_mapping)},
        "alternatives_econ": [
            {"Code": _safe_str(r.get("Code"), "ALT"), "CAPEX_COP": _safe_float(r.get("CAPEX_COP"), 0.0), "OpEx_10_years_COP": _safe_float(r.get("OpEx_10_years_COP"), 0.0), "Maintenance_years": _safe_float(r.get("Maintenance_years"), 0.0), "Service_life_years": _safe_float(r.get("Service_life_years"), 0.0), "rep_cost_fraction_of_CAPEX": _safe_float(r.get("rep_cost_fraction_of_CAPEX"), float(rep_fraction))}
            for r in econ_edit.to_dict("records")
            if _safe_str(r.get("Code"), "") != ""
        ],
    }

    stage5_case = {
        "criteria": criteria,
        "pairwise_matrix_aggregated": pd.DataFrame(matrix_edit).astype(float).values.tolist(),
        "hydraulic_scores": [
            {"Code": _safe_str(r.get("Code"), "ALT"), "Hydraulic_score": _safe_float(r.get("Hydraulic_score"), 0.0)}
            for r in hydraulic_edit.to_dict("records")
            if _safe_str(r.get("Code"), "") != ""
        ],
    }

    stage6_case = {
        "criteria_order": criteria_order,
        "expert_points_100": [{k: (_safe_float(v) if k != "Expert" else _safe_str(v, "E")) for k, v in r.items()} for r in experts_edit.to_dict("records") if _safe_str(r.get("Expert"), "") != ""],
        "egk": {"m": float(m_val), "ep": float(ep_val), "beta": float(beta_val), "max_iter": int(max_iter_val), "M_candidates": [int(v) for v in sorted(set(m_candidates))], "seed": int(seed_val)},
    }

    return {"stage1": stage1_case, "stage2": stage2_case, "stage3": stage3_case, "stage4": stage4_case, "stage5": stage5_case, "stage6": stage6_case}


def run_pipeline(stage_inputs: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    s1 = stage1.compute_stage1(stage_inputs["stage1"])
    s2 = stage2.compute_stage2(s1, stage_inputs["stage2"])
    s3 = stage3.compute_stage3(s1, s2, stage_inputs["stage3"])
    s4 = stage4.compute_stage4(s2, s3, stage_inputs["stage4"])
    s5 = stage5.compute_stage5(s2, s3, s4, stage_inputs["stage5"])
    s6 = stage6.compute_stage6(s5, stage_inputs["stage6"])
    return {"stage1": s1, "stage2": s2, "stage3": s3, "stage4": s4, "stage5": s5, "stage6": s6}


def baseline_outputs() -> Dict[str, Dict[str, Any]]:
    return {
        "stage1": copy.deepcopy(stage1.OUTPUTS[CASE_NAME]),
        "stage2": copy.deepcopy(stage2.OUTPUTS[CASE_NAME]),
        "stage3": copy.deepcopy(stage3.OUTPUTS[CASE_NAME]),
        "stage4": copy.deepcopy(stage4.OUTPUTS[CASE_NAME]),
        "stage5": copy.deepcopy(stage5.OUTPUTS[CASE_NAME]),
        "stage6": copy.deepcopy(stage6.OUTPUTS[CASE_NAME]),
    }


def render_header() -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>HydroMaterials Decision Intelligence</h1>
            <p>Multi-criteria optimization of materials for small hydropower, integrating hydraulic, energy, reliability, and life-cycle cost analysis.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overview_context(current: Dict[str, Dict[str, Any]] | None, base: Dict[str, Dict[str, Any]] | None) -> None:
    _ = (current, base)
    st.subheader("Model Overview and Methodology")

    c1, c2, c3 = st.columns(3)
    c1.markdown(
        """
        <div class="card">
            <b>Problem</b><br/>
            Low-head SHP selection requires balancing hydraulic behavior, durability, reliability, and long-term cost under uncertainty.
        </div>
        """,
        unsafe_allow_html=True,
    )
    c2.markdown(
        """
        <div class="card">
            <b>Approach</b><br/>
            A six-stage computational workflow links physics, economics, multi-criteria ranking, and robustness validation in one traceable pipeline.
        </div>
        """,
        unsafe_allow_html=True,
    )
    c3.markdown(
        """
        <div class="card">
            <b>Value</b><br/>
            Decision-makers can evaluate alternatives consistently, explain criteria trade-offs, and justify final selection with confidence.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if ARTICLE_PUBLICATION_URL.strip():
        st.markdown(f"**Technical reference source:** [Published article]({ARTICLE_PUBLICATION_URL.strip()})")
    else:
        st.info("Technical reference source: published article URL will be provided here (currently under peer review).")
    st.caption(f"Publication status: {ARTICLE_PUBLICATION_STATUS}.")

    badges = "".join([f'<span class="badge">{line}</span>' for line in PLATFORM_HIGHLIGHTS])
    st.markdown(badges, unsafe_allow_html=True)

    st.markdown("### End-to-End Methodology (Stage 1 to Stage 6)")
    st.caption("Overview tab intentionally shows methodology only. Numerical results are available in the other tabs.")
    row_size = 3
    for start in range(0, len(METHODOLOGY_STAGES), row_size):
        cols = st.columns(row_size)
        for idx, item in enumerate(METHODOLOGY_STAGES[start : start + row_size]):
            cols[idx].markdown(
                f"""
                <div class="method-card">
                    <div class="method-stage">{item["stage"]}</div>
                    <p class="method-title">{item["name"]}</p>
                    <p class="method-line"><b>Input:</b> {item["inputs"]}</p>
                    <p class="method-line"><b>Process:</b> {item["process"]}</p>
                    <p class="method-line"><b>Output:</b> {item["outputs"]}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### How to Use This Platform")
    p1, p2, p3 = st.columns(3)
    p1.markdown(
        """
        <div class="card">
            <b>1) Configure Inputs</b><br/>
            Use the Inputs tab to set hydraulic, material, reliability, economic, and decision parameters.
        </div>
        """,
        unsafe_allow_html=True,
    )
    p2.markdown(
        """
        <div class="card">
            <b>2) Run Integrated Pipeline</b><br/>
            The platform automatically executes Stages 1-6 and propagates dependencies across all computations.
        </div>
        """,
        unsafe_allow_html=True,
    )
    p3.markdown(
        f"""
        <div class="card">
            <b>3) Review Decision Evidence</b><br/>
            Explore outputs in Results, App_MHS Figures, and Sensitivity tabs for technical and robustness analysis.
            <br/><br/><b>Publication status:</b> {ARTICLE_PUBLICATION_STATUS}.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary(current: Dict[str, Dict[str, Any]], base: Dict[str, Dict[str, Any]]) -> None:
    st.subheader("Executive summary")
    best_curr = current["stage5"]["alternatives"][0]
    best_base = base["stage5"]["alternatives"][0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Top alternative (Current)", best_curr["Code"])
    c2.metric("Current score", f"{best_curr['S_weighted']:.4f}")
    c3.metric("Top alternative (Base)", best_base["Code"])
    c4.metric("Base score", f"{best_base['S_weighted']:.4f}", f"{best_curr['S_weighted'] - best_base['S_weighted']:+.4f}")

    _metric_row(
        {"Ph_W": current["stage1"]["results"]["Ph_W"], "Ia_bar": current["stage2"]["Ia_bar"], "alpha_R": current["stage3"]["alternatives"][0]["alpha_R"], "LCC_tilde": current["stage4"]["alternatives"][0]["LCC_tilde"]},
        {"Ph_W": base["stage1"]["results"]["Ph_W"], "Ia_bar": base["stage2"]["Ia_bar"], "alpha_R": base["stage3"]["alternatives"][0]["alpha_R"], "LCC_tilde": base["stage4"]["alternatives"][0]["LCC_tilde"]},
        {"Ph_W": "Hydraulic power [W]", "Ia_bar": "Abrasion intensity", "alpha_R": "Top reliability", "LCC_tilde": "Top economic index"},
    )


def render_stage_results(current: Dict[str, Dict[str, Any]], base: Dict[str, Dict[str, Any]]) -> None:
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Stage 1", "Stage 2", "Stage 3", "Stage 4", "Stage 5", "Stage 6"])

    with tab1:
        st.markdown("**Hydraulic outputs and loss budget**")
        r = current["stage1"]["results"]
        rb = base["stage1"]["results"]
        _metric_row({"V_mps": r["V_mps"], "hf_m": r["hf_m"], "Hn_m": r["Hn_m"], "Ph_W": r["Ph_W"]}, {"V_mps": rb["V_mps"], "hf_m": rb["hf_m"], "Hn_m": rb["Hn_m"], "Ph_W": rb["Ph_W"]}, {"V_mps": "V [m/s]", "hf_m": "hf [m]", "Hn_m": "Hn [m]", "Ph_W": "Ph [W]"})
        loss_df = pd.DataFrame(current["stage1"]["loss_budget"])
        if not loss_df.empty:
            fig = px.bar(loss_df.sort_values("hL_m", ascending=False), x="Element", y="hL_m", color="K", title="Local head losses per element")
            fig.update_layout(height=380, xaxis_title="", yaxis_title="hL [m]")
            st.plotly_chart(fig, width="stretch")
            st.dataframe(loss_df, width="stretch")

    with tab2:
        st.markdown("**Sediment abrasion and durability**")
        mats_df = pd.DataFrame(current["stage2"]["materials"])
        alts_df = pd.DataFrame(current["stage2"]["alternatives"])
        if not mats_df.empty:
            fig = px.bar(mats_df.sort_values("T_eff_tilde", ascending=False), x="Material", y="T_eff_tilde", color="alpha_mat", title="Durability normalized index (T_eff_tilde)")
            fig.update_layout(height=360, xaxis_title="", yaxis_title="T_eff_tilde")
            st.plotly_chart(fig, width="stretch")
            st.dataframe(mats_df, width="stretch")
        if not alts_df.empty:
            st.markdown("**Alternatives mapping to abrasive control surface**")
            st.dataframe(alts_df, width="stretch")

    with tab3:
        st.markdown("**Reliability indicators from degradation coupling**")
        alts_df = pd.DataFrame(current["stage3"]["alternatives"])
        if not alts_df.empty:
            fig = px.bar(alts_df.sort_values("alpha_R", ascending=False), x="Code", y="alpha_R", color="ENS_kWh_per_year", title="alpha_R by alternative (color = ENS)")
            fig.update_layout(height=360, xaxis_title="", yaxis_title="alpha_R")
            st.plotly_chart(fig, width="stretch")
            st.dataframe(alts_df, width="stretch")

    with tab4:
        st.markdown("**Life-cycle cost decomposition and normalized economic performance**")
        alts_df = pd.DataFrame(current["stage4"]["alternatives"])
        if not alts_df.empty:
            stack_df = alts_df[["Code", "CAPEX_COP", "PV_maint_COP", "PV_int_COP", "PV_rep_COP"]].melt(id_vars="Code", var_name="Component", value_name="COP")
            fig_stack = px.bar(stack_df, x="Code", y="COP", color="Component", title="Discounted cost decomposition")
            fig_stack.update_layout(height=390, xaxis_title="", yaxis_title="COP")
            st.plotly_chart(fig_stack, width="stretch")

            fig_norm = px.bar(alts_df.sort_values("LCC_tilde", ascending=False), x="Code", y="LCC_tilde", color="LCC_COP", title="Economic normalized score (LCC_tilde)")
            fig_norm.update_layout(height=350, xaxis_title="", yaxis_title="LCC_tilde")
            st.plotly_chart(fig_norm, width="stretch")
            st.dataframe(alts_df, width="stretch")

    with tab5:
        st.markdown("**AHP consistency and final MCDA ranking**")
        ahp = current["stage5"]["ahp"]
        criteria = current["stage5"]["criteria"]
        w_df = pd.DataFrame({"Criterion": criteria, "Weight": ahp["weights"]})

        c1, c2, c3 = st.columns(3)
        c1.metric("lambda_max", f"{ahp['lambda_max']:.6f}")
        c2.metric("CI", f"{ahp['CI']:.6f}")
        c3.metric("CR", f"{ahp['CR']:.6f}")

        fig_w = px.bar(w_df.sort_values("Weight", ascending=False), x="Criterion", y="Weight", title="AHP weights")
        fig_w.update_layout(height=330, xaxis_title="", yaxis_title="Weight")
        st.plotly_chart(fig_w, width="stretch")

        rank_df = pd.DataFrame(current["stage5"]["alternatives"])
        if not rank_df.empty:
            fig_r = px.bar(rank_df.sort_values("S_weighted", ascending=True), x="S_weighted", y="Code", orientation="h", color="Ranking", title="Weighted MCDA score ranking")
            fig_r.update_layout(height=420, xaxis_title="S_weighted", yaxis_title="")
            st.plotly_chart(fig_r, width="stretch")
            st.dataframe(rank_df, width="stretch")

    with tab6:
        st.markdown("**EGK robustness verification**")
        best = current["stage6"]["selection"]["best"]
        candidates_df = pd.DataFrame(current["stage6"]["selection"]["candidates"])
        if not candidates_df.empty:
            fig_c = px.line(candidates_df.sort_values("M"), x="M", y="xie_beni", markers=True, title="Xie-Beni by candidate M")
            fig_c.update_layout(height=320)
            st.plotly_chart(fig_c, width="stretch")

        u = np.array(best["U_MxN"], dtype=float)
        if u.size > 0:
            experts = [f"E{i+1}" for i in range(u.shape[1])]
            clusters = [f"C{i+1}" for i in range(u.shape[0])]
            heat = go.Figure(data=go.Heatmap(z=u, x=experts, y=clusters, colorscale="Blues", colorbar={"title": "u(k,i)"}))
            heat.update_layout(title="Fuzzy membership matrix U", height=380)
            st.plotly_chart(heat, width="stretch")

        cons = current["stage6"]["consensus"]
        l1 = current["stage6"]["ahp_comparison"]["L1_AHP_to_centroid"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Selected M", int(best["M"]))
        c2.metric("Best Xie-Beni", f"{best['xie_beni']:.6f}")
        c3.metric("L1(AHP, centroid)", "N/A" if l1 is None else f"{l1:.6f}")
        st.dataframe(pd.DataFrame({"Hard counts": cons["hard_counts"], "Soft mass": cons["soft_mass"]}), width="stretch")


def _score_df(stage5_output: Dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame([{"Code": row["Code"], "Score": float(row["S_weighted"]), "Ranking": int(row["Ranking"])} for row in stage5_output.get("alternatives", [])])


def render_app_mhs_charts(current: Dict[str, Dict[str, Any]], base: Dict[str, Dict[str, Any]]) -> None:
    st.subheader("App_MHS visual set mapped to Stage 1-6")
    st.caption("The four core chart styles from App_MHS are placed as base/current comparative views.")

    base_rank = _score_df(base["stage5"])
    curr_rank = _score_df(current["stage5"])
    if base_rank.empty or curr_rank.empty:
        st.info("No alternatives available for comparison.")
        return

    merged = base_rank[["Code", "Score"]].rename(columns={"Score": "Base"}).merge(curr_rank[["Code", "Score"]].rename(columns={"Score": "Current"}), on="Code", how="outer").fillna(0.0)

    c1, c2 = st.columns([1.25, 1.0])
    with c1:
        best_base = base["stage5"]["alternatives"][0]
        best_curr = current["stage5"]["alternatives"][0]
        criteria = current["stage5"]["criteria"]
        base_vals = [float(best_base["scores"].get(c, 0.0)) for c in criteria]
        curr_vals = [float(best_curr["scores"].get(c, 0.0)) for c in criteria]
        close = criteria + [criteria[0]]

        radar = go.Figure()
        radar.add_trace(go.Scatterpolar(r=base_vals + [base_vals[0]], theta=close, fill="toself", name="Base Best", opacity=0.35))
        radar.add_trace(go.Scatterpolar(r=curr_vals + [curr_vals[0]], theta=close, fill="toself", name="Current Best", opacity=0.55, line={"width": 3}))
        radar.update_layout(title="Criteria radar: Base Best vs Current Best", polar={"radialaxis": {"visible": True, "range": [0, 1]}}, height=440)
        st.plotly_chart(radar, width="stretch")

    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**Decision spotlight**")
        st.write(f"Base winner: `{base['stage5']['alternatives'][0]['Code']}`")
        st.write(f"Current winner: `{current['stage5']['alternatives'][0]['Code']}`")
        margin_b = base["stage5"]["alternatives"][0]["S_weighted"] - base["stage5"]["alternatives"][1]["S_weighted"] if len(base["stage5"]["alternatives"]) > 1 else 0.0
        margin_c = current["stage5"]["alternatives"][0]["S_weighted"] - current["stage5"]["alternatives"][1]["S_weighted"] if len(current["stage5"]["alternatives"]) > 1 else 0.0
        st.metric("Margin Top1-Top2 Base", f"{margin_b:.4f}")
        st.metric("Margin Top1-Top2 Current", f"{margin_c:.4f}")
        st.markdown("</div>", unsafe_allow_html=True)

    fig_rank = go.Figure()
    fig_rank.add_trace(go.Bar(x=merged["Code"], y=merged["Base"], name="Base", opacity=0.45))
    fig_rank.add_trace(go.Bar(x=merged["Code"], y=merged["Current"], name="Current", opacity=0.90))
    fig_rank.update_layout(title="Ranking by alternative (Base vs Current)", barmode="group", height=420, yaxis_title="MCDA Score")
    st.plotly_chart(fig_rank, width="stretch")

    base_s3 = pd.DataFrame(base["stage3"]["alternatives"])[["Code", "lambda_Mi_events_per_year", "alpha_R"]]
    base_s4 = pd.DataFrame(base["stage4"]["alternatives"])[["Code", "LCC_COP", "LCC_tilde"]]
    curr_s3 = pd.DataFrame(current["stage3"]["alternatives"])[["Code", "lambda_Mi_events_per_year", "alpha_R"]]
    curr_s4 = pd.DataFrame(current["stage4"]["alternatives"])[["Code", "LCC_COP", "LCC_tilde"]]
    perf_base = base_s3.merge(base_s4, on="Code", how="inner")
    perf_curr = curr_s3.merge(curr_s4, on="Code", how="inner")
    perf_base["Scenario"] = "Base"
    perf_curr["Scenario"] = "Current"
    perf = pd.concat([perf_base, perf_curr], ignore_index=True)

    if not perf.empty:
        perf_fig = px.scatter(perf, x="LCC_COP", y="lambda_Mi_events_per_year", color="Scenario", symbol="Scenario", size="alpha_R", hover_data=["Code", "LCC_tilde", "alpha_R"], title="Alternatives performance plane: LCC vs failure rate")
        perf_fig.update_layout(height=450, xaxis_title="LCC [COP]", yaxis_title="lambda_Mi [events/year]")
        st.plotly_chart(perf_fig, width="stretch")

    top_n = 10
    base_top = base_rank.sort_values("Score", ascending=False).head(top_n)["Code"].tolist()
    curr_top = curr_rank.sort_values("Score", ascending=False).head(top_n)["Code"].tolist()
    chosen = list(dict.fromkeys(curr_top + base_top))
    dm = merged[merged["Code"].isin(chosen)].copy()
    dm["mx"] = dm[["Base", "Current"]].max(axis=1)
    dm = dm.sort_values("mx", ascending=False).drop(columns="mx").reset_index(drop=True)
    dm["y"] = np.arange(len(dm))

    dumbbell = go.Figure()
    for _, row in dm.iterrows():
        dumbbell.add_shape(type="line", x0=row["Base"], y0=row["y"], x1=row["Current"], y1=row["y"], line={"color": "rgba(50,50,50,.33)", "width": 2})
    dumbbell.add_trace(go.Scatter(x=dm["Base"], y=dm["y"], mode="markers", marker={"size": 11, "symbol": "circle-open", "line": {"width": 2}}, name="Base", text=dm["Code"], hovertemplate="Code=%{text}<br>Base=%{x:.4f}<extra></extra>"))
    dumbbell.add_trace(go.Scatter(x=dm["Current"], y=dm["y"], mode="markers", marker={"size": 14, "symbol": "circle", "line": {"width": 1}}, name="Current", text=dm["Code"], hovertemplate="Code=%{text}<br>Current=%{x:.4f}<extra></extra>"))
    dumbbell.update_layout(title="Top alternatives dumbbell comparison", height=500, yaxis={"tickmode": "array", "tickvals": dm["y"], "ticktext": dm["Code"], "autorange": "reversed"}, xaxis_title="MCDA Score")
    st.plotly_chart(dumbbell, width="stretch")


def _pareto_front(df: pd.DataFrame, x_col: str, y_col: str, minimize_x: bool = True, maximize_y: bool = True) -> pd.Series:
    x = df[x_col].to_numpy(dtype=float)
    y = df[y_col].to_numpy(dtype=float)
    dominated = np.zeros(len(df), dtype=bool)
    for i in range(len(df)):
        for j in range(len(df)):
            if i == j:
                continue
            better_x = x[j] <= x[i] if minimize_x else x[j] >= x[i]
            better_y = y[j] >= y[i] if maximize_y else y[j] <= y[i]
            strictly = (x[j] < x[i] if minimize_x else x[j] > x[i]) or (y[j] > y[i] if maximize_y else y[j] < y[i])
            if better_x and better_y and strictly:
                dominated[i] = True
                break
    return pd.Series(~dominated, index=df.index)


def _scenario_scores(stage5_output: Dict[str, Any], weights_map: Dict[str, float]) -> pd.DataFrame:
    source = stage5_output.get("source_scores", {})
    criteria = list(stage5_output.get("criteria", []))
    by_code: Dict[str, Dict[str, float]] = {}
    for crit in criteria:
        crit_map = source.get(crit, {})
        for code, val in crit_map.items():
            by_code.setdefault(str(code), {})[crit] = float(val)

    rows = []
    for code, crit_vals in by_code.items():
        used_weights = []
        used_values = []
        for crit in criteria:
            if crit in weights_map and crit in crit_vals:
                used_weights.append(float(weights_map[crit]))
                used_values.append(float(crit_vals[crit]))
        if not used_weights:
            continue
        sw = float(sum(used_weights))
        if sw <= 0:
            continue
        used_weights = [w / sw for w in used_weights]
        score = float(sum(w * v for w, v in zip(used_weights, used_values)))
        rows.append({"Code": code, "Score": score})

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out.sort_values("Score", ascending=False).reset_index(drop=True)
    out["Rank"] = np.arange(1, len(out) + 1)
    return out


def _norm_series(values: pd.Series) -> pd.Series:
    vals = values.astype(float)
    vmin = float(vals.min())
    vmax = float(vals.max())
    if vmax == vmin:
        return pd.Series([0.5] * len(vals), index=vals.index, dtype=float)
    return (vals - vmin) / (vmax - vmin)


def _build_dynamic_material_df(current: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    s2m = pd.DataFrame(current["stage2"]["materials"]).copy()
    s3m = pd.DataFrame(current["stage3"]["materials"]).copy()
    s4a = pd.DataFrame(current["stage4"]["alternatives"]).copy()

    if s2m.empty:
        return s2m

    mat = s2m.merge(s3m[["Material", "alpha_R", "ENS_kWh_per_year"]], on="Material", how="left")

    lcc_map = s4a.groupby("abrasive_control_surface", as_index=False)["LCC_COP"].mean()
    lcc_map = lcc_map.rename(columns={"abrasive_control_surface": "Material", "LCC_COP": "LCC_material_COP"})
    capex_map = s4a.groupby("abrasive_control_surface", as_index=False)["CAPEX_COP"].mean()
    capex_map = capex_map.rename(columns={"abrasive_control_surface": "Material", "CAPEX_COP": "CAPEX_material_COP"})

    mat = mat.merge(lcc_map, on="Material", how="left")
    mat = mat.merge(capex_map, on="Material", how="left")

    if mat["LCC_material_COP"].isna().any():
        fallback = float(s4a["LCC_COP"].median()) if not s4a.empty else 1.0
        k_norm = _norm_series(mat["k_M"])
        mat["LCC_material_COP"] = mat["LCC_material_COP"].fillna(fallback * (1.0 + 0.45 * k_norm))

    if mat["CAPEX_material_COP"].isna().any():
        fallback_capex = float(s4a["CAPEX_COP"].median()) if not s4a.empty else 1.0
        n_norm = _norm_series(mat["n0"])
        mat["CAPEX_material_COP"] = mat["CAPEX_material_COP"].fillna(fallback_capex * (1.15 - 0.25 * n_norm))

    lcc_min = max(float(mat["LCC_material_COP"].min()), 1e-12)
    mat["LCC_pu"] = mat["LCC_material_COP"] / lcc_min

    n_norm = _norm_series(mat["n0"])
    mat["HydLoss_pu"] = 0.10 + 0.18 * n_norm
    mat["Durability_pu"] = 0.65 + 0.30 * mat["T_eff_tilde"].astype(float)
    mat["Efficiency_pu"] = 0.90 - 0.30 * n_norm
    mat["DurabilityScore_pu"] = 0.70 + 0.22 * mat["T_eff_tilde"].astype(float)

    capex_inv = 1.0 / mat["CAPEX_material_COP"].astype(float)
    capex_inv_norm = _norm_series(capex_inv)
    mat["Manufacturability_pu"] = 0.60 + 0.30 * capex_inv_norm

    mat["MaterialCode"] = mat["Material"].astype(str).str.extract(r"^(M\d+)")[0].fillna(mat["Material"])
    mat["Label"] = mat["Material"].astype(str).str.replace("_", " ")
    return mat


def _build_dynamic_turbine_df(current: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    src = current["stage5"]["source_scores"]
    codes = sorted({str(c) for m in src.values() for c in m.keys()})
    if not codes:
        return pd.DataFrame()

    code_to_turbine = {
        "A1_GalvSteel_HighThkEpoxy": "Pelton",
        "A2_PaintedCarbonSteel": "Francis",
        "A3_SS304_Unpainted": "Banki",
        "A4_HDPE_Channel_MetalSupports": "Axial/Kaplan",
    }

    rows = []
    for code in codes:
        h = float(src.get("Hydraulic", {}).get(code, np.nan))
        lcc = float(src.get("LCC", {}).get(code, np.nan))
        dur = float(src.get("Durability", {}).get(code, np.nan))
        rel = float(src.get("Reliability", {}).get(code, np.nan))
        part = 0.5 * (dur + rel) if np.isfinite(dur) and np.isfinite(rel) else np.nan

        rows.append(
            {
                "Code": code,
                "TurbineType": code_to_turbine.get(code, code),
                "Efficiency": h,
                "Cost(1/CAPEX)": lcc,
                "Flow Flexibility (HQ)": rel,
                "Durability": dur,
                "Partial Load": part,
            }
        )
    return pd.DataFrame(rows)


def _build_dynamic_weight_scenarios(current: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    criteria = [str(c) for c in current["stage5"].get("criteria", [])]
    weights = [float(w) for w in current["stage5"].get("ahp", {}).get("weights", [])]
    if not criteria or len(criteria) != len(weights):
        return pd.DataFrame()

    base = {c: w for c, w in zip(criteria, weights)}
    n = len(criteria)

    def normalized_map(raw: Dict[str, float]) -> Dict[str, float]:
        total = sum(max(v, 0.0) for v in raw.values())
        if total <= 0:
            return {k: 1.0 / len(raw) for k in raw}
        return {k: max(v, 0.0) / total for k, v in raw.items()}

    def boost(target: str | None, boost_value: float) -> Dict[str, float]:
        vals = dict(base)
        if target in vals:
            vals[target] = vals[target] + boost_value
        return normalized_map(vals)

    lcc_key = next((c for c in criteria if c.lower() == "lcc"), None)
    dur_key = next((c for c in criteria if c.lower() == "durability"), None)

    cost_dom = boost(lcc_key, 0.20)
    balanced = {c: 1.0 / n for c in criteria}
    dur_prio = boost(dur_key, 0.20)

    labels = []
    for c in criteria:
        low = c.lower()
        if low == "reliability":
            labels.append("Delivery")
        else:
            labels.append(c)

    return pd.DataFrame(
        {
            "Criteria": labels,
            "Cost-dominant": [cost_dom[c] for c in criteria],
            "Balanced": [balanced[c] for c in criteria],
            "Durability-priority": [dur_prio[c] for c in criteria],
        }
    )


def render_dynamic_article_figures(current: Dict[str, Dict[str, Any]]) -> None:
    st.markdown("**Dynamic Reproduction of Figures 6-10 (Driven by Stage Outputs)**")
    st.caption("All plots below are recomputed from Stage 1-6 outputs on every input change.")

    mat = _build_dynamic_material_df(current)
    if mat.empty:
        st.info("No material data available from current stage outputs.")
        return

    c1, c2 = st.columns(2)

    with c1:
        f6 = mat[["MaterialCode", "Label", "LCC_pu", "HydLoss_pu"]].copy()
        pareto_mask = _pareto_front(f6.rename(columns={"LCC_pu": "x", "HydLoss_pu": "y"}), "x", "y", minimize_x=True, maximize_y=False)
        f6["Pareto"] = pareto_mask
        fig6 = px.scatter(f6, x="LCC_pu", y="HydLoss_pu", text="MaterialCode", color="Pareto", symbol="Pareto", title="Fig. 6 Dynamic - Pareto front (Hydraulic Loss vs LCC)")
        fig6.update_traces(textposition="top center")
        fig6.update_layout(xaxis_title="Life Cycle Cost (p.u.)", yaxis_title="Hydraulic Loss (p.u.)", height=430)
        st.plotly_chart(fig6, width="stretch")

    with c2:
        f7 = mat[["MaterialCode", "Efficiency_pu", "DurabilityScore_pu", "Manufacturability_pu"]].copy()
        f7m = f7.melt(id_vars="MaterialCode", var_name="Metric", value_name="Score")
        f7m["Metric"] = f7m["Metric"].map({"Efficiency_pu": "Efficiency", "DurabilityScore_pu": "Durability", "Manufacturability_pu": "Manufacturability"})
        fig7 = px.bar(f7m, x="MaterialCode", y="Score", color="Metric", barmode="group", title="Fig. 7 Dynamic - Comparison of key materials")
        fig7.update_layout(xaxis_title="Materials", yaxis_title="Score (p.u.)", height=430)
        st.plotly_chart(fig7, width="stretch")

    c3, c4 = st.columns(2)
    with c3:
        f8 = mat[["MaterialCode", "LCC_pu", "Durability_pu"]].copy()
        pareto_mask8 = _pareto_front(f8.rename(columns={"LCC_pu": "x", "Durability_pu": "y"}), "x", "y", minimize_x=True, maximize_y=True)
        f8["Pareto"] = pareto_mask8
        fig8 = px.scatter(f8, x="LCC_pu", y="Durability_pu", text="MaterialCode", color="Pareto", symbol="Pareto", title="Fig. 8 Dynamic - Pareto material optimization")
        fig8.update_traces(textposition="top center")
        fig8.update_layout(xaxis_title="Life-Cycle Cost (p.u.)", yaxis_title="Material Durability (p.u.)", height=430)
        st.plotly_chart(fig8, width="stretch")

    with c4:
        turb = _build_dynamic_turbine_df(current)
        if turb.empty:
            st.info("No alternative criteria available for dynamic Fig. 9.")
        else:
            f9m = turb.melt(id_vars=["Code", "TurbineType"], var_name="Criterion", value_name="Value")
            fig9 = px.bar(f9m, x="TurbineType", y="Value", color="Criterion", barmode="group", title="Fig. 9 Dynamic - Comparison by MCDA criteria")
            fig9.update_layout(xaxis_title="Turbine Type", yaxis_title="Normalized Criteria (p.u.)", height=430)
            st.plotly_chart(fig9, width="stretch")

    wdf = _build_dynamic_weight_scenarios(current)
    if not wdf.empty:
        f10m = wdf.melt(id_vars="Criteria", var_name="Scenario", value_name="Weight")
        fig10 = px.bar(f10m, x="Criteria", y="Weight", color="Scenario", barmode="group", title="Fig. 10 Dynamic - MCDA weighting scenarios")
        fig10.update_layout(xaxis_title="Criteria", yaxis_title="Relative Weight (p.u.)", height=430)
        st.plotly_chart(fig10, width="stretch")


def render_sensitivity_and_olade(current: Dict[str, Dict[str, Any]]) -> None:
    st.subheader("Sensitivity, Pareto, and OLADE contextual comparison")
    render_dynamic_article_figures(current)

    c1, c2 = st.columns(2)
    with c1:
        fig_olade = px.scatter(
            OLADE_TURBINES,
            x="Flow_m3s",
            y="NetHead_m",
            size="ExpectedOutput_kW",
            color="Efficiency_pct",
            hover_name="Turbine",
            text="Alternative",
            title="OLADE turbine envelope (article contextual table)",
        )
        fig_olade.update_traces(textposition="top center")
        fig_olade.update_layout(height=420, xaxis_title="Flow [m^3/s]", yaxis_title="Net head [m]")
        st.plotly_chart(fig_olade, width="stretch")

    with c2:
        fig_olade2 = px.bar(
            OLADE_TURBINES.sort_values("ExpectedOutput_kW", ascending=False),
            x="Alternative",
            y="ExpectedOutput_kW",
            color="Turbine",
            title="Expected output by OLADE alternative",
        )
        fig_olade2.update_layout(height=420, xaxis_title="", yaxis_title="Expected Output [kW]")
        st.plotly_chart(fig_olade2, width="stretch")

    alts4 = pd.DataFrame(current["stage4"]["alternatives"])
    src = current["stage5"]["source_scores"]
    hyd_map = src.get("Hydraulic", {})
    if not alts4.empty and hyd_map:
        pareto_df = alts4[["Code", "LCC_COP"]].copy()
        pareto_df["Hydraulic"] = pareto_df["Code"].map(lambda c: float(hyd_map.get(c, np.nan)))
        pareto_df = pareto_df.dropna()
        if not pareto_df.empty:
            pareto_df["Pareto"] = _pareto_front(pareto_df, "LCC_COP", "Hydraulic", minimize_x=True, maximize_y=True)
            fig_p = px.scatter(
                pareto_df,
                x="LCC_COP",
                y="Hydraulic",
                color="Pareto",
                text="Code",
                title="Pareto front (Economic cost vs Hydraulic score)",
            )
            fig_p.update_traces(textposition="top center")
            fig_p.update_layout(height=430, xaxis_title="LCC [COP]", yaxis_title="Hydraulic score")
            st.plotly_chart(fig_p, width="stretch")

    st.markdown("**MCDA weighting scenarios (article Figure 10 style)**")
    scenario_rows = []
    for name, w_map in SCENARIO_WEIGHTS.items():
        s_df = _scenario_scores(current["stage5"], w_map)
        if s_df.empty:
            continue
        for _, r in s_df.iterrows():
            scenario_rows.append({"Scenario": name, "Code": r["Code"], "Score": r["Score"], "Rank": int(r["Rank"])})

    scenario_df = pd.DataFrame(scenario_rows)
    if not scenario_df.empty:
        fig_s = px.bar(
            scenario_df,
            x="Code",
            y="Score",
            color="Code",
            animation_frame="Scenario",
            range_y=[0, max(1.0, float(scenario_df["Score"].max()) * 1.12)],
            title="Sensitivity animation across weighting scenarios",
        )
        fig_s.update_layout(height=470, showlegend=False)
        st.plotly_chart(fig_s, width="stretch")

        top_by_s = scenario_df.sort_values(["Scenario", "Score"], ascending=[True, False]).groupby("Scenario").head(1)
        st.dataframe(top_by_s[["Scenario", "Code", "Score", "Rank"]], width="stretch")


def render_robustness_tables(current: Dict[str, Dict[str, Any]]) -> None:
    st.subheader("Supplementary robustness tables (S1-S3 style)")
    criteria = current["stage6"]["criteria_order"]
    centroid = current["stage6"]["consensus"]["overall_centroid"]
    s1_df = pd.DataFrame({"Criterion": criteria, "CentroidWeight": centroid})
    s2_df = pd.DataFrame(current["stage6"]["selection"]["candidates"])
    hard = current["stage6"]["consensus"]["hard_assignment"]
    dists = current["stage6"]["consensus"]["expert_L1_to_centroid"]
    s3_df = pd.DataFrame({"Expert": [f"E{i+1}" for i in range(len(hard))], "Cluster": hard, "L1Distance": dists})

    c1, c2, c3 = st.columns(3)
    c1.markdown("**Table S1 - Consensus centroid**")
    c1.dataframe(s1_df, width="stretch")
    c2.markdown("**Table S2 - EGK candidates**")
    c2.dataframe(s2_df, width="stretch")
    c3.markdown("**Table S3 - Experts and distance to centroid**")
    c3.dataframe(s3_df, width="stretch")


def render_export(current: Dict[str, Dict[str, Any]], base: Dict[str, Dict[str, Any]], inputs: Dict[str, Dict[str, Any]]) -> None:
    st.subheader("Audit and export")
    payload = {"case_name": CASE_NAME, "article_source": ARTICLE_SOURCE_PATH, "inputs_current": inputs, "outputs_current": current, "outputs_base": base}
    text = json.dumps(payload, ensure_ascii=True, indent=2)
    st.download_button("Download JSON snapshot", data=text, file_name="shp_decision_snapshot.json", mime="application/json")
    st.code(text[:7000] + ("\n... (truncated)" if len(text) > 7000 else ""), language="json")


def main() -> None:
    st.set_page_config(page_title="HydroMaterials Decision Intelligence", layout="wide")
    inject_styles()
    render_header()

    tab_context, tab_inputs, tab_summary, tab_results, tab_mhs, tab_sens, tab_export = st.tabs(
        ["Overview", "Inputs", "Executive Summary", "Results by Stage", "App_MHS Figures", "Sensitivity and OLADE", "Export"]
    )

    with tab_inputs:
        inputs = _build_stage_inputs()

    try:
        current = run_pipeline(inputs)
        base = baseline_outputs()
    except Exception as exc:  # noqa: BLE001
        with tab_context:
            render_overview_context(None, None)
        st.error("Pipeline execution failed with current inputs.")
        st.exception(exc)
        return

    with tab_context:
        render_overview_context(current, base)

    with tab_summary:
        render_summary(current, base)

    with tab_results:
        render_stage_results(current, base)

    with tab_mhs:
        render_app_mhs_charts(current, base)

    with tab_sens:
        render_sensitivity_and_olade(current)
        render_robustness_tables(current)

    with tab_export:
        render_export(current, base, inputs)


if __name__ == "__main__":
    import logging
    from streamlit.runtime.scriptrunner import get_script_run_ctx

    logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").setLevel(logging.ERROR)
    if get_script_run_ctx() is None:
        print("Run with: .\\.venv\\Scripts\\python.exe -m streamlit run streamlit_app.py")
    else:
        main()

