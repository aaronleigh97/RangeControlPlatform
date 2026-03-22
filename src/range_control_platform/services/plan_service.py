import csv
from datetime import datetime, timezone
import json
import math
from collections import Counter
from pathlib import Path
from uuid import uuid4

from range_control_platform.config import settings


DEFAULT_RANGE_CONTROL_DATASET = "jds-gcp-dev-dl-odm-analytics.RangeControlPlatform"

CSV_HEADERS = [
    "plan_id",
    "branch_id",
    "facia",
    "department",
    "plan_name",
    "is_active",
    "store_grade",
    "allowed_space",
    "used_space",
    "remaining_space",
    "stand_count",
    "selected_stands_json",
    "created_at",
    "updated_at",
    "saved_at",
]

VALIDATION_CSV_HEADERS = [
    "plan_key",
    "branch_id",
    "facia",
    "department",
    "validation_status",
    "validated_at",
]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_plan_csv_path() -> Path:
    return _project_root() / "data_exports" / "plans.csv"


def get_validation_csv_path() -> Path:
    return _project_root() / "data_exports" / "plan_validations.csv"


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_bool(value, default=True):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    return default


def _plan_dataset() -> str:
    if settings.BQ_PROJECT and settings.BQ_DATASET:
        return f"{settings.BQ_PROJECT}.{settings.BQ_DATASET}"
    if settings.BQ_DATASET and "." in settings.BQ_DATASET:
        return settings.BQ_DATASET
    return DEFAULT_RANGE_CONTROL_DATASET


def _use_bigquery_plan_storage() -> bool:
    return settings.ENV == "jd"


def _load_bigquery_modules():
    try:
        from deploy_frameworks.bigquery import bigquery
    except ImportError as exc:
        raise RuntimeError(
            "deploy_frameworks.bigquery is not installed or unavailable. "
            "Plan persistence cannot use BigQuery."
        ) from exc
    return bigquery


def _sql_string(value) -> str:
    if value is None:
        return "NULL"
    escaped = str(value).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def _sql_int(value) -> str:
    if value is None:
        return "NULL"
    return str(_safe_int(value, 0))


def _sql_timestamp(value) -> str:
    if not value:
        return "CURRENT_TIMESTAMP()"
    return f"TIMESTAMP({_sql_string(value)})"


def _clean_missing(value):
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def resolve_plan_is_active(plan: dict | None) -> bool:
    status = str((plan or {}).get("status") or "").strip().lower()
    if status == "deleted":
        return False
    return True


def compute_stand_count(selected_stands: list[dict] | None) -> int:
    return sum(_safe_int(stand.get("quantity"), 0) for stand in (selected_stands or []))


def compute_used_space(selected_stands: list[dict] | None) -> float:
    return round(
        sum(_safe_float(stand.get("total_sqm"), 0.0) for stand in (selected_stands or [])),
        2,
    )


def _instance_row_id(stand: dict, row_index: int, copy_index: int) -> str:
    stand_id = str(stand.get("stand_id") or "stand")
    return f"legacy-{stand_id}-{row_index + 1}-{copy_index + 1}"


def normalize_assigned_products(assigned_products: list[dict] | None) -> list[dict]:
    normalized = []
    seen_product_ids = set()
    for product in assigned_products or []:
        product_id = str(product.get("product_id") or "").strip()
        if not product_id or product_id in seen_product_ids:
            continue
        seen_product_ids.add(product_id)
        normalized.append(
            {
                "product_id": product_id,
                "product_code": str(product.get("product_code") or "").strip() or None,
                "product_name": str(product.get("product_name") or "").strip() or None,
                "department_name": str(product.get("department_name") or "").strip() or None,
                "range_name": str(product.get("range_name") or "").strip() or None,
            }
        )
    normalized.sort(
        key=lambda product: (
            str(product.get("range_name") or ""),
            str(product.get("product_name") or ""),
            str(product.get("product_code") or ""),
            str(product.get("product_id") or ""),
        )
    )
    return normalized


