import sys
import types
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda: None))

from range_control_platform.services.validation_logic import build_validation_result


class TestValidationLogic(unittest.TestCase):
    def setUp(self):
        self.ref_data = {
            "stores": [
                {
                    "branch_id": "0001",
                    "store_grade": "B",
                }
            ],
            "department_grade_allocations": [
                {
                    "department_name": "Camping",
                    "grade": "B",
                    "allowed_linear_meterage": 10,
                }
            ],
        }

    def test_build_validation_result_passes_when_used_space_is_within_allowance(self):
        plan = {
            "branch_id": "0001",
            "department": "Camping",
            "selected_stands": [
                {"stand_id": "ST01", "quantity": 2, "sqm": 2.0, "total_sqm": 4.0}
            ],
        }

        result = build_validation_result(plan, self.ref_data, click_ts=101)

        self.assertEqual("PASS", result["validation_status"])
        self.assertEqual("success", result["color"])
        self.assertIn("Camping: remaining headroom 6.00.", result["details"])

    def test_build_validation_result_fails_when_used_space_exceeds_allowance(self):
        plan = {
            "branch_id": "0001",
            "department": "Camping",
            "selected_stands": [
                {"stand_id": "ST01", "quantity": 3, "sqm": 4.0, "total_sqm": 12.0}
            ],
        }

        result = build_validation_result(plan, self.ref_data, click_ts=202)

        self.assertEqual("FAIL", result["validation_status"])
        self.assertEqual("danger", result["color"])
        self.assertIn("Camping: over by 2.00.", result["details"])

    def test_build_validation_result_reports_missing_allocation(self):
        plan = {
            "branch_id": "0001",
            "department": "Footwear",
            "selected_stands": [],
            "departments": [
                {
                    "department": "Footwear",
                    "allowed_space": None,
                    "selected_stands": [],
                    "plan_department_id": "dept-1",
                }
            ],
        }

        result = build_validation_result(plan, self.ref_data, click_ts=303)

        self.assertEqual("FAIL: One or more department allowances were exceeded.", result["message"])
        self.assertEqual("danger", result["color"])
        self.assertIn(
            "No department allocation found for Footwear at grade B.",
            result["details"],
        )


if __name__ == "__main__":
    unittest.main()
