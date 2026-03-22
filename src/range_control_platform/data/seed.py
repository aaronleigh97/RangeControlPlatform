def seed_reference_data():
    """
    Local fallback reference data for when the JD BigQuery source is unavailable.
    """
    facias = [
        "BLACKS",
        "GO OUTDOORS",
        "GO OUTDOORS EXPRESS",
        "ULTIMATE OUTDOORS",
        "MILLETS",
    ]
    grades = ["A", "B", "C", "D", "E", "F"]
    departments = ["Footwear", "Clothing", "Camping", "Equipment"]
    branches = [
        {"branch_id": "0001", "branch_name": "Manchester", "grade": "B", "facia": "GO OUTDOORS"},
        {"branch_id": "0002", "branch_name": "Leeds", "grade": "C", "facia": "GO OUTDOORS"},
        {"branch_id": "0003", "branch_name": "Sheffield", "grade": "A", "facia": "BLACKS"},
        {"branch_id": "0006", "branch_name": "Glasgow", "grade": "C", "facia": "BLACKS"},
        {"branch_id": "0004", "branch_name": "Liverpool", "grade": "B", "facia": "MILLETS"},
        {"branch_id": "0005", "branch_name": "Bolton", "grade": "D", "facia": "MILLETS"},
        {"branch_id": "0007", "branch_name": "Birmingham", "grade": "D", "facia": "GO OUTDOORS EXPRESS"},
        {"branch_id": "0008", "branch_name": "York", "grade": "E", "facia": "GO OUTDOORS EXPRESS"},
        {"branch_id": "0009", "branch_name": "Chester", "grade": "C", "facia": "ULTIMATE OUTDOORS"},
        {"branch_id": "0010", "branch_name": "Harrogate", "grade": "D", "facia": "ULTIMATE OUTDOORS"},
    ]
    stand_limits = {
        "A": 12,
        "B": 8,
        "C": 5,
        "D": 3,
        "E": 2,
        "F": 1,
    }
    stand_library = [
        {
            "stand_id": "ST01",
            "stand_name": "Wall Bay Single",
            "stand_type": "single",
            "stand_height": "Single",
            "arms": 2,
            "sqm": 1.2,
        },
        {
            "stand_id": "ST05",
            "stand_name": "Double Gondola 4 Arm",
            "stand_type": "double",
            "stand_height": "Double",
            "arms": 4,
            "sqm": 2.0,
        },
        {
            "stand_id": "ST12",
            "stand_name": "Feature Rail Single",
            "stand_type": "single",
            "stand_height": "Large",
            "arms": 1,
            "sqm": 1.8,
        },
        {
            "stand_id": "ST14",
            "stand_name": "Bulk Rail Double",
            "stand_type": "double",
            "stand_height": "Large",
            "arms": 0,
            "sqm": 3.0,
        },
    ]
    stores = [
        {
            "branch_id": branch["branch_id"],
            "branch_name": branch["branch_name"],
            "fascia": branch["facia"],
            "status": "Open",
            "square_footage": 20000,
            "budget_2026": 1000000,
            "store_grade": branch["grade"],
            "region": None,
            "fit_type": None,
            "indoor_tent_field_sqft": None,
            "outdoor_tent_field_sqft": None,
        }
        for branch in branches
    ]
    grade_space_lookup = {
        "A": 60,
        "B": 48,
        "C": 36,
        "D": 28,
        "E": 20,
        "F": 12,
    }
    department_grade_allocations = [
        {
            "department_name": department,
            "grade": grade,
            "allowed_linear_meterage": allowance,
        }
        for department in departments
        for grade, allowance in grade_space_lookup.items()
    ]

    return {
        "facias": facias,
        "grades": grades,
        "departments": departments,
        "categories": {
            "Footwear": ["Walking Boots", "Trainers"],
            "Clothing": ["Jackets", "Base Layers"],
            "Camping": ["Tents", "Sleeping"],
            "Equipment": ["Packs", "Accessories"],
        },
        "stand_limits": stand_limits,
        "branches": branches,
        "stores": stores,
        "department_grade_allocations": department_grade_allocations,
        "stand_library": stand_library,
        "products": [
            {
                "product_id": "CAMP-001",
                "product_code": "CAMP-001",
                "product_name": "Nimbus 2 Tent",
                "department_name": "Camping",
                "range_name": "Tents",
            },
            {
                "product_id": "CAMP-002",
                "product_code": "CAMP-002",
                "product_name": "Summit Sleeping Bag",
                "department_name": "Camping",
                "range_name": "Sleeping",
            },
            {
                "product_id": "CAMP-003",
                "product_code": "CAMP-003",
                "product_name": "Trail Stove Kit",
                "department_name": "Camping",
                "range_name": "Cooking",
            },
            {
                "product_id": "FOOT-001",
                "product_code": "FOOT-001",
                "product_name": "Ridge Mid Boot",
                "department_name": "Footwear",
                "range_name": "Walking Boots",
            },
            {
                "product_id": "FOOT-002",
                "product_code": "FOOT-002",
                "product_name": "Sprint Trail Shoe",
                "department_name": "Footwear",
                "range_name": "Trail Shoes",
            },
            {
                "product_id": "CLOT-001",
                "product_code": "CLOT-001",
                "product_name": "Altitude Waterproof Jacket",
                "department_name": "Clothing",
                "range_name": "Jackets",
            },
            {
                "product_id": "EQUIP-001",
                "product_code": "EQUIP-001",
                "product_name": "Transit 35 Pack",
                "department_name": "Equipment",
                "range_name": "Packs",
            },
        ],
    }
