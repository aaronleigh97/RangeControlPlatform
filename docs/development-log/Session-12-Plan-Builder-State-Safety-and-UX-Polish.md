# Session 12: Plan Builder State Safety and UX Polish

## Date
2026-03-21

## Summary
This session focused on tightening the Plan Builder workflow after the branch-plan save/load model had already been established. The goal was to reduce accidental user actions, improve visibility of draft status, and remove temporary debugging artefacts that were no longer appropriate for the current stage of the project.

The main theme of the session was not new business scope. It was state safety, UI clarity, and consistency between the current editing context and the accumulated branch draft.

## What Was Added

### 1. Explicit unload/reset workflow for loaded plans

An `Unload Current Plan` action was added to the Plan Builder.

What it does:
- clears the currently loaded or in-progress plan context
- clears the selected saved-plan snapshot reference
- clears current draft state stores
- clears plan name, facia, branch, department, and stand-library selections
- leaves the app ready for a fresh draft or a different saved-plan load

Why it was added:
- a loaded snapshot could otherwise remain live in the builder and be changed unintentionally
- this makes the difference between "loaded historical snapshot" and "new draft in progress" clearer for users
- it reduces the risk of accidental edits before a deliberate save

Why it matters for the synoptic project:
- improves usability and control in a real workflow
- demonstrates safe state handling rather than only basic UI interaction
- strengthens the case that the project is designed as a business tool, not just a prototype form

### 2. Status indicators for branch and department space context

Quick-glance status badges were added to:
- the branch-level summary card
- the current department summary card

Status wording now includes:
- `Plenty of Space`
- `Moderate Space`
- `Running Low`
- `No Space Remaining`
- `Unknown`

Why it was added:
- users can now understand planning headroom without reading every metric first
- this improves scanability and supports faster decision-making
- the UI now makes better use of the space/allowance calculations already present in the model

Why it matters for the synoptic project:
- visibly supports the process-improvement goal of reducing manual judgement
- creates stronger screenshot/evidence material because the builder now communicates planning state more clearly
- is easy to explain in terms of user-centred design and requirements-led UI enhancement

### 3. Branch summary wording clarified

The previous `Store Context` wording was changed to `Branch Draft Status`.

Other labels were also clarified:
- `Departments currently added`
- `Branch accommodated space (sqm)`
- `Branch remaining space (sqm)`

Why it was added:
- the summary card represents the accumulated branch draft, not the currently highlighted department
- clearer wording reduces confusion between branch-level and department-level views

Why it matters for the synoptic project:
- improves domain language alignment
- better reflects the corrected branch-plan model introduced in earlier sessions
- makes the UI easier to defend in a report or demo

### 4. Regression coverage for plan-controller state transitions

A new unit test file was added:
- `tests/unit/test_plan_controller.py`

What it now checks:
- empty department rows are removed from the branch draft when their final stand is removed
- switching the department dropdown does not incorrectly promote the selected department into the real branch draft

Why it was added:
- several of the issues found in this session were state-transition bugs rather than persistence bugs
- targeted tests help prevent these behaviours from reappearing as the builder becomes more complex

Why it matters for the synoptic project:
- strengthens evidence of software quality control
- shows that business workflow bugs are being converted into repeatable automated checks

## What Was Removed

### 1. Temporary `Draft Debug` panel

The `Draft Debug` panel and its callback output were removed from the Plan Builder.

Why it was removed:
- it had served its purpose during branch-draft state troubleshooting
- leaving it in would weaken the quality of the user-facing workflow now that the builder has stabilised
- Git history preserves it if it ever needs to be referenced again

Why it matters for the synoptic project:
- demonstrates progression from debug-phase scaffolding to a cleaner business-facing interface
- supports a more professional final walkthrough and screenshot set

### 2. Ghost department-row behaviour in draft state

This was not a visible component removal, but an important logic removal.

Incorrect behaviour removed:
- selecting a department in the dropdown could be treated as if that department had already been added to the real branch draft
- changing departments could create inconsistent `Department Breakdown` behaviour
- the branch-level status could respond to temporary department context rather than actual saved draft rows

What changed in logic:
- branch summaries now use explicit accumulated draft departments only
- current department metrics still use the active dropdown selection as the editing context
- removing the final stand from a department now removes that department row from the live draft breakdown

Why it matters:
- this directly improves correctness of the planning workflow
- it reinforces the separation between current editing context and persisted/accumulated plan structure

## Verification Completed

The following checks passed after the changes:

- `py -3 -m unittest discover -s tests -p "test_*.py"`
- `py -3 -m compileall src/range_control_platform tests`