def _normalize_capacity_class(capacity_class) -> str | None:
    normalized = str(capacity_class or "").strip().lower()
    if normalized in {"single", "double"}:
        return normalized
    return None


def compute_stand_product_capacity(arms, capacity_class, quantity=1) -> int | None:
    normalized_type = _normalize_capacity_class(capacity_class)
    if normalized_type is None:
        return None

    base_arms = max(_safe_int(arms, 0), 0)
    base_capacity = base_arms + 1
    if normalized_type == "double":
        base_capacity *= 2

    stand_quantity = max(_safe_int(quantity, 0), 0)
    if stand_quantity <= 0:
        return 0
    return base_capacity * stand_quantity


def build_stand_product_capacity_status(
    assigned_products: list[dict] | None,
    arms,
    capacity_class,
    quantity=1,
) -> dict:
    normalized_products = normalize_assigned_products(assigned_products)
    assigned_count = len(normalized_products)
    capacity = compute_stand_product_capacity(arms, capacity_class, quantity=quantity)

    if capacity is None:
        return {
            "status": "unknown",
            "label": "Unknown",
            "color": "secondary",
            "assigned_count": assigned_count,
            "capacity": None,
            "remaining_slots": None,
        }

    remaining_slots = capacity - assigned_count
    if assigned_count > capacity:
        status = "over_capacity"
        label = "Over Capacity"
        color = "danger"
    elif assigned_count == capacity:
        status = "just_right"
        label = "Just Right"
        color = "success"
    else:
        status = "underfilled"
        label = "Underfilled"
        color = "warning"

    return {
        "status": status,
        "label": label,
        "color": color,
        "assigned_count": assigned_count,
        "capacity": capacity,
        "remaining_slots": remaining_slots,
    }


def normalize_selected_stands(selected_stands: list[dict] | None) -> list[dict]:
    normalized = []
    for row_index, stand in enumerate(selected_stands or []):
        quantity = _safe_int(stand.get("quantity"), 0)
        sqm = _safe_float(stand.get("sqm"), 0.0)
        if quantity <= 0:
            continue
        assigned_products = normalize_assigned_products(stand.get("assigned_products"))
        explicit_instance_id = str(stand.get("stand_instance_id") or "").strip() or None
        if explicit_instance_id:
            instance_ids = [explicit_instance_id]
        else:
            source_instance_ids = [
                str(value).strip()
                for value in (stand.get("stand_instance_ids") or [])
                if str(value).strip()
            ]
            if source_instance_ids:
                instance_ids = source_instance_ids
            else:
                instance_ids = [_instance_row_id(stand, row_index, copy_index) for copy_index in range(quantity)]

        for copy_index, stand_instance_id in enumerate(instance_ids[: max(quantity, 1)]):
            normalized.append(
                {
                    "stand_instance_id": stand_instance_id,
                    "stand_id": stand.get("stand_id"),
                    "stand_name": stand.get("stand_name"),
                    "stand_type": stand.get("stand_type"),
                    "stand_height": stand.get("stand_height"),
                    "arms": stand.get("arms"),
                    "sqm": round(sqm, 2),
                    "quantity": 1,
                    "total_sqm": round(sqm, 2),
                    "assigned_products": assigned_products if copy_index == 0 or explicit_instance_id else [],
                }
            )
    normalized.sort(
        key=lambda item: (
            str(item.get("stand_id") or ""),
            str(item.get("stand_instance_id") or ""),
        )
    )
    return normalized


def serialize_selected_stands(selected_stands: list[dict] | None) -> str:
    return json.dumps(normalize_selected_stands(selected_stands), ensure_ascii=True)


def deserialize_selected_stands(value) -> list[dict]:
    if not value:
        return []
    if isinstance(value, list):
        return normalize_selected_stands(value)
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    if not isinstance(parsed, list):
        return []
    return normalize_selected_stands(parsed)


