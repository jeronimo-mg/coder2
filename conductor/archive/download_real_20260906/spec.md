# Specification: Real File Download and Extraction

## Overview
Implement the robust file transfer and local extraction of sandbox archives, moving beyond the current stub implementation.

## Functional Requirements
- **HTTP/API Transfer:** Utilize efficient transfer protocols to retrieve the archive from the agent environment.
- **Zip Compression:** Use the `.zip` format for all archives created by the agent.
- **OS-native Extraction:** Leverage OS system commands (e.g., `unzip`) for efficient archive extraction.

## Acceptance Criteria
- [ ] Archive file is successfully transferred from the agent.
- [ ] Archive is correctly extracted to the user-specified destination using system commands.
- [ ] Download process includes error handling for failed transfers or corrupt archives.

## Out of Scope
- Support for multiple archive formats (starting with .tar.gz).
