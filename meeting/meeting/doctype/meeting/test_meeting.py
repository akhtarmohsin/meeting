# Copyright (c) 2026, Mohsin Akhtar and contributors
# For license information, please see license.txt

from datetime import timedelta

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_months, add_to_date, get_datetime, now_datetime

from meeting.api import meetings as api
from meeting.frappe_calendar import FrappeCalendar, iso_duration
from meeting.invites import MeetingInvite
from meeting.recurrence import MeetingSeries
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

	def test_weekly_series_creates_occurrences(self):
		start = next_weekday(0, hour=10)  # a Monday, 10:00
		rule = {"frequency": "weekly", "interval": 1, "byDay": [{"day": "mo"}, {"day": "we"}], "count": 4}
		root = make_meeting(
			start=start,
			end=add_to_date(start, minutes=45),
			repeat=1,
			repeat_rule=rule,
			attendees=[{"user": ATTENDEE}],
			agenda=[{"topic": "Updates", "duration": 15}],
			minutes="<p>Only for the first meeting</p>",
		)
		occurrences = series_of(root)

		expected = [add_to_date(start, days=d) for d in (2, 7, 9)]  # Wed, next Mon, next Wed
		self.assertEqual([get_datetime(o.start) for o in occurrences], expected)
		for o in occurrences:
			self.assertEqual(get_datetime(o.end) - get_datetime(o.start), timedelta(minutes=45))
			self.assertEqual(o.title, root.title)
			self.assertEqual(o.get_attendee(ATTENDEE).rsvp, "Pending")
			self.assertEqual([a.topic for a in o.agenda], ["Updates"])
			self.assertFalse(o.minutes)
			self.assertFalse(o.repeat)

	def test_series_ends_on_until_date(self):
		start = next_weekday(0, hour=9)
		until = add_to_date(start, days=3).strftime("%Y-%m-%dT23:59:59")
		root = make_meeting(start=start, repeat=1, repeat_rule={"frequency": "daily", "interval": 1, "until": until})
		self.assertEqual(len(series_of(root)), 3)

	def test_open_ended_series_stops_at_horizon(self):
		root = make_meeting(repeat=1, repeat_rule={"frequency": "weekly", "interval": 1})
		last = get_datetime(series_of(root)[-1].start)
		self.assertLessEqual(last, add_months(now_datetime(), MeetingSeries.HORIZON_MONTHS))
		self.assertGreaterEqual(len(series_of(root)), 11)

	def test_series_rule_cannot_change_and_delete_detaches(self):
		root = make_meeting(repeat=1, repeat_rule={"frequency": "daily", "interval": 1, "count": 3})
		api.save_meeting({"repeat_rule": {"frequency": "daily", "interval": 1, "count": 9}}, root.name)
		self.assertEqual(frappe.parse_json(frappe.db.get_value("Meeting", root.name, "repeat_rule"))["count"], 3)

		names = [o.name for o in series_of(root)]
		frappe.delete_doc("Meeting", root.name)
		for name in names:
			self.assertIsNone(frappe.db.get_value("Meeting", name, "repeat_of"))

	def test_series_invite_has_rrule(self):
		root = make_meeting(repeat=1, repeat_rule={"frequency": "weekly", "interval": 2, "byDay": [{"day": "tu"}], "count": 5})
		self.assertIn("RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=TU;COUNT=5", MeetingInvite(root).ics())
		self.assertNotIn("RRULE", MeetingInvite(series_of(root)[0]).ics())

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


def next_weekday(weekday: int, hour: int):
	"""The next given weekday (0 = Monday) at least a day away, at the given hour."""
	day = add_to_date(now_datetime(), days=1).replace(hour=hour, minute=0, second=0, microsecond=0)
	return add_to_date(day, days=(weekday - day.weekday()) % 7)


def series_of(root):
	names = frappe.get_all("Meeting", filters={"repeat_of": root.name}, order_by="start asc", pluck="name")
	return [frappe.get_doc("Meeting", n) for n in names]