def normalize_department_plan(department_plan: dict | None) -> dict | None:
    if not department_plan or not department_plan.get("department"):
        return None

    selected_stands = normalize_selected_stands(department_plan.get("selected_stands"))
    allowed_space_raw = department_plan.get("allowed_space")
    allowed_space = None if allowed_space_raw is None else round(_safe_float(allowed_space_raw), 2)
    used_space = compute_used_space(selected_stands)
    remaining_space = None if allowed_space is None else round(allowed_space - used_space, 2)

    return {
        "plan_department_id": department_plan.get("plan_department_id"),
        "department": department_plan.get("department"),
        "store_grade": department_plan.get("store_grade"),
        "allowed_space": allowed_space,
        "used_space": used_space,
        "remaining_space": remaining_space,
        "stand_count": compute_stand_count(selected_stands),
        "selected_stands": selected_stands,
    }


def normalize_plan_departments(plan: dict | None) -> list[dict]:
    departments = []
    for department_plan in (plan or {}).get("departments") or []:
        normalized = normalize_department_plan(department_plan)
        if normalized:
            departments.append(normalized)

    if departments:
        departments.sort(key=lambda row: str(row.get("department") or ""))
        return departments

    fallback = normalize_department_plan(
        {
            "plan_department_id": (plan or {}).get("plan_department_id"),
            "department": (plan or {}).get("department"),
            "store_grade": (plan or {}).get("store_grade"),
            "allowed_space": (plan or {}).get("allowed_space"),
            "selected_stands": (plan or {}).get("selected_stands"),
        }
    )
    if fallback:
        departments = [fallback]

    departments.sort(key=lambda row: str(row.get("department") or ""))
    return departments


def flatten_plan_stands(plan: dict | None) -> list[dict]:
    rows = []
    for department_plan in normalize_plan_departments(plan):
        department_name = department_plan.get("department")
        for stand in department_plan.get("selected_stands") or []:
            rows.append(
                {
                    **stand,
                    "department": department_name,
                    "plan_department_id": department_plan.get("plan_department_id"),
                }
            )
    rows.sort(
        key=lambda row: (
            str(row.get("department") or ""),
            str(row.get("stand_id") or ""),
            str(row.get("stand_instance_id") or ""),
        )
    )
    return rows


def summarize_plan_departments(plan: dict | None) -> dict:
    departments = normalize_plan_departments(plan)
    return {
        "department_count": len(departments),
        "total_stand_units": sum(department.get("stand_count", 0) for department in departments),
        "total_used_space": round(
            sum(_safe_float(department.get("used_space"), 0.0) for department in departments),
            2,
        ),
    }


def branch_saved_plan_ref(plan: dict | None) -> str | None:
    if not plan:
        return None
    return plan.get("plan_key") or plan.get("saved_plan_ref") or plan.get("plan_id")


def _normalized_plan_name_key(value) -> str:
    return str(value or "").strip().lower()


def make_plan_key(row: dict) -> str:
    plan_name_key = _normalized_plan_name_key((row or {}).get("plan_name"))
    return "|".join([
        str((row or {}).get("branch_id") or ""),
        str((row or {}).get("facia") or ""),
        plan_name_key,
    ])


def _ensure_plan_csv_schema(csv_path: Path) -> None:
    if not csv_path.exists():
        return

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        existing_headers = next(reader, [])

    if existing_headers == CSV_HEADERS:
        return

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        existing_rows = list(reader)

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for existing_row in existing_rows:
            writer.writerow(
                {
                    "plan_id": existing_row.get("plan_id") or "",
                    "branch_id": existing_row.get("branch_id"),
                    "facia": existing_row.get("facia"),
                    "department": existing_row.get("department"),
                    "plan_name": existing_row.get("plan_name"),
                    "is_active": _safe_bool(existing_row.get("is_active"), True),
                    "store_grade": existing_row.get("store_grade"),
                    "allowed_space": round(_safe_float(existing_row.get("allowed_space"), 0.0), 2),
                    "used_space": round(_safe_float(existing_row.get("used_space"), 0.0), 2),
                    "remaining_space": round(
                        _safe_float(existing_row.get("remaining_space"), 0.0),
                        2,
                    ),
                    "stand_count": _safe_int(existing_row.get("stand_count"), 0),
                    "selected_stands_json": existing_row.get("selected_stands_json") or "[]",
                    "created_at": existing_row.get("created_at"),
                    "updated_at": existing_row.get("updated_at"),
                    "saved_at": existing_row.get("saved_at"),
                }
            )


