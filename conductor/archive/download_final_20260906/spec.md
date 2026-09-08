# Specification: File Download (Polling & Transfer)

## Overview
Implement the full polling mechanism for archive completion and the subsequent local transfer/extraction of files.

## Functional Requirements
- **Polling:** CLI will poll the agent for archive completion every 5 seconds.
- **Timeout:** 5-minute timeout.
- **Transfer:** Retrieve the file content/archive from the agent.
- **Extraction:** Extract the archive directly into the user-specified destination.

## Acceptance Criteria
- [ ] Polling logic works reliably.
- [ ] Timeout handles hanging tasks correctly.
- [ ] Files are transferred and extracted successfully.
- [ ] User is prompted/warned for conflicts.
