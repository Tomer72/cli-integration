"""Focused checks of the requests TicketForgeClient sends and how it reads replies."""

import base64
import json
import unittest
from unittest.mock import Mock, patch

from client import LoginRequired, TicketForgeClient, TicketForgeError


def reply(data, status=200):
    return Mock(status=status, read=lambda: json.dumps(data).encode())


class ClientTests(unittest.TestCase):
    def setUp(self):
        patcher = patch("client.HTTPSConnection")
        self.connection = patcher.start().return_value
        self.addCleanup(patcher.stop)
        self.client = TicketForgeClient("demo", "dummy")

    def respond(self, data, status=200):
        self.connection.getresponse.return_value = reply(data, status)

    def sent(self):
        """Return (method, path, json_body) of the last request."""
        call = self.connection.request.call_args
        body = call.kwargs["body"]
        return (*call.args, json.loads(body) if body else None)

    def test_requests_use_basic_auth(self):
        self.respond({})
        self.client.check_login()
        headers = self.connection.request.call_args.kwargs["headers"]
        token = base64.b64encode(b"demo:dummy").decode()
        self.assertEqual(headers["Authorization"], f"Basic {token}")

    def test_create_posts_ticket_and_returns_ref(self):
        self.respond({"workitem": {"ref": "TF-7"}})
        ref = self.client.create_ticket("Fix filter", "Hide closed", ["TF-1"])
        self.assertEqual(ref, "TF-7")
        self.assertEqual(
            self.sent(),
            (
                "POST",
                "/api/tforge/workitem/publish",
                {
                    "title": "Fix filter",
                    "description": "Hide closed",
                    "dependsOn": ["TF-1"],
                },
            ),
        )

    def test_create_without_dependencies_sends_null(self):
        self.respond({"workitem": {"ref": "TF-8"}})
        self.client.create_ticket("Title", "", [])
        self.assertIsNone(self.sent()[2]["dependsOn"])

    def test_list_passes_cursor_and_returns_next_one(self):
        self.respond(
            {
                "workitems": [{"ref": "TF-1"}],
                "pagination": {"hasMore": True, "nextCursor": "c2"},
            }
        )
        items, cursor = self.client.list_tickets("a:b")
        self.assertEqual(
            self.sent()[1], "/api/tforge/workitems/mine?limit=5&cursor=a%3Ab"
        )
        self.assertEqual((items, cursor), ([{"ref": "TF-1"}], "c2"))

    def test_last_page_has_no_cursor(self):
        self.respond({"workitems": [], "pagination": {"hasMore": False}})
        self.assertEqual(self.client.list_tickets(), ([], None))

    def test_update_sends_only_editable_fields(self):
        self.respond({})
        ticket = {
            "ref": "TF-1",
            "title": "T",
            "description": "",
            "stage": "review",
            "dependsOn": None,
            "customFields": {},
            "owner": {"username": "demo"},
        }
        self.client.update_ticket("TF-1", ticket)
        method, path, body = self.sent()
        self.assertEqual((method, path), ("PUT", "/api/tforge/workitem/TF-1"))
        self.assertNotIn("owner", body)
        self.assertNotIn("ref", body)
        self.assertEqual(body["stage"], "review")

    def test_new_ticket_without_optional_fields_can_be_saved(self):
        # A freshly created ticket omits dependsOn/description/customFields.
        self.respond({"workitem": {"ref": "TF-9", "title": "New", "stage": "open"}})
        ticket = self.client.get_ticket("TF-9")
        self.respond({})
        self.client.update_ticket("TF-9", dict(ticket, stage="review"))
        self.assertEqual(
            self.sent()[2],
            {
                "title": "New",
                "description": "",
                "stage": "review",
                "dependsOn": None,
                "customFields": {},
            },
        )

    def test_401_raises_login_required_and_closes_connection(self):
        self.respond({}, status=401)
        with self.assertRaises(LoginRequired):
            self.client.list_tickets()
        self.connection.close.assert_called_once()

    def test_server_error_raises_ticketforge_error(self):
        self.respond({}, status=500)
        with self.assertRaisesRegex(TicketForgeError, "HTTP 500"):
            self.client.get_ticket("TF-1")

    def test_malformed_response_raises_ticketforge_error(self):
        self.respond({"workitems": "oops"})
        with self.assertRaisesRegex(TicketForgeError, "workitems"):
            self.client.list_tickets()

    def test_lost_create_response_is_not_retried(self):
        self.connection.getresponse.side_effect = OSError("connection lost")
        with self.assertRaises(TicketForgeError):
            self.client.create_ticket("Example", "", ["TF-100"])
        self.connection.request.assert_called_once()
        self.connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
