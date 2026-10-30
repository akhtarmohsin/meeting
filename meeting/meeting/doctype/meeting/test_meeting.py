# Copyright (c) 2026, Mohsin Akhtar and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from meeting.api import meetings as api
from meeting.invites import MeetingInvite

ORGANIZER = "meeting-organizer@example.com"
ATTENDEE = "meeting-attendee@example.com"
OUTSIDER = "meeting-outsider@example.com"

# User links pull in ERPNext master data, which these tests do not need.
IGNORE_TEST_RECORD_DEPENDENCIES = ["User"]


class TestMeeting(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		for email in (ORGANIZER, ATTENDEE, OUTSIDER):
			make_user(email)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_end_must_be_after_start(self):
		start = add_to_date(now_datetime(), hours=1)
		doc = make_meeting(start=start, end=start, insert=False)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_organizer_added_and_attendees_deduped(self):
		doc = make_meeting(attendees=[{"user": ATTENDEE}, {"email": ATTENDEE}])
		emails = [row.email for row in doc.attendees]
		self.assertEqual(sorted(emails), sorted([ATTENDEE, ORGANIZER]))
		self.assertEqual(doc.get_attendee(ORGANIZER).rsvp, "Accepted")

	def test_attendee_can_rsvp_but_outsider_cannot_see(self):
		doc = make_meeting(attendees=[{"user": ATTENDEE}])

		frappe.set_user(ATTENDEE)
		api.rsvp(doc.name, "Accepted")
		self.assertEqual(frappe.get_doc("Meeting", doc.name).get_attendee(ATTENDEE).rsvp, "Accepted")
		self.assertFalse(frappe.get_doc("Meeting", doc.name).has_permission("write"))

		frappe.set_user(OUTSIDER)
		self.assertNotIn(doc.name, [m.name for m in api.get_meetings("all")])
		self.assertRaises(frappe.PermissionError, api.get_meeting, doc.name)

	def test_ics_contains_event(self):
		doc = make_meeting(attendees=[{"user": ATTENDEE}], video_link="https://meet.example.com/x")
		ics = MeetingInvite(doc).ics()
		self.assertIn("BEGIN:VEVENT", ics)
		self.assertIn(f"ATTENDEE;RSVP=TRUE:mailto:{ATTENDEE}", ics)
		self.assertIn("LOCATION:https://meet.example.com/x", ics)


def make_user(email: str):
	if frappe.db.exists("User", email):
		return
	user = frappe.get_doc(
		{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0}
	).insert(ignore_permissions=True)
	user.add_roles("Meeting User")


def make_meeting(insert: bool = True, **kwargs):
	start = kwargs.pop("start", add_to_date(now_datetime(), days=1))
	doc = frappe.get_doc(
		{
			"doctype": "Meeting",
			"title": "Weekly sync",
			"organizer": ORGANIZER,
			"start": start,
			"end": kwargs.pop("end", add_to_date(start, hours=1)),
			**kwargs,
		}
	)
	return doc.insert() if insert else doc
