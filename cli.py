from getpass import getpass
from http.client import HTTPException

from client import LoginRequired, TicketForgeClient


def choose_dependencies(client: TicketForgeClient):
    """Return selected references, or None to cancel creation."""
    while True:
        choice = input("Dependencies: 1 to select | Enter to skip | c to cancel: ").strip()
        if not choice:
            return []
        if choice.lower() == "c":
            return None
        if choice != "1":
            print("Choose 1, Enter, or c.")
            continue
        try:
            candidates = client.dependency_candidates()
        except (OSError, HTTPException, ValueError):
            print("Could not load tickets. Retry, skip dependencies, or cancel.")
            continue
        if not candidates:
            print("No tickets available. Skip dependencies or cancel.")
            continue
        for ref, title in candidates.items():
            print(f"{ref}  {title}")
        while True:
            selection = input("References separated by commas (Enter to skip, c to cancel): ").strip()
            if not selection:
                return []
            if selection.lower() == "c":
                return None
            refs = [part.strip() for part in selection.split(",")]
            if all(ref in candidates for ref in refs):
                return list(dict.fromkeys(refs))
            print("Choose references from the displayed tickets.")


STAGES = ("open", "in_progress", "review", "closed")


def choose_stage(current: str) -> str:
    print(f"Current stage: {current.replace('_', ' ').title()}")
    for number, stage in enumerate(STAGES, start=1):
        print(f"{number}. {stage.replace('_', ' ').title()}")
    while True:
        choice = input("Choose 1–4, or press Enter to keep the current stage: ").strip()
        if not choice:
            return current
        if choice in ("1", "2", "3", "4"):
            return STAGES[int(choice) - 1]
        print("Please enter a number from 1 to 4.")


def edit_ticket(client, ref):
    try:
        original = client.get_ticket(ref)
    except (OSError, HTTPException, ValueError):
        print("Could not load current ticket details.")
        return
    draft = original.copy()
    for key in ("title", "description", "stage", "dependsOn"):
        if key not in original:
            print("Incomplete ticket details. Edit cancelled.")
            return
        if key == "stage":
            draft[key] = choose_stage(original[key])
            continue
        hint = "Enter to keep"
        if key in ("description", "dependsOn"):
            hint += ", /clear to clear"
        if key == "dependsOn":
            hint += ", or enter comma-separated references"
        while True:
            value = input(f"{key} [{original[key]}] ({hint}): ")
            if not value:
                break
            if key == "title" and not value.strip():
                print("A title is required.")
                continue
            if key == "dependsOn":
                refs = [part.strip() for part in value.split(",")]
                if value != "/clear" and (not all(refs) or ref in refs):
                    print("Enter valid references to other tickets.")
                    continue
                draft[key] = [] if value == "/clear" else list(dict.fromkeys(refs))
            else:
                draft[key] = "" if key == "description" and value == "/clear" else value.strip()
            break
    if draft == original:
        print("No changes.")
        return
    if input("Save changes? [y/N]: ").strip().lower() != "y":
        print("Edit cancelled.")
        return
    try:
        client.update_ticket(ref, draft)
    except (OSError, HTTPException, ValueError):
        print("Could not confirm save. Reopen the ticket before retrying.")
        return
    print(f"Saved {ref}.")
    try:
        return client.get_ticket(ref)
    except (OSError, HTTPException, ValueError):
        print("Saved, but could not refresh the details.")


def browse_tickets(client: TicketForgeClient) -> None:
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
                    print("Could not load tickets. Please try again.")
                    return
                print("Could not load more tickets. Enter m to retry.")
            else:
                tickets.extend(rows)
                cursor = None
                if pagination["hasMore"]:
                    token = pagination.get("nextCursor")
                    if isinstance(token, str) and token and token not in seen_cursors:
                        cursor = token
                        seen_cursors.add(token)
                    else:
                        print("TicketForge returned an invalid cursor. Further pages are unavailable.")
                if not tickets and cursor is None:
                    print("No tickets to display.")
                    return
            load_page = False

        for number, ticket in enumerate(tickets, start=1):
            print(f"{number}. {ticket['ref']}  {ticket.get('title', '')}  [{ticket.get('stage', '—')}]")
        options = " | m: Show 5 more" if cursor else ""
        choice = input(f"Enter a ticket number to view or edit{options} | Enter to go back: ").strip()
        if not choice:
            return
        if cursor and choice.lower() == "m":
            load_page = True
            continue
        try:
            number = int(choice)
        except ValueError:
            number = 0
        if not 1 <= number <= len(tickets):
            print(f"Choose a number from 1 to {len(tickets)}.")
            continue

        ticket = tickets[number - 1]
        for field in ("ref", "title", "description", "stage", "created", "updated"):
            print(f"{field.capitalize()}: {ticket.get(field) or '—'}")
        if input("Type e to edit this ticket, or press Enter to return to the list: ").strip().lower() == "e":
            saved = edit_ticket(client, ticket["ref"])
            if saved:
                ticket.update(saved)
                for field in ("ref", "title", "description", "stage", "dependsOn", "updated"):
                    print(f"{field}: {ticket.get(field)}")
                input("Press Enter to return to the list.")


def signed_in_menu(client: TicketForgeClient) -> None:
    while True:
        choice = input("1. Create ticket | 2. List and edit tickets | Enter to log out: ").strip()
        if not choice:
            return
        if choice == "2":
            try:
                browse_tickets(client)
            except LoginRequired:
                print("Please sign in again.")
                return
            continue
        if choice != "1":
            print("Choose 1, 2, or press Enter.")
            continue

        title = input("Title: ").strip()
        if not title:
            print("A title is required.")
            continue
        description = input("Description: ")
        try:
            dependencies = choose_dependencies(client)
            if dependencies is None:
                continue
            ref = client.create_ticket(title, description, dependencies)
        except LoginRequired:
            print("Please sign in again.")
            return
        except (OSError, HTTPException, ValueError):
            print("Could not confirm creation. Check your dashboard before retrying.")
        else:
            print(f"Created {ref}.")


def run() -> None:
    while True:
        username = input("Username (Enter to exit): ").strip()
        if not username:
            return

        client = TicketForgeClient(username, getpass("Password: "))
        try:
            status = client.check_login()
        except (OSError, HTTPException):
            print("Could not connect to TicketForge. Check your connection and try again.")
        else:
            if status == 200:
                print(f"Signed in as {username}.")
                signed_in_menu(client)
                print("Logged out.")
            elif status == 401:
                print("Incorrect username or password. Try again.")
            else:
                print(f"TicketForge returned HTTP {status}. Login failed.")
        del client


if __name__ == "__main__":
    try:
        run()
    except (EOFError, KeyboardInterrupt):
        print()
