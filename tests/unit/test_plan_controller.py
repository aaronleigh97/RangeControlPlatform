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
        html=types.SimpleNamespace(
            Div=lambda children=None, **kwargs: types.SimpleNamespace(children=children, **kwargs),
        ),
        no_update=object(),
    ),
)
sys.modules.setdefault(
    "dash_bootstrap_components",
    types.SimpleNamespace(
        Badge=lambda children=None, **kwargs: types.SimpleNamespace(children=children, **kwargs),
    ),
)

from range_control_platform.controllers.plan_controller import (
    _branch_remaining_space,
    _build_plan_context,
    _merge_latest_saved_plan,
    _over_limit_warning,
    _remaining_space_indicator,
    _replace_department_plan,
    _replace_stand_in_department,
    _selected_stand_departments,
    _saved_plan_options_from_rows,
)


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
                            "stand_height": "Double",
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
                            "stand_height": "Single",
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

    def test_replace_stand_in_department_keeps_product_rows_on_target_stand_only(self):
        department_plan = {
            "department": "Camping",
            "selected_stands": [
                {
                    "stand_id": "ST01",
                    "stand_name": "Wall Bay Single",
                    "stand_type": "Gondola",
                    "stand_height": "Single",
                    "arms": 2,
                    "sqm": 1.2,
                    "quantity": 1,
                    "assigned_products": [{"product_id": "P1"}],
                },
                {
                    "stand_id": "ST05",
                    "stand_name": "Double Gondola 4 Arm",
                    "stand_type": "Gondola",
                    "stand_height": "Double",
                    "arms": 4,
                    "sqm": 2.0,
                    "quantity": 1,
                    "assigned_products": [{"product_id": "P2"}],
                },
            ],
        }

        updated_department = _replace_stand_in_department(
            department_plan,
            {
                "stand_id": "ST01",
                "stand_name": "Wall Bay Single",
                "stand_type": "Gondola",
                "stand_height": "Single",
                "arms": 2,
                "sqm": 1.2,
                "quantity": 1,
                "assigned_products": [{"product_id": "P3"}],
            },
        )

        stands_by_id = {row["stand_id"]: row for row in updated_department["selected_stands"]}
        self.assertEqual(["P3"], [row["product_id"] for row in stands_by_id["ST01"]["assigned_products"]])
        self.assertEqual(["P2"], [row["product_id"] for row in stands_by_id["ST05"]["assigned_products"]])

    def test_merge_latest_saved_plan_replaces_matching_named_plan_instead_of_duplicating(self):
        existing = {
            "plan_id": "plan-old",
            "saved_plan_ref": "plan-old",
            "plan_key": "0487|BLACKS|487 blacks draft",
            "branch_id": "0487",
            "facia": "BLACKS",
            "plan_name": "487 BLACKS Draft",
            "saved_at": "2026-03-22T12:07:00+00:00",
        }
        saved = {
            "plan_id": "plan-new",
            "saved_plan_ref": "plan-new",
            "plan_key": "0487|BLACKS|487 blacks draft",
            "branch_id": "0487",
            "facia": "BLACKS",
            "plan_name": "487 BLACKS Draft",
            "saved_at": "2026-03-22T12:08:00+00:00",
        }

        merged = _merge_latest_saved_plan([existing], saved)
        options = _saved_plan_options_from_rows(merged, {"stores": [], "branches": []})

        self.assertEqual(1, len(merged))
        self.assertEqual("plan-new", merged[0]["plan_id"])
        self.assertEqual(1, len(options))
        self.assertEqual("plan-new", options[0]["value"])

    def test_saved_plan_options_dedupes_duplicate_saved_refs(self):
        rows = [
            {
                "saved_plan_ref": "plan-123",
                "branch_id": "0487",
                "facia": "BLACKS",
                "plan_name": "Test 2",
                "saved_at": "2026-03-22T12:10:00+00:00",
            },
            {
                "saved_plan_ref": "plan-123",
                "branch_id": "0487",
                "facia": "BLACKS",
                "plan_name": "Test 2",
                "saved_at": "2026-03-22T12:10:00+00:00",
            },
        ]

        options = _saved_plan_options_from_rows(rows, {"stores": [], "branches": []})

        self.assertEqual(1, len(options))
        self.assertEqual("plan-123", options[0]["value"])

    def test_branch_remaining_space_uses_square_footage_not_department_allowance_total(self):
        allowed, remaining = _branch_remaining_space(
            {
                "square_footage": 4089,
                "total_used_space": 1.2,
                "departments": [
                    {
                        "department": "ACCESSORIES",
                        "allowed_space": 3,
                        "selected_stands": [
                            {
                                "stand_id": "ST01",
                                "stand_name": "Wall Bay Single",
                                "stand_type": "Wall",
                                "stand_height": "Single",
                                "sqm": 1.2,
                                "quantity": 1,
                            }
                        ],
                    }
                ],
            }
        )

        self.assertEqual(4089.0, allowed)
        self.assertEqual(4087.8, remaining)

    def test_remaining_space_indicator_uses_over_limit_for_negative_remaining(self):
        badge = _remaining_space_indicator(6, -3.6)
        self.assertEqual("Status: Over Limit", badge.children)

        zero_badge = _remaining_space_indicator(6, 0)
        self.assertEqual("Status: No Space Remaining", zero_badge.children)

    def test_over_limit_warning_shows_exact_sqm_overage(self):
        warning = _over_limit_warning(-3.6)
        self.assertEqual("Over department allowance by 3.60 sqm.", warning.children)
        self.assertIsNone(_over_limit_warning(0))

    def test_selected_stand_departments_returns_only_departments_with_stands(self):
        departments = _selected_stand_departments(
            {
                "departments": [
                    {
                        "department": "ACCESSORIES",
                        "selected_stands": [
                            {
                                "stand_instance_id": "1",
                                "stand_id": "ST01",
                                "sqm": 1.2,
                                "quantity": 1,
                            }
                        ],
                    },
                    {
                        "department": "CARAVANING",
                        "selected_stands": [
                            {
                                "stand_instance_id": "2",
                                "stand_id": "ST06",
                                "sqm": 2.2,
                                "quantity": 1,
                            }
                        ],
                    },
                    {
                        "department": "FOOTWEAR",
                        "selected_stands": [],
                    },
                ]
            }
        )

        self.assertEqual(["ACCESSORIES", "CARAVANING"], departments)


if __name__ == "__main__":
    unittest.main()
