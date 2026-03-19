# Repository Remote Context

## Purpose

This note records the intended meaning of the configured Git remotes so future sessions do not mix the work-context and post-employment versions of the project.

## Remote meanings

- `origin`
  - Work-context repository
  - Use for changes that are part of the JD-integrated version of the Range Control Platform
  - This is the version that can use JD-backed / BigQuery-backed data while access still exists

- `personal`
  - Personal continuation repository
  - Use for the non-work version of the application after employment ends and JD data access is no longer available
  - This is the likely home for the future local-data / internal-database variant of the tool

## Working rule

When a change depends on JD tables, JD credentials, or JD-integrated behavior, treat `origin` as the relevant remote.

When a change is specifically for the standalone post-employment version of the app, treat `personal` as the relevant remote.
