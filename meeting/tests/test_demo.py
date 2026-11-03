import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import get_datetime

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
