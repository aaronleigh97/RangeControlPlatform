# Session 09: Plan Builder and Validation BigQuery Flow

## Date
2026-03-18

## Summary
This session moved the app from the old stand-count demo flow to a first real planning workflow driven by the BigQuery-backed `stores`, `department_grade_allocations`, and `stand_library` data already loaded through the JD repository.

## What changed
- Reworked the plan builder so users now:
  - select a facia, store, and department
  - see the store grade and derived department allowance
  - add stands from the stand library with quantities
  - see selected stand totals, used space, and remaining space
- Replaced the saved-plan snapshot structure so local CSV snapshots now carry:
  - `store_grade`
  - `allowed_space`
  - `used_space`
  - `remaining_space`
  - `selected_stands_json`
- Added CSV schema migration for older local `plans.csv` files before appending new snapshot rows
- Reworked validation so it now:
  - looks up the store's fixed grade from `stores`
  - looks up department allowance from `department_grade_allocations`
  - totals selected stand `sqm`
  - returns pass/fail based on used space vs allowed space
- Expanded fallback seed data so the updated flow still works when BigQuery loading is unavailable

## Why it matters
The planning and validation flow now reflects Dawid's workbook-driven model instead of the original stand-count placeholder. The app can now demonstrate the intended milestone more credibly: fixture-based department planning against a grade-based space allowance.

## Evidence of progress
- The plan builder no longer depends on the legacy `stand-count` input
- Saved plans now retain selected stand rows and derived space totals in local snapshots
- Validation output now states:
  - store grade
  - department allowance
  - selected stand space used
  - remaining or exceeded space
- `py -3 -m compileall src/range_control_platform` completed successfully after the changes

## Blockers or limitations
- Plan persistence is still local CSV only; `plans` and `plan_stands` are not yet written to BigQuery
- The current builder supports add and clear actions, but not row-level stand removal or quantity editing
- Validation still assumes `allowed_linear_meterage` can be compared directly to stand `sqm` until the business confirms the unit rule
- Reporting still summarizes historical snapshots mainly through legacy stand-count metrics

## Key files
- [plan_controller.py](C:/Users/aaron/PycharmProjects/RangeControlPlatform/src/range_control_platform/controllers/plan_controller.py)
- [validation_controller.py](C:/Users/aaron/PycharmProjects/RangeControlPlatform/src/range_control_platform/controllers/validation_controller.py)
- [plan_service.py](C:/Users/aaron/PycharmProjects/RangeControlPlatform/src/range_control_platform/services/plan_service.py)
- [plan_builder.py](C:/Users/aaron/PycharmProjects/RangeControlPlatform/src/range_control_platform/views/pages/plan_builder.py)
- [validation.py](C:/Users/aaron/PycharmProjects/RangeControlPlatform/src/range_control_platform/views/pages/validation.py)
- [seed.py](C:/Users/aaron/PycharmProjects/RangeControlPlatform/src/range_control_platform/data/seed.py)

## Next step after this session
Persist the new stand-based plan shape into BigQuery `plans` and `plan_stands`, then add row-level stand editing so the builder does not rely on clear-and-rebuild behaviour.
