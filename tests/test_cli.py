"""End-to-end smoke test: drive `python cli.py` in plain mode with simulated replies."""

import io
import json
import runpy
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

TICKET = {
    "ref": "TF-101",
    "title": "Fix filter",
    "description": "Hide closed tickets",
    "stage": "open",
    "dependsOn": None,
    "customFields": {"priority": "1"},
    "owner": {"username": "demo"},
    "created": "2026-11-22T11:00:00Z",
}


def reply(data, status=200):
    return Mock(status=status, read=lambda: json.dumps(data).encode())


def run_cli(steps):
    """Run the CLI. Each step is (typed input, server replies that input triggers)."""
    inputs = iter(text for text, _ in steps)
    replies = [r for _, step_replies in steps for r in step_replies]
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
        https.return_value.getresponse.side_effect = replies
        runpy.run_module("cli", run_name="__main__")
    return output.getvalue(), https.return_value.request.call_args_list


class SmokeTest(unittest.TestCase):
    def test_login_create_browse_edit_logout(self):
        page_one = {
            "workitems": [dict(TICKET, ref="TF-100")],
            "pagination": {"hasMore": True, "nextCursor": "c2"},
        }
        page_two = {"workitems": [TICKET], "pagination": {"hasMore": False}}
        steps = [
            ("demo", [reply({}, 401)]),  # username; wrong password
            ("demo", [reply({})]),  # username; correct password
            ("1", []),  # Home → Create ticket
            (TICKET["title"], []),
            (TICKET["description"], []),
            ("s", [reply({"workitem": TICKET})]),  # skip dependencies → POST
            ("2", [reply(page_one)]),  # Home → List
            ("m", [reply(page_two)]),  # Show 5 more
            ("2", [reply({"workitem": TICKET})]),  # open TF-101
            ("e", [reply({"workitem": TICKET})]),  # edit
            ("", []),  # keep title
            ("", []),  # keep description
            ("3", []),  # stage → Review
            ("k", []),  # keep dependencies
            ("y", [reply({}), reply({"workitem": dict(TICKET, stage="review")})]),
            ("b", []),  # back to tickets
            ("b", []),  # back to home
            ("3", []),  # log out
            ("/exit", []),
        ]
        output, calls = run_cli(steps)

        for text in (
            "Incorrect username",
            "Created TF-101",
            "Saved TF-101",
            "Review",
            "Logged out",
        ):
            self.assertIn(text, output)
        self.assertNotIn("dummy", output)
        self.assertEqual(
            output.count("/ Commands"), output.count("TicketForge CLI   |")
        )

        put = next(c for c in calls if c.args[0] == "PUT")
        self.assertEqual(put.args[1], "/api/tforge/workitem/TF-101")
        self.assertEqual(
            json.loads(put.kwargs["body"]),
            {
                "title": TICKET["title"],
                "description": TICKET["description"],
                "stage": "review",
                "dependsOn": None,
                "customFields": {"priority": "1"},
            },
        )

    def test_expired_session_returns_to_sign_in(self):
        steps = [
            ("demo", [reply({})]),
            ("2", [reply({}, 401)]),  # list → 401
            ("/exit", []),
        ]
        output, _ = run_cli(steps)
        self.assertIn("Your session expired", output)
        self.assertEqual(output.count("Sign in to TicketForge"), 2)

    def test_server_error_on_list_keeps_user_signed_in(self):
        steps = [
            ("demo", [reply({})]),
            ("2", [reply({}, 500)]),
            ("3", []),
            ("/exit", []),
        ]
        output, _ = run_cli(steps)
        self.assertIn("Could not load tickets", output)
        self.assertIn("Logged out", output)


if __name__ == "__main__":
    unittest.main()
