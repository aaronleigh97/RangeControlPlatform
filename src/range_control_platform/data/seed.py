def seed_reference_data():
    """
    Dummy reference data so we can build the UI before we know the real JD tables.
    Replace later with ConfigRepo backed by BigQuery.
    """
    return {
        "facias": ["GO Outdoors", "Blacks", "Millets", "GO Express", "Naylors"],
        "grades": ["A", "B", "C", "D", "E", "F"],
        "departments": ["Footwear", "Clothing", "Camping", "Equipment"],
        "categories": {
            "Footwear": ["Walking Boots", "Trainers"],
            "Clothing": ["Jackets", "Base Layers"],
            "Camping": ["Tents", "Sleeping"],
            "Equipment": ["Packs", "Accessories"],
        },
        "stand_limits": {
            "A": 12,
            "B": 8,
            "C": 5,
            "D": 3,
            "E": 2,
            "F": 1
        },
        "branches": [
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
        ],
    }
