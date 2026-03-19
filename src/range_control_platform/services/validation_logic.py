from range_control_platform.services.plan_service import (
    compute_stand_count,
    compute_used_space,
    normalize_plan_departments,
    summarize_plan_departments,
)


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
    department_plans = normalize_plan_departments(plan)
    if not department_plans:
        return {
            "message": "No department plan rows found.",
            "color": "warning",
            "details": [],
            "last_run_click_ts": click_ts,
        }

    details = []
    failures = []
    for department_plan in department_plans:
        department = department_plan.get("department")
        allowed = department_plan.get("allowed_space")
        if allowed is None:
            allowed = find_department_allocation(ref_data, department, grade)

        if allowed is None:
            failures.append(
                f"No department allocation found for {department or 'N/A'} at grade {grade or 'N/A'}."
            )
            continue

        selected_stands = department_plan.get("selected_stands") or []
        planned = compute_used_space(selected_stands) or 0.0
        remaining = round(float(allowed) - planned, 2)

        details.extend(
            [
                f"{department}: allowance {float(allowed):.2f}, planned {planned:.2f} sqm across {compute_stand_count(selected_stands)} stand(s).",
                "Current implementation compares department linear meterage directly with stand sqm pending business conversion guidance.",
            ]
        )

        if planned > float(allowed):
            failures.append(f"{department}: over by {round(planned - float(allowed), 2):.2f}.")
        else:
            details.append(f"{department}: remaining headroom {remaining:.2f}.")

    totals = summarize_plan_departments(plan)
    details.append(
        f"Branch plan total stand area: {totals.get('total_used_space', 0.0):.2f} sqm across {totals.get('department_count', 0)} department(s)."
    )

    if failures:
        return {
            "message": "FAIL: One or more department allowances were exceeded.",
            "color": "danger",
            "details": details + failures,
            "validation_status": "FAIL",
            "last_run_click_ts": click_ts,
        }

    return {
        "message": "PASS: All planned departments are within allowance.",
        "color": "success",
        "details": details,
        "validation_status": "PASS",
        "last_run_click_ts": click_ts,
    }