def _csv_row_from_plan(plan: dict) -> dict:
    return {
        "plan_id": plan.get("plan_id") or "",
        "branch_id": plan.get("branch_id"),
        "facia": plan.get("facia"),
        "department": plan.get("department"),
        "plan_name": plan.get("plan_name"),
        "is_active": resolve_plan_is_active(plan),
        "store_grade": plan.get("store_grade"),
        "allowed_space": round(_safe_float(plan.get("allowed_space"), 0.0), 2),
        "used_space": round(_safe_float(plan.get("used_space"), 0.0), 2),
        "remaining_space": round(_safe_float(plan.get("remaining_space"), 0.0), 2),
        "stand_count": compute_stand_count(plan.get("selected_stands")),
        "selected_stands_json": serialize_selected_stands(plan.get("selected_stands")),
        "created_at": plan.get("created_at"),
        "updated_at": plan.get("updated_at"),
        "saved_at": plan.get("updated_at"),
    }


def _plan_from_csv_row(row: dict) -> dict:
    clean = dict(row)
    clean["plan_id"] = clean.get("plan_id") or None
    clean["plan_key"] = make_plan_key(clean)
    clean["plan_name"] = clean.get("plan_name") or None
    clean["is_active"] = _safe_bool(clean.get("is_active"), True)
    clean["stand_count"] = _safe_int(clean.get("stand_count"), 0)
    clean["allowed_space"] = _safe_float(clean.get("allowed_space"), 0.0)
    clean["used_space"] = _safe_float(clean.get("used_space"), 0.0)
    clean["remaining_space"] = _safe_float(clean.get("remaining_space"), 0.0)
    clean["selected_stands"] = deserialize_selected_stands(clean.get("selected_stands_json"))
    if clean["selected_stands"]:
        clean["stand_count"] = compute_stand_count(clean["selected_stands"])
        clean["used_space"] = compute_used_space(clean["selected_stands"])
        clean["remaining_space"] = round(clean["allowed_space"] - clean["used_space"], 2)
    clean["saved_plan_ref"] = clean.get("plan_id") or clean["plan_key"]
    clean["storage_backend"] = "csv"
    return clean


def persist_plan_snapshot_to_csv(plan: dict) -> Path:
    csv_path = get_plan_csv_path()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    _ensure_plan_csv_schema(csv_path)

    row = _csv_row_from_plan(plan)
    file_exists = csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    return csv_path


def load_plan_snapshots_from_csv() -> list[dict]:
    csv_path = get_plan_csv_path()
    if not csv_path.exists():
        return []

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [_plan_from_csv_row(row) for row in reader]


def _bigquery_plan_header_row(plan: dict) -> dict:
    return {
        "plan_id": str(uuid4()),
        "branch_id": str(plan.get("branch_id") or ""),
        "plan_name": plan.get("plan_name"),
        "created_by": plan.get("created_by"),
        "created_at": plan.get("updated_at") or plan.get("created_at"),
        "status": plan.get("status") or "draft",
        "is_active": resolve_plan_is_active(plan),
    }


def _bigquery_plan_department_rows(plan_id: str, plan: dict) -> list[dict]:
    rows = []
    for department_plan in normalize_plan_departments(plan):
        rows.append(
            {
                "plan_department_id": str(uuid4()),
                "plan_id": plan_id,
                "department_name": str(department_plan.get("department") or ""),
                "store_grade": department_plan.get("store_grade"),
                "allowed_space": (
                    "NULL"
                    if department_plan.get("allowed_space") is None
                    else round(_safe_float(department_plan.get("allowed_space")), 2)
                ),
                "selected_stands": department_plan.get("selected_stands") or [],
            }
        )
    return rows


