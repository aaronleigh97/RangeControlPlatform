# Excel to BigQuery Import Mapping

## Purpose
This file defines exactly how the three Excel workbooks should load into the existing BigQuery tables:

- `RangeControlPlatform.stores`
- `RangeControlPlatform.department_grade_allocations`
- `RangeControlPlatform.stand_library`

This mapping is intentionally narrow.

For the wide `Store Grade and Budget 2026.xlsx` workbook, only the store-level columns listed here should be loaded.

## Target Dataset
Dataset:

`jds-gcp-dev-dl-odm-analytics.RangeControlPlatform`

## 1. `grading_model.xlsx`
Workbook:

`grading_model.xlsx`

Sheet:

`Grading Model`

Target table:

`department_grade_allocations`

### Source to destination mapping
| Source column | Destination column | Type | Notes |
|---|---|---|---|
| `Department` | `department_name` | `STRING` | Trim spaces, uppercase for consistency |
| `Grade` | `grade` | `STRING` | Trim spaces, uppercase |
| `Linear Meterage` | `allowed_linear_meterage` | `NUMERIC` | Cast to numeric |

### Cleaning rules
- Trim leading and trailing spaces from all text fields
- Normalize empty strings to null before filtering
- Uppercase `department_name`
- Uppercase `grade`
- Cast `allowed_linear_meterage` to numeric
- Remove rows where `department_name`, `grade`, or `allowed_linear_meterage` is blank
- Remove fully blank rows
- De-duplicate by `department_name + grade`, keeping the last non-blank row if duplicates exist

## 2. `stand_library.xlsx`
Workbook:

`stand_library.xlsx`

Sheet:

`Stand Library`

Target table:

`stand_library`

### Source to destination mapping
| Source column | Destination column | Type | Notes |
|---|---|---|---|
| `Stand ID` | `stand_id` | `STRING` | Trim spaces, keep exact ID |
| `Stand Name` | `stand_name` | `STRING` | Trim spaces |
| `Type` | `stand_type` | `STRING` | Trim spaces |
| `Height` | `stand_height` | `STRING` | Trim spaces |
| `Arms` | `arms` | `INT64` | Cast to integer |
| `Sqm` | `sqm` | `NUMERIC` | Cast to numeric |

### Cleaning rules
- Trim leading and trailing spaces from all text fields
- Normalize empty strings to null before filtering
- Cast `arms` to integer
- Cast `sqm` to numeric
- Remove rows where `stand_id`, `stand_name`, or `sqm` is blank
- Remove fully blank rows
- De-duplicate by `stand_id`, keeping the last non-blank row if duplicates exist

## 3. `Store Grade and Budget 2026.xlsx`
Workbook:

`Store Grade and Budget 2026.xlsx`

Sheet:

`STORE_DEPT_GRADES`

Target table:

`stores`

## Important handling for this workbook
This workbook is very wide and contains many department and sub-department columns that should not be loaded into `stores`.

Only the store-level columns below should be imported.

The actual useful header row is the second header row in the sheet.

In pandas terms, read this sheet with:

`header=1`

### Source to destination mapping
| Source column | Destination column | Type | Notes |
|---|---|---|---|
| `No.` | `branch_id` | `STRING` | Convert to string, trim spaces, preserve as business key |
| `Name` | `branch_name` | `STRING` | Trim spaces |
| `Fascia` | `fascia` | `STRING` | Trim spaces, uppercase for consistency |
| `Status` | `status` | `STRING` | Trim spaces |
| `Sq. Ft.` | `square_footage` | `INT64` | Remove commas, cast to integer |
| `2026` | `budget_2026` | `NUMERIC` | Remove currency symbols and commas, cast to numeric |
| `Grade` | `store_grade` | `STRING` | Trim spaces, uppercase |
| `Region` | `region` | `STRING` | Trim spaces |
| `Fit type` | `fit_type` | `STRING` | Trim spaces |
| `INDOOR TENT FIELD SQ FT` | `indoor_tent_field_sqft` | `INT64` | Remove commas, cast to integer |
| `OUTDOOR TENT FIELD SQ FT` | `outdoor_tent_field_sqft` | `INT64` | Remove commas, cast to integer |

### Cleaning rules
- Read the sheet using the second header row only
- Select only the 11 store-level columns listed above
- Ignore all department-grade and category columns
- Trim leading and trailing spaces from all text fields
- Normalize empty strings to null before filtering
- Convert `branch_id` to string
- Remove commas from `square_footage`, `indoor_tent_field_sqft`, and `outdoor_tent_field_sqft` before casting
- Remove `£`, commas, and spaces from `budget_2026` before casting
- Uppercase `fascia`
- Uppercase `store_grade`
- Remove fully blank rows
- Remove rows where `branch_id` is blank
- De-duplicate by `branch_id`, keeping the last non-blank row if duplicates exist

### Optional business filter
If you only want active stores in the app, filter after import or at query time:

`status = 'Open'`

I would still load all rows first unless the business tells you to exclude closed stores from the table itself.

## Recommended load order
Load in this order:

1. `department_grade_allocations`
2. `stand_library`
3. `stores`

That gives you the rule tables first, then the larger store master table.

## Suggested validation checks after load

### `department_grade_allocations`
- one row per `department_name + grade`
- no blank grades
- no blank departments

### `stand_library`
- one row per `stand_id`
- `sqm > 0`
- `quantity` is not relevant here

### `stores`
- one row per `branch_id`
- `branch_id` is never blank
- `store_grade` is populated where expected
- numeric fields load as numeric, not strings
