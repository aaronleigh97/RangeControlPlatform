# Synoptic Project Plan

## Project
Product Grading & Space Control Tool

## Purpose of this plan
This file turns the synoptic requirements into an execution order that can be used across sessions. It also records what appears to be complete already, what is partially built, and what still needs to be done.

## Data Reality Note

The current source data confirmed for this project supports:

- store-level context from `stores`
- department allowance by grade from `department_grade_allocations`
- stand footprint from `stand_library.sqm`

The current source data does **not** include product/SKU physical-space fields such as:

- SKU dimensions
- facings
- units per stand
- per-product fixture capacity

This means the implemented planning model is currently strongest and most defensible as:

`store -> department allowance -> stand selection -> used stand sqm -> remaining space`

If later phases introduce category or SKU rules, they should be described honestly as one of:

1. a separate simplified business-rule model, such as per-category max SKU counts or per-stand-type item limits; or
2. an extension that requires additional source data not currently present in the imported Excel workbooks.

The project should not imply that it has true product-level physical-capacity data unless such a dataset is added explicitly.

## Product Range Direction

Latest business guidance confirms that the next product-facing slice should introduce guidance rails rather than attempt true physical product-space modelling.

Confirmed direction:

- stand `sqm` continues to control physical space usage
- stand `arms` will be used as a simplified product-capacity signal
- users should be guided when they have selected too many, not enough, or the right amount of product for a department/grade context
- buyer decisions should remain auditable so that product-range choices can be reviewed later

Current working rule for stand product capacity:

- `0 arms` + `single` stand_type = `1` item slot
- `0 arms` + `double` stand_type = `2` item slots
- `1 arm` + `single` stand_type = `2` item slots
- `1 arm` + `double` stand_type = `4` item slots
- the same trend continues as `arms` increase

Simple implementation formula:

- `single` stand_type: `capacity = arms + 1`
- `double` stand_type: `capacity = (arms + 1) * 2`

This should be treated as a simplified business-capacity model, not as a claim that the tool has product-dimension data.

## Daily Update - 2026-03-23

### Last completed
- [x] Corrected Product Range capacity guidance to use the real JD single/double class shape from `stand_height`
- [x] Fixed saved-plan keying so multiple named plans on the same branch remain separate in the saved snapshot list
- [x] Hardened plan persistence so non-deleted saves cannot accidentally persist with `is_active = false`
- [x] Corrected branch draft remaining-space logic so branch status uses branch square footage rather than the current department allowance total
- [x] Added clearer over-limit messaging and exact sqm overage warnings on the branch and department status cards
- [x] Refactored selected stand draft rows to stand-instance level so edit/remove actions target one stand at a time
- [x] Added a department filter above `Selected Stands` so the longer stand-instance list remains usable

### In progress
- [ ] Extend the Validation page so it reflects branch-level and stand-level rule outcomes, not just department space allowance

### Blockers
- Still waiting for the real product query/source shape so the Product Range offcanvas can move off the temporary seed/fallback list
- BigQuery plan persistence still has no agreed schema for saving stand-level product assignments as first-class audit records

### Next actions
1. Extend the Validation page and validation logic for branch over-space, department over-space, and stand product over-capacity rules
2. Wire the real product query into the repository layer once the source shape is confirmed
3. Decide the BigQuery persistence shape for stand-level product assignments and later audit history

### Files touched
- `src/range_control_platform/controllers/plan_controller.py`
- `src/range_control_platform/data/repositories/jd_bigquery_repo.py`
- `src/range_control_platform/data/seed.py`
- `src/range_control_platform/services/plan_service.py`
- `src/range_control_platform/views/pages/plan_builder.py`
- `tests/unit/test_plan_controller.py`
- `tests/unit/test_plan_service.py`
- `docs/Synoptic-Project-Plan.md`
- `docs/Project-Progress-Summary-2026-03-18.md`
- `docs/development-log/Session-12-Plan-Builder-State-Safety-and-UX-Polish.md`