## Files Most Relevant To This Session

- [plan_controller.py](C:/Users/aaron/PycharmProjects/RangeControlPlatform/src/range_control_platform/controllers/plan_controller.py)
- [plan_builder.py](C:/Users/aaron/PycharmProjects/RangeControlPlatform/src/range_control_platform/views/pages/plan_builder.py)
- [test_plan_controller.py](C:/Users/aaron/PycharmProjects/RangeControlPlatform/tests/unit/test_plan_controller.py)

## Synoptic / Software Engineering Value

This session is useful evidence for the project because it shows:

- controlled evolution of an existing product rather than one-off code generation
- correction of real workflow defects discovered during use
- stronger state modelling around branch-plan editing
- user-centred improvement of the UI through clearer status and safer interactions
- removal of temporary debug artefacts as the product matures
- addition of targeted automated tests to lock in corrected behaviour

This is a good example of professional engineering discipline because the work:
- addresses real usage defects
- improves the quality of the user journey
- keeps business terminology aligned to the domain model
- preserves traceability through incremental changes and documentation

## Recommended Next Step

The next best move is to stop extending temporary builder polish and move into the next real synoptic business slice.

Recommended next implementation focus:
1. add a Product Range workflow inside the existing Plan Builder using a compact offcanvas interaction
2. use stand `arms` plus `stand_type` as a simplified product-capacity rule rather than pretending product dimensions exist
3. introduce guidance rails so the user can see when a department/stand is overfilled, underfilled, or in the acceptable range
4. preserve auditability of product-range decisions so buyer choices can be reviewed later

Why this is next:
- the branch-plan foundation is now materially more stable
- the biggest remaining synoptic gap is no longer builder state, it is missing the next defensible business-rule slice
- current source data supports a simplified capacity model through stand metadata, especially `arms`
- this provides a realistic bridge between stand planning and later audit/validation/reporting requirements

## End-of-Session Reflection

Additional business clarification received at the end of the session:

- the Product Range feature should use `stand_type` (`single` / `double`) rather than `stand_height` for the simplified capacity rule
- the purpose of the feature is not to imitate true product-dimension planning
- the purpose is to create guidance rails and auditable buyer decisions at stand / department level

That means the next implementation should be framed as:

- a controlled product-allocation aid
- capacity based on stand metadata already available in the model
- visual feedback for underfilled / just-right / over-capacity states
- auditable decision capture rather than opaque buyer judgement

## Ready Start For Next Session

Use this implementation order next:

1. Add a repository method for product data and confirm the minimum query fields
2. Add a pure helper for stand product capacity:
   - `single = arms + 1`
   - `double = (arms + 1) * 2`
3. Add unit tests for the helper and status thresholds
4. Extend the plan draft model so each selected stand can hold assigned product rows
5. Add a Plan Builder offcanvas for one selected stand at a time
6. Filter products by department inside the offcanvas
7. Add live status feedback for:
   - underfilled
   - just right
   - over capacity
8. Decide how to persist and later audit product-range choices

## Suggested Next Prompt

```text
Read docs/Synoptic-Project-Plan.md, docs/Project-Progress-Summary-2026-03-18.md, and docs/development-log/Session-12-Plan-Builder-State-Safety-and-UX-Polish.md. Continue from the latest Daily Update section. Start by wiring a product BigQuery query behind the repository layer, then implement a Product Range offcanvas on the Plan Builder that assigns products to selected stands using the simplified capacity rule `single = arms + 1` and `double = (arms + 1) * 2`. Add visual guidance for underfilled / just-right / over-capacity states, add tests for the capacity helper and draft-state behaviour, and update the docs when finished.
```

## Follow-up Outcome - 2026-03-22

The next session completed the recommended Product Range slice on the existing Plan Builder page.

Completed in follow-up:

- added a repository-backed product query shape with minimum fields:
  - `product_id`
  - `product_code`
  - `product_name`
  - `department_name`
  - `range_name`
- added pure helpers for stand product capacity and guidance status
- extended selected stand draft rows so assigned product rows live with the stand they belong to
- added a compact offcanvas for stand-level product assignment
- filtered the available product list by the currently selected department
- surfaced live `underfilled`, `just right`, and `over capacity` feedback in the stand table and offcanvas
- covered the new helper logic and stand-assignment state updates with unit tests

Important follow-up note:

- BigQuery reference-data loading now falls back to seed product rows if the product table/query is unavailable, without discarding the rest of the JD-backed reference data
- BigQuery plan persistence still needs a confirmed schema extension before assigned product rows can be saved and reloaded as first-class audit records
