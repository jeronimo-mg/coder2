# Specification: Official File Download (Files API)

## Overview
Implement the official file download mechanism for sandbox snapshots as documented in the Gemini API.

## Functional Requirements
- **Files API Integration:** Utilize `https://generativelanguage.googleapis.com/v1beta/files/environment-{env_id}:download` to retrieve the snapshot.
- **Snapshot Extraction:** Use Python's `tarfile` library to extract the downloaded `.tar` snapshot.
- **Authentication:** Use `x-goog-api-key` header with the configured API Key.

## Acceptance Criteria
- [ ] Successfully retrieve environment snapshot using `environment_id`.
- [ ] Snapshot is saved and extracted to the correct local directory.
- [ ] Proper error handling for failed API requests or invalid snapshots.
---