### Notes for next Codex session
- Product guidance now works against the real JD stand shape by using `stand_height` for the simplified single/double capacity class while leaving `stand_type` as descriptive fixture type
- Selected stands are now stored as stand instances in the draft so each row can be edited or removed independently
- The saved-plan dropdown now identifies logical plans by branch + facia + plan name, which avoids named plans overwriting one another in the list
- Validation is the next best slice because the builder state is now much richer than the Validation page currently reflects

## Daily Update - 2026-03-22

### Last completed
- [x] Added repository-backed product-range reference data with a simple BigQuery query shape and seed fallback
- [x] Added reusable stand product-capacity helpers using `arms` and `stand_type`
- [x] Extended selected stand draft rows so product/range assignments are stored against each stand row
- [x] Added a compact Product Range offcanvas to the existing Plan Builder page with department-filtered product selection
- [x] Added live underfilled / just-right / over-capacity guidance in both the stand table and offcanvas
- [x] Added unit tests for the capacity helper, status logic, and stand assignment state updates

### In progress
- [ ] Decide the first persistent audit shape for product-range assignments in the BigQuery `plan_stands` model

### Blockers
- BigQuery plan persistence does not yet have a confirmed column/schema shape for saving assigned product rows, so product assignments are currently draft-state / CSV-auditable only

### Next actions
1. Extend the BigQuery plan schema so `plan_stands` (or a child table) can persist assigned product rows without hiding the audit shape
2. Surface saved product-range assignments on reload from BigQuery once the persistence contract is agreed
3. Fold the new product-capacity status into the later validation/reporting slices

### Files touched
- `src/range_control_platform/data/repositories/jd_bigquery_repo.py`
- `src/range_control_platform/data/seed.py`
- `src/range_control_platform/services/plan_service.py`
- `src/range_control_platform/controllers/plan_controller.py`
- `src/range_control_platform/views/pages/plan_builder.py`
- `tests/unit/test_plan_service.py`
- `tests/unit/test_plan_controller.py`

### Notes for next Codex session
- Minimum in-app product row shape is now `product_id`, `product_code`, `product_name`, `department_name`, `range_name`
- Product selection is filtered by the active department and attached to the selected stand row, not to the whole department
- Capacity guidance is intentionally simplified: assigned row count vs `single` / `double` capacity from `arms`, multiplied by stand quantity
- The UI still presents this as guidance rails and auditability, not physical optimisation
- BigQuery reference-data loading now tolerates product-query failure and falls back to seed products without dropping the rest of the JD reference data

## Daily Update - 2026-03-21

### Last completed
- [x] Added a safer branch-plan editing workflow with explicit unload/reset behaviour for loaded plans
- [x] Added branch-level and department-level space status indicators to make current planning headroom easier to read
- [x] Removed the temporary `Draft Debug` panel and cleaned the related callback output
- [x] Fixed branch-draft state bugs where temporary department selection could leak into real draft rows
- [x] Recorded that the available data supports stand-space planning but not true product-dimension capacity planning
- [x] Agreed the next Product Range feature will use a simplified `arms` + `stand_type` capacity rule and should be built inside an offcanvas on the Plan Builder page

### In progress
- [ ] Prepare the next Product Range implementation slice so it can start from a clear repository/query contract and draft-state design

### Blockers
- Need the product BigQuery query / source shape so product rows can be filtered by department and attached to selected stands

### Next actions
1. Add the product query behind the repository layer and define the minimum product fields needed in-app
2. Add a capacity helper using `arms` and `stand_type`, then cover it with unit tests
3. Extend the branch draft model so each selected stand can hold assigned product/range rows
4. Add an offcanvas on the Plan Builder for product assignment per selected stand
5. Add live visual guidance for underfilled / just-right / over-capacity product assignment
6. Decide the first auditable persistence shape for product-range choices

### Files touched
- `src/range_control_platform/controllers/plan_controller.py`
- `src/range_control_platform/views/pages/plan_builder.py`
- `tests/unit/test_plan_controller.py`
- `docs/development-log/Session-12-Plan-Builder-State-Safety-and-UX-Polish.md`
- `docs/Project-Progress-Summary-2026-03-18.md`
- `docs/Synoptic-Project-Plan.md`

