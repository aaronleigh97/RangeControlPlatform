from datetime import datetime, timezone
from uuid import uuid4

from dash import ALL, Input, Output, State, ctx, html, no_update
import dash_bootstrap_components as dbc

from range_control_platform.services.plan_service import (
    build_stand_product_capacity_status,
    branch_saved_plan_ref,
    compute_stand_product_capacity,
    deactivate_plan,
    flatten_plan_stands,
    get_saved_plan,
    list_latest_plans,
    normalize_assigned_products,
    normalize_selected_stands,
    normalize_department_plan,
    normalize_plan_departments,
    persist_plan,
    summarize_plan_departments,
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


def _remaining_space_indicator(allowed_space, remaining_space):
    if allowed_space is None or remaining_space is None:
        return dbc.Badge("Status: Unknown", color="secondary", className="ms-2")

    try:
        allowed = float(allowed_space)
        remaining = float(remaining_space)
    except (TypeError, ValueError):
        return dbc.Badge("Status: Unknown", color="secondary", className="ms-2")

    if remaining < 0:
        return dbc.Badge("Status: Over Limit", color="danger", className="ms-2")

    if remaining == 0:
        return dbc.Badge("Status: No Space Remaining", color="danger", className="ms-2")

    if allowed <= 0:
        return dbc.Badge("Status: Limited Space", color="warning", className="ms-2")

    ratio = remaining / allowed
    if ratio > 0.5:
        return dbc.Badge("Status: Plenty of Space", color="success", className="ms-2")
    if ratio > 0.2:
        return dbc.Badge("Status: Moderate Space", color="warning", className="ms-2")
    return dbc.Badge(
        "Status: Running Low",
        color="warning",
        text_color="dark",
        className="ms-2",
    )


def _over_limit_warning(remaining_space):
    if remaining_space is None:
        return None
    try:
        remaining = float(remaining_space)
    except (TypeError, ValueError):
        return None
    if remaining >= 0:
        return None
    return html.Div(
        f"Over department allowance by {_fmt_number(abs(remaining))} sqm.",
        style={"color": "crimson", "fontWeight": "600"},
    )


def _branch_remaining_space(plan):
    square_footage = (plan or {}).get("square_footage")
    if square_footage is not None:
        try:
            branch_capacity = float(square_footage)
            branch_used = float((plan or {}).get("total_used_space") or 0.0)
            return branch_capacity, round(branch_capacity - branch_used, 2)
        except (TypeError, ValueError):
            return None, None

    departments = normalize_plan_departments({"departments": (plan or {}).get("departments") or []})
    if not departments:
        return None, None

    allowed_total = sum(
        float(row.get("allowed_space") or 0.0)
        for row in departments
        if row.get("allowed_space") is not None
    )
    used_total = sum(float(row.get("used_space") or 0.0) for row in departments)
    return allowed_total, round(allowed_total - used_total, 2)


def _hydrate_saved_plan(row, ref_data):
    store = _find_store(ref_data, row.get("branch_id")) or {}
    hydrated = dict(row)
    hydrated["facia"] = hydrated.get("facia") or store.get("fascia")
    hydrated["branch_name"] = hydrated.get("branch_name") or store.get("branch_name")
    hydrated["store_grade"] = hydrated.get("store_grade") or store.get("store_grade")
    hydrated["square_footage"] = hydrated.get("square_footage") or store.get("square_footage")
    hydrated["budget_2026"] = hydrated.get("budget_2026") or store.get("budget_2026")
    hydrated["plan_name"] = hydrated.get("plan_name")
    return hydrated


def _saved_plan_options(ref_data):
    rows = list_latest_plans()
    return _saved_plan_options_from_rows(rows, ref_data)


def _saved_plan_options_from_rows(rows, ref_data):
    options = []
    seen_values = set()
    for row in rows or []:
        row = _hydrate_saved_plan(row, ref_data)
        title = row.get("plan_name") or f"{row.get('branch_id')} | {row.get('facia')}"
        label = (
            f"{title} | "
            f"{row.get('branch_id')} | {row.get('facia')} | "
            f"{row.get('saved_at') or row.get('updated_at') or ''}"
        )
        value = row.get("saved_plan_ref") or row.get("plan_id") or row.get("plan_key")
        if value in seen_values:
            continue
        seen_values.add(value)
        options.append({"label": label, "value": value})
    return options


def _merge_latest_saved_plan(rows, saved_plan):
    saved_plan = dict(saved_plan or {})
    if not saved_plan:
        return rows or []

    saved_key = saved_plan.get("plan_key")
    merged_rows = []
    replaced = False
    for row in rows or []:
        row_key = row.get("plan_key")
        if row_key == saved_key:
            merged_rows.append(saved_plan)
            replaced = True
        else:
            merged_rows.append(row)

    if not replaced:
        merged_rows.append(saved_plan)

    merged_rows.sort(
        key=lambda row: str(row.get("saved_at") or row.get("updated_at") or ""),
        reverse=True,
    )
    return merged_rows


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


def _find_product(ref_data, product_id, department=None):
    if not ref_data or not product_id:
        return None
    return next(
        (
            row
            for row in ref_data.get("products", [])
            if row.get("product_id") == product_id
            and (not department or row.get("department_name") == department)
        ),
        None,
    )


def _product_options(ref_data, department):
    if not ref_data or not department:
        return []

    products = [
        row
        for row in ref_data.get("products", [])
        if row.get("department_name") == department
    ]
    products.sort(
        key=lambda row: (
            str(row.get("range_name") or ""),
            str(row.get("product_name") or ""),
            str(row.get("product_code") or ""),
        )
    )
    return [
        {
            "label": (
                f"{row.get('product_code') or row.get('product_id')} - "
                f"{row.get('product_name') or 'Unnamed Product'}"
                + (
                    f" ({row.get('range_name')})"
                    if row.get("range_name")
                    else ""
                )
            ),
            "value": row.get("product_id"),
        }
        for row in products
    ]


def _find_selected_stand(plan, department, stand_id):
    department_plan = _get_department_plan(plan, department)
    if not department_plan:
        return None
    target_instance_id = None
    target_stand_id = stand_id
    if isinstance(stand_id, dict):
        target_instance_id = stand_id.get("stand_instance_id")
        target_stand_id = stand_id.get("stand_id")
    return next(
        (
            row
            for row in department_plan.get("selected_stands") or []
            if (
                (target_instance_id and row.get("stand_instance_id") == target_instance_id)
                or (not target_instance_id and row.get("stand_id") == target_stand_id)
            )
        ),
        None,
    )


def _replace_stand_in_department(department_plan, updated_stand):
    selected_stands = []
    replaced = False
    for stand in normalize_selected_stands((department_plan or {}).get("selected_stands")):
        if stand.get("stand_instance_id") == updated_stand.get("stand_instance_id"):
            selected_stands.append(updated_stand)
            replaced = True
        else:
            selected_stands.append(stand)

    if not replaced:
        selected_stands.append(updated_stand)

    return {
        **(department_plan or {}),
        "selected_stands": normalize_selected_stands(selected_stands),
    }


def _stand_product_feedback(stand):
    capacity_class = stand.get("stand_height") or stand.get("stand_type")
    status = build_stand_product_capacity_status(
        stand.get("assigned_products"),
        stand.get("arms"),
        capacity_class,
        quantity=stand.get("quantity"),
    )
    if status["capacity"] is None:
        body = "Product guidance is unavailable because this stand does not expose a supported single/double capacity class."
    elif status["status"] == "over_capacity":
        body = (
            f"{status['assigned_count']} assigned against capacity {status['capacity']}. "
            f"Remove {abs(status['remaining_slots'])} row(s) to get back within guidance."
        )
    elif status["status"] == "just_right":
        body = f"{status['assigned_count']} assigned against capacity {status['capacity']}. This stand is at guidance capacity."
    else:
        body = (
            f"{status['assigned_count']} assigned against capacity {status['capacity']}. "
            f"{status['remaining_slots']} slot(s) still open."
        )

    return dbc.Alert(
        [
            html.Strong(f"Status: {status['label']}"),
            html.Div(body),
            html.Small(
                "This is a simplified guidance rail based on stand arms and single/double class, not product dimensions."
            ),
        ],
        color=status["color"],
        className="mb-0",
    )


def _get_department_plan(plan, department):
    if not plan or not department:
        return None
    for department_plan in normalize_plan_departments(plan):
        if department_plan.get("department") == department:
            return department_plan
    return None


def _replace_department_plan(plan, department_plan):
    if not department_plan:
        return normalize_plan_departments(plan)

    updated_departments = []
    replaced = False
    for existing in normalize_plan_departments(plan):
        if existing.get("department") == department_plan.get("department"):
            updated_departments.append(normalize_department_plan(department_plan))
            replaced = True
        else:
            updated_departments.append(existing)

    if not replaced:
        updated_departments.append(normalize_department_plan(department_plan))

    updated_departments = [
        row
        for row in updated_departments
        if row and (row.get("selected_stands") or [])
    ]
    updated_departments.sort(key=lambda row: str(row.get("department") or ""))
    return updated_departments


def _decorate_plan(plan, ref_data):
    plan = dict(plan or {})
    branch_id = plan.get("branch_id")
    store = _find_store(ref_data, branch_id) or {}
    store_grade = store.get("store_grade") or store.get("grade") or plan.get("store_grade")
    current_department = plan.get("department")
    departments = normalize_plan_departments({"departments": plan.get("departments") or []})
    current_department_plan = _get_department_plan({"departments": departments}, current_department)

    allowed_space = None
    selected_stands = []
    plan_department_id = None
    if current_department_plan:
        allowed_space = current_department_plan.get("allowed_space")
        selected_stands = current_department_plan.get("selected_stands") or []
        plan_department_id = current_department_plan.get("plan_department_id")
    elif current_department:
        allowed_space = _find_department_allocation(ref_data, current_department, store_grade)

    used_space = normalize_department_plan(
        {
            "department": current_department,
            "allowed_space": allowed_space,
            "selected_stands": selected_stands,
        }
    ) or {
        "used_space": 0.0,
        "remaining_space": (
            None if allowed_space is None else round(float(allowed_space) - 0.0, 2)
        ),
        "stand_count": 0,
    }
    totals = summarize_plan_departments({"departments": departments})

    return {
        **plan,
        "branch_name": store.get("branch_name") or plan.get("branch_name"),
        "facia": plan.get("facia") or store.get("fascia"),
        "store_grade": store_grade,
        "square_footage": store.get("square_footage") or plan.get("square_footage"),
        "budget_2026": store.get("budget_2026") or plan.get("budget_2026"),
        "departments": departments,
        "plan_department_id": plan_department_id,
        "allowed_space": allowed_space,
        "allowed_space_unit": "linear_meter",
        "used_space": used_space.get("used_space", 0.0),
        "remaining_space": used_space.get("remaining_space"),
        "stand_count": used_space.get("stand_count", 0),
        "selected_stands": selected_stands,
        "department_count": totals.get("department_count", 0),
        "total_used_space": totals.get("total_used_space", 0.0),
        "total_stand_units": totals.get("total_stand_units", 0),
    }


def _build_plan_context(ref_data, facia, branch_id, department, existing_plan=None):
    existing_plan = existing_plan or {}
    effective_facia = facia or existing_plan.get("facia")
    effective_branch_id = branch_id or existing_plan.get("branch_id")
    # The active editing department should only come from the visible dropdown selection.
    effective_department = department

    same_branch = (
        existing_plan.get("branch_id") == effective_branch_id
        and (existing_plan.get("facia") == effective_facia or not effective_facia)
    )
    departments = normalize_plan_departments(
        {"departments": (existing_plan or {}).get("departments") or []}
        if same_branch
        else None
    )
    department_context_changed = existing_plan.get("department") != effective_department
    return _decorate_plan(
        {
            **existing_plan,
            "branch_id": effective_branch_id,
            "facia": effective_facia,
            "department": effective_department,
            "departments": departments,
            "plan_department_id": (
                None if department_context_changed else existing_plan.get("plan_department_id")
            ),
            "allowed_space": None if department_context_changed else existing_plan.get("allowed_space"),
            "used_space": 0.0 if department_context_changed else existing_plan.get("used_space"),
            "remaining_space": (
                None if department_context_changed else existing_plan.get("remaining_space")
            ),
            "stand_count": 0 if department_context_changed else existing_plan.get("stand_count"),
            "selected_stands": [] if department_context_changed else existing_plan.get("selected_stands"),
        },
        ref_data,
    )


def _compose_plan(ref_data, draft_plan=None, departments=None):
    draft_plan = dict(draft_plan or {})
    return _decorate_plan(
        {
            **draft_plan,
            "departments": departments or [],
        },
        ref_data,
    )


def _default_plan_name(plan):
    if not plan:
        return None
    existing_name = str(plan.get("plan_name") or "").strip()
    if existing_name:
        return existing_name
    branch_id = plan.get("branch_id")
    facia = plan.get("facia")
    if branch_id and facia:
        return f"{branch_id} {facia} Draft"
    if branch_id:
        return f"{branch_id} Draft"
    return None


def _cleared_plan_builder_state(status_message=None, *, clear_saved_selection=True):
    return (
        None if clear_saved_selection else no_update,
        None,
        None,
        [],
        "",
        None,
        None,
        None,
        None,
        status_message,
    )


def _cleared_plan_builder_state_without_options(status_message=None, *, clear_saved_selection=True):
    return (
        None if clear_saved_selection else no_update,
        None,
        None,
        [],
        "",
        None,
        None,
        None,
        status_message,
    )


def _plan_summary_children(plan):
    if not plan:
        return html.Div("Select a store and department to start building a plan.")

    totals = summarize_plan_departments(plan)
    departments = normalize_plan_departments(plan)
    current_department = plan.get("department") or "N/A"
    branch_allowed_space, branch_remaining_space = _branch_remaining_space(plan)

    breakdown_table = html.Div("No departments added to the current branch draft yet.")
    if departments:
        breakdown_header = html.Thead(
                    html.Tr(
                        [
                            html.Th("Department"),
                            html.Th("Allowed (sqm)"),
                            html.Th("Used (sqm)"),
                            html.Th("Remaining (sqm)"),
                            html.Th("Stand Units"),
                        ]
                    )
        )
        breakdown_body = html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(row.get("department") or "N/A"),
                        html.Td(_fmt_number(row.get("allowed_space"))),
                        html.Td(_fmt_number(row.get("used_space"))),
                        html.Td(_fmt_number(row.get("remaining_space"))),
                        html.Td(row.get("stand_count", 0)),
                    ]
                )
                for row in departments
            ]
        )
        breakdown_table = dbc.Table(
            [breakdown_header, breakdown_body],
            bordered=False,
            hover=True,
            striped=True,
            size="sm",
        )

    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div(
                                        [
                                            html.H6("Branch Draft Status", className="mb-0"),
                                            _remaining_space_indicator(
                                                branch_allowed_space,
                                                branch_remaining_space,
                                            ),
                                        ],
                                        className="d-flex align-items-center justify-content-between",
                                    ),
                                    html.Div(f"Branch: {plan.get('branch_id') or 'N/A'}"),
                                    html.Div(f"Facia: {plan.get('facia') or 'N/A'}"),
                                    html.Div(f"Plan name: {plan.get('plan_name') or 'N/A'}"),
                                    html.Div(f"Store grade: {plan.get('store_grade') or 'N/A'}"),
                                    html.Div(
                                        f"Square footage: {_fmt_number(plan.get('square_footage'))}"
                                    ),
                                    html.Div(
                                        f"Departments currently added: {totals.get('department_count', 0)}"
                                    ),
                                    html.Div(
                                        "Branch accommodated space (sqm): "
                                        f"{_fmt_number(totals.get('total_used_space'))}"
                                    ),
                                    html.Div(
                                        "Branch remaining space (sqm): "
                                        f"{_fmt_number(branch_remaining_space)}"
                                    ),
                                    html.Div(
                                        f"Branch plan stand units: {totals.get('total_stand_units', 0)}"
                                    ),
                                    _over_limit_warning(branch_remaining_space),
                                ]
                            )
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div(
                                        [
                                            html.H6("Current Department", className="mb-0"),
                                            _remaining_space_indicator(
                                                plan.get("allowed_space"),
                                                plan.get("remaining_space"),
                                            ),
                                        ],
                                        className="d-flex align-items-center justify-content-between",
                                    ),
                                    html.Div(f"Editing department: {current_department}"),
                                    html.Div(
                                        "Allowed department space (sqm): "
                                        f"{_fmt_number(plan.get('allowed_space'))}"
                                    ),
                                    html.Div(
                                        f"Used stand area (sqm): {_fmt_number(plan.get('used_space'))}"
                                    ),
                                    html.Div(
                                        "Remaining department space (sqm): "
                                        f"{_fmt_number(plan.get('remaining_space'))}"
                                    ),
                                    html.Div(
                                        f"Selected stand units: {plan.get('stand_count', 0)}"
                                    ),
                                    _over_limit_warning(plan.get("remaining_space")),
                                    html.Small(
                                        "Department space allowance is derived from the store grade "
                                        "and department allocation rules."
                                    ),
                                ]
                            )
                        ),
                        width=6,
                    ),
                ],
                className="g-2",
            ),
            html.Hr(),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H6("Department Breakdown"),
                        breakdown_table,
                    ]
                )
            ),
        ]
    )


