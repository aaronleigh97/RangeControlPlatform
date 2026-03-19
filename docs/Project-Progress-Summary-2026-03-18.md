# Project Progress Summary - 2026-03-18

## Purpose

This document records what has been implemented so far in the Range Control Platform and explains how the work completed to date supports both:

1. the practical business application;
2. the synoptic Software Engineering objectives of the project.

It is intended to provide an honest and defensible summary of progress at this stage.

---

## Current Application Progress

The project has now moved beyond an initial scaffold and basic demo behaviour into a first real business-aligned planning workflow.

The application can currently:

- load reference data from BigQuery-backed sources for:
  - `stores`
  - `department_grade_allocations`
  - `stand_library`
- fall back to local seed data when BigQuery loading is unavailable
- allow a user to select:
  - fascia
  - store
  - department
- derive the selected store's fixed grade
- derive department allowance from grade-based department allocation data
- allow a user to add stands from the stand library with quantities
- calculate:
  - used stand space
  - remaining department allowance
- validate the saved plan against department space allowance
- save local plan snapshots with:
  - selected stands
  - store grade
  - allowed space
  - used space
  - remaining space
- reload saved local plan snapshots
- save validation outcomes locally

This means the application now reflects a real business workflow path:

`store -> grade -> department allowance -> stand selection -> used space -> validation`

That is a significant improvement over the earlier stand-count-only prototype logic.

---

## Work Completed So Far

### 1. BigQuery reference-data foundation

The project now has a defined first-pass BigQuery data foundation for the planning model.

Completed work:

- defined core BigQuery schema for:
  - `stores`
  - `department_grade_allocations`
  - `stand_library`
  - `plans`
  - `plan_stands`
- imported workbook data into the BigQuery reference-data tables
- updated repository logic so the application can read BigQuery-backed reference data
- introduced repository selection and startup loading through a cleaner application structure
- added fallback behaviour so local seed data is used if BigQuery loading fails

This establishes the system-of-record direction for the project and reduces dependence on temporary Excel-driven or purely hard-coded demo data.

### 2. Plan builder improvements

The plan builder has been updated so it no longer relies only on a simple stand-count input.

Completed work:

- replaced stand-count entry with stand-library selection
- enabled stand quantity entry
- added selected-stand accumulation within the plan
- added plan summary values for:
  - store grade
  - allowed department space
  - used stand space
  - remaining space
- widened the local plan snapshot model to store richer plan data

This changes the application from a rough prototype into a more realistic planning tool.

### 3. Validation improvements

Validation now uses the new business inputs rather than simple grade-based stand-count rules.

Completed work:

- replaced legacy stand-limit validation with department allocation validation
- derived the selected store grade from store data
- derived the department allowance from `department_grade_allocations`
- totalled stand usage from selected stand `sqm`
- returned pass/fail based on used space vs allowed department space
- extracted validation decision logic into reusable testable code

This creates a more realistic business-rule engine and a better basis for future validation extensions.

### 4. Persistence improvements

The project now has a richer local snapshot model that better reflects real planning data.

Completed work:

- expanded local CSV snapshot structure to include:
  - `store_grade`
  - `allowed_space`
  - `used_space`
  - `remaining_space`
  - `selected_stands_json`
- added CSV schema migration handling for older snapshot files
- preserved local save/load behaviour while moving toward a richer plan model

This is still an interim persistence solution, but it is materially better than a single stand-count field.

### 5. Testing improvements

The project now includes simple and explainable automated tests around key business logic.

Completed work:

- added tests for plan service logic
- added tests for validation logic
- verified:
  - stand normalization
  - stand count calculation
  - used space calculation
  - CSV snapshot compatibility/migration
  - validation pass behaviour
  - validation fail behaviour
  - missing allocation behaviour

The tests were kept intentionally simple so they can be explained clearly as part of synoptic evidence.

### 6. Incremental version control discipline

The implementation work has been broken into small pushes rather than one large undifferentiated code drop.