### Notes for next Codex session
- The current builder now behaves more safely: loaded plans can be unloaded explicitly, empty department rows are pruned, and temporary dropdown state no longer pollutes the real branch draft
- `Store Context` has been reframed as `Branch Draft Status` so branch-level progress and current-department context are separated
- The next product-facing slice should remain on the Plan Builder page, but in a compact offcanvas rather than inline on the long page
- The agreed simplified stand product-capacity rule should use `arms` and `stand_type`, not product dimensions and not `stand_height`
- The product feature should be presented honestly as guidance rails and auditability, not as true physical product-space optimisation

## Daily Update - 2026-03-19

### Last completed
- [x] Added branch-plan soft delete using `plans.is_active` so deleted plans drop out of the active snapshot list without requiring BigQuery hard deletes
- [x] Added persisted `plan_name` support to the branch plan header and surfaced it in the Plan Builder and Saved Plan Snapshot dropdown
- [x] Clarified the Plan Builder summary so branch context, current department space, and department-by-department breakdown are shown separately
- [x] Updated saved-plan load/save status messaging so the latest logical plan stays selected and feedback appears at the top of the page
- [x] Confirmed with the business that department allowance should be treated as `sqm`, then updated the UI wording to reflect that decision

### In progress
- [ ] Tidy the remaining temporary debug UI in the Plan Builder and continue polishing the branch-plan editing experience

### Blockers
- None currently blocking the branch-plan workflow

### Next actions
1. Remove the temporary `Draft Debug` panel once the latest branch-plan flow is considered stable
2. Update the supporting docs/schema wording to reflect that department allowance is now confirmed as `sqm`
3. Continue to the next business slice after builder polish rather than extending state/debug logic further

### Files touched
- `src/range_control_platform/controllers/plan_controller.py`
- `src/range_control_platform/services/plan_service.py`
- `src/range_control_platform/views/pages/plan_builder.py`
- `tests/unit/test_plan_service.py`
- `docs/Repository-Remote-Context.md`

### Notes for next Codex session
- Saved plans are now deduped in the active snapshot dropdown by logical branch-plan key, not by raw snapshot `plan_id`
- Deleting a saved plan now writes a new inactive snapshot rather than attempting a BigQuery hard delete
- `plan_name` now belongs on the branch-level `plans` header and is used as the primary user-facing label in the saved-plan dropdown
- The status/flash message now appears near the top of the Plan Builder instead of below the save button
- Department allowance is now confirmed as `sqm`, so the old linear-meter caveat should not be reintroduced

## Daily Update - 2026-03-18

### Last completed
- [x] Updated the plan builder UI to use BigQuery-backed stores, department-grade allocations, and stand library data
- [x] Replaced stand-count validation with department allocation validation using selected stand space
- [x] Expanded local plan snapshots so saved plans now include selected stands and derived space metrics

### In progress
- [ ] Correct the plan model so one branch plan can contain multiple departments, then persist it to BigQuery

### Blockers
- Need business confirmation on whether department `allowed_linear_meterage` can be compared directly with stand `sqm`, or whether a conversion rule is required

### Next actions
1. Correct the BigQuery plan schema to `plans` -> `plan_departments` -> `plan_stands`
2. Refactor the in-app plan model from a single-department snapshot to a branch plan with department rows
3. Update validation and summaries to show branch-level and department-level views

### Files touched
- `src/range_control_platform/controllers/plan_controller.py`
- `src/range_control_platform/controllers/validation_controller.py`
- `src/range_control_platform/services/plan_service.py`
- `src/range_control_platform/views/pages/plan_builder.py`
- `src/range_control_platform/views/pages/validation.py`
- `src/range_control_platform/views/layout.py`
- `src/range_control_platform/data/seed.py`
- `src/range_control_platform/views/pages/admin.py`
- `docs/BigQuery-Core-Reference-Schema.md`
- `docs/Branch-Plan-Model-Correction-2026-03-18.md`

