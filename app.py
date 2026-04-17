from __future__ import annotations

import sys
from datetime import date, timedelta
from html import escape
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_evaluator import (
    PricingInput,
    ProjectInput,
    aggregate_pricing_estimates,
    estimate_price,
    evaluate_project,
    get_pricing_options,
    load_historical_projects,
    load_pricing_matrix,
)


DATA_PATH = ROOT / "data" / "historical_projects.csv"
PRICING_PATH = ROOT / "data" / "pricing_matrix.csv"
PACKAGE_IDS_STATE_KEY = "element_package_ids"

APP_CSS = """
<style>
:root {
    --ink: #1a2420;
    --muted: #6b7c75;
    --line: #d4ddd8;
    --surface: #ffffff;
    --surface-soft: #f4f7f5;
    --lime: #4a8c1c;
    --cyan: #0e8f9c;
    --coral: #d94f45;
    --app-bg: #f0f4f2;
    --sidebar-bg: #ffffff;
    --input-bg: #ffffff;
}

.stApp {
    background: var(--app-bg);
    color: var(--ink);
}

.block-container {
    max-width: 1220px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

h1, h2, h3, h4, h5, h6, p, span, button, label {
    letter-spacing: 0;
}

h1, h2, h3 {
    color: var(--ink);
}

#MainMenu,
footer {
    visibility: hidden;
}

[data-testid="stHeader"] {
    background: rgba(240, 244, 242, 0.95);
    border-bottom: 1px solid var(--line);
}

button, [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-primary"] {
    border-radius: 8px !important;
}

[data-testid="stSidebar"] {
    background: var(--sidebar-bg);
    border-right: 1px solid var(--line);
}

[data-testid="stSidebar"],
[data-testid="stSidebar"] * {
    color: var(--ink) !important;
}

[data-testid="stSidebar"] section {
    padding-top: 1rem;
}

[data-testid="stSidebar"] small,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: var(--muted) !important;
}

[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"] > div {
    background: var(--input-bg) !important;
    border: 1px solid var(--line) !important;
    border-radius: 8px !important;
    color: var(--ink) !important;
}

[data-testid="stSidebar"] button {
    background: var(--surface-soft) !important;
    border-color: var(--line) !important;
    color: var(--ink) !important;
}

[data-testid="stSidebar"] [data-testid="stMetric"] {
    background: var(--surface-soft);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 0.8rem;
}

[data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    overflow: visible !important;
}

[data-testid="stDataFrame"] {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    overflow: hidden;
}

[data-testid="stDataFrame"] * {
    color: var(--ink);
}

[data-testid="stExpander"] {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
}

[data-testid="stExpander"] summary,
[data-testid="stExpander"] p {
    color: var(--ink) !important;
}

[data-testid="stAlert"] {
    border-radius: 8px;
}

[data-testid="stCheckbox"] label,
[data-testid="stCheckbox"] p {
    color: var(--ink) !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.4rem;
    border-bottom: 1px solid var(--line);
    background: transparent;
}

[data-baseweb="popover"] {
    z-index: 999999 !important;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 0.7rem 1rem;
    background: transparent;
}

.stTabs [data-baseweb="tab"] p {
    color: var(--muted) !important;
}

.stTabs [aria-selected="true"] p {
    color: var(--coral) !important;
}

/* Input fields light styling */
input, textarea, [data-baseweb="select"] > div, [data-baseweb="input"] > div {
    background: var(--input-bg) !important;
    border-color: var(--line) !important;
    color: var(--ink) !important;
}

/* ---- Custom components ---- */

.app-header {
    margin: 0 0 1.25rem;
    padding: 0.5rem 0 1.25rem;
    border-bottom: 1px solid var(--line);
}

.eyebrow {
    color: var(--muted);
    font-size: 0.78rem;
    font-weight: 700;
    margin: 0 0 0.35rem;
    text-transform: uppercase;
}

.app-header h1 {
    font-size: 2.5rem;
    line-height: 1.07;
    margin: 0;
    color: var(--ink);
}

.header-subtitle {
    color: var(--muted);
    font-size: 1.05rem;
    line-height: 1.6;
    margin: 0.7rem 0 1rem;
    max-width: 760px;
}

.header-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
}

.meta-pill,
.status-pill {
    align-items: center;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    color: var(--ink);
    display: inline-flex;
    font-size: 0.88rem;
    gap: 0.35rem;
    line-height: 1.35;
    min-width: 0;
    padding: 0.45rem 0.65rem;
    word-break: break-word;
}

.status-pill.good {
    background: #eef7e6;
    border-color: #6aaa2e;
    color: #2d6010;
}

.status-pill.watch {
    background: #e6f5f7;
    border-color: #2a9daa;
    color: #0d5f68;
}

.status-pill.critical {
    background: #fdecea;
    border-color: #c9433b;
    color: #8b1c18;
}

.section-heading {
    margin: 1.4rem 0 0.8rem;
}

.section-heading h2 {
    font-size: 1.45rem;
    line-height: 1.25;
    margin: 0;
    color: var(--ink);
}

.section-heading p {
    color: var(--muted);
    margin: 0.25rem 0 0;
}

.metric-card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    min-height: 132px;
    padding: 1rem;
}

.metric-card.good {
    border-left: 6px solid var(--lime);
}

.metric-card.watch {
    border-left: 6px solid var(--cyan);
}

.metric-card.critical {
    border-left: 6px solid var(--coral);
}

.metric-label {
    color: var(--muted);
    display: block;
    font-size: 0.82rem;
    font-weight: 700;
    margin-bottom: 0.45rem;
    text-transform: uppercase;
}

.metric-value {
    color: var(--ink);
    display: block;
    font-size: 1.55rem;
    font-weight: 780;
    line-height: 1.15;
    overflow-wrap: anywhere;
}

.metric-helper {
    color: var(--muted);
    display: block;
    font-size: 0.9rem;
    line-height: 1.45;
    margin-top: 0.65rem;
}

.score-panel,
.callout {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    margin: 1rem 0;
    padding: 1rem;
}

.score-panel.good {
    border-left: 6px solid var(--lime);
}

.score-panel.watch {
    border-left: 6px solid var(--cyan);
}

.score-panel.critical {
    border-left: 6px solid var(--coral);
}

.score-topline {
    align-items: center;
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    justify-content: space-between;
    margin-bottom: 0.75rem;
    color: var(--ink);
}

.score-rail {
    background: #e2e8e5;
    border-radius: 8px;
    height: 14px;
    overflow: hidden;
}

.score-fill {
    background: var(--cyan);
    border-radius: 8px;
    height: 14px;
}

.score-fill.good {
    background: var(--lime);
}

.score-fill.critical {
    background: var(--coral);
}

.callout.good {
    background: #f0f9e8;
    border-color: #6aaa2e;
    color: var(--ink);
}

.callout.watch {
    background: #e8f6f8;
    border-color: #2a9daa;
    color: var(--ink);
}

.callout.critical {
    background: #fdf0ef;
    border-color: #c9433b;
    color: var(--ink);
}

.callout h3 {
    font-size: 1.05rem;
    margin: 0 0 0.6rem;
    color: var(--ink);
}

.callout ul {
    margin: 0;
    padding-left: 1.2rem;
}

.callout li {
    margin: 0.3rem 0;
    color: var(--ink);
}

.source-note {
    background: var(--surface-soft);
    border: 1px solid var(--line);
    border-radius: 8px;
    color: var(--muted);
    line-height: 1.55;
    margin-top: 0.8rem;
    padding: 0.8rem 1rem;
}

@media (max-width: 900px) {
    .app-header h1 {
        font-size: 2rem;
    }
}
</style>
"""

