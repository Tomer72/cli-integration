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
        choice = input(f"Ticket number{options} | Enter to go back: ").strip()
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
        input("Press Enter to return to the list.")


def signed_in_menu(client: TicketForgeClient) -> None:
    while True:
        choice = input("1. Create ticket | 2. List tickets | Enter to log out: ").strip()
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
