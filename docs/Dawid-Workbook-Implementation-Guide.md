# Dawid Workbook Implementation Guide

## Why this file exists
This is a simple working note for turning Dawid's email and the three Excel files into clear next steps for the Range Control Platform.

The aim is not to build everything at once.

The aim is to:
- understand the new business inputs
- map them to your current app
- implement them in a sensible order

## Current status
Completed in the latest session:
- BigQuery core tables were defined for `stores`, `department_grade_allocations`, `stand_library`, `plans`, and `plan_stands`
- Data was imported from the three Excel workbooks into:
  - `jds-gcp-dev-dl-odm-analytics.RangeControlPlatform.stores`
  - `jds-gcp-dev-dl-odm-analytics.RangeControlPlatform.department_grade_allocations`
  - `jds-gcp-dev-dl-odm-analytics.RangeControlPlatform.stand_library`
- The JD repository now reads those three BigQuery tables into the app reference-data layer
- The plan builder now lets the user select a store, choose a department, add stands from the stand library, and save a local plan snapshot with derived space metrics
- Validation now compares selected stand space against the department allocation for the store's fixed grade

Current loaded row counts:
- `stores`: 357
- `department_grade_allocations`: 114
- `stand_library`: 20

What this means:
- the Excel workbooks are now source/import files, not the runtime source for the app
- the tool should now move forward using the BigQuery tables as the system of record
- the next job is to persist the new stand-based plan structure into `plans` and `plan_stands`

## What Dawid is asking for
The business has agreed a more structured planning method based on three fixed inputs:

1. Store size and fixed store grade
2. Department space allowance by grade
3. Standard stand library with known space footprint

That means the tool should stop relying on manual judgement and instead do this:

1. Start with the store
2. Look up its fixed grade
3. Look up each department's allowed space for that grade
4. Let the user choose stands
5. Add up the stand space used
6. Warn or block when the selected stands exceed the allowed space

## What the three workbooks appear to contain

### 1. `Store Grade and Budget 2026.xlsx`
This looks like the estate-level source file.

Useful columns near the start:
- Branch number
- Branch name
- Square footage
- 2026 budget
- Fascia
- Grade
- Status

It also contains many department and sub-department grade columns.

What I found:
- 359 rows total
- 179 rows marked `Open`
- 175 rows marked `Closed`
- Fascias include `BLACKS`, `GO OUTDOORS`, `GO OUTDOORS EXPRESS`, `MILLETS`, `ULTIMATE OUTDOORS`

What this workbook should do in your tool:
- become the store master input
- provide the branch list
- provide store square footage
- provide fixed store grade
- optionally provide budget later

### 2. `grading_model.xlsx`
This is the department grading curve.

It has three columns:
- `Department`
- `Grade`
- `Linear Meterage`

This is the clearest rules table of the three files.

Example values:
- `MENSWEAR`: A=61, B=58, C=53, D=48, E=45, F=35
- `WOMENSWEAR`: A=48, B=45, C=36, D=34, E=27, F=16
- `WALKING`: A=52, B=49, C=43, D=36, E=28, F=20
- `CAMPING`: A=46, B=43, C=38, D=32, E=25, F=18

What this workbook should do in your tool:
- define the allowed space per department for a given grade
- become the main validation table for department capacity

### 3. `stand_library.xlsx`
This is the physical fixture library.

It has these columns:
- `Stand ID`
- `Stand Name`
- `Type`
- `Height`
- `Arms`
- `Sqm`

Examples:
- `ST01 Wall Bay Single = 1.2 sqm`
- `ST05 Double Gondola 4 Arm = 2.0 sqm`
- `ST12 Feature Table Large = 1.8 sqm`
- `ST14 Bulk Stack Large = 3.0 sqm`

What this workbook should do in your tool:
- provide the allowed stand catalogue
- let a user build a department from real fixtures
- calculate used space from stand selections

## What this means for your app
Your current app already has the right broad structure, but the business rules are still too simple.

