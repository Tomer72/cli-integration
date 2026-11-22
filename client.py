"""Authenticated HTTPS access to the TicketForge API."""

import base64
import json
import os
from http.client import HTTPException, HTTPSConnection
from urllib.parse import quote, urlencode

HOST = os.environ.get(
    "TICKETFORGE_HOST", "integrations-assignment-ticketforge.vercel.app"
)
PAGE_SIZE = 5
EDITABLE_FIELDS = ("title", "description", "stage", "dependsOn", "customFields")


class TicketForgeError(Exception):
    """A request failed or TicketForge returned an unexpected response."""


class LoginRequired(Exception):
    """TicketForge rejected the current credentials (HTTP 401)."""


def _field(data, key, kind):
    """Return data[key] if it has the expected type, else raise TicketForgeError."""
    value = data.get(key) if isinstance(data, dict) else None
    if not isinstance(value, kind):
        raise TicketForgeError(f"TicketForge response is missing '{key}'")
    return value


def _workitems(data):
    """Return the ticket list from a response, checking every row has a ref."""
    items = _field(data, "workitems", list)
    for item in items:
        _field(item, "ref", str)
    return items


def _workitem_path(ref):
    return "/api/tforge/workitem/" + quote(ref, safe="")


class TicketForgeClient:
    def __init__(self, username: str, password: str):
        token = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
        self._headers = {"Authorization": f"Basic {token}"}

    def _request(self, method, path, payload=None):
        """Send one request and return the decoded JSON body. Never retries."""
        headers = dict(self._headers)
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(payload).encode()
        connection = HTTPSConnection(HOST, timeout=10)
        try:
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            if response.status == 401:
                raise LoginRequired()
            if not 200 <= response.status < 300:
                raise TicketForgeError(f"TicketForge returned HTTP {response.status}")
            return json.load(response)
        except (OSError, HTTPException) as error:
            raise TicketForgeError("Could not reach TicketForge") from error
        except ValueError as error:
            raise TicketForgeError("TicketForge sent an unreadable response") from error
        finally:
            connection.close()

    def check_login(self) -> None:
        """Raise LoginRequired or TicketForgeError unless the credentials work."""
        self._request("GET", "/api/tforge/workitems/mine")

    def list_tickets(self, cursor=None):
        """Return (tickets, next_cursor); next_cursor is None on the last page."""
        query = {"limit": PAGE_SIZE}
        if cursor:
            query["cursor"] = cursor
        data = self._request("GET", "/api/tforge/workitems/mine?" + urlencode(query))
        items = _workitems(data)
        pagination = _field(data, "pagination", dict)
        next_cursor = (
            pagination.get("nextCursor") if pagination.get("hasMore") else None
        )
        return items, (
            next_cursor if isinstance(next_cursor, str) and next_cursor else None
        )

    def dependency_candidates(self):
        """Return {ref: title} for the tickets that can be chosen as dependencies."""
        data = self._request("GET", "/api/tforge/workitems/mine")
        return {item["ref"]: item.get("title", "") for item in _workitems(data)}

    def get_ticket(self, ref: str):
        data = self._request("GET", _workitem_path(ref) + "?view=deep")
        item = _field(data, "workitem", dict)
        if item.get("ref") != ref:
            raise TicketForgeError("TicketForge returned a different ticket")
        # New tickets come back without optional fields that were empty at
        # creation (e.g. dependsOn). Fill them so every ticket can be edited.
        item.setdefault("description", "")
        item.setdefault("dependsOn", None)
        item.setdefault("customFields", {})
        return item

    def update_ticket(self, ref: str, ticket: dict):
        """Replace the editable fields. The API expects all of them on every PUT."""
        payload = {field: ticket[field] for field in EDITABLE_FIELDS}
        return self._request("PUT", _workitem_path(ref), payload)

    def create_ticket(self, title: str, description: str, dependencies=None) -> str:
        """Create a ticket and return its reference, such as TF-101."""
        payload = {
            "title": title,
            "description": description,
            "dependsOn": dependencies or None,
        }
        data = self._request("POST", "/api/tforge/workitem/publish", payload)
        return _field(_field(data, "workitem", dict), "ref", str)