st.set_page_config(
    page_title="Construction Project Efficiency Estimator",
    layout="wide",
)


@st.cache_data
def get_historical_projects():
    return load_historical_projects(DATA_PATH)


@st.cache_data
def get_pricing_rows():
    return load_pricing_matrix(PRICING_PATH)


def _get_package_ids() -> list[int]:
    if PACKAGE_IDS_STATE_KEY not in st.session_state:
        st.session_state[PACKAGE_IDS_STATE_KEY] = [0]
    return list(st.session_state[PACKAGE_IDS_STATE_KEY])


def _add_package_row() -> None:
    package_ids = _get_package_ids()
    next_id = max(package_ids, default=-1) + 1
    st.session_state[PACKAGE_IDS_STATE_KEY] = [*package_ids, next_id]


def _remove_package_row(package_id: int) -> None:
    remaining_ids = [item for item in _get_package_ids() if item != package_id]
    st.session_state[PACKAGE_IDS_STATE_KEY] = remaining_ids or [0]
    for prefix in ("element_type", "width", "height", "quantity"):
        st.session_state.pop(f"{prefix}_{package_id}", None)


def main() -> None:
    _inject_design()

    pricing_rows = get_pricing_rows()
    historical_projects = get_historical_projects()

    input_column, output_column = st.columns([0.30, 0.70], gap="large")

    with input_column:
        with st.container(border=True):
            project, pricing_estimate = render_inputs(pricing_rows)

    result = evaluate_project(project, historical_projects)

    with output_column:
        render_header(project, result)
        render_summary(result, project)

        price_tab, scoring_tab, matrix_tab, history_tab = st.tabs(
            ["Price Build-up", "Risk Logic", "Price Matrix", "Historical Cases"]
        )
        with price_tab:
            render_pricing_estimate(pricing_estimate)
        with scoring_tab:
            render_explainability(result)
        with matrix_tab:
            render_price_matrix(pricing_rows, pricing_estimate)
        with history_tab:
            render_historical_context(result)