Right now the app mainly does:
- branch / facia / department selection
- stand count entry
- one grade-based stand-count validation

The new requirement changes the model to:

1. Store has a fixed grade and square footage
2. Department gets an allowed space amount from the grading model
3. User chooses actual stand types from the stand library
4. Tool totals stand `sqm`
5. Tool compares `used sqm` vs `allowed sqm`

That is the next real version of the product.

## The build order you should follow
Do these in order. Do not jump ahead to reporting or advanced UI yet.

### Step 1. Clean and confirm the source data
Goal: make sure the three files can be trusted as inputs.

Do this:
- confirm which stores should be included: probably `Open` only
- confirm whether all fascias should be included
- confirm whether store grade should come only from the store master workbook
- confirm whether the valid working grade scale is `A-F` or something wider for some fascias
- confirm whether department meterage should stay in linear meters or be converted to square meters for validation

Output:
- one short note listing agreed assumptions

Why this matters:
- if the grade scale or unit of measure is unclear, the tool logic will be wrong

### Step 2. Add the new reference-data entities to the app
Goal: get the right data shapes into the repository layer.

Add these reference tables to your app model:
- `stores`
- `department_grade_allocations`
- `stand_library`

Suggested fields:

`stores`
- branch_id
- branch_name
- fascia
- status
- square_footage
- budget_2026
- store_grade

`department_grade_allocations`
- department_name
- grade
- allowed_linear_meterage

`stand_library`
- stand_id
- stand_name
- stand_type
- stand_height
- arms
- sqm

Output:
- seed or imported reference data in a stable app shape

### Recommended first-pass field definitions
Use these as the first version unless the business gives a stronger rule.

#### `stores`
Purpose: one row per store in the estate master.

Recommended fields:
- `branch_id`: string
- `branch_name`: string
- `branch_display_name`: string
- `fascia`: string
- `status`: string
- `square_footage`: integer
- `budget_2026`: numeric
- `store_grade`: string
- `region`: string
- `fit_type`: string
- `indoor_tent_field_sqft`: integer
- `outdoor_tent_field_sqft`: integer
- `source_file`: string
- `source_sheet`: string
- `source_row_number`: integer

Keep on day 1:
- `branch_id`
- `branch_name`
- `fascia`
- `status`
- `square_footage`
- `budget_2026`
- `store_grade`

Helpful notes:
- `branch_display_name` can be something like `BEDFORD (GO)` if you want the UI label separate from the raw key
- keep `source_row_number` while importing because it makes workbook tracing easier
- filter to `Open` stores in app logic unless the business says otherwise

#### `department_grade_allocations`
Purpose: one row per department x grade rule.

Recommended fields:
- `department_name`: string
- `grade`: string
- `allowed_linear_meterage`: numeric
- `unit_of_measure`: string
- `is_active`: boolean
- `source_file`: string
- `source_sheet`: string
- `source_row_number`: integer

Keep on day 1:
- `department_name`
- `grade`
- `allowed_linear_meterage`

Helpful notes:
- set `unit_of_measure` to `linear_meter` for now so the unit is explicit
- if later the business converts this to square meters, do not overwrite the original field; add a derived field

#### `stand_library`
Purpose: one row per standard stand type.

Recommended fields:
- `stand_id`: string
- `stand_name`: string
- `stand_type`: string
- `stand_height`: string
- `arms`: integer
- `sqm`: numeric
- `is_active`: boolean
- `source_file`: string
- `source_sheet`: string
- `source_row_number`: integer

Keep on day 1:
- `stand_id`
- `stand_name`
- `stand_type`
- `stand_height`
- `arms`
- `sqm`

Helpful notes:
- keep `arms` nullable for stands where it does not matter
- keep `sqm` as the validation measure coming from the stand library

### What to create first
If you only do one thing first, define these three clean business keys:

- `stores.branch_id`
- `department_grade_allocations.department_name + grade`
- `stand_library.stand_id`

Those keys are enough to start wiring the app.

