import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from range_control_platform.services import plan_service


class TestPlanService(unittest.TestCase):
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

            plan = {
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
            }

            with patch.object(plan_service, "_project_root", return_value=Path(temp_dir)):
                plan_service.persist_plan_snapshot_to_csv(plan)
                rows = plan_service.load_plan_snapshots_from_csv()

            self.assertEqual(plan_service.CSV_HEADERS, csv_path.read_text(encoding="utf-8").splitlines()[0].split(","))
            self.assertEqual(2, len(rows))
            latest_row = rows[-1]
            self.assertEqual("0002", latest_row["branch_id"])
            self.assertEqual(3, latest_row["stand_count"])
            self.assertEqual(3.6, latest_row["used_space"])
            self.assertEqual("ST01", latest_row["selected_stands"][0]["stand_id"])


if __name__ == "__main__":
    unittest.main()
