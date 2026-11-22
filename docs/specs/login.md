# Login · approved

## Brief
An existing TicketForge user can sign in from the terminal and log out.

## Scope
Existing-account login, retry, and logout. Registration and ticket actions belong to later features.

## Files involved
- `cli.py` starts the CLI with `python3 cli.py` and handles prompts and the signed-in menu.
- `client.py` handles requests to TicketForge.
- `README.md` explains how to run and use login.

## Requirements
- Prompt for a username and a hidden password. A blank username exits.
- Check credentials with Basic authentication over HTTPS using `GET /api/tforge/workitems/mine`.
- On HTTP 200, show the signed-in menu. On 401, offer a retry. For other HTTP errors or connection failures, explain the failure and return to the login prompt.
- Keep credentials in memory and discard the client on logout.

## Design
Use one class, `TicketForgeClient`, to hold credentials and provide `check_login()`. Later, create, list, and update can reuse this client's authenticated connection settings. A plain `run()` function handles terminal interaction.

## Tasks
1. Implement the client and credential check.
2. Connect it to the prompts, logout action, and entry point.
3. Document the command and verify the flow.

## Validation
Drive the CLI with dummy credentials and simulated API responses. Try a wrong password (401), retry successfully (200), log out, and exit. Simulate a connection failure and a server error (500). Check the request method, path, and authentication, then report each action and observed result.
