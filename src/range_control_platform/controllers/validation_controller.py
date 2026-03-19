from dash import Input, Output, State, html, no_update

from range_control_platform.services.plan_service import (
    compute_stand_count,
    normalize_plan_departments,
    persist_validation_result_to_csv,
    summarize_plan_departments,
)
from range_control_platform.services.validation_logic import build_validation_result


def _fmt_number(value):
    if value is None:
        return "N/A"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "N/A"
    if number.is_integer():
        return str(int(number))
    return f"{number:.2f}"


def register_validation_callbacks(app):
    @app.callback(
        Output("current-plan-summary", "children"),
        Input("plan-store", "data"),
    )
    def show_plan(plan):
        if not plan:
            return html.Div("No saved plan available yet.")

        totals = summarize_plan_departments(plan)

        return html.Ul(
            [
                html.Li(f"Branch ID: {plan.get('branch_id')}"),
                html.Li(f"Facia: {plan.get('facia')}"),
                html.Li(f"Current department context: {plan.get('department') or 'N/A'}"),
                html.Li(f"Store grade: {plan.get('store_grade') or 'N/A'}"),
                html.Li(f"Allowed space: {_fmt_number(plan.get('allowed_space'))}"),
                html.Li(f"Used space: {_fmt_number(plan.get('used_space'))}"),
                html.Li(f"Remaining space: {_fmt_number(plan.get('remaining_space'))}"),
                html.Li(f"Stand quantity: {compute_stand_count(plan.get('selected_stands'))}"),
                html.Li(f"Departments in plan: {len(normalize_plan_departments(plan))}"),
                html.Li(f"Branch plan stand area: {_fmt_number(totals.get('total_used_space'))}"),
                html.Li(f"Updated: {plan.get('updated_at')}"),
            ]
        )

    @app.callback(
        Output("validation-store", "data", allow_duplicate=True),
        Input("plan-store", "data"),
        State("validation-store", "data"),
        prevent_initial_call=True,
    )
    def clear_validation_when_plan_changes(_plan, existing_validation):
        return {
            "last_run_click_ts": (existing_validation or {}).get("last_run_click_ts")
        }

    @app.callback(
        Output("validation-store", "data"),
        Input("run-validation-btn", "n_clicks_timestamp"),
        State("plan-store", "data"),
        State("ref-data-store", "data"),
        State("validation-store", "data"),
        prevent_initial_call=True,
    )
    def run_validation(click_ts, plan, ref_data, existing_validation):
        if click_ts is None or click_ts < 0:
            return no_update

        if (existing_validation or {}).get("last_run_click_ts") == click_ts:
            return no_update

        result = build_validation_result(plan, ref_data, click_ts)
        validated_at = plan.get("updated_at") or ""

        if result.get("validation_status") == "PASS":
            try:
                persist_validation_result_to_csv(plan, "PASS", validated_at)
            except Exception:
                pass
            return result

        if result.get("validation_status") == "FAIL":
            try:
                persist_validation_result_to_csv(plan, "FAIL", validated_at)
            except Exception:
                pass
        return result

    @app.callback(
        Output("validation-alert", "children"),
        Output("validation-alert", "color"),
        Output("validation-details", "children"),
        Input("validation-store", "data"),
    )
    def render_validation(validation_data):
        if not validation_data or not validation_data.get("message"):
            return "No validation run yet.", "secondary", None

        detail_lines = validation_data.get("details", [])
        details = None
        if detail_lines:
            details = html.Div(
                [
                    html.P(
                        line,
                        style={"color": "crimson"} if line.startswith("Over by ") else None,
                    )
                    for line in detail_lines
                ]
            )

        return (
            validation_data.get("message", "No validation run yet."),
            validation_data.get("color", "secondary"),
            details,
        )