### Notes for next Codex session
- The plan builder now creates a draft plan from store -> department -> stand library selections and saves snapshots with `selected_stands`, `used_space`, and `allowed_space`.
- Validation now compares saved plan stand-space usage against `department_grade_allocations` for the store's fixed grade.
- Current validation still assumes `allowed_linear_meterage` can be compared directly with stand `sqm`; keep this assumption visible until the business confirms it.
- Existing legacy CSV snapshots are schema-migrated on save so new snapshot rows can be appended safely.
- A design correction has now been identified: the current saved-plan model behaves like a single department snapshot, but the real workflow needs one branch plan containing multiple departments.
- The next implementation step should correct the schema and in-app model before adding more persistence or UI behavior on top of the current single-department structure.

## Daily Update - 2026-03-17

### Last completed
- [x] Defined the first-pass BigQuery schema for `stores`, `department_grade_allocations`, `stand_library`, `plans`, and `plan_stands`
- [x] Imported Excel workbook data into the three reference-data BigQuery tables
- [x] Updated the JD repository so the app now reads `stores`, `department_grade_allocations`, and `stand_library` from BigQuery

### In progress
- [ ] Replace the current stand-count planning flow with stand-library selection and department-allocation validation

### Blockers
- Need business confirmation on whether department `allowed_linear_meterage` can be compared directly with stand `sqm`, or whether a conversion rule is required

### Next actions
1. Update the plan builder UI to use BigQuery-backed stores and stand library
2. Replace seed `stand_limits` validation with department allocation validation using `department_grade_allocations`
3. Update plan persistence so the next real version can save to `plans` and `plan_stands`

### Files touched
- `docs/Dawid-Workbook-Implementation-Guide.md`
- `docs/BigQuery-Core-Reference-Schema.md`
- `docs/Excel-To-BigQuery-Import-Mapping.md`
- `scripts/import_reference_data_to_bigquery.py`
- `src/range_control_platform/data/repositories/jd_bigquery_repo.py`

### Notes for next Codex session
- The Excel files were used only as import sources. The runtime source should now be the BigQuery tables.
- Current BigQuery row counts are `stores=357`, `department_grade_allocations=114`, `stand_library=20`.
- `jd_bigquery_repo.py` now returns `stores`, `department_grade_allocations`, and `stand_library` in addition to the older keys the UI still expects.
- `branches` is currently derived from `stores` and filtered to `Open` status for the existing UI flow.
- The next useful milestone is: select a store, select a department, add stands from the stand library, and validate space used against department allowance.

## Current baseline

### Completed already
- [x] Standalone project scaffold exists.
- [x] Core app shell and routing exist.
- [x] Main pages exist for home, plan builder, validation, admin, overrides, and reports.
- [x] Local plan snapshot persistence to CSV is implemented.
- [x] Local validation result persistence to CSV is implemented.
- [x] Branch, facia, and department selection flow exists.
- [x] Basic grade-based stand-count validation exists.
- [x] First-pass stand-library planning and department space validation now exist.
- [x] Seed reference data exists for facias, grades, departments, categories, stand limits, and branches.
- [x] Initial architecture structure exists: controllers, services, models, repositories, views, tests, docs.
- [x] BigQuery core tables have been defined for `stores`, `department_grade_allocations`, `stand_library`, `plans`, and `plan_stands`.
- [x] Workbook data has been imported into the BigQuery reference-data tables.
- [x] The JD repository can now load `stores`, `department_grade_allocations`, and `stand_library` from BigQuery.

### Partially complete
- [ ] Plan creation is only partial.
Current state: the app can save a branch-level stand plan across multiple departments, but it still does not model category composition, SKU assignment, planning period, or final workflow state.
- [ ] Validation is only partial.
Current state: branch and department stand-space validation now exists, but budget, override-aware validation, and any category/SKU-level rule set are still missing.
- [ ] Admin is only partial.
Current state: admin page only displays seed reference data and does not manage configuration.
- [ ] Overrides are only partial.
Current state: overrides page is mostly UI placeholder; workflow, approval, persistence, and audit are missing.
- [ ] Reporting is only partial.
Current state: report page is mostly placeholder; required report outputs are not implemented.

