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
1. define the next layer of rule-driving data around categories and SKU allocation
2. extend the plan model so category-level planning can sit inside the department rows
3. start the next validation slice with category/SKU allocation and stand-capacity rules

Why this is next:
- the branch-plan foundation is now materially more stable
- the biggest remaining synoptic gap is no longer builder state, it is missing business-rule depth
- category, SKU, and validation logic are central to the final acceptance criteria and reporting requirements
