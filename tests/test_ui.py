import unittest
from unittest.mock import patch

import ui


class TicketDetailsTests(unittest.TestCase):
    def test_field_labels_are_bold_and_values_have_regular_weight(self):
        ticket = {"ref": "TF-1", "stage": "in_progress", "owner": {"username": "demo"}}
        with patch("ui.interactive", return_value=True), patch(
            "ui.color_enabled", return_value=True
        ):
            card = ui.ticket_box(ticket)
        for label in (
            "Stage",
            "Description",
            "Depends on",
            "Owner",
            "Created",
            "Updated",
        ):
            self.assertIn(f"\033[1m{label}\033[0m", card)
        self.assertIn("demo", card)
        self.assertRegex(card, r"\x1b\[38;2;255;175;0m\s*In Progress\x1b\[0m")
