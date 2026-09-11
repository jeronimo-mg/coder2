# Implementation Plan: Sandbox Persistence/Reuse

## Phase 1: Research
- [ ] Task: Review `AntigravityClient` to identify how environment IDs are currently stored and used.
- [ ] Task: Research how to re-initiate an interaction with an existing `environment_id`.

## Phase 2: Implementation
- [ ] Task: Modify `main.py` 'init' logic to detect existing `.sandbox/<project_name>.json`.
- [ ] Task: Implement interactive prompt for user to choose reuse or new sandbox.
- [ ] Task: Update initialization flow in `main.py` to support reconnection.

## Phase 3: Verification
- [x] Task: Verify that reusing a sandbox correctly reconnects the agent and restores state.