### Step 3. Change the plan model
Goal: stop saving only a stand count.

Your saved plan should move toward this structure:
- selected store
- selected department
- store grade
- allowed department space
- selected stands
- used stand space
- validation result

Minimum first version:
- branch_id
- fascia
- department
- store_grade
- allowed_space
- selected_stands
- used_space
- created_at
- updated_at

Output:
- a plan can hold stand selections, not just a number

### Step 4. Replace stand-count entry with stand selection
Goal: make planning fixture-based.

Instead of asking for `Planned Stand Count`, the UI should let the user:
- choose a stand from the library
- add quantity
- see total used space

Simple first version:
- dropdown for stand
- numeric quantity
- add-to-plan button
- small table of chosen stands
- calculated total used sqm

Output:
- the user builds a department from actual fixtures

### Step 5. Build the first real validation rule
Goal: validate department space properly.

Validation logic for first release:
- get the store grade from the selected store
- get the department allowed meterage for that grade
- total the selected stand space
- compare used space against allowed space

For now, keep the rule simple:
- `PASS` if used space is within allowed space
- `FAIL` if used space exceeds allowed space

Output:
- one real business validation based on the new workbooks

### Step 6. Show the user the numbers clearly
Goal: remove guesswork in the UI.

On the plan page, show:
- selected store grade
- store square footage
- selected department
- allowed department space
- used stand space
- remaining space

Output:
- user can see why the plan passes or fails

### Step 7. Only then think about budgets
Goal: avoid mixing too many rules too early.

The store workbook includes budget, but budget validation should come after the space model works.

Phase this later:
- first get store -> department -> stands -> space validation working
- then decide how budget should connect to departments or categories

Output:
- budget becomes phase 2, not phase 1

## What you should do first in this repo
If you want a practical coding order inside this project, do this:

1. Replace the current seed-only `stand_limits` logic with department allocation logic
2. Update the plan page UI to capture stand selections instead of only stand count
3. Update the saved plan structure in `plan_service.py`
4. Replace the current validation callback with space-used vs space-allowed validation
5. Add plan saving to the `plans` and `plan_stands` BigQuery tables after the UI shape is stable
6. Update the report summary later, after the plan model is stable

## Recommended short-term milestone
Keep the next milestone small:

### Milestone 1
"I can select a store and department, add stands from the stand library, and the app tells me whether the department space has been exceeded."

Status:
- implemented in the current local snapshot flow
- still needs BigQuery plan persistence and richer stand editing to complete the next pass cleanly

## Questions to get answered before coding too far
Ask these early:

1. Should closed stores be excluded completely?
2. Is the working store-grade scale definitely `A-F`, or do some fascias use a different scale?
3. Is `Linear Meterage` meant to be used directly, or must it be converted before comparing with stand `sqm`?
4. Should every department be buildable from every stand type, or do some departments have restricted fixture types?
5. Is budget validation needed in the first release of this new model, or can it wait?

## My recommendation
Do not try to solve all three business themes at once.

Build this in two passes:

### Pass 1
- store master
- department grade allocations
- stand library
- stand-based space validation

### Pass 2
- budget rules
- override flow
- reporting
- richer admin tooling

## Definition of done for the next piece of work
You are done with the next meaningful step when:
- the app loads stores from a structured source
- each store has a visible fixed grade
- each department has an allowed space value by grade
- the user can add stands from the stand library
- the app totals used space automatically
- the validation result is based on space usage, not manual stand count

## Suggested next prompt for Codex
Use this when you want to start implementation:

```text
Read docs/Dawid-Workbook-Implementation-Guide.md, docs/BigQuery-Core-Reference-Schema.md, and docs/development-log/Session-08-BigQuery-Reference-Data-Import-and-Repository-Wiring.md. Continue from the current state by implementing Milestone 1 end-to-end, starting with the plan builder UI and validation flow so they use the BigQuery-backed stores, department_grade_allocations, and stand_library data.
```
