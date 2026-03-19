# Session 05: Cloudbuild Structure

## Source
Primary commits: `f0a39b0`, `8075339`, `4fb8ff4`

## Summary
This session focused on deployment configuration. Cloud Build YAML files were introduced and then reorganised into a more appropriate directory structure.

## What changed
- Added Cloud Build YAML files for multiple environments
- Removed the previous CodeQL workflow file
- Moved Cloud Build files out of `.github/workflows`
- Reorganised them into the `cloudbuild/` directory

## Why it matters
This work prepares the application for hosted deployment, which is important because the tool is intended to run on a cloud platform once the environment is available.

## Evidence of progress
- Environment-specific build configurations now exist
- Repository structure is cleaner and less likely to confuse tooling
- Deployment planning is now visible in the repo

## Limitations at this stage
- Hosting is still blocked on platform setup
- These files support deployment readiness but do not complete the business logic

## Key files
- [Cloudbuild.yml](C:/Users/aaron/PycharmProjects/RangeControlPlatform/cloudbuild/Cloudbuild.yml)
- [Cloudbuild-uat.yaml](C:/Users/aaron/PycharmProjects/RangeControlPlatform/cloudbuild/Cloudbuild-uat.yaml)
- [Cloudbuild-ppd.yaml](C:/Users/aaron/PycharmProjects/RangeControlPlatform/cloudbuild/Cloudbuild-ppd.yaml)
- [Cloudbuild-prd.yaml](C:/Users/aaron/PycharmProjects/RangeControlPlatform/cloudbuild/Cloudbuild-prd.yaml)

## Next step after this session
Translate the synoptic requirements into a more structured delivery plan and align the app with real data sources.
