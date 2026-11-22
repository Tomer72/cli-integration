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


def signed_in_menu(client: TicketForgeClient) -> None:
    while True:
        choice = input("1. Create ticket | Enter to log out: ").strip()
        if not choice:
            return
        if choice != "1":
            print("Choose 1 or press Enter.")
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
