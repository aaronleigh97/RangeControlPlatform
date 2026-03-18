def seed_reference_data():
    """
    Local fallback reference data for when the JD BigQuery source is unavailable.
    """
    facias = ["GO Outdoors", "Blacks", "Millets", "GO Express", "Naylors"]
    grades = ["A", "B", "C", "D", "E", "F"]
    departments = ["Footwear", "Clothing", "Camping", "Equipment"]
    branches = [
        {"branch_id": "0001", "branch_name": "Manchester", "grade": "B", "facia": "GO Outdoors"},
        {"branch_id": "0002", "branch_name": "Leeds", "grade": "C", "facia": "GO Outdoors"},
        {"branch_id": "0003", "branch_name": "Sheffield", "grade": "A", "facia": "Blacks"},
        {"branch_id": "0006", "branch_name": "Glasgow", "grade": "C", "facia": "Blacks"},
        {"branch_id": "0004", "branch_name": "Liverpool", "grade": "B", "facia": "Millets"},
        {"branch_id": "0005", "branch_name": "Bolton", "grade": "D", "facia": "Millets"},
        {"branch_id": "0007", "branch_name": "Birmingham", "grade": "D", "facia": "GO Express"},
        {"branch_id": "0008", "branch_name": "York", "grade": "E", "facia": "GO Express"},
        {"branch_id": "0009", "branch_name": "Chester", "grade": "C", "facia": "Naylors"},
        {"branch_id": "0010", "branch_name": "Harrogate", "grade": "D", "facia": "Naylors"},
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
            "stand_type": "Wall",
            "stand_height": "Single",
            "arms": 2,
            "sqm": 1.2,
        },
        {
            "stand_id": "ST05",
            "stand_name": "Double Gondola 4 Arm",
            "stand_type": "Gondola",
            "stand_height": "Double",
            "arms": 4,
            "sqm": 2.0,
        },
        {
            "stand_id": "ST12",
            "stand_name": "Feature Table Large",
            "stand_type": "Table",
            "stand_height": "Large",
            "arms": None,
            "sqm": 1.8,
        },
        {
            "stand_id": "ST14",
            "stand_name": "Bulk Stack Large",
            "stand_type": "Bulk Stack",
            "stand_height": "Large",
            "arms": None,
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
    }
