from range_control_platform.services.plan_service import compute_stand_count, compute_used_space


def find_store(ref_data, branch_id):
    for store in (ref_data or {}).get("stores", []):
        if store.get("branch_id") == branch_id:
            return store
    return None


def find_department_allocation(ref_data, department, grade):
    for allocation in (ref_data or {}).get("department_grade_allocations", []):
        if allocation.get("department_name") == department and allocation.get("grade") == grade:
            try:
                return round(float(allocation.get("allowed_linear_meterage")), 2)
            except (TypeError, ValueError):
                return None
    return None


def build_validation_result(plan, ref_data, click_ts):
    if not plan:
        return {
            "message": "No plan found. Save a plan first.",
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

    branch_id = plan.get("branch_id")
    store = find_store(ref_data, branch_id)
    if not store:
        return {
            "message": f"Store {branch_id} not found in reference data.",
            "color": "danger",
            "details": [],
            "last_run_click_ts": click_ts,
        }

    grade = store.get("store_grade") or plan.get("store_grade")
    department = plan.get("department")
    allowed = find_department_allocation(ref_data, department, grade)

    if allowed is None:
        return {
            "message": "No department allocation found for this store grade.",
            "color": "danger",
            "details": [
                f"Department: {department or 'N/A'}",
                f"Store grade: {grade or 'N/A'}",
            ],
            "last_run_click_ts": click_ts,
        }

    selected_stands = plan.get("selected_stands") or []
    planned = compute_used_space(selected_stands) or 0.0
    remaining = round(allowed - planned, 2)

    details = [
        f"Store grade {grade} allows {allowed:.2f} linear meters for {department}.",
        f"Selected stands use {planned:.2f} sqm across {compute_stand_count(selected_stands)} stand(s).",
        "Current implementation compares department linear meterage directly with stand sqm pending business conversion guidance.",
    ]

    if planned <= allowed:
        return {
            "message": "PASS: Department space is within allowance.",
            "color": "success",
            "details": details + [f"Remaining space: {remaining:.2f}."],
            "validation_status": "PASS",
            "last_run_click_ts": click_ts,
        }

    breach = round(planned - allowed, 2)
    return {
        "message": "FAIL: Department space allowance exceeded.",
        "color": "danger",
        "details": details + [f"Over by {breach:.2f}."],
        "validation_status": "FAIL",
        "last_run_click_ts": click_ts,
    }
