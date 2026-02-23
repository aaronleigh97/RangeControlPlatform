from datetime import datetime, timezone

from dash import Input, Output, State, html, no_update

from range_control_platform.services.plan_service import (
    get_latest_plan_by_key,
    list_latest_plans_from_csv,
    make_plan_key,
    persist_plan_snapshot_to_csv,
)


def _saved_plan_options():
    rows = list_latest_plans_from_csv()
    options = []
    for row in rows:
        label = (
            f"{row.get('branch_id')} | {row.get('facia')} | {row.get('department')} | "
            f"Stands {row.get('stand_count', 0)} | {row.get('saved_at') or row.get('updated_at') or ''}"
        )
        options.append({"label": label, "value": row.get("plan_key")})
    return options


def register_plan_callbacks(app):
    @app.callback(
        Output("saved-plan-dd", "options"),
        Input("ref-data-store", "data"),
        Input("plan-store", "data"),
    )
    def populate_saved_plan_list(_ref_data, _plan):
        return _saved_plan_options()

    @app.callback(
        Output("plan-load-btn", "disabled"),
        Input("saved-plan-dd", "value"),
    )
    def toggle_load_button(selected_plan_key):
        return not bool(selected_plan_key)

    @app.callback(
        Output("facia-dd", "value", allow_duplicate=True),
        Output("branch-dd", "value", allow_duplicate=True),
        Output("dept-dd", "value", allow_duplicate=True),
        Output("stand-count", "value", allow_duplicate=True),
        Output("plan-store", "data", allow_duplicate=True),
        Output("plan-status", "children", allow_duplicate=True),
        Input("plan-load-btn", "n_clicks"),
        State("saved-plan-dd", "value"),
        prevent_initial_call=True,
    )
    def load_selected_plan(_n_clicks, selected_plan_key):
        if not selected_plan_key:
            return no_update, no_update, no_update, no_update, no_update, no_update

        row = get_latest_plan_by_key(selected_plan_key)
        if not row:
            status = html.Div(
                "Selected plan could not be found in local CSV snapshots.",
                style={"color": "crimson"},
            )
            return no_update, no_update, no_update, no_update, no_update, status

        plan = {
            "branch_id": row.get("branch_id"),
            "facia": row.get("facia"),
            "department": row.get("department"),
            "stand_count": int(row.get("stand_count") or 0),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at") or row.get("saved_at"),
        }

        status = html.Div(
            [
                html.Strong("Plan loaded from local CSV snapshot."),
                html.Div(
                    f"Branch: {plan['branch_id']} | Facia: {plan['facia']} | "
                    f"Dept: {plan['department']} | Stands: {plan['stand_count']}"
                ),
                html.Small(f"Loaded snapshot timestamp: {row.get('saved_at') or 'N/A'}"),
            ]
        )

        return (
            plan["facia"],
            plan["branch_id"],
            plan["department"],
            plan["stand_count"],
            plan,
            status,
        )

    @app.callback(
        Output("facia-dd", "options"),
        Output("branch-dd", "options"),
        Output("branch-dd", "disabled"),
        Input("ref-data-store", "data"),
        Input("facia-dd", "value"),
    )
    def populate_facia_and_branch(ref_data, selected_facia):
        if not ref_data:
            return [], [], True

        facias = [{"label": f, "value": f} for f in ref_data.get("facias", [])]

        if not selected_facia:
            return facias, [], True

        branches_raw = ref_data.get("branches", [])
        branches_filtered = [b for b in branches_raw if b.get("facia") == selected_facia]
        branches = [
            {
                "label": f'{b["branch_id"]} - {b["branch_name"]} (Grade {b["grade"]})',
                "value": b["branch_id"],
            }
            for b in branches_filtered
        ]
        return facias, branches, False

    @app.callback(
        Output("dept-dd", "options"),
        Output("dept-dd", "disabled"),
        Input("ref-data-store", "data"),
        Input("facia-dd", "value"),
        Input("branch-dd", "value"),
    )
    def populate_department_options(ref_data, selected_facia, selected_branch):
        if not ref_data:
            return [], True

        if not (selected_facia and selected_branch):
            return [], True

        depts = [{"label": d, "value": d} for d in ref_data.get("departments", [])]
        return depts, False

    @app.callback(
        Output("stand-count", "disabled"),
        Input("facia-dd", "value"),
        Input("branch-dd", "value"),
        Input("dept-dd", "value"),
    )
    def toggle_stand_count_disabled(facia, branch_id, department):
        return not all([facia, branch_id, department])

    @app.callback(
        Output("branch-dd", "value"),
        Input("branch-dd", "options"),
        State("branch-dd", "value"),
        prevent_initial_call=True,
    )
    def reset_branch_when_invalid(branch_options, current_branch_id):
        if not current_branch_id:
            return no_update
        option_values = {opt.get("value") for opt in (branch_options or [])}
        if current_branch_id in option_values:
            return no_update
        return None

    @app.callback(
        Output("dept-dd", "value"),
        Input("dept-dd", "options"),
        State("dept-dd", "value"),
        prevent_initial_call=True,
    )
    def reset_dept_when_invalid(dept_options, current_department):
        if not current_department:
            return no_update
        option_values = {opt.get("value") for opt in (dept_options or [])}
        if current_department in option_values:
            return no_update
        return None

    @app.callback(
        Output("plan-save-btn", "disabled"),
        Input("facia-dd", "value"),
        Input("branch-dd", "value"),
        Input("dept-dd", "value"),
    )
    def toggle_save_button(facia, branch_id, department):
        return not all([facia, branch_id, department])

    @app.callback(
        Output("plan-store", "data"),
        Output("plan-status", "children"),
        Output("saved-plan-dd", "value"),
        Input("plan-save-btn", "n_clicks"),
        State("branch-dd", "value"),
        State("facia-dd", "value"),
        State("dept-dd", "value"),
        State("stand-count", "value"),
        State("plan-store", "data"),
        prevent_initial_call=True,
    )
    def save_plan(n_clicks, branch_id, facia, department, stand_count, existing_plan):
        missing = [
            name
            for name, val in [
                ("Branch", branch_id),
                ("Facia", facia),
                ("Department", department),
            ]
            if not val
        ]

        if missing:
            return existing_plan, html.Div(
                f"Missing required fields: {', '.join(missing)}",
                style={"color": "crimson"},
            ), no_update

        now = datetime.now(timezone.utc).isoformat()

        if not existing_plan:
            plan = {
                "branch_id": branch_id,
                "facia": facia,
                "department": department,
                "stand_count": int(stand_count or 0),
                "created_at": now,
                "updated_at": now,
            }
            msg = "Plan created."
        else:
            plan = {
                **existing_plan,
                "branch_id": branch_id,
                "facia": facia,
                "department": department,
                "stand_count": int(stand_count or 0),
                "updated_at": now,
            }
            if not plan.get("created_at"):
                plan["created_at"] = now
            msg = "Plan updated."

        csv_note = None
        try:
            csv_path = persist_plan_snapshot_to_csv(plan)
            csv_note = html.Small(f"Saved to CSV: {csv_path}")
        except Exception as exc:
            csv_note = html.Small(
                f"CSV save failed: {exc}",
                style={"color": "crimson"},
            )

        status_children = [
            html.Strong(msg),
            html.Div(
                f"Branch: {plan['branch_id']} | Facia: {plan['facia']} | "
                f"Dept: {plan['department']} | Stands: {plan['stand_count']}"
            ),
            html.Small(f"Last updated: {plan['updated_at']}"),
        ]
        if csv_note is not None:
            status_children.append(html.Br())
            status_children.append(csv_note)

        saved_plan_key = make_plan_key(plan)
        status = html.Div(status_children)
        return plan, status, saved_plan_key