def _bigquery_plan_stand_rows(
    plan_department_id: str,
    selected_stands: list[dict] | None,
) -> list[dict]:
    stand_counts = {}
    for stand in normalize_selected_stands(selected_stands):
        stand_id = stand.get("stand_id")
        if not stand_id:
            continue
        stand_counts[stand_id] = stand_counts.get(stand_id, 0) + 1

    rows = []
    for stand_id, quantity in stand_counts.items():
        rows.append(
            {
                "plan_stand_id": f"{plan_department_id}-{stand_id}",
                "plan_department_id": plan_department_id,
                "stand_id": stand_id,
                "quantity": quantity,
            }
        )
    return rows


def _plan_from_bigquery_rows(rows: list[dict]) -> dict | None:
    if not rows:
        return None

    first = {key: _clean_missing(value) for key, value in rows[0].items()}
    departments_by_id = {}
    for row in rows:
        row = {key: _clean_missing(value) for key, value in row.items()}
        plan_department_id = row.get("plan_department_id")
        department_name = row.get("department_name")
        if not plan_department_id or not department_name:
            continue
        department = departments_by_id.setdefault(
            plan_department_id,
            {
                "plan_department_id": plan_department_id,
                "department": department_name,
                "store_grade": row.get("persisted_store_grade") or row.get("store_grade"),
                "allowed_space": _clean_missing(row.get("allowed_space")),
                "selected_stands": [],
            },
        )
        if not row.get("stand_id"):
            continue
        quantity = _safe_int(row.get("quantity"), 0)
        sqm = _safe_float(row.get("sqm"), 0.0)
        if quantity <= 0:
            continue
        for instance_index in range(quantity):
            department["selected_stands"].append(
                {
                    "stand_instance_id": f"{plan_department_id}-{row.get('stand_id')}-{instance_index + 1}",
                    "stand_id": row.get("stand_id"),
                    "stand_name": row.get("stand_name"),
                    "stand_type": row.get("stand_type"),
                    "stand_height": row.get("stand_height"),
                    "arms": row.get("arms"),
                    "sqm": round(sqm, 2),
                    "quantity": 1,
                    "total_sqm": round(sqm, 2),
                    "assigned_products": [],
                }
            )

    departments = [
        normalized
        for normalized in (
            normalize_department_plan(department) for department in departments_by_id.values()
        )
        if normalized
    ]
    if not departments:
        return None
    departments.sort(key=lambda department: str(department.get("department") or ""))
    current_department = departments[0]
    totals = summarize_plan_departments({"departments": departments})

    plan = {
        "plan_id": first.get("plan_id"),
        "branch_id": first.get("branch_id"),
        "plan_name": first.get("plan_name"),
        "branch_name": first.get("branch_name"),
        "facia": first.get("facia"),
        "department": current_department.get("department"),
        "store_grade": first.get("store_grade") or current_department.get("store_grade"),
        "square_footage": first.get("square_footage"),
        "created_by": first.get("created_by"),
        "created_at": first.get("created_at"),
        "updated_at": first.get("created_at"),
        "saved_at": first.get("created_at"),
        "status": first.get("status"),
        "is_active": _safe_bool(first.get("is_active"), True),
        "plan_department_id": current_department.get("plan_department_id"),
        "allowed_space": current_department.get("allowed_space"),
        "allowed_space_unit": "linear_meter",
        "used_space": current_department.get("used_space"),
        "remaining_space": current_department.get("remaining_space"),
        "stand_count": current_department.get("stand_count"),
        "selected_stands": current_department.get("selected_stands"),
        "departments": departments,
        "total_used_space": totals["total_used_space"],
        "total_stand_units": totals["total_stand_units"],
        "department_count": totals["department_count"],
        "plan_key": make_plan_key(
            {
                "branch_id": first.get("branch_id"),
                "facia": first.get("facia"),
                "plan_name": first.get("plan_name"),
            }
        ),
        "saved_plan_ref": first.get("plan_id"),
        "storage_backend": "bigquery",
    }
    return plan


