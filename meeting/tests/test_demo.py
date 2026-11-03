import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import get_datetime

from meeting.api.demo import load_demo
from meeting.api.meetings import meetings_needing_minutes
from meeting.demo import MeetingDemo

DEMO_TITLES = {
	"Q4 Business Review",
	"Sales Pipeline Review",
	"Vendor Evaluation Call",
	"Hiring Sync",
	"Marketing Campaign Kickoff",
	"Design Review",
	"Engineering Standup",
	"Customer Feedback Session",
	"Q1 Planning Offsite",
	"All Hands",
}


class TestMeetingDemo(IntegrationTestCase):
	def test_reset_leaves_only_the_demo(self):
		emails_before = frappe.db.count("Email Queue")
		demo = MeetingDemo(site_url="http://demo.localhost:8000")
		demo.run(reset=True)

		titles = frappe.get_all("Meeting", pluck="title")
		self.assertEqual(set(titles), DEMO_TITLES)
		self.assertEqual(titles.count("Engineering Standup"), 9)
		self.assertEqual(frappe.db.count("Meeting Action Item"), 7)
		self.assertEqual(
			[m.title for m in meetings_needing_minutes("Administrator")], ["Vendor Evaluation Call"]
		)
		self.assertEqual(frappe.db.count("Email Queue"), emails_before)
		for group in ("Sales Team", "Engineering", "Marketing", "Leadership"):
			self.assertTrue(frappe.db.exists("User Group", group))

	def test_demo_reads_like_a_real_calendar(self):
		MeetingDemo().run(reset=True)
		for start in frappe.get_all("Meeting", pluck="start"):
			self.assertLess(get_datetime(start).weekday(), 5, "no demo meeting on a weekend")

		review = frappe.get_doc("Meeting", {"title": "Q4 Business Review"})
		self.assertNotIn("Pending", {a.rsvp for a in review.attendees})
		declined = [a for a in review.attendees if a.rsvp == "Declined"]
		self.assertTrue(declined and not any(a.attended for a in declined))

		feedback = frappe.get_doc("Meeting", {"title": "Customer Feedback Session"})
		self.assertEqual(feedback.get_attendee("Administrator").rsvp, "Pending")

	def test_falls_back_without_suite(self):
		demo = MeetingDemo()
		if demo.use_meet or demo.use_calendar:
			self.skipTest("Frappe Suite is set up on this site")
		demo.run(reset=True)
		self.assertFalse(frappe.db.count("Meeting", {"video_provider": "Frappe Meet"}))
		self.assertFalse(frappe.db.count("Meeting", {"calendar_event": ["is", "set"]}))
		self.assertTrue(frappe.db.count("Meeting", {"video_provider": "Google Meet"}))

	def test_settings_loads_demo_around_the_current_user(self):
		me = "demo-loader@example.com"
		if not frappe.db.exists("User", me):
			frappe.get_doc(
				{"doctype": "User", "email": me, "first_name": "Demo", "send_welcome_email": 0}
			).insert(ignore_permissions=True)
		user = frappe.get_doc("User", me)

		frappe.set_user(me)
		self.assertRaises(frappe.PermissionError, load_demo, reset=True)

		frappe.set_user("Administrator")
		user.add_roles("System Manager")
		frappe.set_user(me)
		try:
			load_demo(reset=True)
			self.assertEqual(frappe.session.user, me)
			self.assertEqual([m.title for m in meetings_needing_minutes(me)], ["Vendor Evaluation Call"])
			feedback = frappe.get_doc("Meeting", {"title": "Customer Feedback Session"})
			self.assertEqual(feedback.get_attendee(me).rsvp, "Pending")
		finally:
			frappe.set_user("Administrator")
			user.remove_roles("System Manager")
