# Session 10: Branch Plan Draft State and Multi-Department Builder

Date: 2026-03-18

## Purpose

This session focused on correcting the in-app planning model so the Plan Builder behaves like a branch-level plan rather than a single-department snapshot.

The main goal was:

- keep one branch plan in progress
- allow multiple departments to accumulate stand selections in the same draft
- make the Selected Stands section show rows across departments
- persist/load the corrected branch-plan shape through BigQuery-backed `plans`, `plan_departments`, and `plan_stands`

This was also a synoptic-aligned correction because the earlier department-only behavior did not properly reflect the real business planning workflow.

## What Was Completed

### 1. Corrected branch-plan persistence model in code

The app-side persistence path now uses:

- `plans` as the branch-level header
- `plan_departments` as one row per department in the saved branch plan
- `plan_stands` as stand rows linked via `plan_department_id`

This replaced the earlier department-on-plan-header assumption.

Key files:

- `src/range_control_platform/services/plan_service.py`
- `src/range_control_platform/controllers/plan_controller.py`

### 2. BigQuery plan save/load now works against the corrected schema

The builder can now:

- save a branch snapshot to BigQuery
- retrieve saved branch snapshots from BigQuery
- load the saved snapshot back into the builder

Important note:

- the current save model is still snapshot-based
- editing a loaded plan means creating a new saved snapshot, not mutating a previous snapshot in place

This was chosen deliberately because it is simpler, safer, and avoids BigQuery update complications around recently streamed rows.

### 3. Branch draft state was reworked to support multiple departments

The important behavioral correction made in this session is:

- changing the Department dropdown no longer means “this is the only department in the plan”
- the active department is now just the editing context
- the accumulated department rows live separately and are rendered as the branch draft ledger

This is what finally enabled:

- add stand in department A
- switch to department B
- add stand in department B
- see both A and B in Selected Stands

### 4. Selected Stands now reflects branch-level draft rows

The Selected Stands section now:

- shows a `Department` column
- lists stand rows across multiple departments
- includes a `Remove` action per row

This aligns the UI with the real branch-planning workflow much better than the earlier single-department view.

### 5. Store Context and Space Summary were clarified

The UI wording was improved so that:

- Store Context is store-level only
- department-specific information is not incorrectly presented as if the store has one department
- the summary makes it clearer that the allowance comes from department allocation rules, not directly from total store square footage
- the current assumption around comparing stand `sqm` to department allowance is explicitly stated

### 6. Validation logic now supports the branch-plan shape

Validation was updated so it can reason across department rows in the branch plan rather than only validating a single current department snapshot.

Key file:

- `src/range_control_platform/services/validation_logic.py`

### 7. Tests were kept updated

Simple explainable `unittest` coverage exists for:

- BigQuery plan row shaping
- branch-plan reconstruction from BigQuery rows
- CSV fallback behavior
- validation outcomes

Current test files:

- `tests/unit/test_plan_service.py`
- `tests/unit/test_validation_logic.py`

Verification completed successfully at end of session:

- `py -3 -m compileall src/range_control_platform`
- `py -3 -m unittest discover -s tests -p "test_*.py"`

## Important Technical Decisions Made

### Snapshot model retained

The app still treats each save as a new snapshot.

That means:

- removing a stand from a loaded plan should affect the new snapshot being built
- previously saved snapshots remain unchanged

This is appropriate for now because:

- it preserves auditability naturally
- it avoids overcomplicating BigQuery mutation behavior
- it is easier to explain in the synoptic context

### No `is_active` flag added yet

A soft-delete flag on `plan_stands` was discussed, but it was not implemented in this session.

Reason:

- the current snapshot model does not require in-place mutation yet
- the simplest and most defensible behavior is still “save a new snapshot”

This may be revisited later if the project needs true record-level edit history inside a single live plan record rather than snapshot-based revisions.

### Separate draft context from accumulated department rows

This became the key fix late in the session.

The previous bugs were caused by mixing:

- current editing context
- stored department rows

The app now uses:

