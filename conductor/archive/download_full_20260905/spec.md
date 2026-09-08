# Specification: File Download Functionality (Full)

## Overview
Implement the full file download functionality by polling for archive creation completion and performing the actual file transfer and extraction to the local machine.

## Functional Requirements
- **Polling Mechanism:** The CLI will poll the agent for archive completion every 5 seconds.
- **Timeout Policy:** If the archive is not ready within 5 minutes, the operation will fail.
- **Direct Extraction:** Downloaded archives will be extracted directly into the user-specified destination folder.

## Acceptance Criteria
- [ ] CLI correctly polls interaction status until completion.
- [ ] Archive is successfully transferred and extracted locally.
- [ ] Timeout functionality works as expected.
- [ ] Extracted files do not violate existing local files without confirmation.

## Out of Scope
- Support for multiple archive formats (starting with .tar.gz).
