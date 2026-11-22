"""Create, browse, and edit workflows built on the client and UI modules."""

import ui
from client import EDITABLE_FIELDS, PAGE_SIZE, TicketForgeClient, TicketForgeError

STAGES = ("open", "in_progress", "review", "closed")


# ----- Shared prompts ---------------------------------------------------------


def pick_dependencies(client, selected, exclude=None):
    """Show the dependency checklist. Return chosen refs, or None if nothing was chosen."""
    try:
        candidates = client.dependency_candidates()
    except TicketForgeError:
        ui.message("Could not load tickets.")
        return None
    for ref in selected:
        candidates.setdefault(ref, "")
    candidates.pop(exclude, None)
    if not candidates:
        ui.message("No tickets available.")
        return None
    return ui.checklist(candidates, selected)


def edit_text(name, current, *, required=False, clearable=False):
    """Ask for a new value; Enter keeps the current one."""
    ui.message(f"Current {name}: {ui.display(current) or '—'}")
    hint = "Enter to keep, /clear to clear" if clearable else "Enter to keep"
    while True:
        value = ui.field(f"Enter a new {name} ({hint}): ")
        if not value:
            return current
        value = "" if clearable and value == "/clear" else value.strip()
        if required and not value:
            ui.message(f"A {name} is required.")
            continue
        ui.message(f"New {name}: {ui.display(value) or '—'}")
        return value


def choose_stage(current):
    ui.message(f"Current stage: {ui.stage_label(current)}")
    stages = {str(n): stage for n, stage in enumerate(STAGES, 1)}
    options = [(key, ui.stage_label(stage)) for key, stage in stages.items()]
    default = next((key for key, stage in stages.items() if stage == current), "k")
    if default == "k":
        options.append(("k", "Keep current stage"))
    key = ui.menu(options, default=default, stages=stages)
    return stages.get(key, current)


def edit_dependencies(client, ref, current):
    existing = current or []
    ui.message(f"Dependencies: {ui.display(', '.join(existing) or 'None')}")
    if ui.menu([("k", "Keep dependencies"), ("s", "Select dependencies")]) == "s":
        selected = pick_dependencies(client, existing, exclude=ref)
        if selected is not None and set(selected) != set(existing):
            return selected
    return current


# ----- Create -----------------------------------------------------------------


def create_ticket(client: TicketForgeClient, username: str) -> None:
    ui.header("Create ticket", username)
    title = ui.field("Enter a ticket title: ").strip()
    if not title:
        ui.message("A title is required.")
        return
    ui.message(f"Title: {ui.display(title)}")
    description = ui.field("Enter a description: ")
    ui.message(f"Description: {ui.display(description) or '—'}")

    while True:
        choice = ui.menu(
            [
                ("1", "Choose dependencies"),
                ("s", "Skip dependencies"),
                ("c", "Cancel ticket"),
            ],
            default="s",
        )
        if choice == "c":
            return
        dependencies = [] if choice == "s" else pick_dependencies(client, [])
        if dependencies is not None:
            break
        ui.message("Choose again, skip dependencies, or cancel.")

    try:
        ref = client.create_ticket(title, description, dependencies)
    except TicketForgeError:
        ui.message("Could not confirm creation. Check your dashboard before retrying.")
    else:
        ui.message(f"Created {ref}.")


# ----- Browse -----------------------------------------------------------------


def browse_tickets(client: TicketForgeClient, username: str) -> None:
    """List tickets a page at a time; open any row to view or edit it."""
    try:
        tickets, cursor = client.list_tickets()
    except TicketForgeError:
        ui.message("Could not load tickets. Please try again.")
        return
    if not tickets and not cursor:
        ui.message("No tickets to display.")
        return

    while True:
        ui.header("My tickets", username)
        rows = dict(enumerate(tickets, 1))
        options = [
            (
                str(n),
                f"{t['ref']}  {t.get('title', '')}  ·  {ui.stage_label(t.get('stage'))}",
            )
            for n, t in rows.items()
        ]
        if cursor:
            options.append(("m", f"Show {PAGE_SIZE} more"))
        options.append(("b", "Back to home"))
        choice = ui.menu(
            options, stages={str(n): t.get("stage") for n, t in rows.items()}
        )
        if choice == "b":
            return
        if choice == "m":
            try:
                page, cursor = client.list_tickets(cursor)
            except TicketForgeError:
                ui.message("Could not load more tickets. Enter m to retry.")
            else:
                tickets.extend(page)
        else:
            show_ticket(client, rows[int(choice)], username)


def show_ticket(client, ticket, username):
    """Show one ticket's full details and offer to edit it."""
    ui.header(f"Ticket {ticket['ref']}", username)
    try:
        ticket.update(client.get_ticket(ticket["ref"]))
    except TicketForgeError:
        ui.message("Could not load ticket details.")
        return
    ui.message(lambda: ui.ticket_box(ticket))  # re-rendered on resize
    if ui.menu([("e", "Edit ticket"), ("b", "Back to tickets")], default="b") != "e":
        return
    ui.header(f"Edit {ticket['ref']}", username)
    saved = edit_ticket(client, ticket["ref"])
    if saved:
        ticket.update(saved)
        ui.message(lambda: ui.ticket_box(ticket))
        ui.menu([("b", "Back to tickets")])


# ----- Edit -------------------------------------------------------------------


def edit_ticket(client, ref):
    """Walk through each editable field. Return the refreshed ticket after a save."""
    try:
        original = client.get_ticket(ref)
    except TicketForgeError:
        ui.message("Could not load current ticket details.")
        return None
    missing = [field for field in EDITABLE_FIELDS if field not in original]
    if missing:
        ui.message(f"Ticket is missing {', '.join(missing)}. Edit cancelled.")
        return None

    draft = dict(original)
    draft["title"] = edit_text("title", original["title"], required=True)
    draft["description"] = edit_text(
        "description", original["description"], clearable=True
    )
    draft["stage"] = choose_stage(original["stage"])
    draft["dependsOn"] = edit_dependencies(client, ref, original["dependsOn"])

    changes = {key: value for key, value in draft.items() if original[key] != value}
    if not changes:
        ui.message("No changes.")
        return None
    ui.message("\n" + ui.tint("Changes to save", ui.ACCENT))
    for key, value in changes.items():
        old, new = ui.display(original[key]), ui.display(value)
        ui.message(f"  {key}: {old} → {ui.tint(new, ui.CHANGED)}")
    if ui.menu([("y", "Save changes"), ("n", "Discard changes")], default="n") != "y":
        ui.message("Edit cancelled.")
        return None

    try:
        client.update_ticket(ref, draft)
    except TicketForgeError:
        ui.message("Could not confirm save. Reopen the ticket before retrying.")
        return None
    ui.message(f"Saved {ref}.")
    try:
        return client.get_ticket(ref)
    except TicketForgeError:
        ui.message("Saved, but could not refresh the details.")
        return None
