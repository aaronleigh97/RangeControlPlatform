# Branch Plan Model Correction - 2026-03-18

## Why this correction is needed

The current implementation saves a plan as if one plan equals one branch and one department.

That is internally consistent for a narrow "department snapshot" workflow, but it does not match the fuller business process the Range Control Platform is intended to support.

In the real planning model:

- one branch contains multiple departments
- each department has its own allowance
- each department can contain multiple stand selections
- the branch plan should show how space is being accommodated across departments, not only within the last selected department

This means the current model is too narrow.

---

## Current problem

At present, the application behaves like this:

- user selects one branch
- user selects one department
- user adds stands
- the saved plan stores only that single department context

This creates the following issue:

- when a plan is saved, the last selected department becomes the plan's only department
- store context and summary values are therefore tied only to that department snapshot
- the application cannot represent a branch plan made up of multiple departments

That is not a strong fit for the intended business workflow.

---

## Correct target model

The correct model should be:

### 1. Branch-level plan header

One saved plan should represent a branch planning session.

Suggested header meaning:

- one `plan_id`
- one `branch_id`
- one branch-level planning state

The branch-level plan should hold:

- branch/store identity
- planning metadata
- creator
- created timestamp
- status

### 2. Department plan rows inside a branch plan

A branch plan should contain multiple department entries.

Each department entry should hold:

- department name
- allowed space for that department at the branch grade
- selected stands for that department
- used space for that department
- remaining space for that department

This is the real business unit for the current space-allocation logic.

### 3. Stand rows under a department entry

Stand selections belong to a department, not directly to the whole branch plan.

Each stand row should therefore be attached to a department row, not only to a branch plan header.

---

## Recommended BigQuery structure

The current first-pass schema is not sufficient for the corrected model.

### Current tables

- `plans`
- `plan_stands`

### Recommended structure

#### `plans`
One row per branch plan.

Recommended meaning:

- `plan_id`
- `branch_id`
- `created_by`
- `created_at`
- `status`

#### `plan_departments`
One row per department inside a branch plan.

Recommended columns:

- `plan_department_id`
- `plan_id`
- `department_name`
- `store_grade`
- `allowed_space`

Optional later fields:

- `used_space_cached`
- `remaining_space_cached`
- `validation_status`

#### `plan_stands`
One row per stand selection inside a plan department.

Recommended columns:

- `plan_stand_id`
- `plan_department_id`
- `stand_id`
- `quantity`

This gives a clean relationship:

- `plans` -> branch-level header
- `plan_departments` -> department rows within the branch
- `plan_stands` -> stand rows within a department

---

## Recommended in-app data shape

The in-app plan object should move from:

```python
{
    "branch_id": "...",
    "department": "...",
    "selected_stands": [...],
    "allowed_space": ...,
    "used_space": ...
}
```

to something more like:

```python
{
    "plan_id": "...",
    "branch_id": "...",
    "facia": "...",
    "store_grade": "...",
    "square_footage": ...,
    "status": "draft",
    "department_plans": [
        {
            "department_name": "CAMPING",
            "allowed_space": 32.0,
            "used_space": 6.0,
            "remaining_space": 26.0,
            "selected_stands": [
                {
                    "stand_id": "ST01",
                    "quantity": 5,
                    "sqm": 1.2,
                    "total_sqm": 6.0
                }
            ]
        },
        {
            "department_name": "MENSWEAR",
            "allowed_space": 48.0,
            "used_space": 10.0,
            "remaining_space": 38.0,
            "selected_stands": [...]
        }
    ],
    "created_at": "...",
    "updated_at": "..."
}
```

This allows the app to:

- edit one department at a time
- retain multiple departments in the same branch plan
- show a branch summary and department breakdown

---

## UI implications

The Plan Builder should still allow a user to work department-by-department, but the selected department should edit one department entry inside the branch plan rather than replacing the whole saved plan.

This means:

- branch selection establishes the branch plan context
- department selection changes which department entry is being edited
- stands are added to the selected department entry
- switching departments should retain prior department entries

The summary should be split into:

### Branch/store context

- branch
- facia
- store grade
- square footage
- total departments currently added
- total used space across all departments

### Current department summary

- current department allowance
- current department used space
- current department remaining space

### Department breakdown

A table or list should show all departments already added to the branch plan, each with:

- department name
- allowance
- used
- remaining
- stand quantity

---

## Validation implications

Validation should no longer assume the whole plan has a single department.

Instead:

### Department-level validation

For each department row:

- get allowance from `department_grade_allocations`
- total stand usage
- compare usage to allowance

### Branch-level validation summary

The validation output should then summarise:

- how many departments pass
- how many fail
- which departments are over

This would better reflect the branch planning workflow.

---

## Why this is better for the synoptic project

This corrected model supports the synoptic and software engineering goals more strongly because it:

- reflects the real business workflow more accurately
- shows better domain modelling
- improves separation between header, department rows, and stand rows
- demonstrates more thoughtful architecture and data design
- supports future category, SKU, budget, override, and audit extensions more naturally

It is therefore a more defensible and professional design.

---

## Recommended implementation order

1. Correct the documented plan model.
2. Correct the in-app plan state shape.
3. Update the plan builder so department edits accumulate within one branch plan.
4. Update validation to validate all department rows in the branch plan.
5. Update BigQuery schema/persistence to support `plan_departments`.
6. Update reports and saved-plan loading to use the corrected model.

---

## Important note

The current BigQuery schema is not sufficient for the corrected branch-plan model.

That means the application should not keep deepening the current single-department persistence approach without first correcting the design, otherwise more rework will be created later.
