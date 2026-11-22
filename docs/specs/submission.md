# Submission preparation · approved

## Brief
Make the CLI easy to run, review, test, and submit from a fresh checkout.

## Scope
Separate ticket workflows from application navigation, format the Python source, verify credential hygiene, and finish the reviewer documentation and run evidence.

## Files involved
- cli.py handles login, session lifecycle, and routing.
- tickets.py owns create, browse, edit, and their shared selectors.
- client.py owns authenticated HTTP calls; ui.py owns terminal presentation.
- tests/ contains repeatable offline tests. README.md, .gitignore, and the demo evidence support submission.

## Requirements
Keep python3 cli.py and the current keyboard flows working. Use dummy credentials and redact authorization headers from examples and evidence. Document installation, assumptions, limits, AI use, and exact verification commands.

## Design
Keep TicketForgeClient as the single HTTP client. Use functions for ticket workflows; pass the client explicitly. Use standard-library unittest and a simulated transport for repeatable coverage.

## Tasks
1. Extract ticket flows, keeping UI rendering and network access in their existing modules.
2. Add regression coverage, format code, and run checks.
3. Capture a labeled simulated CLI run, validate the README from a clean checkout, and inspect the proposed push for credentials and generated files.

## Validation
Run tests, compilation, formatting checks, and a terminal smoke test. Exercise login, create, pagination, edit, and failure recovery. Verify ignore rules and inspect Git history for credential-like material without printing values. Report simulated and live verification separately.
