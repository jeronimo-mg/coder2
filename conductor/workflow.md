# Conductor Workflow

## Overview
This workflow defines the development process for Coderagy, focusing on Test-Driven Development (TDD) and iterative task implementation.

## Task Workflow
1. **Plan Phase**:
    - Analyze the task requirements and generate a test plan.
    - Confirm the plan with the user (`ask_user`).
2. **Implementation Phase**:
    - Write tests for the task.
    - Implement the feature/fix.
    - Run tests to verify >80% coverage.
    - If tests fail, iterate on implementation until passing.
3. **Verification Phase**:
    - Perform manual verification if required by the plan.
    - Commit changes.

## Quality Standards
- **Test Coverage**: >80%
- **Commit Frequency**: Per Task
