from datetime import datetime, timezone

from dash import Input, Output, State, ctx, html, no_update
import dash_bootstrap_components as dbc

from range_control_platform.services.plan_service import (
    compute_stand_count,
    compute_used_space,
    get_latest_plan_by_key,
    list_latest_plans_from_csv,
    make_plan_key,
    normalize_selected_stands,
    persist_plan_snapshot_to_csv,
)


def _branch_option_label(branch):
    branch_label = branch.get("branch_label")
    if branch_label:
        return branch_label

    branch_id = branch.get("branch_id", "")
    branch_name = branch.get("branch_name")
    grade = branch.get("grade") or branch.get("store_grade") or "Unknown"

    if branch_name and branch_name != branch_id:
        return f"{branch_id} - {branch_name} (Grade {grade})"
    return f"{branch_id} (Grade {grade})"


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


def _saved_plan_options():
    rows = list_latest_plans_from_csv()
    options = []
    for row in rows:
        label = (
            f"{row.get('branch_id')} | {row.get('facia')} | {row.get('department')} | "
            f"Used {_fmt_number(row.get('used_space'))} / Allowed {_fmt_number(row.get('allowed_space'))} | "
            f"{row.get('saved_at') or row.get('updated_at') or ''}"
        )
        options.append({"label": label, "value": row.get("plan_key")})
    return options


def _find_store(ref_data, branch_id):
    if not ref_data or not branch_id:
        return None

    stores = ref_data.get("stores", [])
    store = next((row for row in stores if row.get("branch_id") == branch_id), None)
    if store:
        return store

    branches = ref_data.get("branches", [])
    branch = next((row for row in branches if row.get("branch_id") == branch_id), None)
    if not branch:
        return None

    return {
        "branch_id": branch.get("branch_id"),
        "branch_name": branch.get("branch_name"),
        "fascia": branch.get("facia"),
        "store_grade": branch.get("grade"),
        "square_footage": branch.get("square_footage"),
        "budget_2026": branch.get("budget_2026"),
    }


def _find_department_allocation(ref_data, department, grade):
    if not ref_data or not department or not grade:
        return None

    for row in ref_data.get("department_grade_allocations", []):
        if row.get("department_name") == department and row.get("grade") == grade:
            try:
                return round(float(row.get("allowed_linear_meterage")), 2)
            except (TypeError, ValueError):
                return None
    return None


def _find_stand(ref_data, stand_id):
    if not ref_data or not stand_id:
        return None
    return next(
        (row for row in ref_data.get("stand_library", []) if row.get("stand_id") == stand_id),
        None,
    )


def _build_plan_context(ref_data, facia, branch_id, department, existing_plan=None):
    existing_plan = existing_plan or {}
    same_context = (
        existing_plan.get("branch_id") == branch_id
        and existing_plan.get("facia") == facia
        and existing_plan.get("department") == department
    )
    selected_stands = normalize_selected_stands(
        existing_plan.get("selected_stands") if same_context else []
    )

    store = _find_store(ref_data, branch_id) or {}
    store_grade = store.get("store_grade") or store.get("grade")
    allowed_space = _find_department_allocation(ref_data, department, store_grade)
    used_space = compute_used_space(selected_stands)
    remaining_space = None if allowed_space is None else round(allowed_space - used_space, 2)

    return {
        **existing_plan,
        "branch_id": branch_id,
        "branch_name": store.get("branch_name") or existing_plan.get("branch_name"),
        "facia": facia or store.get("fascia"),
        "department": department,
        "store_grade": store_grade,
        "square_footage": store.get("square_footage"),
        "budget_2026": store.get("budget_2026"),
        "allowed_space": allowed_space,
        "allowed_space_unit": "linear_meter",
        "used_space": used_space,
        "remaining_space": remaining_space,
        "stand_count": compute_stand_count(selected_stands),
        "selected_stands": selected_stands,
    }


def _plan_summary_children(plan):
    if not plan:
        return html.Div("Select a store and department to start building a plan.")

    return dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H6("Store Context"),
                            html.Div(f"Branch: {plan.get('branch_id') or 'N/A'}"),
                            html.Div(f"Facia: {plan.get('facia') or 'N/A'}"),
                            html.Div(f"Department: {plan.get('department') or 'N/A'}"),
                            html.Div(f"Store grade: {plan.get('store_grade') or 'N/A'}"),
                            html.Div(
                                f"Square footage: {_fmt_number(plan.get('square_footage'))}"
                            ),
                        ]
                    )
                ),
                width=6,
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H6("Space Summary"),
                            html.Div(
                                "Allowed department space: "
                                f"{_fmt_number(plan.get('allowed_space'))}"
                            ),
                            html.Div(
                                f"Used stand space: {_fmt_number(plan.get('used_space'))}"
                            ),
                            html.Div(
                                "Remaining space: "
                                f"{_fmt_number(plan.get('remaining_space'))}"
                            ),
                            html.Div(
                                f"Selected stand quantity: {plan.get('stand_count', 0)}"
                            ),
                        ]
                    )
                ),
                width=6,
            ),
        ],
        className="g-2",
    )


