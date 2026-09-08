# Specification: File Download Functionality

## Overview
Implement functionality to download files generated in the sandbox environment to the user's local machine, fulfilling the project goal of extracting agent-generated code.

## Functional Requirements
- **Whole Sandbox Download:** Support downloading the entire content of the sandbox environment.
- **User Prompt for Destination:** The CLI will prompt the user for the local destination path for each download operation.
- **Conflict Handling:** The CLI will ask the user for confirmation before overwriting any existing local files.

## Acceptance Criteria
- [ ] A new `download` command is available in the CLI.
- [ ] Entire sandbox content is compressed (e.g., tar/zip) before download.
- [ ] User is prompted for destination path.
- [ ] User is warned/prompted in case of file conflicts.

## Out of Scope
- Partial file downloads.
- Automatic sync/merge of remote and local files.
