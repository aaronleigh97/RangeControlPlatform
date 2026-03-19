# BigQuery Core Reference Schema

## Purpose
This is the lean first-pass BigQuery schema needed to get the app working.

It covers only:
1. `stores`
2. `department_grade_allocations`
3. `stand_library`
4. `plans`
5. `plan_departments`
6. `plan_stands`

It does not include:
- audit
- overrides
- source tracking
- validation history

## Current implementation status
Completed in the latest session:
- the first-pass reference and plan tables were created in `jds-gcp-dev-dl-odm-analytics.RangeControlPlatform`
- the three reference-data tables were populated from the Excel source workbooks
- the app's JD repository was updated to read:
  - `stores`
  - `department_grade_allocations`
  - `stand_library`

Current populated row counts:
- `stores`: 357
- `department_grade_allocations`: 114
- `stand_library`: 20

Not yet implemented:
- correcting the first-pass plan schema so one branch plan can contain multiple departments
- writing branch plans into `plans`
- writing department rows into `plan_departments`
- writing selected stands into `plan_stands`
- updating the UI and validation flow to use the corrected branch-plan model

## Dataset Address
From the schema screenshot, the dataset is:

`jds-gcp-dev-dl-odm-analytics.RangeControlPlatform`

The tables below assume that exact dataset.

## 1. `stores`
Purpose: one row per store so the app can select a store and read its fixed planning attributes.

Final columns:
- `branch_id`
- `branch_name`
- `fascia`
- `status`
- `square_footage`
- `budget_2026`
- `store_grade`
- `region`
- `fit_type`
- `indoor_tent_field_sqft`
- `outdoor_tent_field_sqft`

Why each column is needed:
- `branch_id`: unique key for selecting the store in the app
- `branch_name`: readable store name for the UI
- `fascia`: needed for grouping and filtering stores
- `status`: needed to exclude closed stores from planning
- `square_footage`: core store-size input from Dawid's note
- `budget_2026`: kept because it exists in the workbook and will likely be used later
- `store_grade`: core driver for department space allocation
- `region`: useful for filtering and analysis
- `fit_type`: preserves a useful store characteristic without adding complexity
- `indoor_tent_field_sqft`: part of store capacity context
- `outdoor_tent_field_sqft`: part of store capacity context

```sql
CREATE TABLE IF NOT EXISTS `jds-gcp-dev-dl-odm-analytics.RangeControlPlatform.stores` (
  branch_id STRING NOT NULL,
  branch_name STRING NOT NULL,
  fascia STRING NOT NULL,
  status STRING NOT NULL,
  square_footage INT64,
  budget_2026 NUMERIC,
  store_grade STRING,
  region STRING,
  fit_type STRING,
  indoor_tent_field_sqft INT64,
  outdoor_tent_field_sqft INT64
);
```

## 2. `department_grade_allocations`
Purpose: one row per department and grade so the app can look up the allowed space for a department at a given store grade.

Final columns:
- `department_name`
- `grade`
- `allowed_linear_meterage`

Why each column is needed:
- `department_name`: identifies the department being planned
- `grade`: links the rule to the store grade
- `allowed_linear_meterage`: the actual capacity rule from the grading workbook

```sql
CREATE TABLE IF NOT EXISTS `jds-gcp-dev-dl-odm-analytics.RangeControlPlatform.department_grade_allocations` (
  department_name STRING NOT NULL,
  grade STRING NOT NULL,
  allowed_linear_meterage NUMERIC NOT NULL
);
```

## 3. `stand_library`
Purpose: one row per stand type so the app can build plans from real fixtures and calculate used space.

Final columns:
- `stand_id`
- `stand_name`
- `stand_type`
- `stand_height`
- `arms`
- `sqm`

Why each column is needed:
- `stand_id`: unique key for stand selection
- `stand_name`: readable stand label in the UI
- `stand_type`: useful for grouping and later restrictions
- `stand_height`: preserves a meaningful stand characteristic
- `arms`: supports fixture detail where relevant
- `sqm`: the value used to total stand space in the plan

