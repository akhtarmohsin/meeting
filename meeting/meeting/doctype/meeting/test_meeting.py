# Copyright (c) 2026, Mohsin Akhtar and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from meeting.api import meetings as api
from meeting.frappe_calendar import FrappeCalendar, iso_duration
from meeting.invites import MeetingInvite
from meeting.video import FrappeMeet

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

	def test_meet_room_cleared_when_provider_changes(self):
		doc = make_meeting(video_provider="Frappe Meet", meet_room="abcd-efgh-ijkl")
		self.assertEqual(doc.meet_room, "abcd-efgh-ijkl")

		doc.video_provider = "Zoom"
		doc.save()
		self.assertFalse(doc.meet_room)

	def test_frappe_meet_link_needs_suite(self):
		if FrappeMeet.is_available():
			self.skipTest("Frappe Suite is installed on this site")
		self.assertRaises(frappe.ValidationError, api.create_frappe_meet_link, "Weekly sync")

	def test_calendar_duration_is_iso_8601(self):
		self.assertEqual(iso_duration(30 * 60), "PT30M")
		self.assertEqual(iso_duration(90 * 60), "PT1H30M")
		self.assertEqual(iso_duration(2 * 3600), "PT2H")

	def test_add_to_calendar_needs_suite(self):
		if FrappeCalendar().is_available():
			self.skipTest("Frappe Calendar is set up for this user")
		doc = make_meeting(add_to_calendar=1, insert=False)
		self.assertRaises(frappe.ValidationError, doc.insert)

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
