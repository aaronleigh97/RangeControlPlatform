import csv
from collections import Counter
from pathlib import Path


CSV_HEADERS = [
    "branch_id",
    "facia",
    "department",
    "stand_count",
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


def make_plan_key(row: dict) -> str:
    return "|".join([
        str(row.get("branch_id") or ""),
        str(row.get("facia") or ""),
        str(row.get("department") or ""),
    ])


def persist_plan_snapshot_to_csv(plan: dict) -> Path:
    """
    Append a snapshot row for the current plan to a CSV file.
    """
    csv_path = get_plan_csv_path()
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    row = {
        "branch_id": plan.get("branch_id"),
        "facia": plan.get("facia"),
        "department": plan.get("department"),
        "stand_count": plan.get("stand_count"),
        "created_at": plan.get("created_at"),
        "updated_at": plan.get("updated_at"),
        "saved_at": plan.get("updated_at"),
    }

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
        rows = []
        for row in reader:
            clean = dict(row)
            clean["plan_key"] = make_plan_key(clean)
            clean["stand_count"] = _safe_int(clean.get("stand_count"), 0)
            rows.append(clean)
        return rows


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
    unique_plans = {
        r.get("plan_key") or make_plan_key(r)
        for r in rows
    }
    latest_saved_at = max((r.get("saved_at") or "") for r in rows) or None

    stand_values = []
    for row in rows:
        try:
            stand_values.append(int(row.get("stand_count") or 0))
        except (TypeError, ValueError):
            continue

    stand_min = min(stand_values) if stand_values else None
    stand_max = max(stand_values) if stand_values else None
    stand_avg = (sum(stand_values) / len(stand_values)) if stand_values else None

    recent_rows = sorted(rows, key=lambda r: r.get("saved_at") or "", reverse=True)[:10]

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
