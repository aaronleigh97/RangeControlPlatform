# ADR-002: Application Architecture

## Status
Accepted

## Context
The project needs to support a standalone Dash application now, while still allowing reference data to move from local seed data to JD BigQuery-backed data.

The current app already has separate pages for:
- home
- plan builder
- validation
- overrides
- reports
- admin

The architecture also needs to remain simple enough to explain clearly in synoptic evidence.

## Decision
Use a layered structure:

- `views/` for page layouts and reusable UI components
- `controllers/` for Dash callbacks and page orchestration
- `services/` for business logic and local persistence helpers
- `data/repositories/` for reference-data access
- `models/` for domain and validation structures

Reference data is accessed through a repository boundary so the page and callback code can work with one shared data shape regardless of source.

Repository selection is environment-driven:
- `ENV=local` uses in-memory seed reference data
- `ENV=jd` uses JD BigQuery-backed queries

The JD repository currently supplies:
- facias
- branches via `CONCAT(BR_NAME, ' - ', CAST(BRCH AS STRING))`
- branch grades
- departments

The app preloads reference data into a shared `ref-data-store` at startup. If JD BigQuery loading fails, the app falls back to seed data and surfaces the load error in the UI so development can continue.

## Consequences
Positive:
- UI callbacks stay simple because dropdowns consume one shared reference-data structure
- moving from demo data to JD data does not require rewriting page logic
- the architecture is straightforward to explain and evidence
- the app remains usable when Google authentication is unavailable

Negative:
- fallback mode can mask data-source issues unless the warning is checked
- some business logic is still inside controllers rather than dedicated services
- branch selection currently stores the JD branch label string rather than a separate raw branch code

## Notes
This ADR describes the current implemented architecture, not the final target state.

The next architectural extension is to move more rule-driving entities behind the repository boundary, including categories, allocations, stand rules, and budgets.
