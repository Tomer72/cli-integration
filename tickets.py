from http.client import HTTPException

import ui
from client import TicketForgeClient


def choose_dependencies(client: TicketForgeClient):
    """Return selected references, or None to cancel creation."""
    while True:
        choice = ui.menu(
            [
                ("1", "Choose dependencies"),
                ("s", "Skip dependencies"),
                ("c", "Cancel ticket"),
            ],
            default="s",
        )
        if choice == "s":
            return []
        if choice.lower() == "c":
            return None
        if choice != "1":
            ui.message("Choose 1, Enter, or c.")
            continue
        try:
            candidates = client.dependency_candidates()
        except (OSError, HTTPException, ValueError):
            ui.message("Could not load tickets. Retry, skip dependencies, or cancel.")
            continue
        if not candidates:
            ui.message("No tickets available. Skip dependencies or cancel.")
            continue
        selected = ui.checklist(candidates, [])
        if selected is not None:
            return selected


STAGES = ("open", "in_progress", "review", "closed")


def choose_stage(current: str) -> str:
    ui.message(f"Current stage: {ui.display(current).replace('_', ' ').title()}")
    options = [
        (str(n), stage.replace("_", " ").title()) for n, stage in enumerate(STAGES, 1)
    ]
    if current in STAGES:
        selected = str(STAGES.index(current) + 1)
    else:
        options.append(("k", "Keep current stage"))
        selected = "k"
    key = ui.menu(
        options, default=selected, stages=dict(zip(("1", "2", "3", "4"), STAGES))
    )
    return current if key == "k" else STAGES[int(key) - 1]


def edit_ticket(client, ref):
    try:
        original = client.get_ticket(ref)
    except (OSError, HTTPException, ValueError):
        ui.message("Could not load current ticket details.")
        return
    draft = original.copy()
    for key in ("title", "description", "stage", "dependsOn"):
        if key not in original:
            ui.message("Incomplete ticket details. Edit cancelled.")
            return
        if key == "stage":
            draft[key] = choose_stage(original[key])
            continue
        if key == "dependsOn":
            existing = original[key] or []
            ui.message(f"Dependencies: {ui.display(', '.join(existing) or 'None')}")
            if (
                ui.menu([("k", "Keep dependencies"), ("s", "Select dependencies")])
                == "s"
            ):
                try:
                    candidates = client.dependency_candidates()
                except (OSError, HTTPException, ValueError):
                    ui.message("Could not load dependencies. Existing selection kept.")
                    continue
                for dependency in existing:
                    candidates.setdefault(dependency, "")
                candidates.pop(ref, None)
                if candidates:
                    selection = ui.checklist(candidates, existing)
                    if selection is not None and set(selection) != set(existing):
                        draft[key] = selection
                else:
                    ui.message("No available dependencies.")
            continue
        ui.message(f"Current {key}: {ui.display(original[key]) or '—'}")
        hint = (
            "Enter to keep, /clear to clear"
            if key == "description"
            else "Enter to keep"
        )
        while True:
            value = ui.field(f"Enter a new {key} ({hint}): ")
            if not value:
                break
            if key == "title" and not value.strip():
                ui.message("A title is required.")
                continue
            draft[key] = (
                "" if key == "description" and value == "/clear" else value.strip()
            )
            ui.message(f"New {key}: {ui.display(draft[key]) or '—'}")
            break
    if draft == original:
        ui.message("No changes.")
        return
    ui.message("\n" + ui.tint("Changes to save", 45))
    for key, value in draft.items():
        if original.get(key) != value:
            ui.message(
                f"  {key}: {ui.display(original[key])} → {ui.tint(ui.display(value), 35)}"
            )
    if ui.menu([("y", "Save changes"), ("n", "Discard changes")], default="n") != "y":
        ui.message("Edit cancelled.")
        return
    try:
        client.update_ticket(ref, draft)
    except (OSError, HTTPException, ValueError):
        ui.message("Could not confirm save. Reopen the ticket before retrying.")
        return
    ui.message(f"Saved {ref}.")
    try:
        return client.get_ticket(ref)
    except (OSError, HTTPException, ValueError):
        ui.message("Saved, but could not refresh the details.")


def show_details(ticket):
    ui.message(lambda: ui.ticket_box(ticket))


def browse_tickets(client: TicketForgeClient, username) -> None:
    tickets = []
    seen_cursors = set()
    cursor = None
    load_page = True
    while True:
        if load_page:
            try:
                rows, pagination = client.list_tickets(cursor)
            except (OSError, HTTPException, ValueError):
                if cursor is None:
                    ui.message("Could not load tickets. Please try again.")
                    return
                ui.message("Could not load more tickets. Enter m to retry.")
            else:
                tickets.extend(rows)
                cursor = None
                if pagination["hasMore"]:
                    token = pagination.get("nextCursor")
                    if isinstance(token, str) and token and token not in seen_cursors:
                        cursor = token
                        seen_cursors.add(token)
                    else:
                        ui.message(
                            "TicketForge returned an invalid cursor. Further pages are unavailable."
                        )
                if not tickets and cursor is None:
                    ui.message("No tickets to display.")
                    return
            load_page = False

        ui.header("My tickets", username)
        options = [
            (
                str(n),
                f"{ticket['ref']}  {ticket.get('title', '')}  ·  "
                f"{ticket.get('stage', '—').replace('_', ' ').title()}",
            )
            for n, ticket in enumerate(tickets, 1)
        ]
        if cursor:
            options.append(("m", "Show 5 more"))
        options.append(("b", "Back to home"))
        choice = ui.menu(
            options, stages={str(n): t.get("stage") for n, t in enumerate(tickets, 1)}
        )
        if choice == "b":
            return
        if cursor and choice.lower() == "m":
            load_page = True
            continue
        ticket = tickets[int(choice) - 1]
        ui.header(f"Ticket {ticket['ref']}", username)
        try:
            ticket.update(client.get_ticket(ticket["ref"]))
        except (OSError, HTTPException, ValueError):
            ui.message("Could not load ticket details.")
            continue
        show_details(ticket)
        if (
            ui.menu([("e", "Edit ticket"), ("b", "Back to tickets")], default="b")
            == "e"
        ):
            ui.header(f"Edit {ticket['ref']}", username)
            saved = edit_ticket(client, ticket["ref"])
            if saved:
                ticket.update(saved)
                show_details(ticket)
                ui.menu([("b", "Back to tickets")])


def create_ticket(client: TicketForgeClient, username: str) -> None:
    ui.header("Create ticket", username)
    title = ui.field("Enter a ticket title: ").strip()
    if not title:
        ui.message("A title is required.")
        return
    ui.message(f"Title: {ui.display(title)}")
    description = ui.field("Enter a description: ")
    ui.message(f"Description: {ui.display(description) or '—'}")
    try:
        dependencies = choose_dependencies(client)
        if dependencies is None:
            return
        ref = client.create_ticket(title, description, dependencies)
    except (OSError, HTTPException, ValueError):
        ui.message("Could not confirm creation. Check your dashboard before retrying.")
    else:
        ui.message(f"Created {ref}.")
