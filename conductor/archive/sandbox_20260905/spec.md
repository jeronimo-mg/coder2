# Specification: Sandbox Persistence

## Overview
Implement functionality to persist and reuse sandbox environments for Coderagy projects, enabling continuation of agent tasks.

## Functional Requirements
- **Local Storage:** Sandbox state will be stored locally within the project directory.
- **Project-scoped:** Each project will maintain its own isolated sandbox environment state.
- **Manual Cleanup:** Users will explicitly trigger the cleanup/removal of sandbox environments when they are no longer needed.

## Acceptance Criteria
- [ ] Sandbox state is saved upon agent task completion or interruption.
- [ ] Sandbox state is correctly reloaded when resuming a project task.
- [ ] A CLI command is available to trigger manual sandbox cleanup.

## Out of Scope
- Remote/Cloud synchronization of sandbox states.
- Automated garbage collection of sandbox environments.