def _selected_stand_departments(plan):
    departments = sorted(
        {
            stand.get("department")
            for stand in flatten_plan_stands(plan)
            if stand.get("department")
        }
    )
    return departments


def _stand_table(plan, department_filter=None):
    selected_stands = flatten_plan_stands(plan)
    if department_filter:
        selected_stands = [
            stand for stand in selected_stands if stand.get("department") == department_filter
        ]
    if not selected_stands:
        if department_filter:
            return html.Div(f"No stands added yet for {department_filter}.")
        return html.Div("No stands added yet.")

    header = html.Thead(
        html.Tr(
            [
                html.Th("Department"),
                html.Th("Instance"),
                html.Th("Stand ID"),
                html.Th("Stand"),
                html.Th("Type"),
                html.Th("Sqm"),
                html.Th("Product Guidance"),
                html.Th("Product Range"),
                html.Th("Remove"),
            ]
        )
    )
    body = html.Tbody(
        [
            html.Tr(
                [
                    html.Td(stand.get("department") or "N/A"),
                    html.Td(stand.get("stand_instance_id") or "N/A"),
                    html.Td(stand.get("stand_id")),
                    html.Td(stand.get("stand_name")),
                    html.Td(stand.get("stand_type") or ""),
                    html.Td(_fmt_number(stand.get("sqm"))),
                    html.Td(
                        dbc.Badge(
                            (
                                f"{status.get('label')}: "
                                f"{status.get('assigned_count')}/{_fmt_number(status.get('capacity'))}"
                            ),
                            color=status.get("color"),
                        )
                    ),
                    html.Td(
                        dbc.Button(
                            "Edit",
                            id={
                                "type": "open-product-range-btn",
                                "department": stand.get("department"),
                                "stand_id": stand.get("stand_id"),
                                "stand_instance_id": stand.get("stand_instance_id"),
                            },
                            color="secondary",
                            size="sm",
                            outline=True,
                        )
                    ),
                    html.Td(
                        dbc.Button(
                            "Remove",
                            id={
                                "type": "remove-stand-btn",
                                "department": stand.get("department"),
                                "stand_id": stand.get("stand_id"),
                                "stand_instance_id": stand.get("stand_instance_id"),
                            },
                            color="link",
                            size="sm",
                            className="p-0",
                        )
                    ),
                ]
            )
            for stand in selected_stands
            for status in [
                build_stand_product_capacity_status(
                    stand.get("assigned_products"),
                    stand.get("arms"),
                    stand.get("stand_height") or stand.get("stand_type"),
                    stand.get("quantity"),
                )
            ]
        ]
    )
    return dbc.Table([header, body], bordered=False, hover=True, striped=True, size="sm")