def render_inputs(pricing_rows) -> tuple[ProjectInput, object]:
    st.title("Inputs")
    st.caption("Adjust the package, commercial values, schedule, and known uncertainty.")
    st.divider()

    st.subheader("Element Package")
    package_ids = _get_package_ids()
    package_rows = []
    remove_package_id = None

    for position, package_id in enumerate(package_ids, start=1):
        if position > 1:
            st.divider()

        heading_col, action_col = st.columns([0.72, 0.28])
        with heading_col:
            st.caption(f"Construction {position}")
        with action_col:
            if st.button(
                "Remove",
                key=f"remove_package_{package_id}",
                use_container_width=True,
                disabled=len(package_ids) == 1,
            ):
                remove_package_id = package_id

        package_rows.append(
            {
                "element_type": st.selectbox(
                    "Element type",
                    get_pricing_options(pricing_rows, "element_type"),
                    key=f"element_type_{package_id}",
                ),
                "width_m": st.number_input(
                    "Width, m",
                    min_value=0.1,
                    value=1.0,
                    step=0.1,
                    key=f"width_{package_id}",
                ),
                "height_m": st.number_input(
                    "Height, m",
                    min_value=0.1,
                    value=1.0,
                    step=0.1,
                    key=f"height_{package_id}",
                ),
                "quantity": int(
                    st.number_input(
                        "Quantity",
                        min_value=1,
                        value=1,
                        step=1,
                        key=f"quantity_{package_id}",
                    )
                ),
            }
        )

    if remove_package_id is not None:
        _remove_package_row(remove_package_id)
        st.rerun()

    if st.button("Add construction", use_container_width=True):
        _add_package_row()
        st.rerun()

    glass_supply_model = st.selectbox(
        "Glass supply model",
        get_pricing_options(pricing_rows, "glass_supply_model"),
        format_func=_format_glass_supply_model,
    )
    wind_load = st.selectbox("Wind load", get_pricing_options(pricing_rows, "wind_load"))
    thermal_performance = st.selectbox(
        "Thermal performance",
        get_pricing_options(pricing_rows, "thermal_performance"),
    )
    coating_type = st.selectbox("Coating type", get_pricing_options(pricing_rows, "coating_type"))

    pricing_inputs = [
        PricingInput(
            element_type=package_row["element_type"],
            width_m=package_row["width_m"],
            height_m=package_row["height_m"],
            quantity=package_row["quantity"],
            glass_supply_model=glass_supply_model,
            wind_load=wind_load,
            thermal_performance=thermal_performance,
            coating_type=coating_type,
        )
        for package_row in package_rows
    ]
    pricing_estimate = aggregate_pricing_estimates(
        [estimate_price(pricing_input, pricing_rows) for pricing_input in pricing_inputs]
    )
    st.caption(
        "Package summary: "
        f"{pricing_estimate.package_count} construction"
        f"{'' if pricing_estimate.package_count == 1 else 's'}, "
        f"{pricing_estimate.total_quantity} units, {pricing_estimate.total_area_m2:.1f} m2"
    )

    project_name = _project_name_from_packages(package_rows)
    project_type = _project_type_from_packages(package_rows)
    material_type = _material_type_from_packages(package_rows)
    region = _coating_to_region(coating_type)
    wind_exposure = _wind_load_to_exposure(wind_load)
    technical_complexity = _technical_complexity_from_selection(wind_exposure, coating_type)
    design_repetition = _design_repetition_from_packages(package_rows)
    installation_model = _glass_supply_to_installation_model(glass_supply_model)

    st.divider()
    st.subheader("Commercial and Schedule")
    use_price_for_financials = st.checkbox(
        "Use calculated price for financial evaluation",
        value=True,
    )
    if use_price_for_financials:
        contract_value = pricing_estimate.total_final_price_gbp
        estimated_cost = pricing_estimate.total_cost_before_margin_gbp
        st.metric("Contract value", _gbp(contract_value))
        st.metric("Estimated cost before margin", _gbp(estimated_cost))
    else:
        contract_value = st.number_input(
            "Contract value, GBP",
            min_value=0.0,
            value=pricing_estimate.total_final_price_gbp,
            step=100.0,
        )
        estimated_cost = st.number_input(
            "Estimated cost, GBP",
            min_value=0.0,
            value=pricing_estimate.total_cost_before_margin_gbp,
            step=100.0,
        )

    evaluation_date = st.date_input("Evaluation date", value=date.today())
    requested_deadline = st.date_input(
        "Target project implementation date",
        value=date.today() + timedelta(weeks=14),
    )
    material_lead_time_weeks = st.number_input("Material lead time, weeks", min_value=0, value=10, step=1)
    production_capacity_hours_per_week = st.number_input(
        "Production capacity, hours/week",
        min_value=1,
        value=40,
        step=1,
    )

    st.divider()
    st.subheader("Known Uncertainties")
    non_standard_profiles = st.checkbox("Non-standard profiles")
    incomplete_drawings = st.checkbox("Incomplete drawings")
    missing_installation_details = st.checkbox("Missing installation details", value=True)

    project = ProjectInput(
        project_name=project_name,
        project_type=project_type,
        contract_value=contract_value,
        estimated_cost=estimated_cost,
        evaluation_date=evaluation_date,
        requested_deadline=requested_deadline,
        material_type=material_type,
        region=region,
        wind_exposure=wind_exposure,
        technical_complexity=technical_complexity,
        design_repetition=design_repetition,
        installation_model=installation_model,
        element_quantity=pricing_estimate.total_quantity,
        package_area_m2=pricing_estimate.total_area_m2,
        production_hours_per_unit=pricing_estimate.fabrication_time_hours_per_unit,
        production_capacity_hours_per_week=float(production_capacity_hours_per_week),
        material_lead_time_weeks=int(material_lead_time_weeks),
        non_standard_profiles=non_standard_profiles,
        incomplete_drawings=incomplete_drawings,
        missing_installation_details=missing_installation_details,
    )
    return project, pricing_estimate