def _load_bigquery_plan_rows(saved_plan_ref: str | None = None) -> list[dict]:
    bigquery = _load_bigquery_modules()
    dataset = _plan_dataset()
    filter_clause = ""
    if saved_plan_ref:
        escaped_saved_plan_ref = str(saved_plan_ref).replace("'", "\\'")
        filter_clause = f"WHERE p.plan_id = '{escaped_saved_plan_ref}'"

    query = f"""
    SELECT
      p.plan_id,
      p.branch_id,
      p.plan_name,
      p.created_by,
      p.created_at,
      p.status,
      p.is_active,
      pd.plan_department_id,
      pd.department_name,
      pd.store_grade AS persisted_store_grade,
      pd.allowed_space,
      s.branch_name,
      s.fascia,
      s.store_grade,
      s.square_footage,
      ps.plan_stand_id,
      ps.stand_id,
      ps.quantity,
      sl.stand_name,
      sl.stand_type,
      sl.stand_height,
      sl.arms,
      sl.sqm
    FROM `{dataset}.plans` p
    INNER JOIN `{dataset}.plan_departments` pd
      ON p.plan_id = pd.plan_id
    LEFT JOIN `{dataset}.stores` s
      ON p.branch_id = s.branch_id
    LEFT JOIN `{dataset}.plan_stands` ps
      ON pd.plan_department_id = ps.plan_department_id
    LEFT JOIN `{dataset}.stand_library` sl
      ON ps.stand_id = sl.stand_id
    {filter_clause}
    ORDER BY p.created_at DESC, ps.plan_stand_id
    """
    return bigquery(query).to_dict("records")


def persist_plan_to_bigquery(plan: dict) -> dict:
    bigquery = _load_bigquery_modules()
    plan_header_row = _bigquery_plan_header_row(plan)
    plan_id = plan_header_row["plan_id"]
    department_rows = _bigquery_plan_department_rows(plan_id, plan)
    dataset = _plan_dataset()
    plan_insert_sql = f"""
    INSERT INTO `{dataset}.plans` (
      plan_id,
      branch_id,
      plan_name,
      created_by,
      created_at,
      status,
      is_active
    )
    VALUES (
      {_sql_string(plan_header_row['plan_id'])},
      {_sql_string(plan_header_row['branch_id'])},
      {_sql_string(plan_header_row['plan_name'])},
      {_sql_string(plan_header_row['created_by'])},
      {_sql_timestamp(plan_header_row['created_at'])},
      {_sql_string(plan_header_row['status'])},
      {str(plan_header_row['is_active']).upper()}
    )
    """
    bigquery(plan_insert_sql)

    if department_rows:
        department_values_sql = ",\n".join(
            [
                "("
                f"{_sql_string(row['plan_department_id'])}, "
                f"{_sql_string(row['plan_id'])}, "
                f"{_sql_string(row['department_name'])}, "
                f"{_sql_string(row['store_grade'])}, "
                f"{row['allowed_space']}"
                ")"
                for row in department_rows
            ]
        )
        department_insert_sql = f"""
        INSERT INTO `{dataset}.plan_departments` (
          plan_department_id,
          plan_id,
          department_name,
          store_grade,
          allowed_space
        )
        VALUES
        {department_values_sql}
        """
        bigquery(department_insert_sql)

    stand_rows = []
    for department_row in department_rows:
        stand_rows.extend(
            _bigquery_plan_stand_rows(
                department_row["plan_department_id"],
                department_row.get("selected_stands"),
            )
        )

    if stand_rows:
        values_sql = ",\n".join(
            [
                "("
                f"{_sql_string(row['plan_stand_id'])}, "
                f"{_sql_string(row['plan_department_id'])}, "
                f"{_sql_string(row['stand_id'])}, "
                f"{_sql_int(row['quantity'])}"
                ")"
                for row in stand_rows
            ]
        )
        stand_insert_sql = f"""
        INSERT INTO `{dataset}.plan_stands` (
          plan_stand_id,
          plan_department_id,
          stand_id,
          quantity
        )
        VALUES
        {values_sql}
        """
        bigquery(stand_insert_sql)

    return {
        **plan,
        "plan_id": plan_id,
        "plan_key": make_plan_key(plan),
        "plan_department_id": None,
        "created_at": plan_header_row["created_at"],
        "updated_at": plan_header_row["created_at"],
        "saved_at": plan_header_row["created_at"],
        "saved_plan_ref": plan_id,
        "storage_backend": "bigquery",
        "status": plan_header_row["status"],
        "is_active": plan_header_row["is_active"],
        "plan_name": plan_header_row["plan_name"],
    }


