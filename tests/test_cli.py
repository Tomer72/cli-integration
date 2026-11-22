"""Exercise the CLI entry point with simulated HTTPS responses."""

import base64
import io
import json
import runpy
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from client import HOST, LoginRequired, TicketForgeClient


class TicketFlowTests(unittest.TestCase):
    def test_session(self):
        ticket = dict(
            ref="TF-101",
            title="Fix filter",
            description="Hide closed tickets",
            stage="open",
            dependsOn=None,
            customFields={"priority": "1"},
            owner={"username": "demo"},
            created="2026-11-22T11:00:00Z",
        )

        def response(data, status=200):
            return Mock(status=status, read=lambda: json.dumps(data).encode())

        sequence = [
            response({}, 401),
            response({}),
            response({"workitem": ticket.copy()}),
            response(
                {
                    "workitems": [dict(ticket, ref="TF-100")],
                    "pagination": {"hasMore": True, "nextCursor": "a:b"},
                }
            ),
            response({"workitems": [ticket.copy()], "pagination": {"hasMore": False}}),
            response({"workitem": ticket.copy()}),
            response({"workitem": ticket.copy()}),
            response({}),
            response({"workitem": dict(ticket, stage="review")}),
        ]
        actions = [
            "demo",
            "demo",
            "1",
            ticket["title"],
            ticket["description"],
            "s",
            "2",
            "m",
            "2",
            "e",
            "",
            "",
            "3",
            "k",
            "y",
            "b",
            "b",
            "3",
            "/exit",
        ]
        inputs = iter(actions)
        output = io.StringIO()

        def answer(prompt):
            value = next(inputs)
            print(prompt + value)
            return value

        with patch("builtins.input", side_effect=answer), patch(
            "ui.getpass", return_value="dummy"
        ), patch("ui.interactive", return_value=False), patch(
            "client.HTTPSConnection"
        ) as https, redirect_stdout(
            output
        ):
            connection = https.return_value
            connection.getresponse.side_effect = sequence
            runpy.run_module("cli", run_name="__main__")
        calls = connection.request.call_args_list
        self.assertEqual(len(calls), len(sequence))
        for call in calls:
            self.assertEqual(
                call.kwargs["headers"]["Authorization"],
                "Basic " + base64.b64encode(b"demo:dummy").decode(),
            )
        self.assertTrue(all(call.args == (HOST,) for call in https.call_args_list))
        self.assertEqual(calls[2].args, ("POST", "/api/tforge/workitem/publish"))
        self.assertEqual(
            json.loads(calls[2].kwargs["body"]),
            dict(
                title=ticket["title"], description=ticket["description"], dependsOn=None
            ),
        )
        self.assertEqual(
            calls[4].args, ("GET", "/api/tforge/workitems/mine?limit=5&cursor=a%3Ab")
        )
        self.assertEqual(calls[7].args, ("PUT", "/api/tforge/workitem/TF-101"))
        self.assertEqual(
            json.loads(calls[7].kwargs["body"]),
            dict(
                title=ticket["title"],
                description=ticket["description"],
                stage="review",
                dependsOn=None,
                customFields={"priority": "1"},
            ),
        )
        for line in (
            "Incorrect username",
            "Created TF-101",
            "Saved TF-101",
            "Review",
            "Logged out",
        ):
            self.assertIn(line, output.getvalue())
        self.assertNotIn("dummy", output.getvalue())

    def test_expired_login_and_connection_cleanup(self):
        with patch("client.HTTPSConnection") as https:
            connection = https.return_value
            connection.getresponse.return_value.status = 401
            with self.assertRaises(LoginRequired):
                TicketForgeClient("demo", "dummy").list_tickets()
            connection.close.assert_called_once()

    def test_lost_create_response_is_not_retried(self):
        with patch("client.HTTPSConnection") as https:
            connection = https.return_value
            connection.getresponse.side_effect = OSError("connection lost")
            with self.assertRaises(OSError):
                TicketForgeClient("demo", "dummy").create_ticket(
                    "Example", "", ["TF-100"]
                )
            connection.request.assert_called_once()
            connection.close.assert_called_once()