### Not started or still placeholder
- [ ] `validation_service.py`
- [ ] `audit_service.py`
- [ ] Integration tests for plan lifecycle and overrides
- [ ] Full reporting layer
- [ ] Role-based permissions
- [ ] Full audit history
- [ ] Period-aware planning
- [ ] Product-to-stand assignment
- [ ] Budget engine
- [ ] Category dashboard with real-time capacity and budget usage

### Data-supported scope note
- [x] Stand-space planning is supported by real imported business data.
- [ ] Product/SKU physical-capacity planning is not currently supported by the available source data.
- [ ] Any future category/SKU limits will need either a new dataset or a simplified rule table defined by the business.

### Verification gaps
- [ ] Automated tests are not currently runnable in this environment because `pytest` is not installed in the local virtual environment.

## Delivery order

### Phase 1: Stabilise the current foundation
Goal: make the existing scaffold coherent before adding major features.

1. Define the plan domain model properly.
2. Introduce planning period into the saved plan structure.
3. Replace ad hoc dict usage with clearer entities or typed structures where practical.
4. Decide the system of record for local persistence during development.
5. Make the placeholder tests executable.

Definition of done:
- [ ] Plan objects include branch, period, department, category scope, and timestamps.
- [ ] Test runner works locally.
- [ ] Existing flows still save and reload correctly.

### Phase 2: Implement reference configuration
Goal: support the configuration required for business rules.

1. Model branch grades.
2. Model department and category allocations in business-rule form.
3. Model stand catalogue, stand types, simplified stand capacities, and grade entitlements.
4. Model category budgets by branch x department x category x period.
5. Extend admin flows so these values can be viewed and maintained.

Definition of done:
- [ ] Reference data includes all rule-driving entities.
- [ ] Admin page manages more than read-only seed data.
- [ ] Data supports branch + period-specific planning.

Current status:
- `stores`, `department_grade_allocations`, and `stand_library` now exist in BigQuery and are readable via the JD repository.
- Category allocations, stand restrictions by department, and budget modelling are still not implemented.
- No source-backed product/SKU physical-capacity dataset has been identified yet.

### Phase 3: Build the real plan builder
Goal: move from a stand-count demo to an actual planning workflow.

1. Add branch and planning period selection.
2. Correct the plan model so one branch plan can contain multiple departments.
3. Add category selection within department.
4. Add stand selection by category.
5. Add a compact Product Range flow within the Plan Builder using an offcanvas rather than a separate page.
6. Persist plan composition, not just summary counts.
7. Handle stand removal and any later category/SKU reassignment rules.

Definition of done:
- [ ] A user can create a plan for a branch and period.
- [ ] A user can retain multiple departments inside one branch plan.
- [ ] A user can add allowed stands.
- [ ] A user can assign product ranges/items to selected stands using the agreed simplified capacity model.
- [ ] Plan state survives save/load.

### Phase 4: Implement the full validation engine
Goal: enforce the core business rules from the requirements.

1. Build `validation_service.py`.
2. Validate stand type allowed by grade.
3. Validate maximum stands per category.
4. Validate category allocation rules where explicit business limits exist.
5. Validate stand product capacity using the agreed `arms`-based simplified rule model.
6. Validate category budget.
7. Support hard stops and configurable soft warnings.
8. Return validation results in a consistent structure for UI and reporting.

Definition of done:
- [ ] All acceptance criteria rules are represented in code.
- [ ] Validation runs deterministically.
- [ ] UI shows clear errors and warnings.

### Phase 5: Build the category dashboard
Goal: provide the real-time visibility required by the brief.

1. Show maximum allowed categories, products, or SKUs based on the actual available rule set.
2. Show current assigned categories, products, or SKUs where that layer is genuinely implemented.
3. Show remaining capacity.
4. Show budget total, used, and remaining.
5. Update values immediately on stand changes and any later category/SKU changes.

Definition of done:
- [ ] Dashboard reflects live plan state.
- [ ] Remaining capacity and budget update without manual refresh.

