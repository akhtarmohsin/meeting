"""Demo data for Meeting: `bench --site <site> meeting-demo [--reset]`.

Builds a small company (people and User Groups) and a set of meetings that between them show
every feature. Dates are relative to today. Sends no email.
"""

from datetime import timedelta

import frappe
from frappe.utils import add_days, get_datetime, get_url, getdate, now_datetime

from meeting.frappe_calendar import FrappeCalendar
from meeting.video import FrappeMeet

ADMIN = "Administrator"
TEAMS = {
	"Sales Team": [("Rahul", "Mehta"), ("Sneha", "Kapoor"), ("Vikram", "Singh")],
	"Engineering": [("Ananya", "Iyer"), ("Karthik", "Nair"), ("Fatima", "Sheikh"), ("Rohan", "Das")],
	"Marketing": [("Neha", "Joshi"), ("Arjun", "Malhotra"), ("Kavya", "Reddy")],
	"Leadership": [("Sanjay", "Gupta"), ("Meera", "Krishnan")],
}
# Team heads also sit in Leadership.
HEADS = ["rahul.mehta", "ananya.iyer", "neha.joshi"]
EXTRA_PEOPLE = [("Priya", "Sharma")]


def u(handle: str) -> str:
	return f"{handle}@example.com"


class MeetingDemo:
	def __init__(self, site_url: str | None = None, me: str = ADMIN):
		# The person the demo is built around: organizer, attendee and owner of action items.
		self.me = me
		self.site_url = (site_url or get_url()).rstrip("/")
		self.today = getdate()
		self.now = now_datetime().replace(second=0, microsecond=0)
		self.use_meet = FrappeMeet.is_available()
		self.use_calendar = FrappeCalendar().is_available()

	def run(self, reset: bool = False) -> str:
		if reset:
			self.reset()
		self.groups = self.ensure_people_and_groups()
		self.create_meetings()
		return self.summary()

	def reset(self):
		"""Delete every action item and meeting (their calendar events go with them)."""
		for name in frappe.get_all("Meeting Action Item", pluck="name"):
			frappe.delete_doc("Meeting Action Item", name, ignore_permissions=True, force=True)
		for name in frappe.get_all("Meeting", order_by="repeat_of desc, creation desc", pluck="name"):
			frappe.delete_doc("Meeting", name, ignore_permissions=True, force=True)

	def ensure_people_and_groups(self) -> dict:
		for first, last in [p for team in TEAMS.values() for p in team] + EXTRA_PEOPLE:
			self.ensure_person(first, last)
		groups = {}
		for group, people in TEAMS.items():
			members = [u(f"{f}.{l}".lower()) for f, l in people]
			if group == "Leadership":
				members += [u(h) for h in HEADS]
			self.ensure_group(group, members)
			groups[group] = members
		return groups

	def ensure_person(self, first: str, last: str):
		email = u(f"{first}.{last}".lower())
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": first,
					"last_name": last,
					"user_type": "System User",
					"send_welcome_email": 0,
				}
			).insert(ignore_permissions=True)
		frappe.get_doc("User", email).add_roles("Meeting User")

	def ensure_group(self, name: str, members: list[str]):
		if not frappe.db.exists("User Group", name):
			frappe.get_doc(
				{
					"doctype": "User Group",
					"__newname": name,
					"user_group_members": [{"user": m} for m in members],
				}
			).insert(ignore_permissions=True)
			return
		doc = frappe.get_doc("User Group", name)
		existing = {m.user for m in doc.user_group_members}
		for m in members:
			if m not in existing:
				doc.append("user_group_members", {"user": m})
		doc.save(ignore_permissions=True)

	def create_meetings(self):
		G = self.groups
		self.q4_review(G)
		self.sales_review(G)
		# Finished but never written up, so Home's "Minutes pending" has something to show.
		self.meeting(
			"Vendor Evaluation Call",
			self.at(self.past_weekday(1), "16:00"),
			minutes=45,
			people=[self.me, u("karthik.nair"), u("meera.krishnan")],
			status="Completed",
			meeting_type="Online",
			video_provider="Google Meet",
			video_link="https://meet.google.com/vnd-eval-0411",
			description="Compare three payroll vendors before renewal.",
			agenda=[
				{
					"topic": "Pricing comparison",
					"presenter": u("meera.krishnan"),
					"duration": 20,
					"discussed": 1,
				},
				{
					"topic": "Integration effort",
					"presenter": u("karthik.nair"),
					"duration": 20,
					"discussed": 1,
				},
			],
		)
		self.meeting(
			"Hiring Sync",
			self.now.replace(minute=self.now.minute // 15 * 15),
			minutes=45,
			people=[self.me, u("meera.krishnan"), u("ananya.iyer")],
			status="In Progress",
			meeting_type="Online",
			agenda=[
				{"topic": "Shortlist for senior engineer role", "presenter": u("ananya.iyer"), "duration": 20}
			],
			**self.video("Hiring Sync"),
		)
		kickoff = max(self.at(0, "17:00"), self.now.replace(minute=0) + timedelta(hours=2))
		self.meeting(
			"Marketing Campaign Kickoff",
			kickoff,
			minutes=60,
			people=[self.me, *G["Marketing"]],
			meeting_type="Online",
			add_to_calendar=int(self.use_calendar),
			description="Plan the January product launch campaign.",
			rsvp={
				u("neha.joshi"): "Accepted",
				u("kavya.reddy"): "Accepted",
				u("arjun.malhotra"): "Tentative",
			},
			agenda=[
				{"topic": "Campaign goals and audience", "presenter": u("neha.joshi"), "duration": 15},
				{"topic": "Channels and budget", "presenter": u("arjun.malhotra"), "duration": 20},
				{"topic": "Creative timeline", "presenter": u("kavya.reddy"), "duration": 15},
			],
			invites_sent_days_ago=1,
			**self.video("Marketing Campaign Kickoff"),
		)
		self.meeting(
			"Design Review",
			self.at(self.next_weekday(1), "11:00"),
			minutes=60,
			people=[self.me, u("fatima.sheikh"), u("rohan.das"), u("kavya.reddy")],
			status="Cancelled",
			meeting_type="Online",
			video_provider="Google Meet",
			video_link="https://meet.google.com/dsg-rvw-1122",
			description="Postponed until the new brand guidelines are ready.",
		)
		self.standup(G)
		self.feedback_session()
		self.offsite(G)
		self.all_hands()
		self.action("Renew video conferencing licences", None, self.me, 6, priority="Low")

	def q4_review(self, G):
		review = self.meeting(
			"Q4 Business Review",
			self.at(self.past_weekday(7), "10:00"),
			minutes=90,
			people=[self.me, *G["Leadership"], u("priya.sharma")],
			status="Completed",
			meeting_type="Hybrid",
			location="Board Room, 4th Floor",
			video_provider="Google Meet",
			video_link="https://meet.google.com/qbr-q4rv-2026",
			description="Quarterly results, pipeline health and priorities for next quarter.",
			rsvp={u("priya.sharma"): "Declined"},
			agenda=[
				{
					"topic": "Q4 revenue and margin",
					"presenter": u("sanjay.gupta"),
					"duration": 20,
					"discussed": 1,
					"notes": "Revenue up 18% QoQ; margin steady at 32%.",
				},
				{
					"topic": "Sales pipeline health",
					"presenter": u("rahul.mehta"),
					"duration": 20,
					"discussed": 1,
					"notes": "Three enterprise deals in final stage.",
				},
				{
					"topic": "Product roadmap status",
					"presenter": u("ananya.iyer"),
					"duration": 25,
					"discussed": 1,
				},
				{"topic": "Hiring plan", "presenter": u("meera.krishnan"), "duration": 15, "discussed": 1},
			],
			minutes_html=(
				"<h3>Summary</h3><p>Q4 closed ahead of target. The team agreed to double down on enterprise accounts "
				"and to keep hiring focused on engineering.</p><ul><li>Revenue up 18% quarter on quarter</li>"
				"<li>Two enterprise renewals confirmed</li><li>Roadmap on track except reporting module</li></ul>"
			),
			decisions="Approve two senior engineering hires\nMove reporting module to Q1\nRun a pricing review for SMB plans",
			invites_sent_days_ago=10,
		)
		self.action(
			"Share Q4 board deck with investors",
			review,
			u("sanjay.gupta"),
			-3,
			status="Done",
			priority="High",
		)
		self.action(
			"Draft job descriptions for two senior engineers",
			review,
			u("ananya.iyer"),
			2,
			status="In Progress",
		)
		self.action(
			"Prepare SMB pricing proposal",
			review,
			self.me,
			-2,
			priority="High",
			description="Compare with three competitors and suggest two options.",
		)

	def sales_review(self, G):
		sales = self.meeting(
			"Sales Pipeline Review",
			self.at(self.past_weekday(2), "15:00"),
			minutes=60,
			people=[self.me, *G["Sales Team"]],
			status="Completed",
			meeting_type="Online",
			video_provider="Zoom",
			video_link="https://zoom.us/j/8841206613",
			absent=[u("vikram.singh")],
			agenda=[
				{
					"topic": "Deals closing this month",
					"presenter": u("rahul.mehta"),
					"duration": 20,
					"discussed": 1,
				},
				{
					"topic": "Stalled opportunities",
					"presenter": u("sneha.kapoor"),
					"duration": 15,
					"discussed": 1,
				},
				{"topic": "Forecast for December", "presenter": u("vikram.singh"), "duration": 15},
			],
			minutes_html="<p>Five deals likely to close this month. Two stalled deals need executive sponsorship.</p>",
			decisions="Sanjay to join calls for stalled enterprise deals",
			invites_sent_days_ago=4,
		)
		self.action("Send revised quote to Northwind", sales, u("sneha.kapoor"), -1, priority="High")
		self.action("Update December forecast", sales, u("vikram.singh"), 1)
		self.action("Book executive call with Contoso", sales, self.me, 3, status="In Progress")

	def standup(self, G):
		first = next(
			self.at(d, "09:30") for d in range(1, 8) if add_days(self.today, d).weekday() in (0, 2, 4)
		)
		self.meeting(
			"Engineering Standup",
			first,
			minutes=15,
			people=[self.me, *G["Engineering"]],
			meeting_type="Online",
			add_to_calendar=int(self.use_calendar),
			repeat=1,
			repeat_rule={
				"frequency": "weekly",
				"interval": 1,
				"byDay": [{"day": "mo"}, {"day": "we"}, {"day": "fr"}],
				"count": 9,
			},
			agenda=[
				{"topic": "Yesterday", "duration": 5},
				{"topic": "Today", "duration": 5},
				{"topic": "Blockers", "duration": 5},
			],
			**self.video("Engineering Standup"),
		)

	def feedback_session(self):
		self.meeting(
			"Customer Feedback Session",
			self.at(self.next_weekday(3), "14:00"),
			minutes=60,
			people=[
				u("sanjay.gupta"),
				self.me,
				u("priya.sharma"),
				u("sneha.kapoor"),
				u("kavya.reddy"),
				u("rahul.mehta"),
			],
			organizer=u("sanjay.gupta"),
			meeting_type="Online",
			video_provider="Microsoft Teams",
			video_link="https://teams.microsoft.com/l/meetup-join/feedback-session",
			description="Walk through the latest NPS comments and agree on fixes.",
			rsvp={
				u("priya.sharma"): "Accepted",
				u("sneha.kapoor"): "Tentative",
				u("kavya.reddy"): "Declined",
			},
			agenda=[
				{"topic": "NPS trends", "presenter": u("priya.sharma"), "duration": 20},
				{"topic": "Top three complaints", "presenter": u("sneha.kapoor"), "duration": 25},
				{"topic": "Owners and next steps", "presenter": u("sanjay.gupta"), "duration": 15},
			],
			invites_sent_days_ago=2,
		)

	def offsite(self, G):
		self.meeting(
			"Q1 Planning Offsite",
			self.at(self.next_weekday(5), "10:00"),
			minutes=7 * 60,
			people=[self.me, *G["Leadership"], u("priya.sharma"), u("arjun.malhotra")],
			optional=[u("priya.sharma"), u("arjun.malhotra")],
			meeting_type="In Person",
			location="Lakeview Conference Centre, Bengaluru",
			description="Full-day planning for Q1 goals, budgets and hiring.",
			rsvp={
				u("sanjay.gupta"): "Accepted",
				u("meera.krishnan"): "Accepted",
				u("rahul.mehta"): "Tentative",
			},
			agenda=[
				{"topic": "Q1 company goals", "presenter": u("sanjay.gupta"), "duration": 60},
				{"topic": "Sales targets", "presenter": u("rahul.mehta"), "duration": 45},
				{"topic": "Engineering roadmap", "presenter": u("ananya.iyer"), "duration": 60},
				{"topic": "Marketing plan", "presenter": u("neha.joshi"), "duration": 45},
				{
					"topic": "Budget and hiring",
					"presenter": u("meera.krishnan"),
					"duration": 60,
					"notes": "Bring headcount requests by team.",
				},
			],
		)

	def all_hands(self):
		everyone = frappe.get_all(
			"Has Role",
			filters={"role": ["in", ["Meeting User", "Meeting Manager"]], "parenttype": "User"},
			pluck="parent",
			distinct=True,
		)
		self.meeting(
			"All Hands",
			self.at(self.next_weekday(8), "17:00"),
			minutes=60,
			people=[self.me, *everyone],
			meeting_type="Hybrid",
			location="Cafeteria",
			video_provider="Jitsi",
			video_link="https://meet.jit.si/acme-all-hands",
			add_to_calendar=int(self.use_calendar),
			description="Company update, wins of the month and open Q&A.",
			agenda=[
				{"topic": "Company update", "presenter": u("sanjay.gupta"), "duration": 20},
				{"topic": "Wins of the month", "presenter": u("meera.krishnan"), "duration": 15},
				{"topic": "Open Q&A", "duration": 25},
			],
		)

	def meeting(
		self,
		title,
		start,
		minutes,
		people,
		organizer=None,
		rsvp=None,
		optional=(),
		absent=(),
		minutes_html=None,
		invites_sent_days_ago=None,
		**fields,
	):
		organizer = organizer or self.me
		rsvp = rsvp or {}
		done = fields.get("status") == "Completed"

		def reply(person):
			if person == organizer:
				return "Accepted"
			# Everyone at a finished meeting answered; only explicit declines stay declined.
			return rsvp.get(person, "Accepted" if done else "Pending")

		doc = frappe.get_doc(
			{
				"doctype": "Meeting",
				"title": title,
				"organizer": organizer,
				"start": start,
				"end": start + timedelta(minutes=minutes),
				"minutes": minutes_html,
				"attendees": [
					{
						"user": p,
						"rsvp": reply(p),
						"optional": int(p in optional),
						"attended": int(done and p not in absent and reply(p) != "Declined"),
					}
					for p in dict.fromkeys(people)
				],
				**fields,
			}
		).insert()
		if invites_sent_days_ago:
			# Shows "Invites sent" without sending anything.
			doc.db_set("invites_sent_on", add_days(self.now, -invites_sent_days_ago))
		return doc

	def action(
		self, title, meeting, assigned_to, due_in_days, status="Open", priority="Medium", description=None
	):
		frappe.get_doc(
			{
				"doctype": "Meeting Action Item",
				"title": title,
				"meeting": meeting.name if meeting else None,
				"assigned_to": assigned_to,
				"due_date": add_days(self.today, due_in_days),
				"status": status,
				"priority": priority,
				"description": description,
			}
		).insert()

	def video(self, title) -> dict:
		"""A real Frappe Meet room where Suite is installed, a Google Meet link elsewhere."""
		if not self.use_meet:
			return {
				"video_provider": "Google Meet",
				"video_link": "https://meet.google.com/demo-" + frappe.scrub(title),
			}
		room = FrappeMeet().create_room(title)["meet_room"]
		return {
			"video_provider": "Frappe Meet",
			"meet_room": room,
			"video_link": f"{self.site_url}/meet/{room}",
		}

	def at(self, day_offset: int, hhmm: str):
		hour, minute = map(int, hhmm.split(":"))
		return get_datetime(add_days(self.today, day_offset)).replace(hour=hour, minute=minute, second=0)

	def next_weekday(self, days: int) -> int:
		"""`days` from today, moved forward off a weekend."""
		while add_days(self.today, days).weekday() >= 5:
			days += 1
		return days

	def past_weekday(self, days_ago: int) -> int:
		offset = -days_ago
		while add_days(self.today, offset).weekday() >= 5:
			offset -= 1
		return offset

	def summary(self) -> str:
		return (
			f"Meeting demo: {frappe.db.count('Meeting')} meetings "
			f"({frappe.db.count('Meeting', {'repeat_of': ['is', 'set']})} standup repeats, "
			f"{frappe.db.count('Meeting', {'calendar_event': ['is', 'set']})} in Frappe Calendar), "
			f"{frappe.db.count('Meeting Action Item')} action items. "
			f"Frappe Meet: {'yes' if self.use_meet else 'no'}, Frappe Calendar: {'yes' if self.use_calendar else 'no'}."
		)
