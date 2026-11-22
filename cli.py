"""Entry point: sign in to TicketForge, then route the home menu."""

import tickets
import ui
from client import LoginRequired, TicketForgeClient, TicketForgeError


def sign_in():
    """Prompt until TicketForge accepts the credentials; return (client, username)."""
    while True:
        ui.header("Sign in to TicketForge")
        username = ui.field("Enter your username: ", login=True).strip()
        if not username:
            continue
        ui.message(f"Username: {ui.display(username)}")
        password = ui.field("Enter your password (hidden): ", secret=True)
        client = TicketForgeClient(username, password)
        try:
            client.check_login()
        except LoginRequired:
            ui.message("Incorrect username or password. Try again.")
        except TicketForgeError as error:
            ui.message(f"{error}. Check your connection and try again.")
        else:
            ui.message(f"Signed in as {ui.display(username)}.")
            return client, username


def home(client: TicketForgeClient, username: str) -> None:
    """Show the home menu until the user logs out or the session expires."""
    while True:
        ui.header("Home", username)
        choice = ui.menu(
            [("1", "Create ticket"), ("2", "List and edit tickets"), ("3", "Log out")]
        )
        if choice == "3":
            return
        try:
            if choice == "1":
                tickets.create_ticket(client, username)
            else:
                tickets.browse_tickets(client, username)
        except LoginRequired:
            ui.message("Your session expired. Please sign in again.")
            return


def run() -> None:
    while True:
        client, username = sign_in()
        home(client, username)
        ui.message("Logged out.")


if __name__ == "__main__":
    try:
        with ui.workspace():
            run()
    except (EOFError, KeyboardInterrupt, ui.ExitRequested):
        print()
