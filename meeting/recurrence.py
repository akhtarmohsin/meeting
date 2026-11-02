import json

import frappe
from dateutil import rrule
from frappe import _
from frappe.utils import add_months, get_datetime, now_datetime

FREQUENCIES = {
	"daily": rrule.DAILY,
	"weekly": rrule.WEEKLY,
	"monthly": rrule.MONTHLY,
	"yearly": rrule.YEARLY,
}
WEEKDAYS = {"mo": rrule.MO, "tu": rrule.TU, "we": rrule.WE, "th": rrule.TH, "fr": rrule.FR, "sa": rrule.SA, "su": rrule.SU}
# Copied from the first meeting to every later one. Minutes, decisions and RSVPs stay per meeting.
COPIED_FIELDS = (
	"title",
	"organizer",
	"meeting_type",
	"location",
	"video_provider",
	"video_link",
	"meet_room",
	"description",
	"add_to_calendar",
)


class MeetingSeries:
	"""A repeating meeting: the first meeting holds the rule, each later occurrence is its own meeting.

	The rule uses Frappe Calendar's shape: frequency, interval, byDay, byMonthDay, until or count.
	"""

	# How far ahead a series with no end is filled; the daily job keeps it topped up.
	HORIZON_MONTHS = 3
	MAX_OCCURRENCES = 200

	def __init__(self, root):
		self.root = root
		self.rule = parse_rule(root.repeat_rule)

	@classmethod
	def extend_all(cls):
		"""Scheduled: keep open-ended series filled up to the horizon."""
		roots = frappe.get_all(
			"Meeting",
			filters={"repeat": 1, "repeat_of": ["is", "not set"], "status": ["!=", "Cancelled"]},
			pluck="name",
		)
		for name in roots:
			series = cls(frappe.get_doc("Meeting", name))
			if not series.has_end():
				series.create_upcoming()

	def create_upcoming(self) -> int:
		existing = set(self.existing_starts())
		created = 0
		for start in self.occurrence_starts():
			if start not in existing:
				self.copy(start)
				created += 1
		return created

	def occurrence_starts(self) -> list:
		"""Starts of every occurrence after the first, up to the rule's end or the horizon."""
		first = get_datetime(self.root.start)
		limit = None if self.has_end() else add_months(now_datetime(), self.HORIZON_MONTHS)
		starts = []
		for start in self.to_rrule(first):
			if start == first:
				continue
			if limit and start > limit or len(starts) >= self.MAX_OCCURRENCES:
				break
			starts.append(start)
		return starts

	def existing_starts(self) -> list:
		starts = frappe.get_all("Meeting", filters={"repeat_of": self.root.name}, pluck="start")
		return [get_datetime(s) for s in starts]

	def copy(self, start):
		length = get_datetime(self.root.end) - get_datetime(self.root.start)
		doc = frappe.new_doc("Meeting")
		doc.update({field: self.root.get(field) for field in COPIED_FIELDS})
		doc.update({"start": start, "end": start + length, "status": "Scheduled", "repeat_of": self.root.name})
		for row in self.root.attendees:
			is_organizer = row.user == self.root.organizer
			doc.append(
				"attendees",
				{
					"user": row.user,
					"email": row.email,
					"full_name": row.full_name,
					"optional": row.optional,
					"rsvp": "Accepted" if is_organizer else "Pending",
				},
			)
		for item in self.root.agenda:
			doc.append(
				"agenda",
				{"topic": item.topic, "presenter": item.presenter, "duration": item.duration, "notes": item.notes},
			)
		doc.insert()
		return doc

	def detach_occurrences(self):
		"""Called when the first meeting is deleted: later ones stay, as standalone meetings."""
		for name in frappe.get_all("Meeting", filters={"repeat_of": self.root.name}, pluck="name"):
			frappe.db.set_value("Meeting", name, "repeat_of", None)

	def has_end(self) -> bool:
		return bool(self.rule.get("until") or self.rule.get("count"))

	def to_rrule(self, first):
		rule = self.rule
		kwargs = {"dtstart": first, "interval": int(rule.get("interval") or 1)}
		if rule.get("byDay"):
			kwargs["byweekday"] = [weekday(d) for d in rule["byDay"]]
		if rule.get("byMonthDay"):
			kwargs["bymonthday"] = rule["byMonthDay"]
		if rule.get("until"):
			kwargs["until"] = get_datetime(rule["until"].rstrip("Z"))
		elif rule.get("count"):
			kwargs["count"] = min(int(rule["count"]), self.MAX_OCCURRENCES + 1)
		return rrule.rrule(FREQUENCIES[rule["frequency"]], **kwargs)


def parse_rule(value) -> dict:
	rule = json.loads(value) if isinstance(value, str) else (value or {})
	if rule.get("frequency") not in FREQUENCIES:
		frappe.throw(_("Repeat needs a frequency: daily, weekly, monthly or yearly"))
	if int(rule.get("interval") or 1) < 1:
		frappe.throw(_("Repeat interval must be at least 1"))
	if rule.get("count") and int(rule["count"]) < 2:
		frappe.throw(_("A repeating meeting needs at least 2 occurrences"))
	return rule


def weekday(by_day: dict):
	day = WEEKDAYS[by_day["day"]]
	return day(by_day["nthOfPeriod"]) if by_day.get("nthOfPeriod") else day


def to_ics_rrule(rule: dict, format_until) -> str:
	"""The rule as an iCalendar RRULE value, for the invite's calendar file.

	`format_until` turns the local until date-time into the form DTSTART uses (UTC there).
	"""
	parts = [f"FREQ={rule['frequency'].upper()}", f"INTERVAL={int(rule.get('interval') or 1)}"]
	if rule.get("byDay"):
		days = [f"{d.get('nthOfPeriod') or ''}{d['day'].upper()}" for d in rule["byDay"]]
		parts.append("BYDAY=" + ",".join(days))
	if rule.get("byMonthDay"):
		parts.append("BYMONTHDAY=" + ",".join(str(d) for d in rule["byMonthDay"]))
	if rule.get("until"):
		parts.append("UNTIL=" + format_until(get_datetime(rule["until"].rstrip("Z"))))
	elif rule.get("count"):
		parts.append(f"COUNT={int(rule['count'])}")
	return ";".join(parts)


def extend_series():
	"""Scheduled daily."""
	MeetingSeries.extend_all()


def repeat_message(rule: dict) -> str:
	"""Plain-English summary, worded like Frappe Calendar: "Every week on Mon, Wed, 10 times"."""
	unit = {"daily": "day", "weekly": "week", "monthly": "month", "yearly": "year"}[rule["frequency"]]
	interval = int(rule.get("interval") or 1)
	message = f"Every {unit}" if interval == 1 else f"Every {interval} {unit}s"
	if rule.get("byDay"):
		names = {"mo": "Mon", "tu": "Tue", "we": "Wed", "th": "Thu", "fr": "Fri", "sa": "Sat", "su": "Sun"}
		message += " on " + ", ".join(names[d["day"]] for d in rule["byDay"])
	if rule.get("until"):
		return f"{message} until {get_datetime(rule['until'].rstrip('Z')).strftime('%b %d, %Y')}"
	if rule.get("count"):
		return f"{message}, {int(rule['count'])} times"
	return message