def render_header(project: ProjectInput, result) -> None:
    tone = _risk_tone(result.risk_level)
    st.markdown(
        f"""
        <section class="app-header">
            <h1>{escape(project.project_name)}</h1>
            <p class="header-subtitle">
                Pricing, schedule, margin, and execution risk for the selected package.
            </p>
            <div class="header-meta">
                <span class="meta-pill">Type: {escape(project.project_type)}</span>
                <span class="meta-pill">Target: {escape(project.requested_deadline.isoformat())}</span>
                <span class="status-pill {tone}">{escape(result.risk_level)}</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_summary(result, project: ProjectInput) -> None:
    tone = _risk_tone(result.risk_level)
    st.markdown(
        """
        <div class="section-heading">
            <p class="eyebrow">Decision signal</p>
            <h2>Risk and efficiency evaluation</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    first, second, third, fourth = st.columns(4)
    with first:
        _metric_card("Efficiency score", f"{result.efficiency_score:.1f}/100", "Weighted tender readiness.", tone)
    with second:
        _metric_card("Risk level", result.risk_level, "Current decision band.", tone)
    with third:
        _metric_card("Target implementation", project.requested_deadline.isoformat(), "Customer target date.")
    with fourth:
        _metric_card("Earliest implementation", result.readiness_date.isoformat(), "Material lead time plus preparation.")

    material_ready_date = project.evaluation_date + timedelta(weeks=result.material_lead_time_weeks)
    if project.requested_deadline < material_ready_date:
        st.error(
            "Material lead time is too short for the selected target date. "
            f"Earliest material readiness date is {material_ready_date.isoformat()}."
        )

    _score_panel(result.efficiency_score, result.risk_level)

    lead_first, lead_second, lead_third, lead_fourth = st.columns(4)
    with lead_first:
        _metric_card("Material lead time", f"{result.material_lead_time_weeks} weeks")
    with lead_second:
        _metric_card(
            "Preparation",
            _format_production_duration(result.preparation_hours, result.preparation_weeks),
            f"{result.preparation_hours:g} hours at {project.production_capacity_hours_per_week:g} h/week",
        )
    with lead_third:
        _metric_card("Total timeline", f"{result.total_preparation_weeks:g} weeks")
    with lead_fourth:
        _metric_card("Package volume", f"{project.element_quantity} units", f"{project.package_area_m2:.0f} m2")

    if result.alerts:
        _callout("Alerts to resolve", result.alerts, "critical")
    else:
        _callout("No critical alerts", ["Current inputs do not trigger a critical alert."], "good")


def render_pricing_estimate(estimate) -> None:
    heading = "Element price estimate" if estimate.package_count == 1 else "Package price estimate"
    st.markdown(
        f"""
        <div class="section-heading">
            <p class="eyebrow">Commercial view</p>
            <h2>{heading}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    price_label = "Final price per unit" if estimate.package_count == 1 else "Average price per unit"
    fabrication_label = "Fabrication time" if estimate.package_count == 1 else "Avg fabrication time"
    fabrication_helper = "Per unit" if estimate.package_count == 1 else f"{estimate.total_fabrication_time_hours:g} hours total"

    first, second, third, fourth = st.columns(4)
    with first:
        _metric_card(price_label, _gbp(estimate.final_price_gbp))
    with second:
        _metric_card("Total final price", _gbp(estimate.total_final_price_gbp))
    with third:
        _metric_card("Margin", _gbp(estimate.total_margin_gbp), f"{estimate.margin_rate * 100:.0f}% pricing rule")
    with fourth:
        _metric_card(
            fabrication_label,
            _format_hours(estimate.fabrication_time_hours_per_unit),
            fabrication_helper,
        )

    if estimate.package_count > 1:
        st.dataframe(
            [
                {
                    "Element": item.source_row["element_type"],
                    "Dimensions": f"{item.width_m:g} x {item.height_m:g} m",
                    "Quantity": item.quantity,
                    "Source item": item.source_item,
                    "Total": _gbp(item.total_final_price_gbp),
                }
                for item in estimate.estimates
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.dataframe(
        [
            {
                "Component": "Material",
                "Per unit": _gbp(estimate.material_gbp),
                "Total": _gbp(estimate.total_material_gbp),
            },
            {
                "Component": "Glass unit",
                "Per unit": _gbp(estimate.glass_gbp),
                "Total": _gbp(estimate.total_glass_gbp),
            },
            {
                "Component": "Labour work",
                "Per unit": _gbp(estimate.labour_gbp),
                "Total": _gbp(estimate.total_labour_gbp),
            },
            {
                "Component": "Coating",
                "Per unit": _gbp(estimate.coating_gbp),
                "Total": _gbp(estimate.total_coating_gbp),
            },
            {
                "Component": f"Margin ({estimate.margin_rate * 100:.0f}%)",
                "Per unit": _gbp(estimate.margin_gbp),
                "Total": _gbp(estimate.total_margin_gbp),
            },
        ],
        use_container_width=True,
        hide_index=True,
    )

    source_items = ", ".join(str(item.source_item) for item in estimate.estimates)
    source_note = (
        "Base prices and fabrication time use the Excel matrix; margin "
        "follows the selected glass supply rule."
    )
    if estimate.package_count == 1:
        source_dimensions = estimate.estimates[0].source_dimensions
        source_summary = f"Source matrix item {escape(str(estimate.estimates[0].source_item))}, base dimensions {escape(source_dimensions)}."
    else:
        source_summary = f"Source matrix items {escape(source_items)}."

    st.markdown(
        f"""
        <div class="source-note">
            {source_summary} {source_note}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_explainability(result) -> None:
    st.markdown(
        """
        <div class="section-heading">
            <p class="eyebrow">Rule trace</p>
            <h2>Scoring logic</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.dataframe(
        [
            {
                "Criterion": key.replace("_", " ").title(),
                "Score": value,
                "Weight": f"{_score_weight(key) * 100:.0f}%",
                "Explanation": result.explanations[key],
            }
            for key, value in result.score_breakdown.items()
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        """
        <div class="section-heading">
            <p class="eyebrow">Next actions</p>
            <h2>Generated checklist</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for index, item in enumerate(result.checklist):
        st.checkbox(item, value=False, key=f"checklist_{index}")


def render_price_matrix(pricing_rows, estimate) -> None:
    st.markdown(
        """
        <div class="section-heading">
            <p class="eyebrow">Source data</p>
            <h2>Price matrix</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.dataframe(pricing_rows, use_container_width=True, hide_index=True)
    with st.expander("Selected source rows" if estimate.package_count > 1 else "Selected source row"):
        if estimate.package_count == 1:
            st.json(estimate.estimates[0].source_row)
        else:
            st.dataframe(
                [
                    {
                        "Element": item.source_row["element_type"],
                        "Dimensions": f"{item.width_m:g} x {item.height_m:g} m",
                        "Quantity": item.quantity,
                        "Source item": item.source_item,
                        "Base dimensions": item.source_dimensions,
                        "Wind load": item.source_row["wind_load"],
                        "Thermal": item.source_row["thermal_performance"],
                        "Coating": item.source_row["coating_type"],
                    }
                    for item in estimate.estimates
                ],
                use_container_width=True,
                hide_index=True,
            )


def render_historical_context(result) -> None:
    st.markdown(
        """
        <div class="section-heading">
            <p class="eyebrow">Reference cases</p>
            <h2>Historical similarity</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.dataframe(result.similar_projects, use_container_width=True, hide_index=True)


def _inject_design() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)


def _metric_card(label: str, value: str, helper: str = "", tone: str = "neutral") -> None:
    helper_html = f'<span class="metric-helper">{escape(helper)}</span>' if helper else ""
    st.markdown(
        f"""
        <div class="metric-card {escape(tone)}">
            <span class="metric-label">{escape(label)}</span>
            <span class="metric-value">{escape(value)}</span>
            {helper_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _score_panel(score: float, risk_level: str) -> None:
    tone = _risk_tone(risk_level)
    safe_score = max(0.0, min(100.0, score))
    st.markdown(
        f"""
        <div class="score-panel {tone}">
            <div class="score-topline">
                <strong>{escape(risk_level)}</strong>
                <span>{safe_score:.1f}/100</span>
            </div>
            <div class="score-rail">
                <div class="score-fill {tone}" style="width: {safe_score:.1f}%"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _callout(title: str, items: list[str], tone: str) -> None:
    list_items = "".join(f"<li>{escape(item)}</li>" for item in items)
    st.markdown(
        f"""
        <div class="callout {escape(tone)}">
            <h3>{escape(title)}</h3>
            <ul>{list_items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _risk_tone(risk_level: str) -> str:
    normalized = risk_level.casefold()
    if normalized.startswith("low"):
        return "good"
    if normalized.startswith("medium"):
        return "watch"
    return "critical"


def _wind_load_to_exposure(wind_load: str) -> str:
    return "Low" if wind_load.startswith("<") else "High"


def _project_name_from_packages(package_rows: list[dict]) -> str:
    element_types = list(dict.fromkeys(row["element_type"] for row in package_rows))
    if len(element_types) == 1:
        return f"Project {element_types[0].lower()} tender"
    if len(element_types) == 2:
        return f"Project {element_types[0].lower()} + {element_types[1].lower()} tender"
    return "Project mixed element tender"


def _project_type_from_packages(package_rows: list[dict]) -> str:
    project_types = list(dict.fromkeys(_element_to_project_type(row["element_type"]) for row in package_rows))
    if len(project_types) == 1:
        return project_types[0]
    return "Mixed package"


def _material_type_from_packages(package_rows: list[dict]) -> str:
    material_types = {_element_to_material_type(row["element_type"]) for row in package_rows}
    if "Glass-heavy facade" in material_types:
        return "Glass-heavy facade"
    if "Steel elements" in material_types:
        return "Steel elements"
    return "Standard aluminum profiles"


def _design_repetition_from_packages(package_rows: list[dict]) -> str:
    unique_types = {row["element_type"] for row in package_rows}
    if len(unique_types) == 1:
        return "Repeated"
    return "Partially similar"


def _element_to_project_type(element_type: str) -> str:
    if "window" in element_type.lower():
        return "Windows"
    if "door" in element_type.lower():
        return "Doors"
    return "Facade"


def _element_to_material_type(element_type: str) -> str:
    if "window" in element_type.lower():
        return "Standard aluminum profiles"
    if "door" in element_type.lower():
        return "Steel elements"
    return "Glass-heavy facade"


def _coating_to_region(coating_type: str) -> str:
    if "Seaside" in coating_type:
        return "Coastal"
    return "Urban"


def _technical_complexity_from_selection(wind_exposure: str, coating_type: str) -> str:
    if wind_exposure == "High" or "Seaside" in coating_type:
        return "Medium"
    return "Low"


def _glass_supply_to_installation_model(glass_supply_model: str) -> str:
    if glass_supply_model.startswith("External supplier"):
        return "Client installation"
    return "Company installation"


def _format_glass_supply_model(glass_supply_model: str) -> str:
    if glass_supply_model.startswith("External supplier"):
        return "Customer supplies glass units (43% material margin only)"
    return "Company supplies glass units (34% full project margin)"


def _format_production_duration(hours: float, weeks: float) -> str:
    if hours and weeks < 1:
        return f"{hours:g} hours"
    return f"{weeks:g} weeks"


def _format_hours(hours: float) -> str:
    return f"{hours:g} hours"


def _gbp(value: float) -> str:
    return f"GBP {value:,.2f}"


def _score_weight(name: str) -> float:
    return {
        "financial": 0.30,
        "technical": 0.25,
        "schedule": 0.25,
        "environment": 0.10,
        "similarity": 0.10,
    }[name]


if __name__ == "__main__":
    main()
