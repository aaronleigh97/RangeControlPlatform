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
            "plan_name": "Camping Trial",
            "store_grade": "B",
            "allowed_space": 48,
            "used_space": 3.6,
            "remaining_space": 44.4,
            "selected_stands": [
                {
                    "stand_id": "ST01",
                    "stand_name": "Wall Bay Single",
                    "stand_type": "single",
                    "stand_height": "Single",
                    "arms": 2,
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
                            "stand_type": "single",
                            "stand_height": "Single",
                            "arms": 2,
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
                            "stand_type": "double",
                            "stand_height": "Double",
                            "arms": 0,
                            "sqm": 1.5,
                            "quantity": 2,
                        }
                    ],
                },
            ],
        }

    def test_normalize_selected_stands_recalculates_totals_and_drops_invalid_rows(self):
        stands = [
            {"stand_id": "ST02", "stand_name": "Table", "stand_type": "Gondola", "stand_height": "Double", "arms": 0, "sqm": "1.5", "quantity": 2},
            {"stand_id": "ST01", "stand_name": "Wall", "stand_type": "Wall", "stand_height": "Single", "arms": 2, "sqm": 1.2, "quantity": 1},
            {"stand_id": "ST99", "stand_name": "Ignore", "stand_type": "Table", "stand_height": "Single", "arms": 1, "sqm": 2.0, "quantity": 0},
        ]

        normalized = plan_service.normalize_selected_stands(stands)

        self.assertEqual(["ST01", "ST02", "ST02"], [stand["stand_id"] for stand in normalized])
        self.assertEqual(3, plan_service.compute_stand_count(normalized))
        self.assertEqual(4.2, plan_service.compute_used_space(normalized))
        self.assertEqual(1.5, normalized[1]["total_sqm"])
        self.assertTrue(all(stand.get("stand_instance_id") for stand in normalized))

    def test_compute_stand_product_capacity_uses_simplified_single_and_double_rule(self):
        self.assertEqual(3, plan_service.compute_stand_product_capacity(2, "Single"))
        self.assertEqual(6, plan_service.compute_stand_product_capacity(2, "Double"))
        self.assertEqual(4, plan_service.compute_stand_product_capacity(1, "Single", quantity=2))
        self.assertIsNone(plan_service.compute_stand_product_capacity(1, "table"))

    def test_compute_stand_product_capacity_supports_real_jd_shape(self):
        self.assertEqual(7, plan_service.compute_stand_product_capacity(6, "Single"))
        self.assertEqual(14, plan_service.compute_stand_product_capacity(6, "Double"))

    def test_build_stand_product_capacity_status_reports_underfilled(self):
        status = plan_service.build_stand_product_capacity_status(
            [
                {"product_id": "P1", "product_name": "Tent One"},
                {"product_id": "P2", "product_name": "Tent Two"},
            ],
            2,
            "Double",
        )

        self.assertEqual("underfilled", status["status"])
        self.assertEqual("Underfilled", status["label"])
        self.assertEqual(2, status["assigned_count"])
        self.assertEqual(6, status["capacity"])
        self.assertEqual(4, status["remaining_slots"])

    def test_build_stand_product_capacity_status_reports_just_right(self):
        status = plan_service.build_stand_product_capacity_status(
            [
                {"product_id": "P1"},
                {"product_id": "P2"},
                {"product_id": "P3"},
            ],
            2,
            "Single",
        )

        self.assertEqual("just_right", status["status"])
        self.assertEqual(0, status["remaining_slots"])

    def test_build_stand_product_capacity_status_reports_over_capacity(self):
        status = plan_service.build_stand_product_capacity_status(
            [
                {"product_id": "P1"},
                {"product_id": "P2"},
                {"product_id": "P3"},
            ],
            0,
            "Double",
        )

        self.assertEqual("over_capacity", status["status"])
        self.assertEqual(2, status["capacity"])
        self.assertEqual(-1, status["remaining_slots"])

    def test_normalize_selected_stands_keeps_assigned_product_rows(self):
        normalized = plan_service.normalize_selected_stands(
            [
                {
                    "stand_id": "ST01",
                    "stand_name": "Wall Bay Single",
                    "stand_type": "Gondola",
                    "stand_height": "Single",
                    "arms": 2,
                    "sqm": 1.2,
                    "quantity": 1,
                    "assigned_products": [
                        {"product_id": "P2", "product_code": "P2", "product_name": "Tent Two"},
                        {"product_id": "P1", "product_code": "P1", "product_name": "Tent One"},
                        {"product_id": "P1", "product_code": "P1", "product_name": "Tent One"},
                    ],
                }
            ]
        )

        self.assertEqual(["P1", "P2"], [row["product_id"] for row in normalized[0]["assigned_products"]])

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
            self.assertEqual("Camping Trial", latest_row["plan_name"])
            self.assertEqual(3, latest_row["stand_count"])
            self.assertEqual(3.6, latest_row["used_space"])
            self.assertTrue(latest_row["is_active"])
            self.assertEqual("ST01", latest_row["selected_stands"][0]["stand_id"])

    def test_bigquery_plan_rows_match_expected_schema_shape(self):
        header_row = plan_service._bigquery_plan_header_row(self.plan)
        department_rows = plan_service._bigquery_plan_department_rows("plan-123", self.plan)
        stand_rows = plan_service._bigquery_plan_stand_rows(
            "plan-dept-123",
            self.plan["selected_stands"],
        )

        self.assertEqual("0002", header_row["branch_id"])
        self.assertEqual("Camping Trial", header_row["plan_name"])
        self.assertEqual("draft", header_row["status"])
        self.assertTrue(header_row["is_active"])
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
                    "plan_name": "Camping Trial",
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
                    "stand_height": "Single",
                    "sqm": 1.2,
                    "quantity": 3,
                    "arms": 2,
                },
                {
                    "plan_id": "plan-123",
                    "plan_department_id": "plan-dept-456",
                    "branch_id": "0002",
                    "plan_name": "Camping Trial",
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
                    "stand_height": "Double",
                    "sqm": 1.5,
                    "quantity": 2,
                    "arms": 0,
                }
            ]
        )

        self.assertEqual("plan-123", plan["plan_id"])
        self.assertEqual("Camping Trial", plan["plan_name"])
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
        self.assertEqual("0002|GO Outdoors|camping trial", plan["plan_key"])
        self.assertEqual("0002|GO Outdoors|camping trial", plan_service.branch_saved_plan_ref(plan))

    def test_list_latest_plans_keeps_only_latest_snapshot_per_named_branch_plan(self):
        older = {
            "plan_id": "plan-older",
            "branch_id": "0002",
            "facia": "GO Outdoors",
            "plan_name": "Camping Trial",
            "department": "Camping",
            "saved_at": "2026-03-18T10:00:00+00:00",
            "updated_at": "2026-03-18T10:00:00+00:00",
            "plan_key": "0002|GO Outdoors|camping trial",
            "saved_plan_ref": "plan-older",
        }
        newer = {
            "plan_id": "plan-newer",
            "branch_id": "0002",
            "facia": "GO Outdoors",
            "plan_name": "Camping Trial",
            "department": "Camping",
            "saved_at": "2026-03-18T11:00:00+00:00",
            "updated_at": "2026-03-18T11:00:00+00:00",
            "plan_key": "0002|GO Outdoors|camping trial",
            "saved_plan_ref": "plan-newer",
        }

        with patch.object(plan_service, "load_plan_snapshots", return_value=[older, newer]):
            latest = plan_service.list_latest_plans()

        self.assertEqual(1, len(latest))
        self.assertEqual("plan-newer", latest[0]["plan_id"])
        self.assertEqual("0002|GO Outdoors|camping trial", latest[0]["plan_key"])

    def test_list_latest_plans_keeps_separate_named_plans_for_same_branch(self):
        first = {
            "plan_id": "plan-1",
            "branch_id": "0002",
            "facia": "GO Outdoors",
            "plan_name": "Test 1",
            "saved_at": "2026-03-18T10:00:00+00:00",
            "updated_at": "2026-03-18T10:00:00+00:00",
            "plan_key": "0002|GO Outdoors|test 1",
            "saved_plan_ref": "plan-1",
            "is_active": True,
        }
        second = {
            "plan_id": "plan-2",
            "branch_id": "0002",
            "facia": "GO Outdoors",
            "plan_name": "Test 2",
            "saved_at": "2026-03-18T11:00:00+00:00",
            "updated_at": "2026-03-18T11:00:00+00:00",
            "plan_key": "0002|GO Outdoors|test 2",
            "saved_plan_ref": "plan-2",
            "is_active": True,
        }

        with patch.object(plan_service, "load_plan_snapshots", return_value=[first, second]):
            latest = plan_service.list_latest_plans()

        self.assertEqual(2, len(latest))
        self.assertEqual({"plan-1", "plan-2"}, {row["plan_id"] for row in latest})

    def test_list_latest_plans_hides_logical_plans_with_inactive_latest_snapshot(self):
        active = {
            "plan_id": "plan-active",
            "branch_id": "0002",
            "facia": "GO Outdoors",
            "plan_name": "Camping Trial",
            "department": "Camping",
            "saved_at": "2026-03-18T10:00:00+00:00",
            "updated_at": "2026-03-18T10:00:00+00:00",
            "plan_key": "0002|GO Outdoors|camping trial",
            "saved_plan_ref": "plan-active",
            "is_active": True,
        }
        deleted = {
            "plan_id": "plan-deleted",
            "branch_id": "0002",
            "facia": "GO Outdoors",
            "plan_name": "Camping Trial",
            "department": "Camping",
            "saved_at": "2026-03-18T11:00:00+00:00",
            "updated_at": "2026-03-18T11:00:00+00:00",
            "plan_key": "0002|GO Outdoors|camping trial",
            "saved_plan_ref": "plan-deleted",
            "is_active": False,
        }

        with patch.object(plan_service, "load_plan_snapshots", return_value=[active, deleted]):
            latest = plan_service.list_latest_plans()

        self.assertEqual([], latest)

    def test_deactivate_plan_persists_inactive_deleted_snapshot(self):
        existing = {
            **self.plan,
            "plan_id": "plan-123",
            "plan_key": "0002|GO Outdoors|camping trial",
            "saved_plan_ref": "plan-123",
            "status": "draft",
            "is_active": True,
        }

        with patch.object(plan_service, "get_saved_plan", return_value=existing):
            with patch.object(plan_service, "persist_plan", side_effect=lambda plan: plan) as persist_mock:
                deleted = plan_service.deactivate_plan("0002|GO Outdoors")

        self.assertFalse(deleted["is_active"])
        self.assertEqual("deleted", deleted["status"])
        self.assertEqual("new-created", deleted["created_at"])
        persist_mock.assert_called_once()

    def test_resolve_plan_is_active_only_allows_false_for_deleted_status(self):
        self.assertTrue(plan_service.resolve_plan_is_active({"status": "draft", "is_active": False}))
        self.assertTrue(plan_service.resolve_plan_is_active({"status": "saved", "is_active": False}))
        self.assertFalse(plan_service.resolve_plan_is_active({"status": "deleted", "is_active": False}))

    def test_persist_plan_forces_active_true_for_non_deleted_snapshots(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(plan_service, "_project_root", return_value=Path(temp_dir)):
                result = plan_service.persist_plan({**self.plan, "is_active": False, "status": "draft"})
                rows = plan_service.load_plan_snapshots_from_csv()

        self.assertTrue(result["is_active"])
        self.assertTrue(rows[-1]["is_active"])

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
            self.assertEqual(plan_service.make_plan_key(self.plan), result["plan_key"])
            self.assertTrue((Path(temp_dir) / "data_exports" / "plans.csv").exists())


if __name__ == "__main__":
    unittest.main()
