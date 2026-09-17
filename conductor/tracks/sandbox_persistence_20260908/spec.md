# Sandbox Persistence/Reuse Specification

## Objective
Implement functionality in Coderagy to allow users to reuse previously utilized Linux sandbox environments instead of always creating a new one.

## Technical Requirements
- Detection of existing sandbox state files in `.sandbox/`.
- Logic to offer the user a choice: "Create new sandbox" or "Reconnect to existing sandbox".
- Integration with `AntigravityClient` to re-establish connection using previously stored `environment_id`.
- Update `main.py` CLI initialization workflow.