def register_plan_callbacks(app):
    @app.callback(
        Output("saved-plan-dd", "options"),
        Input("ref-data-store", "data"),
    )
    def populate_saved_plan_list(ref_data):
        return _saved_plan_options(ref_data)

    @app.callback(
        Output("plan-load-btn", "disabled"),
        Output("plan-delete-btn", "disabled"),
        Output("plan-unload-btn", "disabled"),
        Input("saved-plan-dd", "value"),
        Input("plan-draft-store", "data"),
        Input("plan-departments-store", "data"),
    )
    def toggle_saved_plan_actions(selected_plan_key, draft_plan, departments):
        snapshot_action_disabled = not bool(selected_plan_key)
        has_draft_state = bool(
            draft_plan
            or (departments or [])
            or (draft_plan or {}).get("branch_id")
            or (draft_plan or {}).get("facia")
        )
        return snapshot_action_disabled, snapshot_action_disabled, not has_draft_state

    @app.callback(
        Output("saved-plan-dd", "options", allow_duplicate=True),
        Output("saved-plan-dd", "value", allow_duplicate=True),
        Output("plan-store", "data", allow_duplicate=True),
        Output("plan-draft-store", "data", allow_duplicate=True),
        Output("plan-departments-store", "data", allow_duplicate=True),
        Output("plan-name-input", "value", allow_duplicate=True),
        Output("facia-dd", "value", allow_duplicate=True),
        Output("branch-dd", "value", allow_duplicate=True),
        Output("dept-dd", "value", allow_duplicate=True),
        Output("plan-status", "children", allow_duplicate=True),
        Input("plan-delete-btn", "n_clicks"),
        State("saved-plan-dd", "value"),
        State("ref-data-store", "data"),
        prevent_initial_call=True,
    )
    def delete_selected_plan(_n_clicks, selected_plan_key, ref_data):
        if not selected_plan_key:
            return (no_update,) * 10

        try:
            deleted_plan = deactivate_plan(selected_plan_key)
        except Exception as exc:
            status = html.Div(
                f"Plan delete failed: {exc}",
                style={"color": "crimson"},
            )
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, status

        status = html.Div(
            dbc.Alert(
                [
                    html.Strong("Plan deleted from the active snapshot list."),
                    html.Div(
                        f"Plan name: {deleted_plan.get('plan_name') or 'N/A'}"
                    ),
                    html.Div(
                        f"Branch: {deleted_plan.get('branch_id')} | Facia: {deleted_plan.get('facia')}"
                    ),
                    html.Small(
                        "A new inactive snapshot was saved. Historical snapshots remain in storage."
                    ),
                ],
                color="warning",
                dismissable=True,
                className="mb-0",
            )
        )
        refreshed_options = _saved_plan_options(ref_data)
        return (
            refreshed_options,
            *_cleared_plan_builder_state_without_options(status),
        )

    @app.callback(
        Output("saved-plan-dd", "value", allow_duplicate=True),
        Output("plan-store", "data", allow_duplicate=True),
        Output("plan-draft-store", "data", allow_duplicate=True),
        Output("plan-departments-store", "data", allow_duplicate=True),
        Output("plan-name-input", "value", allow_duplicate=True),
        Output("facia-dd", "value", allow_duplicate=True),
        Output("branch-dd", "value", allow_duplicate=True),
        Output("dept-dd", "value", allow_duplicate=True),
        Output("stand-library-dd", "value", allow_duplicate=True),
        Output("plan-status", "children", allow_duplicate=True),
        Input("plan-unload-btn", "n_clicks"),
        State("plan-draft-store", "data"),
        State("plan-departments-store", "data"),
        prevent_initial_call=True,
    )
    def unload_current_plan(_n_clicks, draft_plan, departments):
        has_draft_state = bool(
            draft_plan
            or (departments or [])
            or (draft_plan or {}).get("branch_id")
            or (draft_plan or {}).get("facia")
        )
        if not has_draft_state:
            return (no_update,) * 10

        status = html.Div(
            dbc.Alert(
                "Loaded plan context cleared. Start a new draft or load another saved plan.",
                color="warning",
                dismissable=True,
                className="mb-0",
            )
        )
        return _cleared_plan_builder_state(status)

    @app.callback(
        Output("facia-dd", "value", allow_duplicate=True),
        Output("branch-dd", "value", allow_duplicate=True),
        Output("dept-dd", "value", allow_duplicate=True),
        Output("plan-name-input", "value", allow_duplicate=True),
        Output("plan-draft-store", "data", allow_duplicate=True),
        Output("plan-departments-store", "data", allow_duplicate=True),
        Output("plan-store", "data", allow_duplicate=True),
        Output("plan-status", "children", allow_duplicate=True),
        Input("plan-load-btn", "n_clicks"),
        State("saved-plan-dd", "value"),
        State("ref-data-store", "data"),
        prevent_initial_call=True,
    )
    def load_selected_plan(_n_clicks, selected_plan_key, ref_data):
        if not selected_plan_key:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

        row = get_saved_plan(selected_plan_key)
        if not row:
            status = html.Div(
                "Selected plan could not be found in the available plan storage.",
                style={"color": "crimson"},
            )
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, status

        row = _hydrate_saved_plan(row, ref_data)
        departments = row.get("departments", [])

        draft_plan = {
            "plan_name": row.get("plan_name"),
            "branch_id": row.get("branch_id"),
            "facia": row.get("facia"),
            "department": row.get("department"),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at") or row.get("saved_at"),
            "plan_id": row.get("plan_id"),
            "status": row.get("status"),
        }
        plan = _compose_plan(ref_data, draft_plan, departments)

        status = html.Div(
            dbc.Alert(
                [
                    html.Strong(
                        f"Plan loaded from {row.get('storage_backend', 'saved')} storage."
                    ),
                    html.Div(
                        f"Plan name: {plan.get('plan_name') or 'N/A'}"
                    ),
                    html.Div(
                        f"Branch: {plan['branch_id']} | Facia: {plan['facia']}"
                    ),
                    html.Div(
                        f"Departments in snapshot: {len(normalize_plan_departments(plan))}"
                    ),
                    html.Small(f"Loaded snapshot timestamp: {row.get('saved_at') or 'N/A'}"),
                ],
                color="success",
                dismissable=True,
                className="mb-0",
            )
        )

        return (
            plan["facia"],
            plan["branch_id"],
            plan["department"],
            plan.get("plan_name"),
            draft_plan,
            departments,
            plan,
            status,
        )

    @app.callback(
        Output("facia-dd", "value", allow_duplicate=True),
        Output("branch-dd", "value", allow_duplicate=True),
        Output("dept-dd", "value", allow_duplicate=True),
        Input("plan-store", "data"),
        Input("plan-draft-store", "data"),
        Input("branch-dd", "options"),
        Input("dept-dd", "options"),
        State("facia-dd", "value"),
        State("branch-dd", "value"),
        State("dept-dd", "value"),
        prevent_initial_call=True,
    )
    def sync_loaded_plan_into_dropdowns(
        saved_plan,
        draft_plan,
        branch_options,
        dept_options,
        current_facia,
        current_branch,
        current_department,
    ):
        source_plan = draft_plan or saved_plan
        if not source_plan:
            return no_update, no_update, no_update

        target_facia = source_plan.get("facia")
        target_branch = source_plan.get("branch_id")
        target_department = source_plan.get("department")

        next_facia = no_update
        next_branch = no_update
        next_department = no_update

        if target_facia and not current_facia:
            next_facia = target_facia

        branch_values = {opt.get("value") for opt in (branch_options or [])}
        if target_branch and target_branch in branch_values and not current_branch:
            next_branch = target_branch

        dept_values = {opt.get("value") for opt in (dept_options or [])}
        if (
            target_department
            and target_department in dept_values
            and not current_department
        ):
            next_department = target_department

        return next_facia, next_branch, next_department

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
            department_names = []

        if not department_names:
            department_names = sorted(
                {
                    row.get("department_name")
                    for row in ref_data.get("department_grade_allocations", [])
                    if row.get("department_name")
                }
            ) or ref_data.get("departments", [])

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
        Input("plan-name-input", "value"),
        Input("facia-dd", "value"),
        Input("branch-dd", "value"),
        Input("dept-dd", "value"),
        State("plan-draft-store", "data"),
        State("plan-departments-store", "data"),
        prevent_initial_call=True,
    )
    def sync_plan_context(ref_data, plan_name, facia, branch_id, department, existing_plan, departments):
        if not ref_data:
            return existing_plan

        effective_facia = facia or (existing_plan or {}).get("facia")
        effective_branch = branch_id or (existing_plan or {}).get("branch_id")

        if not any([effective_facia, effective_branch, department, (existing_plan or {}).get("department")]):
            return None

        plan = _build_plan_context(
            ref_data,
            effective_facia,
            effective_branch,
            department,
            {
                **(existing_plan or {}),
                "plan_name": plan_name or (existing_plan or {}).get("plan_name"),
            },
        )
        same_branch = (
            (existing_plan or {}).get("branch_id") == effective_branch
            and ((existing_plan or {}).get("facia") == effective_facia or not effective_facia)
        )
        kept_departments = departments if same_branch else []
        return {
            **plan,
            "plan_name": plan_name or plan.get("plan_name"),
            "departments": kept_departments or [],
        }

    @app.callback(
        Output("plan-departments-store", "data", allow_duplicate=True),
        Input("facia-dd", "value"),
        Input("branch-dd", "value"),
        State("plan-draft-store", "data"),
        prevent_initial_call=True,
    )
    def clear_department_rows_on_branch_change(selected_facia, selected_branch, existing_plan):
        if not existing_plan:
            return no_update

        existing_facia = existing_plan.get("facia")
        existing_branch = existing_plan.get("branch_id")
        if selected_facia and selected_branch and (
            selected_facia != existing_facia or selected_branch != existing_branch
        ):
            return []
        return no_update

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
        Output("plan-departments-store", "data", allow_duplicate=True),
        Output("plan-draft-store", "data", allow_duplicate=True),
        Output("stand-library-dd", "value"),
        Input("add-stand-btn", "n_clicks"),
        Input("clear-stands-btn", "n_clicks"),
        Input(
            {"type": "remove-stand-btn", "department": ALL, "stand_id": ALL, "stand_instance_id": ALL},
            "n_clicks",
        ),
        State("stand-library-dd", "value"),
        State("stand-qty", "value"),
        State("dept-dd", "value"),
        State("plan-draft-store", "data"),
        State("plan-departments-store", "data"),
        State("ref-data-store", "data"),
        prevent_initial_call=True,
    )
    def update_selected_stands(
        _add_clicks,
        _clear_clicks,
        _remove_clicks,
        stand_id,
        quantity,
        selected_department,
        plan,
        departments,
        ref_data,
    ):
        if not plan:
            return no_update, no_update, no_update

        trigger = ctx.triggered_id
        current_department = selected_department or plan.get("department")
        department_plan_state = {"departments": departments or []}
        current_department_plan = _get_department_plan(department_plan_state, current_department) or {}
        selected_stands = normalize_selected_stands(current_department_plan.get("selected_stands"))
        allowed_space = current_department_plan.get("allowed_space")
        if allowed_space is None:
            allowed_space = _find_department_allocation(
                ref_data,
                current_department,
                plan.get("store_grade"),
            )

        if trigger == "clear-stands-btn":
            updated_departments = _replace_department_plan(
                department_plan_state,
                {
                    **current_department_plan,
                    "department": current_department,
                    "store_grade": plan.get("store_grade"),
                    "allowed_space": allowed_space,
                    "selected_stands": [],
                },
            )
            updated_plan = _compose_plan(
                ref_data,
                {**plan, "department": current_department},
                updated_departments,
            )
            return updated_departments, updated_plan, None

        if isinstance(trigger, dict) and trigger.get("type") == "remove-stand-btn":
            if not any(click_count for click_count in (_remove_clicks or []) if click_count):
                return no_update, no_update, no_update
            department_name = trigger.get("department")
            stand_to_remove = trigger.get("stand_instance_id")
            target_department = _get_department_plan(department_plan_state, department_name) or {}
            filtered_stands = [
                row
                for row in normalize_selected_stands(target_department.get("selected_stands"))
                if row.get("stand_instance_id") != stand_to_remove
            ]
            updated_departments = _replace_department_plan(
                department_plan_state,
                {
                    **target_department,
                    "department": department_name,
                    "store_grade": target_department.get("store_grade") or plan.get("store_grade"),
                    "allowed_space": target_department.get("allowed_space"),
                    "selected_stands": filtered_stands,
                },
            )
            updated_plan = _compose_plan(ref_data, plan, updated_departments)
            return updated_departments, updated_plan, no_update

        stand = _find_stand(ref_data, stand_id)
        if not stand or not quantity or quantity <= 0:
            return no_update, no_update, no_update

        quantity = int(quantity)
        new_instances = [
            {
                "stand_instance_id": str(uuid4()),
                "stand_id": stand.get("stand_id"),
                "stand_name": stand.get("stand_name"),
                "stand_type": stand.get("stand_type"),
                "stand_height": stand.get("stand_height"),
                "arms": stand.get("arms"),
                "sqm": stand.get("sqm"),
                "quantity": 1,
                "assigned_products": [],
            }
            for _ in range(quantity)
        ]
        normalized = normalize_selected_stands([*selected_stands, *new_instances])
        updated_departments = _replace_department_plan(
            department_plan_state,
            {
                **current_department_plan,
                "department": current_department,
                "store_grade": plan.get("store_grade"),
                "allowed_space": allowed_space,
                "selected_stands": normalized,
            },
        )
        updated_plan = _compose_plan(
            ref_data,
            {**plan, "department": current_department},
            updated_departments,
        )
        return updated_departments, updated_plan, None

    @app.callback(
        Output("product-range-offcanvas", "is_open"),
        Output("product-range-stand-store", "data"),
        Output("product-range-dd", "value"),
        Output("product-range-feedback", "children"),
        Input(
            {"type": "open-product-range-btn", "department": ALL, "stand_id": ALL, "stand_instance_id": ALL},
            "n_clicks",
        ),
        Input("product-range-close-btn", "n_clicks"),
        Input("plan-draft-store", "data"),
        Input("plan-departments-store", "data"),
        State("product-range-stand-store", "data"),
        prevent_initial_call=True,
    )
    def toggle_product_range_offcanvas(
        _open_clicks,
        _close_clicks,
        plan,
        departments,
        active_stand,
    ):
        trigger = ctx.triggered_id
        composed_plan = {"departments": departments or []}

        if not plan:
            return False, None, None, None

        if trigger == "product-range-close-btn":
            return False, None, None, None

        if isinstance(trigger, dict) and trigger.get("type") == "open-product-range-btn":
            if not any(click_count for click_count in (_open_clicks or []) if click_count):
                return False, None, None, None
            stand_ref = {
                "department": trigger.get("department"),
                "stand_id": trigger.get("stand_id"),
                "stand_instance_id": trigger.get("stand_instance_id"),
            }
            return True, stand_ref, None, None

        if trigger in {"plan-draft-store", "plan-departments-store"}:
            return False, None, None, None

        return False, None, None, None

    @app.callback(
        Output("product-range-stand-summary", "children"),
        Output("product-range-assigned-table", "children"),
        Output("product-range-dd", "options"),
        Output("product-range-dd", "disabled"),
        Input("product-range-stand-store", "data"),
        Input("plan-departments-store", "data"),
        Input("ref-data-store", "data"),
    )
    def render_product_range_panel(active_stand, departments, ref_data):
        if not active_stand:
            return html.Div("Select a stand to assign product rows."), html.Div(), [], True

        plan = {"departments": departments or []}
        stand = _find_selected_stand(
            plan,
            active_stand.get("department"),
            {
                "stand_id": active_stand.get("stand_id"),
                "stand_instance_id": active_stand.get("stand_instance_id"),
            },
        )
        if not stand:
            return html.Div("Selected stand is no longer available in the draft."), html.Div(), [], True

        capacity = compute_stand_product_capacity(
            stand.get("arms"),
            stand.get("stand_height") or stand.get("stand_type"),
            quantity=stand.get("quantity"),
        )
        summary = html.Div(
            [
                html.Div(
                    f"{active_stand.get('department')} | {stand.get('stand_id')} - {stand.get('stand_name')}"
                ),
                html.Small(
                    f"Instance: {stand.get('stand_instance_id') or 'N/A'} | "
                    f"Stand type: {stand.get('stand_type') or 'N/A'} | Capacity class: {stand.get('stand_height') or 'N/A'} | Arms: {_fmt_number(stand.get('arms'))} | "
                    f"Quantity: {stand.get('quantity') or 0} | Capacity: {_fmt_number(capacity)}"
                ),
                html.Div(className="mt-2", children=_stand_product_feedback(stand)),
            ]
        )

        assigned_products = normalize_assigned_products(stand.get("assigned_products"))
        if assigned_products:
            assigned_table = dbc.Table(
                [
                    html.Thead(
                        html.Tr(
                            [
                                html.Th("Code"),
                                html.Th("Product"),
                                html.Th("Range"),
                                html.Th("Remove"),
                            ]
                        )
                    ),
                    html.Tbody(
                        [
                            html.Tr(
                                [
                                    html.Td(product.get("product_code") or product.get("product_id")),
                                    html.Td(product.get("product_name") or "N/A"),
                                    html.Td(product.get("range_name") or "N/A"),
                                    html.Td(
                                        dbc.Button(
                                            "Remove",
                                            id={
                                                "type": "remove-product-range-btn",
                                                "department": active_stand.get("department"),
                                                "stand_id": active_stand.get("stand_id"),
                                                "stand_instance_id": active_stand.get("stand_instance_id"),
                                                "product_id": product.get("product_id"),
                                            },
                                            color="link",
                                            size="sm",
                                            className="p-0",
                                        )
                                    ),
                                ]
                            )
                            for product in assigned_products
                        ]
                    ),
                ],
                bordered=False,
                hover=True,
                striped=True,
                size="sm",
            )
        else:
            assigned_table = html.Div("No product rows assigned to this stand yet.")

        options = _product_options(ref_data, active_stand.get("department"))
        return summary, assigned_table, options, not bool(options)

    @app.callback(
        Output("product-range-add-btn", "disabled"),
        Input("product-range-stand-store", "data"),
        Input("product-range-dd", "value"),
    )
    def toggle_product_range_add(active_stand, selected_product_id):
        return not bool(active_stand and selected_product_id)

    @app.callback(
        Output("plan-departments-store", "data", allow_duplicate=True),
        Output("plan-draft-store", "data", allow_duplicate=True),
        Output("product-range-dd", "value", allow_duplicate=True),
        Output("product-range-feedback", "children", allow_duplicate=True),
        Input("product-range-add-btn", "n_clicks"),
        Input(
            {
                "type": "remove-product-range-btn",
                "department": ALL,
                "stand_id": ALL,
                "stand_instance_id": ALL,
                "product_id": ALL,
            },
            "n_clicks",
        ),
        State("product-range-dd", "value"),
        State("product-range-stand-store", "data"),
        State("plan-draft-store", "data"),
        State("plan-departments-store", "data"),
        State("ref-data-store", "data"),
        prevent_initial_call=True,
    )
    def update_product_range_assignments(
        _add_clicks,
        _remove_clicks,
        selected_product_id,
        active_stand,
        plan,
        departments,
        ref_data,
    ):
        if not plan or not active_stand:
            return no_update, no_update, no_update, no_update

        trigger = ctx.triggered_id
        department_plan_state = {"departments": departments or []}
        target_department = _get_department_plan(
            department_plan_state,
            active_stand.get("department"),
        )
        if not target_department:
            return no_update, no_update, no_update, no_update

        stand = _find_selected_stand(
            department_plan_state,
            active_stand.get("department"),
            {
                "stand_id": active_stand.get("stand_id"),
                "stand_instance_id": active_stand.get("stand_instance_id"),
            },
        )
        if not stand:
            return no_update, no_update, no_update, no_update

        assigned_products = normalize_assigned_products(stand.get("assigned_products"))

        if isinstance(trigger, dict) and trigger.get("type") == "remove-product-range-btn":
            if not any(click_count for click_count in (_remove_clicks or []) if click_count):
                return no_update, no_update, no_update, no_update
            updated_products = [
                row for row in assigned_products if row.get("product_id") != trigger.get("product_id")
            ]
        else:
            product = _find_product(
                ref_data,
                selected_product_id,
                department=active_stand.get("department"),
            )
            if not product:
                return no_update, no_update, no_update, no_update
            updated_products = normalize_assigned_products([*assigned_products, product])

        updated_stand = {
            **stand,
            "assigned_products": updated_products,
        }
        updated_department = _replace_stand_in_department(target_department, updated_stand)
        updated_departments = _replace_department_plan(
            department_plan_state,
            {
                **updated_department,
                "department": active_stand.get("department"),
            },
        )
        updated_plan = _compose_plan(
            ref_data,
            {**plan, "department": active_stand.get("department")},
            updated_departments,
        )
        return updated_departments, updated_plan, None, _stand_product_feedback(updated_stand)

    @app.callback(
        Output("plan-summary", "children"),
        Output("selected-stands-table", "children"),
        Output("selected-stands-dept-filter", "options"),
        Output("selected-stands-dept-filter", "disabled"),
        Output("selected-stands-dept-filter", "value"),
        Input("plan-draft-store", "data"),
        Input("plan-departments-store", "data"),
        Input("selected-stands-dept-filter", "value"),
        State("ref-data-store", "data"),
    )
    def render_plan_builder(plan, departments, selected_stands_department, ref_data):
        plan = _compose_plan(ref_data, plan, departments)
        stand_departments = _selected_stand_departments(plan)
        filter_options = [{"label": "ALL", "value": "__all__"}] + [
            {"label": department, "value": department}
            for department in stand_departments
        ]
        effective_filter = (
            None
            if not selected_stands_department or selected_stands_department == "__all__"
            else selected_stands_department
        )
        next_filter_value = (
            selected_stands_department
            if selected_stands_department in {option["value"] for option in filter_options}
            else "__all__"
        )
        return (
            _plan_summary_children(plan),
            _stand_table(plan, effective_filter),
            filter_options,
            not bool(stand_departments),
            next_filter_value,
        )

    @app.callback(
        Output("plan-save-btn", "disabled"),
        Input("plan-draft-store", "data"),
        Input("plan-departments-store", "data"),
    )
    def toggle_save_button(plan, departments):
        department_rows = normalize_plan_departments({"departments": departments or []})
        return not bool(
            plan
            and plan.get("branch_id")
            and plan.get("facia")
            and department_rows
            and any(row.get("selected_stands") for row in department_rows)
        )

    @app.callback(
        Output("plan-store", "data"),
        Output("plan-status", "children"),
        Output("saved-plan-dd", "options", allow_duplicate=True),
        Output("saved-plan-dd", "value"),
        Input("plan-save-btn", "n_clicks"),
        State("plan-draft-store", "data"),
        State("plan-departments-store", "data"),
        State("plan-store", "data"),
        State("saved-plan-dd", "options"),
        State("ref-data-store", "data"),
        prevent_initial_call=True,
    )
    def save_plan(
        n_clicks,
        draft_plan,
        departments,
        existing_saved_plan,
        existing_saved_plan_options,
        ref_data,
    ):
        if not n_clicks:
            return no_update, no_update, no_update, no_update

        missing = [
            name
            for name, val in [
                ("Branch", (draft_plan or {}).get("branch_id")),
                ("Facia", (draft_plan or {}).get("facia")),
            ]
            if not val
        ]

        if missing:
            return existing_saved_plan, html.Div(
                f"Missing required fields: {', '.join(missing)}",
                style={"color": "crimson"},
            ), no_update, no_update

        department_rows = normalize_plan_departments({"departments": departments or []})
        if not any(row.get("selected_stands") for row in department_rows):
            return existing_saved_plan, html.Div(
                "Add at least one stand before saving the plan.",
                style={"color": "crimson"},
            ), no_update, no_update

        now = datetime.now(timezone.utc).isoformat()
        created_at = (
            (existing_saved_plan or {}).get("created_at")
            or draft_plan.get("created_at")
            or now
        )

        plan = {
            **draft_plan,
            "plan_name": _default_plan_name(draft_plan),
            "departments": department_rows,
            "created_at": created_at,
            "updated_at": now,
        }
        plan = _compose_plan(None, plan, department_rows)

        storage_note = None
        try:
            persisted_plan = persist_plan(plan)
            plan = {**plan, **persisted_plan}
            backend = plan.get("storage_backend", "unknown")
            if backend == "bigquery":
                storage_note = html.Small(f"Saved to BigQuery plan_id: {plan.get('plan_id')}")
            elif backend == "csv-fallback":
                storage_note = html.Small(
                    f"BigQuery save failed, fell back to CSV: {plan.get('storage_location')}",
                    style={"color": "darkorange"},
                )
            else:
                storage_note = html.Small(f"Saved to CSV: {plan.get('storage_location')}")
        except Exception as exc:
            storage_note = html.Small(
                f"Plan save failed: {exc}",
                style={"color": "crimson"},
            )

        status_children = [
            html.Strong("Plan saved."),
            html.Div(f"Plan name: {plan.get('plan_name') or 'N/A'}"),
            html.Div(
                f"Branch: {plan['branch_id']} | Facia: {plan['facia']}"
            ),
            html.Div(
                f"Departments in snapshot: {len(normalize_plan_departments(plan))}"
            ),
            html.Small(f"Last updated: {plan['updated_at']}"),
        ]
        if storage_note is not None:
            status_children.append(html.Br())
            status_children.append(storage_note)

        saved_plan_key = branch_saved_plan_ref(plan)
        merged_options = _saved_plan_options_from_rows(
            _merge_latest_saved_plan(list_latest_plans(), plan),
            ref_data,
        )
        status = dbc.Alert(
            status_children,
            color="success",
            dismissable=True,
            className="mb-0",
        )
        return plan, status, merged_options, saved_plan_key
