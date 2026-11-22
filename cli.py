from http.client import HTTPException

import tickets
import ui
from client import LoginRequired, TicketForgeClient


def signed_in_menu(client: TicketForgeClient, username) -> None:
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
            ui.message("Please sign in again.")
            return


def run() -> None:
    while True:
        ui.header("Sign in to TicketForge")
        username = ui.field("Enter your username: ", login=True).strip()
        if not username:
            continue

        ui.message(f"Username: {ui.display(username)}")
        client = TicketForgeClient(
            username, ui.field("Enter your password (hidden): ", secret=True)
        )
        try:
            status = client.check_login()
        except (OSError, HTTPException):
            ui.message(
                "Could not connect to TicketForge. Check your connection and try again."
            )
        else:
            if status == 200:
                ui.message(f"Signed in as {username}.")
                signed_in_menu(client, username)
                ui.message("Logged out.")
            elif status == 401:
                ui.message("Incorrect username or password. Try again.")
            else:
                ui.message(f"TicketForge returned HTTP {status}. Login failed.")
        del client


if __name__ == "__main__":
    try:
        with ui.workspace():
            run()
    except (EOFError, KeyboardInterrupt, ui.ExitRequested):
        print()