```sql
CREATE TABLE IF NOT EXISTS `jds-gcp-dev-dl-odm-analytics.RangeControlPlatform.stand_library` (
  stand_id STRING NOT NULL,
  stand_name STRING NOT NULL,
  stand_type STRING NOT NULL,
  stand_height STRING,
  arms INT64,
  sqm NUMERIC NOT NULL
);
```

## 4. `plans`
Purpose: one row per saved branch plan so a user can create and save a branch-level planning session.

Final columns:
- `plan_id`
- `branch_id`
- `created_by`
- `created_at`
- `status`

Why each column is needed:
- `plan_id`: unique key for the saved branch plan
- `branch_id`: links the plan to the selected store
- `created_by`: tells you who created the plan
- `created_at`: needed for ordering and tracking saved plans
- `status`: lets the app distinguish draft from later workflow states

```sql
CREATE TABLE IF NOT EXISTS `jds-gcp-dev-dl-odm-analytics.RangeControlPlatform.plans` (
  plan_id STRING NOT NULL,
  branch_id STRING NOT NULL,
  created_by STRING,
  created_at TIMESTAMP NOT NULL,
  status STRING NOT NULL
);
```

## 5. `plan_departments`
Purpose: one row per department inside a saved branch plan.

Final columns:
- `plan_department_id`
- `plan_id`
- `department_name`
- `store_grade`
- `allowed_space`

Why each column is needed:
- `plan_department_id`: unique key for the department row
- `plan_id`: links the department row back to the branch-level plan
- `department_name`: identifies which department is being planned
- `store_grade`: preserves the branch grade used when the allowance was derived
- `allowed_space`: preserves the department allowance used at save time

```sql
CREATE TABLE IF NOT EXISTS `jds-gcp-dev-dl-odm-analytics.RangeControlPlatform.plan_departments` (
  plan_department_id STRING NOT NULL,
  plan_id STRING NOT NULL,
  department_name STRING NOT NULL,
  store_grade STRING,
  allowed_space NUMERIC
);
```

## 6. `plan_stands`
Purpose: one row per stand selection inside a saved department row.

Final columns:
- `plan_stand_id`
- `plan_department_id`
- `stand_id`
- `quantity`

Why each column is needed:
- `plan_stand_id`: unique key for the row
- `plan_department_id`: links the stand row back to its department row
- `stand_id`: identifies which stand was selected
- `quantity`: stores how many of that stand were chosen

```sql
CREATE TABLE IF NOT EXISTS `jds-gcp-dev-dl-odm-analytics.RangeControlPlatform.plan_stands` (
  plan_stand_id STRING NOT NULL,
  plan_department_id STRING NOT NULL,
  stand_id STRING NOT NULL,
  quantity INT64 NOT NULL
);
```

## Practical Relationships
- `plans.branch_id` -> `stores.branch_id`
- `plan_departments.plan_id` -> `plans.plan_id`
- `plan_departments.department_name` -> `department_grade_allocations.department_name`
- `plan_stands.plan_department_id` -> `plan_departments.plan_department_id`
- `plan_stands.stand_id` -> `stand_library.stand_id`
- `stores.store_grade` -> `department_grade_allocations.grade`

## Minimum Working Flow
These six tables are enough for the corrected branch-plan flow:

1. User selects a store from `stores`
2. App reads the store's `store_grade`
3. App creates or loads one branch-level plan in `plans`
4. App looks up allowed department space in `department_grade_allocations`
5. App saves one row per department into `plan_departments`
6. User adds stands from `stand_library`
7. App saves selected stand rows to `plan_stands`

## Correction Note
The earlier first-pass plan schema treated `plans` as if one plan equalled one branch and one department.

That structure is too narrow for the real planning workflow because a branch is made up of multiple departments.

The corrected model is:

- `plans` = branch-level plan header
- `plan_departments` = department rows within the branch plan
- `plan_stands` = stand rows within a department row

The application should now move toward this corrected model rather than deepening the earlier department-only persistence structure.