### Phase 6: Add overrides and audit trail
Goal: implement controlled exceptions with full traceability.

1. Build `audit_service.py`.
2. Define override request structure.
3. Require reason for override.
4. Record who requested it, when, and which rule was overridden.
5. Add optional admin approval flow.
6. Log SKU add/remove and stand add/remove actions.
7. Prevent finalisation when approval is still pending, if approval is enabled.

Definition of done:
- [ ] Overrides are persisted.
- [ ] Audit history is queryable.
- [ ] Finalisation respects override policy.

### Phase 7: Finalisation workflow
Goal: support validation summary and controlled submission.

1. Produce a validation summary page or panel.
2. Block finalisation when hard-stop rules fail.
3. Allow finalisation only when override rules are satisfied.
4. Mark finalised plans as read-only.
5. Add admin reopen capability if required.

Definition of done:
- [ ] Finalise button only enables under valid conditions.
- [ ] Finalised plans become read-only.

### Phase 8: Reporting
Goal: deliver the required outputs for the synoptic brief.

1. Build Branch Compliance Report.
2. Build Exception Report.
3. Build Grade Impact Report.
4. Build Stand Utilisation Report.
5. Add CSV export first.
6. Add PDF export only if time remains after core requirements are complete.

Definition of done:
- [ ] All four required reports exist.
- [ ] Reports use the real validation and audit data.

### Phase 9: Non-functional completion
Goal: close quality gaps before submission.

1. Add unit tests for validation rules.
2. Add integration tests for plan lifecycle, overrides, and finalisation.
3. Add role-based permissions.
4. Prevent duplicate category/SKU allocation if that model is implemented.
5. Confirm deterministic validation behaviour.
6. Review performance of recalculation and product search.
7. Improve docs and architecture notes for submission evidence.

Definition of done:
- [ ] Core flows are covered by tests.
- [ ] Security and audit basics are in place.
- [ ] Submission documentation matches the implemented system.

## Recommended build sequence by session

### Session 1
- [ ] Make tests runnable.
- [ ] Add planning period to the plan model and save/load flow.
- [ ] Define the missing reference-data structures needed for allocations, budgets, stands, and products.

### Session 2
- [ ] Expand admin configuration to expose editable rule-driving data.
- [ ] Add category selection and stand catalogue support.

### Session 3
- [ ] Implement stand selection rules and stand-capacity rule structure.
- [ ] Add the product-data query source and define how product rows map to departments.

### Session 4
- [ ] Implement category allocation validation if explicit limits are available.
- [ ] Implement stand product-capacity validation using the agreed `arms` rule model.

### Session 5
- [ ] Implement budget model and budget validation.
- [ ] Build the category dashboard.

### Session 6
- [ ] Implement override persistence and audit logging.
- [ ] Connect override state to validation and finalisation.

### Session 7
- [ ] Implement plan finalisation and read-only state.
- [ ] Add reopen/admin behaviour if required.

### Session 8
- [ ] Implement the required reports and CSV export.

### Session 9
- [ ] Add missing tests.
- [ ] Improve docs, acceptance evidence, and submission polish.

## Priority order if time becomes tight
Focus on these first:

1. Branch and period planning flow
2. Category and stand selection
3. Category/SKU rule modelling only if supported by defensible source data or explicit business rules
4. Validation engine
5. Budget control
6. Override and audit
7. Finalisation
8. Reporting
9. Role and performance enhancements

De-scope last:
- [ ] PDF export
- [ ] Advanced admin UX
- [ ] BigQuery integration beyond demo/local mode

## Acceptance criteria checklist
- [ ] User cannot exceed category or SKU limits without override if those limits are defined in a real supported rule model.
- [ ] User cannot exceed stand capacity under the agreed stand-capacity rule model.
- [ ] User cannot exceed category budget without override.
- [ ] User cannot select stand types not permitted by branch grade.
- [ ] Remaining capacity and budget update immediately.
- [ ] Finalisation is blocked when blocking rules are breached.
- [ ] All overrides are fully auditable.
- [ ] Product-range choices are reviewable and auditable at decision level.

