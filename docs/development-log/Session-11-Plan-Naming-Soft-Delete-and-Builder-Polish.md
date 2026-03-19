# Session 11: Plan Naming, Soft Delete, and Builder Polish

## Date
2026-03-19

## Summary
This session tightened the branch-plan user workflow after the earlier multi-department model correction. The focus was on making saved plans easier to manage and understand by adding branch-plan naming, active/inactive snapshot handling, clearer summary UI, and more visible save/load feedback.

## What changed
- Added branch-plan naming through a new `plan_name` field on the `plans` header
- Persisted `plan_name` through both BigQuery-backed plan snapshots and local CSV fallback snapshots
- Updated the Saved Plan Snapshot dropdown to show the plan name first, followed by branch/facia/timestamp metadata
- Changed saved-plan selection logic so the dropdown tracks the latest logical branch plan rather than surfacing every raw snapshot as a separate visible option
- Added append-only soft delete behavior using `plans.is_active`
- Added a `Delete Selected Plan` action in the Plan Builder that writes a new inactive snapshot instead of attempting a BigQuery hard delete
- Moved save/load/delete feedback to the top of the Plan Builder and rendered it as dismissible alerts
- Reworked the summary area so it clearly separates:
  - store context
  - current department metrics
  - department-by-department branch breakdown
- Updated wording to reflect the confirmed business decision that department allowance should be treated as `sqm`

## Why it matters
These changes improve the product in practical terms and strengthen the synoptic evidence trail. The app now behaves more like a real planning tool with named branch plans, clearer snapshot lifecycle behavior, and a UI that better matches the business model of one branch plan containing multiple departments.

## Evidence of progress
- A saved branch plan can now have a user-facing alias instead of relying only on concatenated identifiers
- The Saved Plan Snapshot dropdown now stays focused on the latest visible version of a logical branch plan
- A saved plan can be removed from the active list without requiring unsupported BigQuery delete behavior
- The summary UI now shows department allowances and usage in clearer branch-level context
- `py -3 -m unittest discover -s tests -p "test_*.py"` passed
- `py -3 -m compileall src` passed

## Blockers or limitations
- The temporary `Draft Debug` panel is still present and should be removed once the latest builder flow is considered stable
- Soft delete currently works at the branch-plan header snapshot level only; it does not provide row-level lifecycle management inside a single saved plan version
- Supporting docs still need a tidy pass to replace older references to linear meterage assumptions with the now-confirmed `sqm` rule

## Key files
- [plan_controller.py](C:/Users/aaron/PycharmProjects/RangeControlPlatform/src/range_control_platform/controllers/plan_controller.py)
- [plan_service.py](C:/Users/aaron/PycharmProjects/RangeControlPlatform/src/range_control_platform/services/plan_service.py)
- [plan_builder.py](C:/Users/aaron/PycharmProjects/RangeControlPlatform/src/range_control_platform/views/pages/plan_builder.py)
- [test_plan_service.py](C:/Users/aaron/PycharmProjects/RangeControlPlatform/tests/unit/test_plan_service.py)
- [Synoptic-Project-Plan.md](C:/Users/aaron/PycharmProjects/RangeControlPlatform/docs/Synoptic-Project-Plan.md)
- [Repository-Remote-Context.md](C:/Users/aaron/PycharmProjects/RangeControlPlatform/docs/Repository-Remote-Context.md)

## Next step after this session
Remove the temporary debug UI, tidy the remaining plan-builder wording, and then move on from builder-state polish into the next business slice rather than continuing to deepen temporary workflow support.
