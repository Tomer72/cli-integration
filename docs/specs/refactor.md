# Code review refactor · approved

## Brief
Make the code easier for reviewers to read and the app easier to set up, without changing what users can do.

## Scope
Error handling, client helpers, the create/browse/edit flows, small UI cleanups, focused tests, a host setting, and the README. No new ticket features and no rewrite of the full-screen UI.

## Files involved
- `client.py` gets one `TicketForgeError`, a shared `_request()`, a `_workitems()` helper, and a `TICKETFORGE_HOST` override.
- `cli.py` handles login through exceptions instead of status codes.
- `tickets.py` gets straight-line edit steps, one shared dependency picker, and a shorter browse loop.
- `ui.py` gets one stage color map, a branding constant, bindings created once, and no duplicate "/ Commands" line.
- `tests/test_client.py` (new) adds focused client tests. `tests/test_cli.py` becomes one short smoke test.
- `README.md` puts Setup first. `docs/demo.txt` is re-recorded.

## Requirements
- Menus, prompts, and messages behave as before, except that plain mode prints "/ Commands" once per screen.
- Network, HTTP, and malformed-response failures show the same friendly messages. HTTP 401 still returns the user to sign in.
- `TICKETFORGE_HOST` points the CLI at another host. The default stays the assignment service.
- Editing still refuses to save tickets with missing fields, and sends the full PUT payload (title, description, stage, dependsOn, customFields).
- A create request is never retried after a lost response.

## Design
- `TicketForgeError` covers network, HTTP, and malformed-response failures with a readable message. `LoginRequired` stays separate so a 401 always reaches the sign-in screen.
- `TicketForgeClient._request(method, path, payload)` is the only place that opens connections; `check_login` and every API call use it.
- `pick_dependencies(client, selected, exclude)` serves create and edit. `edit_text(name, current, required, clearable)` handles title and description.
- `browse_tickets` delegates to `show_ticket()`; the page cursor is tracked in a small loop without a seen-set.

## Tasks
1. Client: exceptions, `_request`, `_workitems`, host override.
2. Flows: cli login, edit steps, shared picker, browse split, dead code removal.
3. UI cleanups.
4. Tests, README, demo.

## Validation
Run the unit tests and compileall. Drive `python cli.py` in plain mode with simulated responses: failed login, login, create with skipped dependencies, list with "m", open, edit stage, save, back, logout, `/exit`. Expect the same messages and request payloads as before. Simulate a 500 on list and a 401 mid-session. Report that verification used simulated responses.
