# TicketForge CLI

A terminal app for creating, listing, and updating your TicketForge tickets.
It talks to the TicketForge API, reverse engineered from the web app's network
requests.

## Requirements

- Python 3.9 or newer (developed on 3.12)
- An existing TicketForge account

## Setup

From the repository root:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt

The setup step happens when you sign in: enter your TicketForge username and
password when prompted. They are used for HTTP Basic authentication over HTTPS,
are held in memory only, and are discarded when you log out or quit. No config
file or API key is needed.

Optional settings:

| Variable | Default | Purpose |
| --- | --- | --- |
| `TICKETFORGE_HOST` | `integrations-assignment-ticketforge.vercel.app` | Point the CLI at another TicketForge deployment. |
| `NO_COLOR` | unset | Set to any value to disable colors. |

## Run

    python cli.py

## Example session

    Sign in to TicketForge
    Enter your username: demo
    Enter your password (hidden):
    Signed in as demo.

    Home   ·   demo
       1  Create ticket
       2  List and edit tickets
       3  Log out
    Choose an option [Enter: 1]: 1

    Enter a ticket title: Fix dashboard filter
    Enter a description: Closed tickets appear in the open view.
       1  Choose dependencies
       s  Skip dependencies
       c  Cancel ticket
    Choose an option [Enter: s]:
    Created TF-784.

The full recorded run is in [docs/demo.txt](docs/demo.txt).

## Commands

All commands live in menus. Move with ↑/↓ and press Enter, or type the
shortcut shown next to an option and press Enter.

| Task | How |
| --- | --- |
| **Create** a ticket | Home → `1`. Enter a title and description, then skip (`Enter`) or choose (`1`) dependencies. |
| **List** tickets | Home → `2`. Shows five tickets; `m` loads five more. Type a row number to open a ticket. |
| **Update** a ticket | Open a ticket → `e`. Press Enter to keep a value, type `/clear` to empty the description, pick a stage `1`–`4`, then `y` to save. |
| Log out | Home → `3`. |
| Quit | Type `/exit`, or press Ctrl-C. In menus `/` opens the command palette; while typing text, use Ctrl-P. |

In the dependency checklist, Space toggles a ticket, Enter applies, and Esc
cancels. In a plain (non-interactive) terminal, toggle by number instead.

## Tests

The tests use simulated HTTPS responses, so they need no account or network:

    python -m unittest discover -s tests -v

- `tests/test_client.py` checks request paths, payloads, auth, pagination, and error handling.
- `tests/test_cli.py` drives the real CLI entry point through login, create, list, edit, and failure cases.
- `tests/test_ui.py` checks the ticket details layout.

## Project layout

| File | Responsibility |
| --- | --- |
| `cli.py` | Entry point: sign in, home menu, log out. |
| `tickets.py` | Create, browse, and edit workflows. |
| `client.py` | TicketForge API requests, response checks, and errors. |
| `ui.py` | Terminal rendering and keyboard input. |
| `docs/specs/` | Short spec written before each feature. |

## API endpoints used

| Action | Request |
| --- | --- |
| Check login, list tickets | `GET /api/tforge/workitems/mine?limit=5&cursor=…` |
| Ticket details | `GET /api/tforge/workitem/{ref}?view=deep` |
| Create | `POST /api/tforge/workitem/publish` |
| Update | `PUT /api/tforge/workitem/{ref}` (title, description, stage, dependsOn, customFields) |

## Assumptions and limitations

- The listing follows the service's cursor and loads five rows at a time.
- Dependency selection offers the tickets returned by one lookup.
- Edits keep custom field values unchanged. Custom field administration and
  account registration are out of scope.
- Create and update requests are never retried automatically. If a write
  cannot be confirmed, check the ticket before trying again.

## AI disclosure

OpenAI Codex and Claude Code assisted with interpreting the assignment,
planning features, implementing and refactoring the Python CLI, writing tests,
and simulating user flows. The request and response formats came from browser
network captures of the TicketForge web app.
