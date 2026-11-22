import base64
from http.client import HTTPSConnection

HOST = "integrations-assignment-ticketforge.vercel.app"


class TicketForgeClient:
    def __init__(self, username: str, password: str):
        credentials = f"{username}:{password}".encode("utf-8")
        token = base64.b64encode(credentials).decode("ascii")
        self._headers = {"Authorization": f"Basic {token}"}

    def check_login(self) -> int:
        connection = HTTPSConnection(HOST, timeout=10)
        try:
            connection.request("GET", "/api/tforge/workitems/mine", headers=self._headers)
            return connection.getresponse().status
        finally:
            connection.close()
