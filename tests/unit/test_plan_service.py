import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda: None))

from range_control_platform.services import plan_service


class TestPlanService(unittest.TestCase):
    def setUp(self):
        self.plan = {
            "branch_id": "0002",
            "facia": "GO Outdoors",
            "department": "Camping",
            "store_grade": "B",
            "allowed_space": 48,
            "used_space": 3.6,
            "remaining_space": 44.4,
            "selected_stands": [
                {
                    "stand_id": "ST01",
                    "stand_name": "Wall Bay Single",
                    "stand_type": "Wall",
                    "sqm": 1.2,
                    "quantity": 3,
                }
            ],
            "created_at": "new-created",
            "updated_at": "new-updated",
            "departments": [
                {
                    "department": "Camping",
                    "store_grade": "B",
                    "allowed_space": 48,
                    "selected_stands": [
                        {
                            "stand_id": "ST01",
                            "stand_name": "Wall Bay Single",
                            "stand_type": "Wall",
                            "sqm": 1.2,
                            "quantity": 3,
                        }
                    ],
                },
                {
                    "department": "Accessories",
                    "store_grade": "B",
                    "allowed_space": 12,
                    "selected_stands": [
                        {
                            "stand_id": "ST02",
                            "stand_name": "Table",
                            "stand_type": "Table",
                            "sqm": 1.5,
                            "quantity": 2,
                        }
                    ],
                },
            ],
        }

    def test_normalize_selected_stands_recalculates_totals_and_drops_invalid_rows(self):
        stands = [
            {"stand_id": "ST02", "stand_name": "Table", "stand_type": "Table", "sqm": "1.5", "quantity": 2},
            {"stand_id": "ST01", "stand_name": "Wall", "stand_type": "Wall", "sqm": 1.2, "quantity": 1},
            {"stand_id": "ST99", "stand_name": "Ignore", "stand_type": "Wall", "sqm": 2.0, "quantity": 0},
        ]

        normalized = plan_service.normalize_selected_stands(stands)

        self.assertEqual(["ST01", "ST02"], [stand["stand_id"] for stand in normalized])
        self.assertEqual(3, plan_service.compute_stand_count(normalized))
        self.assertEqual(4.2, plan_service.compute_used_space(normalized))
        self.assertEqual(3.0, normalized[1]["total_sqm"])

    def test_persist_plan_snapshot_writes_selected_stands_and_migrates_legacy_header(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            export_dir = Path(temp_dir) / "data_exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            csv_path = export_dir / "plans.csv"
            csv_path.write_text(
                "branch_id,facia,department,stand_count,created_at,updated_at,saved_at\n"
                "0001,GO Outdoors,Camping,2,old-created,old-updated,old-saved\n",
                encoding="utf-8",
            )

            with patch.object(plan_service, "_project_root", return_value=Path(temp_dir)):
                plan_service.persist_plan_snapshot_to_csv(self.plan)
                rows = plan_service.load_plan_snapshots_from_csv()

            self.assertEqual(plan_service.CSV_HEADERS, csv_path.read_text(encoding="utf-8").splitlines()[0].split(","))
            self.assertEqual(2, len(rows))
            latest_row = rows[-1]
            self.assertEqual("0002", latest_row["branch_id"])
            self.assertEqual(3, latest_row["stand_count"])
            self.assertEqual(3.6, latest_row["used_space"])
            self.assertEqual("ST01", latest_row["selected_stands"][0]["stand_id"])

    def test_bigquery_plan_rows_match_expected_schema_shape(self):
        header_row = plan_service._bigquery_plan_header_row(self.plan)
        department_rows = plan_service._bigquery_plan_department_rows("plan-123", self.plan)
        stand_rows = plan_service._bigquery_plan_stand_rows(
            "plan-dept-123",
            self.plan["selected_stands"],
        )

        self.assertEqual("0002", header_row["branch_id"])
        self.assertEqual("draft", header_row["status"])
        self.assertEqual(2, len(department_rows))
        self.assertEqual({"Accessories", "Camping"}, {row["department_name"] for row in department_rows})
        self.assertTrue(all(row["plan_id"] == "plan-123" for row in department_rows))
        self.assertTrue(all(row["store_grade"] == "B" for row in department_rows))
        self.assertEqual("plan-dept-123-ST01", stand_rows[0]["plan_stand_id"])
        self.assertEqual("plan-dept-123", stand_rows[0]["plan_department_id"])
        self.assertEqual("ST01", stand_rows[0]["stand_id"])
        self.assertEqual(3, stand_rows[0]["quantity"])

    def test_plan_from_bigquery_rows_rebuilds_branch_snapshot_shape(self):
        plan = plan_service._plan_from_bigquery_rows(
            [
                {
                    "plan_id": "plan-123",
                    "plan_department_id": "plan-dept-123",
                    "branch_id": "0002",
                    "branch_name": "Leeds",
                    "facia": "GO Outdoors",
                    "department_name": "Camping",
                    "persisted_store_grade": "B",
                    "allowed_space": 48,
                    "created_by": "user@example.com",
                    "created_at": "2026-03-18T10:00:00+00:00",
                    "status": "draft",
                    "stand_id": "ST01",
                    "stand_name": "Wall Bay Single",
                    "stand_type": "Wall",
                    "sqm": 1.2,
                    "quantity": 3,
                },
                {
                    "plan_id": "plan-123",
                    "plan_department_id": "plan-dept-456",
                    "branch_id": "0002",
                    "branch_name": "Leeds",
                    "facia": "GO Outdoors",
                    "department_name": "Accessories",
                    "persisted_store_grade": "B",
                    "allowed_space": 12,
                    "created_by": "user@example.com",
                    "created_at": "2026-03-18T10:00:00+00:00",
                    "status": "draft",
                    "stand_id": "ST02",
                    "stand_name": "Table",
                    "stand_type": "Table",
                    "sqm": 1.5,
                    "quantity": 2,
                }
            ]
        )

        self.assertEqual("plan-123", plan["plan_id"])
        self.assertEqual("plan-123", plan["saved_plan_ref"])
        self.assertEqual(2, len(plan["departments"]))
        self.assertEqual("Accessories", plan["department"])
        self.assertEqual("B", plan["store_grade"])
        self.assertEqual(12.0, plan["allowed_space"])
        self.assertEqual(3.0, plan["used_space"])
        self.assertEqual(9.0, plan["remaining_space"])
        self.assertEqual(5, plan["total_stand_units"])
        self.assertEqual(6.6, plan["total_used_space"])
        self.assertEqual(2, plan["department_count"])

    def test_persist_plan_falls_back_to_csv_when_bigquery_save_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(plan_service, "_use_bigquery_plan_storage", return_value=True):
                with patch.object(plan_service, "_project_root", return_value=Path(temp_dir)):
                    with patch.object(
                        plan_service,
                        "persist_plan_to_bigquery",
                        side_effect=RuntimeError("bq unavailable"),
                    ):
                        result = plan_service.persist_plan(self.plan)

            self.assertEqual("csv-fallback", result["storage_backend"])
            self.assertEqual(plan_service.make_plan_key(self.plan), result["saved_plan_ref"])
            self.assertTrue((Path(temp_dir) / "data_exports" / "plans.csv").exists())


if __name__ == "__main__":
    unittest.main()
