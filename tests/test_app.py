import tempfile
import unittest
from pathlib import Path

from app import create_ticket, list_tickets, set_ticket_status


class TicketTrackerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.db = Path(self.tempdir.name) / "test.db"

    def tearDown(self):
        self.tempdir.cleanup()

    def sample(self, **changes):
        values = {"title": "Campus Wi-Fi issue", "category": "IT & Technology", "priority": "High",
                  "requester": "Sam Student", "description": "Unable to connect in the library."}
        values.update(changes)
        return values

    def test_create_and_list_ticket(self):
        ticket = create_ticket(self.sample(), self.db)
        self.assertEqual(ticket["title"], "Campus Wi-Fi issue")
        self.assertEqual(ticket["status"], "Open")
        self.assertEqual(len(list_tickets(self.db)), 1)

    def test_required_fields_are_checked(self):
        with self.assertRaisesRegex(ValueError, "complete every field"):
            create_ticket(self.sample(title="  "), self.db)

    def test_priority_is_validated(self):
        with self.assertRaisesRegex(ValueError, "valid priority"):
            create_ticket(self.sample(priority="Urgent"), self.db)

    def test_status_can_be_updated_and_unknown_id_returns_none(self):
        ticket = create_ticket(self.sample(), self.db)
        updated = set_ticket_status(ticket["id"], "Resolved", self.db)
        self.assertEqual(updated["status"], "Resolved")
        self.assertIsNone(set_ticket_status(999, "Resolved", self.db))

    def test_invalid_status_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "valid ticket status"):
            set_ticket_status(1, "Waiting", self.db)


if __name__ == "__main__":
    unittest.main()
