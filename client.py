import base64
import json
from http.client import HTTPSConnection
from urllib.parse import urlencode

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

    def _request_json(self, method, path, payload=None):
        headers = self._headers.copy()
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(payload).encode("utf-8")
        connection = HTTPSConnection(HOST, timeout=10)
        try:
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            if response.status == 401:
                raise LoginRequired()
            if not 200 <= response.status < 300:
                raise ValueError(f"TicketForge returned HTTP {response.status}")
            return json.load(response)
        finally:
            connection.close()

    def list_tickets(self, cursor=None):
        query = {"limit": 5}
        if cursor is not None:
            query["cursor"] = cursor
        page = self._request_json("GET", "/api/tforge/workitems/mine?" + urlencode(query))
        if not isinstance(page, dict) or not isinstance(page.get("workitems"), list):
            raise ValueError("Missing ticket list")
        for item in page["workitems"]:
            if not isinstance(item, dict) or not isinstance(item.get("ref"), str):
                raise ValueError("Missing ticket reference")
        pagination = page.get("pagination")
        if not isinstance(pagination, dict) or not isinstance(pagination.get("hasMore"), bool):
            raise ValueError("Missing pagination information")
        return page["workitems"], pagination

    def dependency_candidates(self):
        data = self._request_json("GET", "/api/tforge/workitems/mine")
        items = data.get("workitems") if isinstance(data, dict) else None
        if not isinstance(items, list):
            raise ValueError("Missing ticket list")
        candidates = {}
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("ref"), str):
                raise ValueError("Missing ticket reference")
            candidates[item["ref"]] = item.get("title", "")
        return candidates

    def create_ticket(self, title: str, description: str, dependencies=None) -> str:
        payload = {"title": title, "description": description, "dependsOn": dependencies or None}
        data = self._request_json("POST", "/api/tforge/workitem/publish", payload)
        item = data.get("workitem") if isinstance(data, dict) else None
        ref = item.get("ref") if isinstance(item, dict) else None
        if not isinstance(ref, str) or not ref.strip():
            raise ValueError("Missing ticket reference")
        return ref


class LoginRequired(Exception):
    """TicketForge rejected the current credentials."""