Pushed commits include:

- `a277e06` - `Add stand-based plan snapshot persistence`
- `0cc5339` - `Build stand-library plan builder flow`
- `0b32ca6` - `Add department allocation validation tests`
- `396ef95` - `Document stand-based planning milestone`
- `d668a53` - `Wire app startup to BigQuery reference data`

This improves the credibility of project progression and demonstrates better engineering discipline.

---

## Synoptic / Software Engineering Objectives Supported So Far

### 1. Business process understanding

The project now maps more clearly to the real planning process rather than acting like a generic demo application.

Evidence of this includes:

- store and fascia selection
- use of fixed store grade
- department allocation by grade
- stand-library-driven planning
- validation against department allowance

This supports the requirement to analyse and redesign a real business process.

### 2. Requirements-led development

The implemented changes have followed the agreed business inputs and workbook-driven planning model.

Evidence of this includes:

- using store grade as the driver of planning rules
- using department allocations by grade
- using a structured stand library
- validating space usage against allowance

This supports the idea that the project is being developed in response to real requirements rather than arbitrary feature additions.

### 3. Modular architecture

The codebase now demonstrates clearer separation of concerns.

Current layers include:

- pages/views
- controllers/callbacks
- services
- repositories
- tests
- documentation

This supports maintainability, explainability, and evidence of deliberate software architecture.

### 4. Scalable and maintainable design

The application has started moving away from hard-coded demo logic and toward a more extensible structure.

Evidence of this includes:

- repository-based reference-data access
- extracted validation logic
- richer plan model
- startup fallback handling
- data-driven stand and allocation logic

This supports the objective of creating a maintainable and scalable solution.

### 5. Product/process improvement mindset

The current implementation already improves the planning concept by:

- reducing manual judgement
- using structured allocation inputs
- improving consistency
- making validation more transparent
- improving realism in stand planning

This supports the synoptic expectation that the project should improve a real process or product concept.

### 6. Quality and testing

The project now has simple but real examples of software quality control.

Evidence includes:

- reusable business-rule functions
- automated unit tests
- validation logic separated from UI wiring
- snapshot compatibility handling

This supports evidence for source code quality and validation quality.

### 7. Documentation and explainability

The project now includes more structured documentation to support both implementation and reporting.

Existing documentation now includes:

- implementation guidance
- project planning
- development logs
- architecture notes
- synoptic instruction context

This supports explainability and written evidence generation.

### 8. Professional delivery discipline

The recent work has been carried out in Git-friendly functional slices rather than as a single large unstructured change.

This supports evidence for:

- version control discipline
- incremental delivery
- scope control
- more realistic professional practice

---

## Important Current Limitations

To remain honest and academically defensible, the following limitations still apply:

- plan persistence is still local CSV rather than BigQuery-backed `plans` and `plan_stands`
- override workflow is not yet implemented
- audit trail is not yet implemented
- product/SKU assignment is not yet implemented
- budget rules and budget validation are not yet implemented
- finalisation workflow is not yet implemented
- reporting remains partial
- the unit comparison assumption still needs business confirmation:
  - whether `allowed_linear_meterage` can be compared directly with stand `sqm`

This means the project has not yet reached the full intended end state.

---

## Honest Stage Assessment

At this point, the project should be described as:

- beyond scaffold/demo stage
- containing a real business-aligned planning and validation slice
- demonstrating architecture, data access, validation, persistence thinking, testing, and documentation
- still incomplete against the full final synoptic target

This is a credible and defensible stage of progress for an assessed software engineering project.

---

## Recommended Next Step

The next most valuable engineering step is:

1. persist the stand-based plan structure into BigQuery `plans` and `plan_stands`;
2. add simple tests around persistence mapping and save behaviour;
3. continue pushing work in small incremental Git units.

This would improve the application's credibility as a real business system and strengthen alignment with the synoptic expectation of app-owned persisted data and professional engineering delivery.
