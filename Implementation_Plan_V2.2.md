# Implementation Plan - V2.2 Refinements

## Goal
Improve file storage organization for user accessibility, implement development audit logging for easier debugging, and fix logging initialization issues.

## Proposed Changes

### 1. Configuration (`app/core/config.py`)
- Add `DEV_AUDIT_MODE` (bool) to settings, default to `False`.

### 2. Logging (`app/core/logging.py`)
- Ensure `logs/` directory is created before adding the file handler.
- Verify log file path.

### 3. Storage (`app/storage/local_adapter.py`)
- Refactor `save_file` to support hierarchical paths based on date (Year/Month/Day).
- [NEW] Logic to create directories: `dados/{settings.STORAGE_PATH}/{yyyy}/{mm}/{dd}/`.

### 4. Ingestion (`app/ingest/service.py`)
- Update `process_new_emails` to determine the date (from Email Date or Current Date).
- Pass this date to `storage.save_file` so it places the file in the correct subfolder.

### 5. Audit System (`app/core/audit.py`) [NEW]
- Create `AuditLogger` class.
- Methods:
    - `save_json(job_id, step, data)`: Saves JSON dump.
    - `save_text(job_id, step, text)`: Saves raw text/prompts.
- Location: `dados/audit/{job_id}/{step}_{timestamp}.json`.
- Only active if `settings.DEV_AUDIT_MODE` is True.

### 6. Integration (`app/textract`, `app/classify`, `app/extract`)
- Inject `AuditLogger` calls in key services to capture:
    - Textract raw response.
    - Classification Prompt & Response.
    - Extraction Prompt & Response.

## Verification Plan

### Automated
- No new unit tests planned for this iteration (User requested manual review/execution).

### Manual Verification
1.  **Logging**: Restart app and verify `logs/app.json` is created and populated.
2.  **Storage**: Send an email, check if attachment appears in `dados/2026/01/20/...` (assuming today's date).
3.  **Audit**: Enable `DEV_AUDIT_MODE`, process a job, and check `dados/audit/{job_id}/` for JSON files containing the prompt and OpenAI response.