- `plan-draft-store` for current branch/department editing context
- `plan-departments-store` for the accumulated department rows in the branch draft

This separation was necessary to stop department changes from wiping or replacing prior stand rows.

## Synoptic / Software Engineering Objectives Evidenced

This session strengthened several synoptic objectives.

### Business process understanding

The app now better reflects the real planning model:

- one branch plan
- many departments within the branch
- stands allocated to departments

That is materially closer to the real business process than the earlier one-department snapshot behavior.

### Requirements-led development

This work was driven by the recognition that a store does not have one sole department plan.

The correction was requirement-driven, not cosmetic:

- a branch contains many departments
- each department has its own allowance
- the branch plan must accumulate across departments

### Modular architecture

The branch-plan correction was handled through:

- controller-level state flow changes
- service-level plan normalization and persistence shaping
- validation logic updates
- test updates

This is good evidence of layered software engineering rather than ad hoc UI scripting.

### Scalable and maintainable design

Separating:

- branch header
- department rows
- stand rows

and separating:

- editing context
- accumulated draft rows

is a more scalable model for future features such as:

- product assignment
- override workflows
- richer reporting
- final approval/status logic

### Quality and testing

The session included repeated compile/test verification and kept the unit suite aligned with the revised behavior.

This supports the synoptic quality/accountability narrative.

### Professional delivery discipline

This work uncovered several state-management issues and was resolved iteratively rather than ignored.

The project now has a much stronger and more honest internal model than it did at the start of the session.

## Current App Status At End Of Session

Working:

- reference data loads from JD/BigQuery in the user runtime
- BigQuery branch-plan save/load works against:
  - `plans`
  - `plan_departments`
  - `plan_stands`
- the builder can now hold multiple department stand rows in one branch draft
- Selected Stands shows rows across departments
- Add Stand works across multiple departments without the previous department being overwritten
- Remove action exists per selected row

Known temporary state:

- a temporary `Draft Debug` panel is still present in the Plan Builder UI
- it was intentionally kept during debugging and should now be removed next session if the user confirms stability

## Known Gaps / Remaining Work

### 1. Remove temporary debug UI

Current temporary debug artifact:

- `Draft Debug` panel in Plan Builder

This should be removed once the branch draft flow is considered stable.

### 2. Clean up wording and polish

The current UI is more accurate, but it still needs a tidy pass after the draft flow stabilisation:

- saved-plan wording
- summary wording
- possible helper text improvements

### 3. Re-test loaded-plan editing carefully

Fresh draft behavior now works.

The next thing to confirm is that:

- load existing branch snapshot
- switch department
- add/remove stands
- save a new snapshot

behaves identically to a fresh draft.

This should be treated as a priority verification task next session.

### 4. Decide whether to keep snapshot-only editing or introduce soft-delete fields later

Not required immediately, but still an open architectural question:

- keep immutable snapshots only
- or later add fields such as `is_active` / `deactivated_at` for finer-grained stand-row lifecycle control

For now, snapshot-only remains the recommended approach.

### 5. Continue toward richer synoptic scope

Still not completed:

- product/SKU assignment
- budget-aware validation
- override workflow
- audit trail
- richer reports
- clearer finalisation/status progression
- confirmed business rule for comparing allocation units vs stand `sqm`

## Recommended Next Step For Tomorrow

1. Verify loaded-plan editing across multiple departments end to end.
2. If stable, remove the temporary `Draft Debug` panel and any temporary debugging logic.
3. Commit/push this branch-plan draft-state correction as its own unit of work.
4. Then move on to the next business slice rather than continuing to patch builder state.

## Files Most Relevant To This Session

- `src/range_control_platform/controllers/plan_controller.py`
- `src/range_control_platform/controllers/validation_controller.py`
- `src/range_control_platform/services/plan_service.py`
- `src/range_control_platform/services/validation_logic.py`
- `src/range_control_platform/views/layout.py`
- `src/range_control_platform/views/pages/plan_builder.py`
- `tests/unit/test_plan_service.py`
- `tests/unit/test_validation_logic.py`

