import sys
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda: None))
sys.modules.setdefault(
    "dash",
    types.SimpleNamespace(
        ALL="ALL",
        Input=lambda *args, **kwargs: None,
        Output=lambda *args, **kwargs: None,
        State=lambda *args, **kwargs: None,
        ctx=types.SimpleNamespace(triggered_id=None),
        html=types.SimpleNamespace(),
        no_update=object(),
    ),
)
sys.modules.setdefault("dash_bootstrap_components", types.SimpleNamespace())

from range_control_platform.controllers.plan_controller import _build_plan_context, _replace_department_plan


class TestPlanController(unittest.TestCase):
    def test_replace_department_plan_drops_department_when_no_stands_remain(self):
        existing_plan = {
            "departments": [
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
            ]
        }

        updated_departments = _replace_department_plan(
            existing_plan,
            {
                "department": "Camping",
                "store_grade": "B",
                "allowed_space": 48,
                "selected_stands": [],
            },
        )

        self.assertEqual(1, len(updated_departments))
        self.assertEqual("Accessories", updated_departments[0]["department"])

    def test_build_plan_context_does_not_promote_selected_department_into_draft_rows(self):
        ref_data = {
            "stores": [
                {
                    "branch_id": "0002",
                    "branch_name": "Leeds",
                    "fascia": "GO OUTDOORS",
                    "store_grade": "B",
                    "square_footage": 20000,
                }
            ],
            "department_grade_allocations": [
                {
                    "department_name": "Accessories",
                    "grade": "B",
                    "allowed_linear_meterage": 12,
                },
                {
                    "department_name": "Camping",
                    "grade": "B",
                    "allowed_linear_meterage": 48,
                },
            ],
        }
        existing_plan = {
            "branch_id": "0002",
            "facia": "GO OUTDOORS",
            "department": "Accessories",
            "departments": [],
        }

        updated_plan = _build_plan_context(
            ref_data,
            "GO OUTDOORS",
            "0002",
            "Camping",
            existing_plan,
        )

        self.assertEqual("Camping", updated_plan["department"])
        self.assertEqual([], updated_plan["departments"])
        self.assertEqual(48.0, updated_plan["allowed_space"])


if __name__ == "__main__":
    unittest.main()