def load_plan_snapshots_from_bigquery() -> list[dict]:
    rows = _load_bigquery_plan_rows()
    grouped_rows = {}
    for row in rows:
        grouped_rows.setdefault(row.get("plan_id"), []).append(row)

    plans = []
    for group in grouped_rows.values():
        plan = _plan_from_bigquery_rows(group)
        if plan:
            plans.append(plan)
    plans.sort(key=lambda row: row.get("saved_at") or "", reverse=True)
    return plans


def load_plan_snapshots() -> list[dict]:
    if _use_bigquery_plan_storage():
        try:
            return load_plan_snapshots_from_bigquery()
        except Exception:
            return load_plan_snapshots_from_csv()
    return load_plan_snapshots_from_csv()


def list_latest_plans() -> list[dict]:
    rows = load_plan_snapshots()
    latest_by_key = {}
    for row in rows:
        key = row.get("plan_key") or make_plan_key(row)
        existing = latest_by_key.get(key)
        row_saved = row.get("saved_at") or row.get("updated_at") or ""
        existing_saved = (existing or {}).get("saved_at") or (existing or {}).get("updated_at") or ""
        if existing is None or row_saved >= existing_saved:
            latest_by_key[key] = row

    latest_rows = list(latest_by_key.values())
    latest_rows = [row for row in latest_rows if _safe_bool(row.get("is_active"), True)]
    latest_rows.sort(key=lambda r: r.get("saved_at") or r.get("updated_at") or "", reverse=True)
    return latest_rows


def get_saved_plan(saved_plan_ref: str) -> dict | None:
    if not saved_plan_ref:
        return None

    if _use_bigquery_plan_storage():
        try:
            plan = _plan_from_bigquery_rows(_load_bigquery_plan_rows(saved_plan_ref))
            if plan:
                return plan
        except Exception:
            pass

    for row in list_latest_plans():
        if row.get("saved_plan_ref") == saved_plan_ref or row.get("plan_key") == saved_plan_ref:
            return row
    return None


def persist_plan(plan: dict) -> dict:
    if _use_bigquery_plan_storage():
        try:
            return persist_plan_to_bigquery(plan)
        except Exception as exc:
            csv_path = persist_plan_snapshot_to_csv(plan)
            return {
                **plan,
                "plan_key": make_plan_key(plan),
                "saved_plan_ref": make_plan_key(plan),
                "storage_backend": "csv-fallback",
                "storage_location": str(csv_path),
                "storage_error": str(exc),
                "is_active": resolve_plan_is_active(plan),
            }

    csv_path = persist_plan_snapshot_to_csv(plan)
    return {
        **plan,
        "plan_key": make_plan_key(plan),
        "saved_plan_ref": make_plan_key(plan),
        "storage_backend": "csv",
        "storage_location": str(csv_path),
        "is_active": resolve_plan_is_active(plan),
    }


def list_latest_plans_from_csv() -> list[dict]:
    rows = load_plan_snapshots_from_csv()
    latest_by_key = {}
    for row in rows:
        key = row.get("plan_key") or make_plan_key(row)
        existing = latest_by_key.get(key)
        row_saved = row.get("saved_at") or ""
        existing_saved = (existing or {}).get("saved_at") or ""
        if existing is None or row_saved >= existing_saved:
            latest_by_key[key] = row

    latest_rows = list(latest_by_key.values())
    latest_rows.sort(key=lambda r: r.get("saved_at") or "", reverse=True)
    return latest_rows


