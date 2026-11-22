from getpass import getpass
from http.client import HTTPException

from client import TicketForgeClient


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
                input("Press Enter to log out.")
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