## Daily update template
Copy this section into the top of the file or into a session note at the start of each Codex session.

```md
## Daily Update - YYYY-MM-DD

### Last completed
- [ ] Item completed 1
- [ ] Item completed 2

### In progress
- [ ] Current task

### Blockers
- None

### Next actions
1. Next task
2. Next task
3. Next task

### Files touched
- `path/to/file.py`

### Notes for next Codex session
- Important context
- Decisions already made
- What still needs checking
```

## Suggested next Codex prompt
Use something like:

```text
Read docs/Synoptic-Project-Plan.md, docs/Project-Progress-Summary-2026-03-18.md, and docs/development-log/Session-12-Plan-Builder-State-Safety-and-UX-Polish.md. Continue from the latest Daily Update section. Start by wiring a product BigQuery query behind the repository layer, then implement a Product Range offcanvas on the Plan Builder that assigns products to selected stands using the simplified capacity rule `single = arms + 1` and `double = (arms + 1) * 2`. Add visual guidance for underfilled / just-right / over-capacity states, add tests for the capacity helper and draft-state behaviour, and update the docs when finished.
```

## Notes
- Completed status in this file is based on the code currently present in the repository, not just the intended design.
- Some items marked partial may need to be split further once the real data model is introduced.
- Test status could not be fully verified because `.venv\Scripts\python.exe -m pytest` failed with `No module named pytest`.

## Evidence Notes

### Example stakeholder feedback
Use this as evidence-style wording for supervisor or manager feedback on the current iteration.

```text
Subject: Range Control Platform - Progress Review

Hi Aaron,

I’ve reviewed the current iteration of the Product Grading & Space Control Tool and this is a solid start. You’ve made good progress in getting the project structure in place and turning the initial requirements into a working foundation rather than just a concept.

The main strengths at this stage are:
- the project is clearly set up as a standalone tool rather than being embedded into the wider AP platform
- you have a usable application structure with separate pages for planning, validation, admin, overrides, and reporting
- the initial branch/facia/department planning flow is in place
- you’ve started to persist plan and validation outputs, which is useful for demonstrating progression and traceability
- the grade-based validation concept is already working at a basic level

That said, the next phase now needs to focus on moving from a scaffold into a true business-ready planning tool. The main things I need you to incorporate next are:

1. Build out the actual data model for the tool, especially around branch, period, department, category, stand, SKU, allocation, and budget.
2. Replace the current placeholder and seed-data approach with real data sources, using BigQuery tables where appropriate.
3. Extend validation beyond stand-count checks so that it covers category PLU/SKU limits, stand capacity, allowed stand types by grade, and budget control.
4. Implement the category dashboard so remaining space capacity and budget can be seen in real time.
5. Build the override and audit process properly so exceptions are controlled and reportable.
6. Complete the reporting outputs required by the brief, particularly compliance, exceptions, grade impact, and stand utilisation.

You should also give some attention now to defining the BigQuery schema carefully before building too much more functionality, as the success of the later stages will depend on having the correct fields and relationships in place.

Overall, this is good progress for an early iteration. The direction is right. The next milestone is to connect the UI and validation flow to a proper underlying data structure so the application starts to reflect the full synoptic requirements more closely.

Regards,
[Manager Name]
```

### Current context note
- [x] Initial iteration exists and is suitable to evidence early progress.
- [x] BigQuery table design has started.
- [x] BigQuery field list has been defined for the first-pass schema.
- [x] Reference workbook data has been loaded into the first-pass BigQuery tables.
- [ ] Connect the planning UI and validation flow to the new BigQuery-backed model.
- [ ] Decide whether future category/SKU rules will be backed by a new dataset or a simplified business-rule model.

### BigQuery design reminder
When continuing the data model, prioritise fields for:

1. Branch and grade
2. Planning period
3. Department and category
4. Stand catalogue and stand type entitlement
5. SKU master and category membership
6. Category allocation limits
7. Stand capacity
8. Budget basis and budget value
9. Override records
10. Audit history
