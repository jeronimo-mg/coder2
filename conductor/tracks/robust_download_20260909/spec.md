# Robust Code Download Specification

## Objective
Implement reliable download and extraction of environment snapshots from the Antigravity agent sandbox.

## Technical Requirements
- Use `AntigravityClient.download_snapshot` to fetch the `.tar` snapshot.
- Implement proper extraction logic for the snapshot archive.
- Ensure the user can specify the destination directory.
- Verify download success and file integrity.
- Update the `main.py` CLI workflow for the `download` command.