def _stand_table(plan):
    selected_stands = (plan or {}).get("selected_stands") or []
    if not selected_stands:
        return html.Div("No stands added yet.")

    header = html.Thead(
        html.Tr(
            [
                html.Th("Stand ID"),
                html.Th("Stand"),
                html.Th("Type"),
                html.Th("Sqm"),
                html.Th("Qty"),
                html.Th("Total Sqm"),
            ]
        )
    )
    body = html.Tbody(
        [
            html.Tr(
                [
                    html.Td(stand.get("stand_id")),
                    html.Td(stand.get("stand_name")),
                    html.Td(stand.get("stand_type") or ""),
                    html.Td(_fmt_number(stand.get("sqm"))),
                    html.Td(stand.get("quantity")),
                    html.Td(_fmt_number(stand.get("total_sqm"))),
                ]
            )
            for stand in selected_stands
        ]
    )
    return dbc.Table([header, body], bordered=False, hover=True, striped=True, size="sm")


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
        Output("plan-draft-store", "data", allow_duplicate=True),
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
            "store_grade": row.get("store_grade"),
            "allowed_space": row.get("allowed_space"),
            "allowed_space_unit": "linear_meter",
            "used_space": row.get("used_space"),
            "remaining_space": row.get("remaining_space"),
            "stand_count": row.get("stand_count", 0),
            "selected_stands": row.get("selected_stands", []),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at") or row.get("saved_at"),
        }

        status = html.Div(
            [
                html.Strong("Plan loaded from local CSV snapshot."),
                html.Div(
                    f"Branch: {plan['branch_id']} | Facia: {plan['facia']} | "
                    f"Dept: {plan['department']} | "
                    f"Used {_fmt_number(plan['used_space'])} / Allowed {_fmt_number(plan['allowed_space'])}"
                ),
                html.Small(f"Loaded snapshot timestamp: {row.get('saved_at') or 'N/A'}"),
            ]
        )

        return (
            plan["facia"],
            plan["branch_id"],
            plan["department"],
            plan,
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
                "label": _branch_option_label(b),
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

        store = _find_store(ref_data, selected_branch) or {}
        grade = store.get("store_grade") or store.get("grade")
        if grade:
            department_names = sorted(
                {
                    row.get("department_name")
                    for row in ref_data.get("department_grade_allocations", [])
                    if row.get("grade") == grade and row.get("department_name")
                }
            )
        else:
            department_names = ref_data.get("departments", [])

        depts = [{"label": d, "value": d} for d in department_names]
        return depts, False

    @app.callback(
        Output("stand-library-dd", "options"),
        Output("stand-library-dd", "disabled"),
        Input("ref-data-store", "data"),
        Input("facia-dd", "value"),
        Input("branch-dd", "value"),
        Input("dept-dd", "value"),
    )
    def populate_stand_library_options(ref_data, facia, branch_id, department):
        if not ref_data or not all([facia, branch_id, department]):
            return [], True

        options = [
            {
                "label": (
                    f"{stand.get('stand_id')} - {stand.get('stand_name')} "
                    f"({_fmt_number(stand.get('sqm'))} sqm)"
                ),
                "value": stand.get("stand_id"),
            }
            for stand in ref_data.get("stand_library", [])
        ]
        return options, False

    @app.callback(
        Output("plan-draft-store", "data"),
        Input("ref-data-store", "data"),
        Input("facia-dd", "value"),
        Input("branch-dd", "value"),
        Input("dept-dd", "value"),
        State("plan-draft-store", "data"),
    )
    def sync_plan_context(ref_data, facia, branch_id, department, existing_plan):
        if not ref_data:
            return existing_plan

        if not any([facia, branch_id, department]):
            return None

        return _build_plan_context(ref_data, facia, branch_id, department, existing_plan)

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
        Output("stand-qty", "disabled"),
        Output("add-stand-btn", "disabled"),
        Output("clear-stands-btn", "disabled"),
        Input("plan-draft-store", "data"),
        Input("stand-library-dd", "value"),
        Input("stand-qty", "value"),
    )
    def toggle_stand_actions(plan, stand_id, quantity):
        context_ready = bool(
            plan
            and plan.get("branch_id")
            and plan.get("facia")
            and plan.get("department")
        )
        quantity_disabled = not context_ready
        add_disabled = not (context_ready and stand_id and (quantity or 0) > 0)
        clear_disabled = not (context_ready and (plan.get("selected_stands") or []))
        return quantity_disabled, add_disabled, clear_disabled

    @app.callback(
        Output("plan-draft-store", "data", allow_duplicate=True),
        Output("stand-library-dd", "value"),
        Input("add-stand-btn", "n_clicks"),
        Input("clear-stands-btn", "n_clicks"),
        State("stand-library-dd", "value"),
        State("stand-qty", "value"),
        State("plan-draft-store", "data"),
        State("ref-data-store", "data"),
        prevent_initial_call=True,
    )
    def update_selected_stands(_add_clicks, _clear_clicks, stand_id, quantity, plan, ref_data):
        if not plan:
            return no_update, no_update

        trigger = ctx.triggered_id
        selected_stands = normalize_selected_stands(plan.get("selected_stands"))

        if trigger == "clear-stands-btn":
            updated_plan = {
                **plan,
                "selected_stands": [],
                "stand_count": 0,
                "used_space": 0.0,
                "remaining_space": (
                    None
                    if plan.get("allowed_space") is None
                    else round(float(plan.get("allowed_space")) - 0.0, 2)
                ),
            }
            return updated_plan, None

        stand = _find_stand(ref_data, stand_id)
        if not stand or not quantity or quantity <= 0:
            return no_update, no_update

        quantity = int(quantity)
        existing_by_id = {row.get("stand_id"): dict(row) for row in selected_stands}
        current = existing_by_id.get(stand_id, {})
        new_quantity = int(current.get("quantity") or 0) + quantity
        existing_by_id[stand_id] = {
            "stand_id": stand.get("stand_id"),
            "stand_name": stand.get("stand_name"),
            "stand_type": stand.get("stand_type"),
            "sqm": stand.get("sqm"),
            "quantity": new_quantity,
        }
        normalized = normalize_selected_stands(list(existing_by_id.values()))
        used_space = compute_used_space(normalized)
        allowed_space = plan.get("allowed_space")

        updated_plan = {
            **plan,
            "selected_stands": normalized,
            "stand_count": compute_stand_count(normalized),
            "used_space": used_space,
            "remaining_space": (
                None
                if allowed_space is None
                else round(float(allowed_space) - used_space, 2)
            ),
        }
        return updated_plan, None

    @app.callback(
        Output("plan-summary", "children"),
        Output("selected-stands-table", "children"),
        Input("plan-draft-store", "data"),
    )
    def render_plan_builder(plan):
        return _plan_summary_children(plan), _stand_table(plan)

    @app.callback(
        Output("plan-save-btn", "disabled"),
        Input("plan-draft-store", "data"),
    )
    def toggle_save_button(plan):
        return not bool(
            plan
            and plan.get("branch_id")
            and plan.get("facia")
            and plan.get("department")
            and plan.get("selected_stands")
        )

    @app.callback(
        Output("plan-store", "data"),
        Output("plan-status", "children"),
        Output("saved-plan-dd", "value"),
        Input("plan-save-btn", "n_clicks"),
        State("plan-draft-store", "data"),
        State("plan-store", "data"),
        prevent_initial_call=True,
    )
    def save_plan(n_clicks, draft_plan, existing_saved_plan):
        if not n_clicks:
            return no_update, no_update, no_update

        missing = [
            name
            for name, val in [
                ("Branch", (draft_plan or {}).get("branch_id")),
                ("Facia", (draft_plan or {}).get("facia")),
                ("Department", (draft_plan or {}).get("department")),
            ]
            if not val
        ]

        if missing:
            return existing_saved_plan, html.Div(
                f"Missing required fields: {', '.join(missing)}",
                style={"color": "crimson"},
            ), no_update

        if not (draft_plan or {}).get("selected_stands"):
            return existing_saved_plan, html.Div(
                "Add at least one stand before saving the plan.",
                style={"color": "crimson"},
            ), no_update

        now = datetime.now(timezone.utc).isoformat()
        created_at = (
            (existing_saved_plan or {}).get("created_at")
            or draft_plan.get("created_at")
            or now
        )

        plan = {
            **draft_plan,
            "created_at": created_at,
            "updated_at": now,
        }

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
            html.Strong("Plan saved."),
            html.Div(
                f"Branch: {plan['branch_id']} | Facia: {plan['facia']} | "
                f"Dept: {plan['department']} | "
                f"Used {_fmt_number(plan['used_space'])} / Allowed {_fmt_number(plan['allowed_space'])}"
            ),
            html.Small(f"Last updated: {plan['updated_at']}"),
        ]
        if csv_note is not None:
            status_children.append(html.Br())
            status_children.append(csv_note)

        saved_plan_key = make_plan_key(plan)
        status = html.Div(status_children)
        return plan, status, saved_plan_key
