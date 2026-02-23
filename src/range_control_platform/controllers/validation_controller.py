from dash import Input, Output, State, html, no_update
from range_control_platform.services.plan_service import persist_validation_result_to_csv


def register_validation_callbacks(app):
    # Show plan summary on the page
    @app.callback(
        Output("current-plan-summary", "children"),
        Input("plan-store", "data"),
    )
    def show_plan(plan):
        if not plan:
            return html.Div("No plan created yet.")

        return html.Ul(
            [
                html.Li(f"Branch ID: {plan.get('branch_id')}"),
                html.Li(f"Facia: {plan.get('facia')}"),
                html.Li(f"Department: {plan.get('department')}"),
                html.Li(f"Stand count: {plan.get('stand_count', 0)}"),
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

    # Run validation and persist result in global store so it survives page navigation
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

        if not plan:
            return {
                "message": "No plan found. Create a plan first.",
                "color": "warning",
                "details": [],
                "last_run_click_ts": click_ts,
            }
        if not ref_data:
            return {
                "message": "Reference data not loaded.",
                "color": "warning",
                "details": [],
                "last_run_click_ts": click_ts,
            }

        # Find branch grade from branches list
        branch_id = plan.get("branch_id")
        branches = ref_data.get("branches", [])
        branch = next((b for b in branches if b.get("branch_id") == branch_id), None)
        if not branch:
            return {
                "message": f"Branch {branch_id} not found in reference data.",
                "color": "danger",
                "details": [],
                "last_run_click_ts": click_ts,
            }

        grade = branch.get("grade")
        stand_limits = ref_data.get("stand_limits", {})
        allowed = stand_limits.get(grade)

        if allowed is None:
            return {
                "message": f"No stand limit configured for grade {grade}.",
                "color": "danger",
                "details": [],
                "last_run_click_ts": click_ts,
            }

        planned = int(plan.get("stand_count", 0))
        validated_at = plan.get("updated_at") or ""

        if planned <= allowed:
            try:
                persist_validation_result_to_csv(plan, "PASS", validated_at)
            except Exception:
                pass
            return {
                "message": "PASS: Stand limit within allowance.",
                "color": "success",
                "details": [
                    f"Grade {grade} allows up to {allowed} stands.",
                    f"Plan requests {planned} stands.",
                ],
                "last_run_click_ts": click_ts,
            }

        # fail case
        breach = planned - allowed
        try:
            persist_validation_result_to_csv(plan, "FAIL", validated_at)
        except Exception:
            pass
        return {
            "message": "FAIL: Stand limit exceeded.",
            "color": "danger",
            "details": [
                f"Grade {grade} allows up to {allowed} stands.",
                f"Plan requests {planned} stands.",
                f"Over by {breach} stand(s).",
            ],
            "last_run_click_ts": click_ts,
        }

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