def get_latest_plan_by_key(plan_key: str) -> dict | None:
    if not plan_key:
        return None
    for row in list_latest_plans_from_csv():
        if row.get("plan_key") == plan_key:
            return row
    return None


def deactivate_plan(saved_plan_ref: str, plan: dict | None = None) -> dict:
    existing_plan = plan or get_saved_plan(saved_plan_ref)
    if not existing_plan:
        raise ValueError("Plan not found for deletion.")

    now = datetime.now(timezone.utc).isoformat()
    deletion_snapshot = {
        **existing_plan,
        "created_at": existing_plan.get("created_at") or existing_plan.get("saved_at") or now,
        "updated_at": now,
        "saved_at": now,
        "status": "deleted",
        "is_active": False,
    }
    return persist_plan(deletion_snapshot)


def summarize_plan_snapshots(rows: list[dict]) -> dict:
    if not rows:
        return {
            "total_snapshots": 0,
            "unique_plans": 0,
            "latest_saved_at": None,
            "stand_min": None,
            "stand_max": None,
            "stand_avg": None,
            "facia_counts": [],
            "department_counts": [],
            "recent_rows": [],
        }

    facia_counts = Counter((r.get("facia") or "(blank)") for r in rows)
    department_counts = Counter((r.get("department") or "(blank)") for r in rows)
    unique_plans = {r.get("plan_key") or make_plan_key(r) for r in rows}
    latest_saved_at = max((r.get("saved_at") or r.get("updated_at") or "") for r in rows) or None

    stand_values = []
    for row in rows:
        try:
            stand_values.append(int(row.get("stand_count") or 0))
        except (TypeError, ValueError):
            continue

    stand_min = min(stand_values) if stand_values else None
    stand_max = max(stand_values) if stand_values else None
    stand_avg = (sum(stand_values) / len(stand_values)) if stand_values else None

    recent_rows = sorted(
        rows,
        key=lambda r: r.get("saved_at") or r.get("updated_at") or "",
        reverse=True,
    )[:10]

    return {
        "total_snapshots": len(rows),
        "unique_plans": len(unique_plans),
        "latest_saved_at": latest_saved_at,
        "stand_min": stand_min,
        "stand_max": stand_max,
        "stand_avg": round(stand_avg, 2) if stand_avg is not None else None,
        "facia_counts": facia_counts.most_common(),
        "department_counts": department_counts.most_common(),
        "recent_rows": recent_rows,
    }


def export_plan_snapshots_to_csv(rows: list[dict], export_path: Path | None = None) -> Path:
    export_path = export_path or (_project_root() / "data_exports" / "plans_export.csv")
    export_path.parent.mkdir(parents=True, exist_ok=True)

    with export_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow(_csv_row_from_plan(row))

    return export_path


def persist_validation_result_to_csv(plan: dict, validation_status: str, validated_at: str) -> Path:
    csv_path = get_validation_csv_path()
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    row = {
        "plan_key": make_plan_key(plan),
        "branch_id": plan.get("branch_id"),
        "facia": plan.get("facia"),
        "department": plan.get("department"),
        "validation_status": validation_status,
        "validated_at": validated_at,
    }

    file_exists = csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=VALIDATION_CSV_HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    return csv_path


def load_latest_validation_status_by_plan_key() -> dict:
    csv_path = get_validation_csv_path()
    if not csv_path.exists():
        return {}

    latest_by_key = {}
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            plan_key = row.get("plan_key")
            if not plan_key:
                continue
            existing = latest_by_key.get(plan_key)
            row_ts = row.get("validated_at") or ""
            existing_ts = (existing or {}).get("validated_at") or ""
            if existing is None or row_ts >= existing_ts:
                latest_by_key[plan_key] = {
                    "validation_status": row.get("validation_status", ""),
                    "validated_at": row.get("validated_at", ""),
                }

    return latest_by_key
