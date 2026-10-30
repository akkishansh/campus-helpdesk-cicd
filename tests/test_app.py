import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from app import (
    cancel_booking,
    create_booking,
    create_ticket,
    get_booking,
    add_schedule_block,
    create_community_post,
    get_profile,
    like_community_post,
    list_availability,
    list_bookings,
    list_community_posts,
    list_owner_turfs,
    list_tickets,
    list_turfs,
    owner_bookings,
    owner_dashboard,
    remove_schedule_block,
    rewards_summary,
    save_profile,
    save_turf,
    set_ticket_status,
    update_owner_booking_status,
)


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

    def booking(self, **changes):
        values = {
            "turf_id": "turf-central",
            "date": (date.today() + timedelta(days=7)).isoformat(),
            "start_time": "18:00",
            "duration_hours": 2,
            "customer_name": "Test Player",
            "email": "player@example.com",
            "phone": "+91 98765 43210",
        }
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

    def test_demo_turfs_are_seeded_and_filterable(self):
        turfs = list_turfs({"city": "Bengaluru", "sport": "Football"}, self.db)
        self.assertEqual(len(turfs), 2)
        self.assertIsInstance(turfs[0]["amenities"], list)

    def test_booking_is_saved_and_reserved_slots_are_unavailable(self):
        booking = create_booking(self.booking(), self.db)
        self.assertEqual(booking["status"], "Confirmed")
        self.assertEqual(booking["total_amount"], 2400)
        slots = list_availability("turf-central", self.booking()["date"], self.db)
        self.assertFalse(next(slot for slot in slots if slot["start_time"] == "18:00")["available"])
        self.assertFalse(next(slot for slot in slots if slot["start_time"] == "19:00")["available"])

    def test_overlapping_booking_is_rejected(self):
        create_booking(self.booking(), self.db)
        with self.assertRaisesRegex(ValueError, "no longer available"):
            create_booking(self.booking(start_time="19:00"), self.db)

    def test_booking_lookup_requires_matching_email_and_cancel_frees_slot(self):
        booking = create_booking(self.booking(), self.db)
        self.assertIsNone(get_booking(booking["id"], "someone@example.com", self.db))
        self.assertEqual(len(list_bookings("PLAYER@example.com", self.db)), 1)
        cancelled = cancel_booking(booking["id"], "player@example.com", self.db)
        self.assertEqual(cancelled["status"], "Cancelled")
        self.assertTrue(next(slot for slot in list_availability("turf-central", booking["booking_date"], self.db)
                             if slot["start_time"] == "18:00")["available"])

    def test_booking_input_validation(self):
        with self.assertRaisesRegex(ValueError, "valid email"):
            create_booking(self.booking(email="not-an-email"), self.db)
        with self.assertRaisesRegex(ValueError, "today or a future date"):
            create_booking(self.booking(date=(date.today() - timedelta(days=1)).isoformat()), self.db)

    def test_owner_can_add_a_turf_and_hide_it_from_player_list(self):
        turf = save_turf({
            "name": "Demo Turf", "location": "Test Road", "city": "Delhi", "sport": "Football",
            "format": "5-a-side", "price_per_hour": 1000, "amenities": ["Parking"], "active": False,
        }, self.db)
        self.assertFalse(turf["active"])
        self.assertNotIn(turf["id"], {item["id"] for item in list_turfs(path=self.db)})
        self.assertIn(turf["id"], {item["id"] for item in list_owner_turfs(self.db)})

    def test_owner_schedule_blocks_slots_and_can_remove_them(self):
        block = add_schedule_block({
            "turf_id": "turf-central", "date": self.booking()["date"],
            "start_time": "09:00", "duration_hours": 2, "reason": "Maintenance",
        }, self.db)
        slots = list_availability("turf-central", self.booking()["date"], self.db)
        self.assertFalse(next(slot for slot in slots if slot["start_time"] == "09:00")["available"])
        self.assertTrue(remove_schedule_block(block["id"], self.db))
        self.assertTrue(next(slot for slot in list_availability("turf-central", self.booking()["date"], self.db)
                             if slot["start_time"] == "09:00")["available"])

    def test_owner_dashboard_and_booking_status(self):
        booking = create_booking(self.booking(), self.db)
        dashboard = owner_dashboard(self.db)
        self.assertEqual(dashboard["confirmed_bookings"], 1)
        self.assertEqual(dashboard["revenue"], 2400)
        self.assertEqual(len(owner_bookings(path=self.db)), 1)
        updated = update_owner_booking_status(booking["id"], "Cancelled", self.db)
        self.assertEqual(updated["status"], "Cancelled")

    def test_community_profile_and_rewards_features(self):
        post = create_community_post({"author": "Test Player", "topic": "Football", "body": "Anyone playing this weekend?"}, self.db)
        self.assertEqual(like_community_post(post["id"], self.db)["likes"], 1)
        self.assertEqual(len(list_community_posts(self.db)), 1)
        profile = save_profile({"email": "player@example.com", "name": "Test Player", "city": "Delhi"}, self.db)
        self.assertEqual(get_profile("PLAYER@example.com", self.db), profile)
        create_booking(self.booking(), self.db)
        self.assertEqual(rewards_summary("player@example.com", self.db)["points"], 24)


if __name__ == "__main__":
    unittest.main()
